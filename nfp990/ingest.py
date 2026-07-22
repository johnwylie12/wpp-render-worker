#!/usr/bin/env python3
"""nfp990/ingest.py — Light-route IRS 990 XML ingestion for WPP.

Flow:
  1. Download the IRS per-year INDEX CSVs (small) -> EIN -> OBJECT_ID map.
  2. For each TARGET EIN (buyer-gated set), pick its most recent full-990 filing.
  3. Fetch ONLY those XMLs from the IRS S3 bucket (irs-form-990).
  4. If an EIN isn't in the index or its object fetch fails -> automatic fallback
     to the year's full ZIP bundle (download once, serve many misses from it).
  5. Parse Part IX functional expenses, hand line items to the EXISTING ERA
     categorizer (part_ix.py), write account_financials + account_categories, and
     record the fetch in nfp990_xml_index (idempotent).

This is the INGESTION/INDEX layer (increment 2) + driver (increment 3). It does
NOT re-implement the categorizer: era_categorize() reuses part_ix.TAG_MAP /
part_ix.map_free_text / part_ix.category_rollups. The DB writes live in db.py.

Run on the Railway worker (disk + egress live there). Python 3.10+, requests, lxml.
    python -m nfp990.ingest --limit 25         # top-25-by-revenue buyer-gated
    python -m nfp990.ingest --smoke            # the 3 spot-check EINs
    python -m nfp990.ingest --dry-run --limit 5  # fetch+parse+categorize, NO writes
"""
from __future__ import annotations
import csv
import io
import os
import sys
import time
import zipfile
import logging
import argparse
from dataclasses import dataclass
from typing import Iterable, Optional

import requests
from requests.adapters import HTTPAdapter, Retry
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from part_ix import TAG_MAP, map_free_text, category_rollups, extract_officers, extract_signing_officer  # noqa: E402
import db  # noqa: E402

log = logging.getLogger("nfp990_ingest")

# ----------------------------------------------------------------------------
# Config — VERIFY these base URLs against the current IRS layout before a full run.
# ----------------------------------------------------------------------------
YEARS = [2024, 2023, 2022]            # newest first; we take the most recent filing per EIN
S3_XML_BASE = "https://s3.amazonaws.com/irs-form-990/{object_id}_public.xml"
IRS_XML_ALT = "https://apps.irs.gov/pub/epostcard/990/xml/{year}/{object_id}_public.xml"
INDEX_URLS = [                        # try in order; first that returns 200 wins
    "https://s3.amazonaws.com/irs-form-990/index_{year}.csv",
    "https://apps.irs.gov/pub/epostcard/990/xml/{year}/index_{year}.csv",
]
ZIP_URL = "https://apps.irs.gov/pub/epostcard/990/xml/{year}/download990xml_{year}_{part}.zip"

# Full-990 only carries Part IX. 990-EZ has no Part IX; 990-PF uses a different
# expense structure -> flag/skip, don't force.
FULL_990_TYPES = {"990"}


def _session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=5, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=32))
    s.headers.update({"User-Agent": "WPP-990-ingest/1.0"})
    return s


HTTP = _session()


# ----------------------------------------------------------------------------
# 1. Index -> EIN -> OBJECT_ID
# ----------------------------------------------------------------------------
@dataclass
class Filing:
    ein: str
    object_id: str
    tax_period: str          # YYYYMM
    return_type: str
    name: str
    year: int


def download_year_index(year: int) -> list[Filing]:
    for tmpl in INDEX_URLS:
        url = tmpl.format(year=year)
        try:
            r = HTTP.get(url, timeout=120)
            if r.status_code != 200 or not r.content:
                continue
        except requests.RequestException as e:
            log.warning("index %s fetch error: %s", url, e)
            continue
        rows: list[Filing] = []
        reader = csv.DictReader(io.StringIO(r.content.decode("utf-8", "replace")))
        for row in reader:
            ein = "".join(ch for ch in (row.get("EIN") or "") if ch.isdigit()).zfill(9)
            oid = (row.get("OBJECT_ID") or "").strip()
            if not ein or not oid:
                continue
            rows.append(Filing(ein=ein, object_id=oid,
                               tax_period=(row.get("TAX_PERIOD") or "").strip(),
                               return_type=(row.get("RETURN_TYPE") or "").strip(),
                               name=(row.get("TAXPAYER_NAME") or "").strip(), year=year))
        log.info("index %s: %d filings", year, len(rows))
        return rows
    log.error("no index available for %s", year)
    return []


