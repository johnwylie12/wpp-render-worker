#!/usr/bin/env python3
"""run_intel990.py — backfill account_intel_findings from filed 990s.

  python run_intel990.py --account 15589      one account, prints what it wrote
  python run_intel990.py --run [--limit N]    the backfill + report
  python run_intel990.py --dry-run --limit N  parse and count, write nothing

POPULATION: every account with account_990_status.propublica_url, joined to its
object_ids in cohort_990_resolution. An account with a URL but no object_id
cannot be parsed and is counted as a zero-findings account, because that is the
honest answer to "does this extend across the book".

SUPERSESSION. Filings are inserted NEWEST FIRST per claim_key, each older row
carrying superseded_by -> the next newer row's id. Only the newest is ever live,
which is what aif_live_claim_idx enforces. The old row is never deleted: the
history IS the trend. When a genuinely newer filing arrives on a later run the
live row is vacated first (pointed at itself) so the partial unique index frees
the slot, then repointed at the new row.

IDEMPOTENCY. A row is identified by (account_id, claim_key, published_on). The
unique index does NOT cover suppressed rows, so officer compensation and
Schedule L would duplicate on every re-run if this were left to the database.
It is not: existing keys are loaded up front and skipped.
"""
import argparse
import os
import statistics
import sys
import concurrent.futures as cf

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extract990                                   # noqa: E402  (GT data-lake fetch)
from intel990 import parse_intel, findings_for, trend_findings   # noqa: E402
from ntee_labels import label_for                   # noqa: E402

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = (os.environ.get("WPP_SB_SECRET")
               or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")).strip()
REST = SUPABASE_URL + "/rest/v1/"


def _h(extra=None):
    h = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
         "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h


def rget(cx, path):
    r = cx.get(REST + path, headers=_h())
    r.raise_for_status()
    return r.json()


def page_all(cx, path, step=1000):
    """PostgREST caps a response; page until short."""
    out, off = [], 0
    while True:
        rows = rget(cx, "%s&limit=%d&offset=%d" % (path, step, off))
        out.extend(rows)
        if len(rows) < step:
            return out
        off += step


def load_population(cx, only=None):
    """-> {account_id: {"ein":…, "ntee":…, "filings":[{object_id, tax_period}]}}"""
    if only:
        stat = rget(cx, "account_990_status?select=account_id,propublica_url"
                        "&account_id=eq.%d&propublica_url=not.is.null" % only)
    else:
        stat = page_all(cx, "account_990_status?select=account_id,propublica_url"
                            "&propublica_url=not.is.null&order=account_id")
    pop = {r["account_id"]: {"ein": None, "ntee": None, "filings": []} for r in stat}
    if not pop:
        return pop
    ids = sorted(pop)
    for i in range(0, len(ids), 400):
        chunk = ",".join(str(x) for x in ids[i:i + 400])
        for r in page_all(cx, "cohort_990_resolution?select=account_id,ein,object_id,"
                              "tax_period&object_id=not.is.null&account_id=in.(%s)" % chunk):
            a = pop.get(r["account_id"])
            if a is None:
                continue
            a["ein"] = a["ein"] or r.get("ein")
            a["filings"].append({"object_id": str(r["object_id"]),
                                 "tax_period": str(r.get("tax_period") or "")})
    eins = sorted({v["ein"] for v in pop.values() if v.get("ein")})
    ntee = {}
    for i in range(0, len(eins), 400):
        chunk = ",".join("'%s'" % e for e in eins[i:i + 400])
        for r in page_all(cx, "nonprofit_index?select=ein,ntee&ein=in.(%s)" % chunk):
            if r.get("ntee"):
                ntee[r["ein"]] = r["ntee"]
    for v in pop.values():
        v["ntee"] = ntee.get(v["ein"])
    # Newest filing first — supersession depends on this order.
    for v in pop.values():
        v["filings"].sort(key=lambda f: f["tax_period"], reverse=True)
    return pop


def existing_keys(cx, account_id):
    rows = page_all(cx, "account_intel_findings?select=claim_key,published_on"
                        "&account_id=eq.%d" % account_id)
    return {(r["claim_key"], r["published_on"]) for r in rows}


def live_rows(cx, account_id):
    rows = page_all(cx, "account_intel_findings?select=id,claim_key,published_on"
                        "&account_id=eq.%d&superseded_by=is.null" % account_id)
    return {r["claim_key"]: r for r in rows if r.get("claim_key")}


def insert(cx, rows):
    if not rows:
        return []
    r = cx.post(REST + "account_intel_findings",
                headers=_h({"Prefer": "return=representation"}), json=rows)
    if r.status_code >= 300:
        raise RuntimeError("insert failed %s: %s" % (r.status_code, r.text[:400]))
    return r.json()


def patch(cx, fid, fields):
    r = cx.patch(REST + "account_intel_findings?id=eq.%d" % fid,
                 headers=_h({"Prefer": "return=minimal"}), json=fields)
    r.raise_for_status()


def build_for_account(acct, meta, timeout=40):
    """Fetch + parse every filing. Returns (rows_by_claim, notes). Never raises."""
    parsed, notes = [], []
    for f in meta["filings"]:
        try:
            xb = extract990.fetch_xml(f["object_id"], timeout=timeout)
        except Exception as e:
            notes.append("fetch %s: %s" % (f["object_id"], type(e).__name__))
            continue
        try:
            p = parse_intel(xb)
        except Exception as e:
            notes.append("parse %s: %s" % (f["object_id"], type(e).__name__))
            continue
        if not p or not p.get("period_end"):
            notes.append("no IRS990 body in %s" % f["object_id"])
            continue
        p["_object_id"] = f["object_id"]
        parsed.append(p)
    if not parsed:
        return {}, notes
    parsed.sort(key=lambda p: p["period_end"], reverse=True)   # newest first
    ein = (meta.get("ein") or parsed[0].get("ein") or "").replace("-", "")
    code3, label = label_for(meta.get("ntee"))

    by_claim = {}
    for i, p in enumerate(parsed):
        rows = findings_for(p, ein=ein, object_id=p["_object_id"],
                            # NTEE is a BMF classification, not a line on the
                            # return: carry it once, on the newest filing.
                            ntee=code3 if i == 0 else None, ntee_label=label)
        if i + 1 < len(parsed):
            rows += trend_findings(p, parsed[i + 1], ein=ein, object_id=p["_object_id"])
        for r in rows:
            r["account_id"] = acct
            by_claim.setdefault(r["claim_key"], []).append(r)
    for k in by_claim:                        # newest first within each claim
        by_claim[k].sort(key=lambda r: r["published_on"], reverse=True)
    return by_claim, notes


def write_account(cx, acct, by_claim):
    """Insert with the supersession chain. Returns rows written."""
    have = existing_keys(cx, acct)
    live = live_rows(cx, acct)
    written = 0
    for claim, rows in by_claim.items():
        rows = [r for r in rows if (r["claim_key"], r["published_on"]) not in have]
        if not rows:
            continue
        prev_id = None
        cur = live.get(claim)
        if cur and rows[0]["published_on"] > (cur["published_on"] or ""):
            # A genuinely newer filing. Vacate the live slot first (self-reference
            # makes the row non-live) so the partial unique index lets the insert
            # through, then repoint it at the new row.
            patch(cx, cur["id"], {"superseded_by": cur["id"]})
            prev_id = cur["id"]
        ins = insert(cx, rows)                       # newest first
        written += len(ins)
        for i, row in enumerate(ins):
            if i + 1 < len(ins):
                patch(cx, ins[i + 1]["id"], {"superseded_by": row["id"]})
        if prev_id is not None:
            patch(cx, prev_id, {"superseded_by": ins[0]["id"]})
        elif cur and ins:
            # Same or older period than the live row: keep the live row live.
            for row in ins:
                if row["published_on"] <= (cur["published_on"] or ""):
                    patch(cx, row["id"], {"superseded_by": cur["id"]})
    return written


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", type=int)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if not SUPABASE_URL or not SERVICE_KEY:
        sys.exit("SUPABASE_URL and a service key are required")

    with httpx.Client(timeout=120) as cx:
        pop = load_population(cx, only=a.account)
        ids = sorted(pop)
        if a.limit:
            ids = ids[:a.limit]
        print("[pop] %d accounts with a propublica_url; %d have at least one filing"
              % (len(ids), sum(1 for i in ids if pop[i]["filings"])), flush=True)

        per_account, zero, notes_all, total = {}, [], [], 0
        with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(build_for_account, i, pop[i]): i for i in ids}
            done = 0
            for fut in cf.as_completed(futs):
                acct = futs[fut]
                done += 1
                try:
                    by_claim, notes = fut.result()
                except Exception as e:
                    by_claim, notes = {}, ["build: %s" % e]
                n = sum(len(v) for v in by_claim.values())
                if notes:
                    notes_all.append((acct, notes))
                if not a.dry_run and by_claim:
                    try:
                        n = write_account(cx, acct, by_claim)
                    except Exception as e:
                        notes_all.append((acct, ["write: %s" % str(e)[:200]]))
                        n = 0
                per_account[acct] = n
                total += n
                if n == 0:
                    zero.append(acct)
                if done % 200 == 0:
                    print("  ...%d/%d accounts, %d findings" % (done, len(ids), total), flush=True)

        counts = sorted(per_account.values())
        nz = [c for c in counts if c]
        print("\n================ BACKFILL REPORT ================")
        print("accounts processed          %d" % len(ids))
        print("findings written            %d" % total)
        print("accounts with >=1 finding   %d" % len(nz))
        print("accounts with ZERO findings %d" % len(zero))
        if nz:
            print("findings per producing account   min %d / median %d / max %d"
                  % (min(nz), int(statistics.median(nz)), max(nz)))
        no_filing = sum(1 for i in ids if not pop[i]["filings"])
        print("  of the zero-finding accounts, %d had no object_id at all" % no_filing)
        print("=================================================")
        if a.account:
            for acct, notes in notes_all:
                print("note %s: %s" % (acct, "; ".join(notes)))


if __name__ == "__main__":
    main()
