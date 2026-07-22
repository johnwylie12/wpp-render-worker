#!/usr/bin/env python3
"""990 Part IX -> ERA category extractor (Python port of the enrich-990 categorizer).

This is the SAME Part IX -> ERA-category mapping the enrich-990 edge function uses
(TAG_MAP / KW / EXCLUDE_TAGS / KW_EXCLUDE), ported verbatim so the render worker
produces identical categorization. We do NOT rebuild the categorizer — we reuse
its mapping tables and rules.

Why the worker needs its own copy: ProPublica dropped object_id, so the edge
function can no longer resolve a filing's XML. The worker instead ingests the IRS
annual 990-XML bundles (disk + egress live on Railway) and parses Part IX directly
from that XML. The XML shape is identical to the {object_id}_public.xml the edge
function used, so the same regex-based extraction applies.

era_category_id values are the public.spend_categories primary keys (verified:
1=Insurance, 5=Office Supplies, 10=Marketing, 11=Professional Services,
12=Travel, 13=Food Services, 14=IT, 15=Telecom, 18=Cleaning, 21=Waste,
22=Utilities, 34=Operating Supply, ...), so a line item's era_category_id is
written straight into account_categories.spend_category_id.

Pure + deterministic (no I/O): unit-testable offline. `irs_index.py` / the driver
feed it XML strings.
"""
import re
from typing import Optional

# --- Part IX standard lines: XML group tag -> (spend_category_id, name) ---------
# Verbatim from enrich-990 TAG_MAP.
TAG_MAP: dict[str, tuple[int, str]] = {
    "FeesForServicesManagementGrp": (11, "Professional Services"),
    "FeesForServicesLegalGrp":      (11, "Professional Services"),
    "FeesForServicesAccountingGrp": (11, "Professional Services"),
    "FeesForServicesOtherGrp":      (11, "Professional Services"),
    "AdvertisingGrp":               (10, "Marketing Services"),
    "OfficeExpensesGrp":            (5,  "Office Supplies"),
    "InformationTechnologyGrp":     (14, "IT Hardware/Services"),
    "OccupancyGrp":                 (22, "Utilities"),
    "TravelGrp":                    (12, "Travel"),
    "InsuranceGrp":                 (1,  "Insurance"),
}

# Part IX lines that are direct personnel / non-addressable and excluded from spend.
EXCLUDE_TAGS: list[str] = [
    "CompensationOfCurrentOfficersGrp", "CompensationNotProvidedGrp", "OtherSalariesAndWagesGrp",
    "PensionPlanContributionsGrp", "OtherEmployeeBenefitsGrp", "PayrollTaxesGrp",
    "InterestGrp", "DepreciationDepletionGrp", "PaymentsToAffiliatesGrp",
    "GrantsToDomesticOrgsGrp", "GrantsToDomesticIndividualsGrp",
]

# Free-text (line 24 "Other expenses") description -> (spend_category_id, name).
# Verbatim from enrich-990 KW, order matters (first match wins).
KW: list[tuple[re.Pattern, int, str]] = [
    (re.compile(r"repair|mainten", re.I),                              19, "Maintenance"),
    (re.compile(r"ground|landscap|turf", re.I),                        20, "Grounds/Landscaping"),
    (re.compile(r"golf|pro ?shop|course|tennis|pool|racquet|recreation", re.I), 34, "Operating Supply"),
    (re.compile(r"food|dining|kitchen|restaurant|cater|beverage|banquet|\bbar\b|f&b", re.I), 13, "Food Services"),
    (re.compile(r"insurance", re.I),                                   1,  "Insurance"),
    (re.compile(r"telecom|telephone|communicat|internet|cable", re.I), 15, "Telecom"),
    (re.compile(r"utilit|electric|\bgas\b|water|sewer|energy|power", re.I), 22, "Utilities"),
    (re.compile(r"clean|janitor|housekeep|laundry", re.I),             18, "Cleaning Services"),
    (re.compile(r"waste|trash|refuse|garbage|recycl|disposal", re.I),  21, "Waste Management"),
    (re.compile(r"uniform|linen", re.I),                               39, "Uniforms"),
    (re.compile(r"security|guard", re.I),                              24, "Security Services"),
    (re.compile(r"pest|exterminat", re.I),                             25, "Pest Control"),
    (re.compile(r"freight|shipping|deliver|cartage", re.I),            26, "Freight (LTL/FTL)"),
    (re.compile(r"postage|mailing", re.I),                             7,  "Mail Services"),
    (re.compile(r"print|reprograph", re.I),                            6,  "Printing"),
    (re.compile(r"bank|merchant|credit ?card|processing fee|payment process", re.I), 3, "Banking Fees"),
    (re.compile(r"software|licens|saas|subscription", re.I),           16, "SaaS / Software"),
    (re.compile(r"profession|consult|legal|account|audit", re.I),      11, "Professional Services"),
    (re.compile(r"market|advertis|promot", re.I),                      10, "Marketing Services"),
    (re.compile(r"travel|lodging|conference|meeting|dues", re.I),      12, "Travel"),
    (re.compile(r"suppl(y|ies)|operating|equipment|\bmro\b", re.I),    34, "Operating Supply"),
    (re.compile(r"office", re.I),                                      5,  "Office Supplies"),
]
KW_EXCLUDE = re.compile(
    r"\btax|interest|deprecia|payroll|wage|salar|benefit|pension|scholar|grant|charit|donat|"
    r"bad debt|cost of goods|inventory|amortiz|licenses? and permit", re.I)