def build_target_object_map(target_eins: Iterable[str], years: list[int] = YEARS) -> dict[str, Filing]:
    """For each target EIN, its most recent FULL-990 filing across `years`."""
    targets = {e.strip().zfill(9) for e in target_eins}
    best: dict[str, Filing] = {}
    for year in years:                       # newest first
        idx = download_year_index(year)
        by_ein: dict[str, list[Filing]] = {}
        for f in idx:
            if f.ein in targets:
                by_ein.setdefault(f.ein, []).append(f)
        for ein, filings in by_ein.items():
            if ein in best:
                continue                      # already have a newer year
            full = [f for f in filings if f.return_type in FULL_990_TYPES]
            pick = max(full or filings, key=lambda f: f.tax_period)
            best[ein] = pick
    missing = targets - best.keys()
    log.info("target map: %d/%d EINs located, %d missing (no e-file on record)",
             len(best), len(targets), len(missing))
    return best


# ----------------------------------------------------------------------------
# 2. Fetch one XML: S3 -> IRS alt -> ZIP fallback
# ----------------------------------------------------------------------------
_zip_cache: dict[int, list[zipfile.ZipFile]] = {}


def _load_year_zips(year: int) -> list[zipfile.ZipFile]:
    if year in _zip_cache:
        return _zip_cache[year]
    zips: list[zipfile.ZipFile] = []
    part = 1
    while True:
        url = ZIP_URL.format(year=year, part=part)
        try:
            r = HTTP.get(url, timeout=600)
        except requests.RequestException:
            break
        if r.status_code != 200 or not r.content:
            break
        zips.append(zipfile.ZipFile(io.BytesIO(r.content)))
        log.info("loaded ZIP %s part %d (%d bytes)", year, part, len(r.content))
        part += 1
    _zip_cache[year] = zips
    return zips


def fetch_xml(f: Filing) -> Optional[bytes]:
    for tmpl in (S3_XML_BASE, IRS_XML_ALT):
        url = tmpl.format(object_id=f.object_id, year=f.year)
        try:
            r = HTTP.get(url, timeout=60)
            if r.status_code == 200 and r.content:
                return r.content
        except requests.RequestException as e:
            log.warning("xml fetch %s: %s", url, e)
    for z in _load_year_zips(f.year):        # ZIP fallback
        try:
            return z.read(f"{f.object_id}_public.xml")
        except KeyError:
            continue
    log.error("could not fetch xml for EIN %s object %s", f.ein, f.object_id)
    return None


# ----------------------------------------------------------------------------
# 3. Parse Part IX functional expenses (namespace-aware, lxml)
# ----------------------------------------------------------------------------
NS = {"irs": "http://www.irs.gov/efile"}

# XML group tag -> internal key. Standard-line tags match part_ix.TAG_MAP exactly,
# so era_categorize can look them up directly.
PARTIX_ELEMENTS = {
    "GrantsToDomesticOrgsGrp": "grants_gov",
    "GrantsToDomesticIndividualsGrp": "grants_indiv",
    "BenefitsToMembersGrp": "benefits_members",
    "CompCurrentOfcrDirectorsGrp": "comp_officers",
    "CompDisqualPersonsGrp": "comp_disqualified",
    "OtherSalariesAndWagesGrp": "other_salaries",
    "PensionPlanContributionsGrp": "pension",
    "OtherEmployeeBenefitsGrp": "other_benefits",
    "PayrollTaxesGrp": "payroll_taxes",
    "FeesForServicesManagementGrp": "fees_management",
    "FeesForServicesLegalGrp": "fees_legal",
    "FeesForServicesAccountingGrp": "fees_accounting",
    "FeesForServicesLobbyingGrp": "fees_lobbying",
    "FeesForServicesProfFundraisingGrp": "fees_fundraising",
    "FeesForServicesInvstMgmntFeesGrp": "fees_investment",
    "FeesForServicesOtherGrp": "fees_other",
    "AdvertisingGrp": "advertising",
    "OfficeExpensesGrp": "office_expenses",
    "InformationTechnologyGrp": "information_technology",
    "RoyaltiesGrp": "royalties",
    "OccupancyGrp": "occupancy",
    "TravelGrp": "travel",
    "TravelEntrtnmntPublicOfficialsGrp": "travel_officials",
    "ConferencesMeetingsGrp": "conferences",
    "InterestGrp": "interest",
    "PaymentsToAffiliatesGrp": "payments_affiliates",
    "DepreciationDepletionGrp": "depreciation",
    "InsuranceGrp": "insurance",
}
# internal key -> XML tag (for era_categorize to reach part_ix.TAG_MAP, keyed by tag).
KEY_TO_TAG = {v: k for k, v in PARTIX_ELEMENTS.items()}


