#!/usr/bin/env python3
"""run990.py — 990 Part IX batch: fetch -> parse -> categorize -> write account_financials.

Driven off the job_990_runs / job_990_targets tables (populated by the app side). A queued
job_990_runs row triggers a batch: the ACCEPTANCE GATE runs first (Carmel CC must reproduce
addressable ~= $5.38M); only on pass does it process every target. Guardrails: exact-EIN via a
pre-resolved object_id (no fuzzy match), reconcile extracted revenue vs the BMF anchor (variance
> 15% -> caution_flag + needs_review, anchor NOT overwritten), idempotent (skip accounts that
already have a source_doc_type='990' row), needs_review on any resolve/parse failure (never
fabricate). Reversible: these are additive INSERTs (delete the batch's 990 rows to revert).

Invoked either by the worker poll loop (run_pending) or directly (python run990.py --run|--gate).
Self-contained: reads SUPABASE_URL + service key from env; talks Supabase REST via httpx.
"""
import os
import sys
import datetime
import traceback
import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extract990  # noqa: E402

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = (os.environ.get("WPP_SB_SECRET")
               or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")).strip()

CARMEL_OBJECT_ID = "202503179349302505"   # Carmel CC FY2024, EIN 56-0507966
CARMEL_EXPECTED_ADDRESSABLE = 5383682
GATE_TOLERANCE = 60000                    # ~1%
VARIANCE_PCT = 15.0                       # revenue reconcile threshold
HI_ADDR_PCT = 45.0                        # soft over-map flag for manual eyeball

def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _headers(extra=None):
    h = {"apikey": SERVICE_KEY, "Authorization": "Bearer " + SERVICE_KEY,
         "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    return h

def rget(cx, path):
    r = cx.get(SUPABASE_URL + "/rest/v1/" + path, headers=_headers())
    r.raise_for_status()
    return r.json()

def rpost(cx, table, obj, prefer="return=minimal"):
    r = cx.post(SUPABASE_URL + "/rest/v1/" + table, headers=_headers({"Prefer": prefer}), json=obj)
    r.raise_for_status()
    return r.json() if prefer.startswith("return=representation") else None

def rpatch(cx, table, filt, fields):
    r = cx.patch(SUPABASE_URL + "/rest/v1/" + table + "?" + filt,
                 headers=_headers({"Prefer": "return=minimal"}), json=fields)
    r.raise_for_status()

def load_rates(cx):
    rows = rget(cx, "spend_categories?select=id,era_savings_low,era_savings_high")
    rates = {}
    for r in rows:
        lo = r.get("era_savings_low")
        hi = r.get("era_savings_high")
        if lo is not None and hi is not None:
            rates[r["id"]] = (float(lo), float(hi))
    return rates

def upsert_990_status(cx, account_id, ein, status, filed_rev, filed_fy, note):
    exists = rget(cx, "account_990_status?account_id=eq.%d&select=account_id&limit=1" % account_id)
    # confidence + reviewed are NOT NULL on account_990_status.
    fields = {"ein": ein, "status": status, "filed_revenue": filed_rev,
              "filed_fy": filed_fy, "note": note[:500] if note else None,
              "confidence": "990-xml", "reviewed": False, "resolved_at": _now()}
    if exists:
        rpatch(cx, "account_990_status", "account_id=eq.%d" % account_id, fields)
    else:
        fields["account_id"] = account_id
        rpost(cx, "account_990_status", fields)

def has_990(cx, account_id):
    # Skip only when a REAL 990 extraction already exists (line_items present), not
    # the header-only revenue shell (line_items null) left by the original import —
    # otherwise ~752 buyer-gated bare shells get falsely skipped and never extract.
    rows = rget(cx, "account_financials?account_id=eq.%d&source_doc_type=eq.990&line_items=not.is.null&select=id&limit=1" % account_id)
    return bool(rows)

def gate(cx, rates):
    res = extract990.extract(CARMEL_OBJECT_ID, rates)
    ok = res["ok"] and abs(res["addressable"] - CARMEL_EXPECTED_ADDRESSABLE) <= GATE_TOLERANCE
    return {"passed": ok, "addressable": res["addressable"],
            "expected": CARMEL_EXPECTED_ADDRESSABLE, "revenue": res["total_revenue"],
            "opportunity_low": res["opportunity_low"], "opportunity_high": res["opportunity_high"],
            "reason": None if ok else (res["reason"] or "addressable_out_of_tolerance")}

def process_target(cx, t, rates):
    """Process one job_990_targets row. Returns a short result string."""
    aid = t["account_id"]
    ein = t.get("ein")
    anchor = t.get("anchor")
    if has_990(cx, aid):
        rpatch(cx, "job_990_targets", "account_id=eq.%d" % aid,
               {"done": True, "result": "skip_existing_990", "processed_at": _now()})
        return "skip_existing"

    res = extract990.extract(t["object_id"], rates)
    if not res["ok"]:
        upsert_990_status(cx, aid, ein, "needs_review", res.get("total_revenue"),
                          t.get("fiscal_year"), "990-xml: " + (res["reason"] or "unknown"))
        rpatch(cx, "job_990_targets", "account_id=eq.%d" % aid,
               {"done": True, "result": "needs_review:" + (res["reason"] or "unknown"),
                "processed_at": _now()})
        return "needs_review"

    rev = res["total_revenue"]
    variance = None
    if anchor and rev:
        variance = round(100.0 * abs(rev - float(anchor)) / float(anchor), 1)
    hi_addr = bool(rev and res["addressable"] and res["addressable"] / rev > HI_ADDR_PCT / 100.0)
    caution = (variance is not None and variance > VARIANCE_PCT) or hi_addr

    # additive insert; keep any prior rows non-primary first (safe even if none exist)
    rpatch(cx, "account_financials", "account_id=eq.%d" % aid, {"is_primary": False})
    row = {"account_id": aid, "fiscal_year": t.get("fiscal_year"), "source_doc_type": "990",
           "total_revenue": rev, "total_expenses": res["total_expenses"],
           "addressable_spend": res["addressable"], "opportunity_low": res["opportunity_low"],
           "opportunity_high": res["opportunity_high"], "currency": "USD",
           "line_items": res["line_items"], "is_primary": True, "updated_at": _now()}
    rpost(cx, "account_financials", row)

    note_bits = []
    if variance is not None and variance > VARIANCE_PCT:
        note_bits.append("revenue variance %.1f%% vs anchor" % variance)
    if hi_addr:
        note_bits.append("addressable %.0f%% of revenue (eyeball)" % (100.0 * res["addressable"] / rev))
    status = "needs_review" if caution else "loaded"
    if caution:
        rpatch(cx, "accounts", "id=eq.%d" % aid, {"caution_flag": True})
    upsert_990_status(cx, aid, ein, status, rev, t.get("fiscal_year"),
                      "990-xml extracted; " + ("; ".join(note_bits) if note_bits else "clean"))
    rpatch(cx, "job_990_targets", "account_id=eq.%d" % aid,
           {"done": True, "result": ("caution" if caution else "ok"), "processed_at": _now()})
    return "caution" if caution else "ok"

def run_batch(cx, run_id):
    rates = load_rates(cx)
    # ---- acceptance gate ----
    rpatch(cx, "job_990_runs", "id=eq.%d" % run_id, {"phase": "gate"})
    g = gate(cx, rates)
    rpatch(cx, "job_990_runs", "id=eq.%d" % run_id, {"gate": g})
    if not g["passed"]:
        rpatch(cx, "job_990_runs", "id=eq.%d" % run_id,
               {"status": "gate_failed", "phase": "gate",
                "note": "Carmel gate failed: %s (addr=%s)" % (g["reason"], g["addressable"]),
                "finished_at": _now()})
        return
    # ---- batch ----
    rpatch(cx, "job_990_runs", "id=eq.%d" % run_id, {"phase": "batch"})
    counts = {"ok": 0, "caution": 0, "needs_review": 0, "skip": 0}
    processed = 0
    while True:
        batch = rget(cx, "job_990_targets?done=eq.false&select=account_id,ein,object_id,fiscal_year,anchor"
                         "&order=anchor.desc.nullslast&limit=25")
        if not batch:
            break
        for t in batch:
            try:
                r = process_target(cx, t, rates)
            except Exception as e:
                r = "error"
                traceback.print_exc()
                rpatch(cx, "job_990_targets", "account_id=eq.%d" % t["account_id"],
                       {"done": True, "result": "error:" + type(e).__name__, "processed_at": _now()})
            processed += 1
            if r == "ok":
                counts["ok"] += 1
            elif r == "caution":
                counts["caution"] += 1
            elif r == "needs_review":
                counts["needs_review"] += 1
            elif r == "skip_existing":
                counts["skip"] += 1
        rpatch(cx, "job_990_runs", "id=eq.%d" % run_id,
               {"processed": processed, "needs_review": counts["needs_review"],
                "cautioned": counts["caution"]})
    rpatch(cx, "job_990_runs", "id=eq.%d" % run_id,
           {"status": "done", "phase": "done", "processed": processed,
            "needs_review": counts["needs_review"], "cautioned": counts["caution"],
            "note": "ok=%d caution=%d needs_review=%d skip=%d" % (
                counts["ok"], counts["caution"], counts["needs_review"], counts["skip"]),
            "finished_at": _now()})

def run_pending():
    """Called by the worker poll loop. Cheap no-op when nothing is queued."""
    if not (SUPABASE_URL and SERVICE_KEY):
        return False
    with httpx.Client(timeout=60.0) as cx:
        queued = rget(cx, "job_990_runs?status=eq.queued&select=id&order=id&limit=1")
        if not queued:
            return False
        run_id = queued[0]["id"]
        rpatch(cx, "job_990_runs", "id=eq.%d" % run_id, {"status": "running", "started_at": _now()})
        try:
            run_batch(cx, run_id)
        except Exception as e:
            traceback.print_exc()
            rpatch(cx, "job_990_runs", "id=eq.%d" % run_id,
                   {"status": "error", "note": "%s: %s" % (type(e).__name__, str(e))[:500],
                    "finished_at": _now()})
        return True

def main():
    if not (SUPABASE_URL and SERVICE_KEY):
        sys.exit("SUPABASE_URL and service key required")
    with httpx.Client(timeout=60.0) as cx:
        if "--gate" in sys.argv:
            print(gate(cx, load_rates(cx)))
            return
        # --run: create a run row and process immediately
        rpost(cx, "job_990_runs", {"status": "queued"})
    run_pending()

if __name__ == "__main__":
    main()