def grp_total(xml: str, tag: str) -> int:
    """First <TotalAmt> inside <tag>…</tag>. 0 when absent. Mirrors enrich-990 grpTotalA."""
    m = re.search(rf"<{tag}>[\s\S]*?<TotalAmt>(-?\d+)</TotalAmt>", xml, re.I)
    return int(m.group(1)) if m else 0


def tag1(xml: str, tag: str) -> Optional[str]:
    m = re.search(rf"<{tag}>([\s\S]*?)</{tag}>", xml, re.I)
    return m.group(1).strip() if m else None


def _int(xml: str, tag: str) -> Optional[int]:
    v = tag1(xml, tag)
    if v is None:
        return None
    try:
        return int(re.sub(r"[^\d-]", "", v))
    except ValueError:
        return None


def map_free_text(desc: str) -> tuple[Optional[int], Optional[str]]:
    """Line 24 free-text description -> (spend_category_id, name). Mirrors mapFreeText."""
    if KW_EXCLUDE.search(desc):
        return (None, None)
    for pat, cid, name in KW:
        if pat.search(desc):
            return (cid, name)
    return (None, None)


_OTHER_RE = re.compile(r"<OtherExpensesGrp>[\s\S]*?<Desc>(.*?)</Desc>[\s\S]*?<TotalAmt>(-?\d+)</TotalAmt>", re.I)


def extract_part_ix(xml: str) -> dict:
    """Parse an IRS 990 XML string into filed totals + ERA-mapped Part IX line items.

    Returns a dict with: ein, tax_year, total_revenue, total_expenses, line_items
    (each {label, amount, era_category_id, era_category_name, note}),
    addressable_spend, and officers/signing_officer (Part VII cross-check).
    """
    ein = tag1(xml, "EIN")
    tax_year = _int(xml, "TaxYr")
    total_revenue = _int(xml, "CYTotalRevenueAmt")
    total_expenses = _int(xml, "CYTotalExpensesAmt")

    items: list[dict] = []
    for tag, (cid, cname) in TAG_MAP.items():
        amt = grp_total(xml, tag)
        if amt > 0:
            items.append({"label": tag[:-3] if tag.endswith("Grp") else tag, "amount": amt,
                          "era_category_id": cid, "era_category_name": cname, "note": "Part IX standard line"})
    for tag in EXCLUDE_TAGS:
        amt = grp_total(xml, tag)
        if amt > 0:
            items.append({"label": tag[:-3] if tag.endswith("Grp") else tag, "amount": amt,
                          "era_category_id": None, "era_category_name": None, "note": "excluded per rules"})
    for m in _OTHER_RE.finditer(xml):
        desc = m.group(1).strip()
        amt = int(m.group(2))
        if amt <= 0:
            continue
        cid, cname = map_free_text(desc)
        items.append({"label": f"Other expenses - {desc}", "amount": amt,
                      "era_category_id": cid, "era_category_name": cname,
                      "note": "line 24 mapped by description" if cid else "line 24 unmapped"})

    addressable = sum(i["amount"] for i in items if i["era_category_id"])

    return {
        "ein": ein,
        "tax_year": tax_year,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "line_items": items,
        "addressable_spend": addressable,
        "officers": extract_officers(xml),
        "signing_officer": extract_signing_officer(xml),
    }


def category_rollups(line_items: list[dict]) -> list[dict]:
    """Roll mapped line items up to one row per spend_category_id (for account_categories).

    Returns [{spend_category_id, era_category_name, spend_amount}], highest first.
    """
    roll: dict[int, dict] = {}
    for it in line_items:
        cid = it.get("era_category_id")
        if not cid:
            continue
        r = roll.setdefault(cid, {"spend_category_id": cid, "era_category_name": it.get("era_category_name"), "spend_amount": 0})
        r["spend_amount"] += it.get("amount", 0)
    return sorted(roll.values(), key=lambda r: r["spend_amount"], reverse=True)


# --- Part VII officers + signing officer (buyer cross-check, second source) ------
_OFFICER_RE = re.compile(
    r"<Form990PartVIISectionAGrp>[\s\S]*?<PersonNm>(.*?)</PersonNm>[\s\S]*?<TitleTxt>(.*?)</TitleTxt>", re.I)


def extract_officers(xml: str) -> list[dict]:
    """Part VII Section A people: [{name, title}]. Best-effort, empty when absent."""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for m in _OFFICER_RE.finditer(xml):
        name = re.sub(r"\s+", " ", m.group(1)).strip()
        title = re.sub(r"\s+", " ", m.group(2)).strip()
        key = (name.lower(), title.lower())
        if name and key not in seen:
            seen.add(key)
            out.append({"name": name, "title": title})
    return out


def extract_signing_officer(xml: str) -> Optional[dict]:
    """The officer who signed the return (BusinessOfficerGrp) — a strong buyer signal."""
    blk = tag1(xml, "BusinessOfficerGrp")
    if not blk:
        return None
    name = tag1(blk, "PersonNm")
    title = tag1(blk, "PersonTitleTxt")
    if not name:
        return None
    return {"name": re.sub(r"\s+", " ", name).strip(),
            "title": re.sub(r"\s+", " ", title).strip() if title else None}