def _amt(el) -> int:
    t = el.find("irs:TotalAmt", NS)
    if t is None or t.text is None:
        return 0
    try:
        return int(float(t.text))
    except ValueError:
        return 0


def _txt(node, path):
    el = node.find(path, NS)
    return el.text.strip() if el is not None and el.text else None


def _money(node, path) -> Optional[int]:
    v = _txt(node, path)
    if v is None:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def parse_part_ix(xml_bytes: bytes) -> dict:
    """Filed totals + raw Part IX amounts + line-24 free text. Empty line_items =>
    not a full 990 (EZ/PF) -> caller flags, does not build."""
    root = etree.fromstring(xml_bytes)
    result: dict = {"line_items": {}, "other_expenses": [], "total_functional_expenses": 0,
                    "tax_year": None, "return_type": None, "ein": None,
                    "total_revenue": None, "total_expenses": None}

    hdr = root.find(".//irs:ReturnHeader", NS)
    if hdr is not None:
        result["tax_year"] = _txt(hdr, "irs:TaxYr")
        result["return_type"] = _txt(hdr, ".//irs:ReturnTypeCd")
    fein = root.find(".//irs:Filer/irs:EIN", NS)
    if fein is not None and fein.text:
        result["ein"] = "".join(ch for ch in fein.text if ch.isdigit()).zfill(9)

    irs990 = root.find(".//irs:ReturnData/irs:IRS990", NS)
    if irs990 is None:
        return result  # 990-EZ / 990-PF / malformed -> no Part IX

    result["total_revenue"] = _money(irs990, "irs:CYTotalRevenueAmt")
    result["total_expenses"] = _money(irs990, "irs:CYTotalExpensesAmt")

    for tag, key in PARTIX_ELEMENTS.items():
        el = irs990.find(f"irs:{tag}", NS)
        if el is not None:
            result["line_items"][key] = _amt(el)
    for grp in irs990.findall("irs:OtherExpensesGrp", NS):
        desc = _txt(grp, "irs:Desc") or ""
        result["other_expenses"].append((desc, _amt(grp)))
    tfe = irs990.find("irs:TotalFunctionalExpensesGrp", NS)
    if tfe is not None:
        result["total_functional_expenses"] = _amt(tfe)
    return result


# ----------------------------------------------------------------------------
# 3b. ERA categorize — REUSES the existing categorizer (part_ix.TAG_MAP / map_free_text).
# ----------------------------------------------------------------------------
def era_categorize(line_items: dict[str, int], other_expenses: list[tuple[str, int]]) -> list[dict]:
    """Map lxml-parsed Part IX amounts to ERA categories using the SAME rules as the
    enrich-990 categorizer. Standard lines -> TAG_MAP by their XML tag; line-24 free
    text -> map_free_text. Output shape matches part_ix.extract_part_ix line items."""
    items: list[dict] = []
    for key, amt in line_items.items():
        if not amt or amt <= 0:
            continue
        tag = KEY_TO_TAG.get(key, "")
        mapped = TAG_MAP.get(tag)
        if mapped:
            cid, name = mapped
            items.append({"label": key, "amount": amt, "era_category_id": cid,
                          "era_category_name": name, "note": "Part IX standard line"})
        else:
            items.append({"label": key, "amount": amt, "era_category_id": None,
                          "era_category_name": None, "note": "excluded/unmapped Part IX line"})
    for desc, amt in other_expenses:
        if not amt or amt <= 0:
            continue
        cid, name = map_free_text(desc)
        items.append({"label": f"Other expenses - {desc}", "amount": amt, "era_category_id": cid,
                      "era_category_name": name,
                      "note": "line 24 mapped by description" if cid else "line 24 unmapped"})
    return items


# ----------------------------------------------------------------------------
# 4. Driver — ties it together (idempotent)
# ----------------------------------------------------------------------------
def ingest(targets: list[dict], dry_run: bool = False) -> dict:
    """targets: [{account_id, ein, name, filed_revenue}] (buyer-gated, revenue desc)."""
    stats = {"located": 0, "fetched": 0, "part_ix_ok": 0, "no_part_ix": 0,
             "skipped_done": 0, "written": 0, "failed": 0}
    ein_to_acct = {t["ein"].strip().zfill(9): t for t in targets if t.get("ein")}
    obj_map = build_target_object_map(list(ein_to_acct.keys()))
    stats["located"] = len(obj_map)

    cx = None if dry_run else db.client()
    try:
        for ein, filing in obj_map.items():
            tgt = ein_to_acct[ein]
            account_id = tgt["account_id"]

            if not dry_run and db.has_object(cx, ein, filing.object_id):
                stats["skipped_done"] += 1
                continue

            xml = fetch_xml(filing)
            if xml is None:
                stats["failed"] += 1
                continue
            stats["fetched"] += 1

            parsed = parse_part_ix(xml)
            if not parsed["line_items"]:
                stats["no_part_ix"] += 1
                log.info("EIN %s (%s): no Part IX (return_type=%s) -> flag EZ/PF, not built",
                         ein, tgt["name"], parsed.get("return_type"))
                continue
            stats["part_ix_ok"] += 1

            line_items = era_categorize(parsed["line_items"], parsed["other_expenses"])
            addressable = sum(i["amount"] for i in line_items if i["era_category_id"])
            rollups = category_rollups(line_items)
            fy = int(parsed["tax_year"]) if parsed.get("tax_year") and str(parsed["tax_year"]).isdigit() else None
            signer = extract_signing_officer(xml.decode("utf-8", "replace"))

            if dry_run:
                log.info("[dry] %s (%s) FY%s: addressable=$%s, %d categories, signer=%s",
                         tgt["name"], ein, fy, f"{addressable:,}", len(rollups),
                         signer["name"] if signer else "-")
                stats["written"] += 1
                continue

            db.write_account_financials(cx, account_id=account_id, fiscal_year=fy,
                                        total_revenue=parsed["total_revenue"],
                                        total_expenses=parsed["total_expenses"],
                                        addressable_spend=addressable, line_items=line_items)
            db.write_account_categories(cx, account_id=account_id, rollups=rollups,
                                        fiscal_year=fy, object_id=filing.object_id)
            db.upsert_xml_index(cx, ein=ein, object_id=filing.object_id, tax_period=filing.tax_period,
                                return_type=filing.return_type,
                                xml_url=S3_XML_BASE.format(object_id=filing.object_id, year=filing.year))
            stats["written"] += 1
            log.info("wrote %s (%s) FY%s: addressable=$%s, %d categories, signer=%s",
                     tgt["name"], ein, fy, f"{addressable:,}", len(rollups),
                     signer["name"] if signer else "-")
            time.sleep(0)
    finally:
        if cx is not None:
            cx.close()

    log.info("ingest complete: %s", stats)
    return stats


SMOKE_TARGETS = [
    {"account_id": 13515, "ein": "237825575", "name": "National Philanthropic Trust", "filed_revenue": 17794939562},
    {"account_id": 14129, "ein": "832671600", "name": "Beth Israel Lahey Health", "filed_revenue": 876101442},
    {"account_id": 13628, "ein": "592174510", "name": "Food For The Poor", "filed_revenue": 412105034},  # EIN corrected
]


def main(argv=None):
    ap = argparse.ArgumentParser(description="IRS 990 Part IX -> ERA ingestion")
    ap.add_argument("--limit", type=int, default=None, help="top-N buyer-gated accounts by revenue")
    ap.add_argument("--smoke", action="store_true", help="run the 3 spot-check EINs")
    ap.add_argument("--dry-run", action="store_true", help="fetch+parse+categorize, no DB writes")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.smoke:
        targets = SMOKE_TARGETS
    else:
        with db.client() as cx:
            targets = db.get_targets(cx, limit=args.limit)
        log.info("pulled %d buyer-gated targets", len(targets))
    print(ingest(targets, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
