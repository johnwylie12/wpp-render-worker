#!/usr/bin/env python3
"""intel990.py — deep-parse an IRS 990 e-file XML into account_intel_findings rows.

PURE. No network, no DB. `parse_intel(xml_bytes)` returns what the filing says;
`findings_for(...)` turns that into rows. Fetching reuses extract990.fetch_xml —
the GivingTuesday 990 Data Lake, keyed by object_id (the AWS irs-form-990 bucket
is dead, and apps.irs.gov is not reachable from the worker).

NO MODEL ANYWHERE IN THIS FILE. Every value below is a numbered line on a filed
return. No model means no fabrication, which is the whole point of doing this
layer before the AI pass.

CITATION vs LOCATOR. source_url is the ProPublica organization page: a CFO can
open it and see their own return, which is the only test a citation has to pass.
The object_id is a machine locator and lives in `detail`.

published_on is the filing's TAX PERIOD END, never the fetch date. A return filed
in 2025 covering FY2024 is dated 2025-06-30 because that is the period it
describes. Dating it to the fetch is how a stale claim looks fresh, which is the
defect this whole programme exists to prevent.

CLEARANCE (LAW 15.4). Officer compensation and Schedule L related-party
transactions are written suppressed=true, outreach_safe=false, printable=false.
They are among the most useful things to know before a call and the most
damaging things to put in a letter. "Your Form 5500 shows the schedule renews in
March" is helpful; "we noticed your broker earned $84,000" is a threat.
"""
import re
import xml.etree.ElementTree as ET

# The ten values account_intel_findings.kind actually accepts. The original
# ticket used a different vocabulary; the table wins.
KIND_COST, KIND_OPS, KIND_SCALE = "cost_program", "operations", "scale"
KIND_CONTRACT, KIND_PERSON = "contract", "person"

PP_ORG = "https://projects.propublica.org/nonprofits/organizations/{ein}"
PUBLISHER = "IRS Form 990 (via ProPublica Nonprofit Explorer)"

# Titles that are governance, not management. A 990 Part VII lists every trustee,
# so an unfiltered pass produces ~50 rows an operator will never read AND collides
# on claim_key (48 people all slugging to officer:board_member). Anyone actually
# PAID is kept regardless of title — payment is what makes them interesting.
# Prefix-matched, not exact: the titles in the wild are "VICE CHAIR BUILDING",
# "BOARD MEMBER (THRU 6/4/2025)", "IMMEDIATE PAST BOARD CHAIR". An anchored
# exact match keeps 8 unpaid vice-chairs while dropping 40 unpaid board members,
# which is an arbitrary line to draw through the same board.
GOVERNANCE_RE = re.compile(
    r"^(board\s+member|board\s+chair|vice\s+chair|chair(man|person|woman)?|"
    r"secretary|treasurer|trustee|director|immediate\s+past|member)\b", re.I)


def _local(tag):
    return tag.split("}", 1)[-1]


def _txt(root, name):
    for el in root.iter():
        if _local(el.tag) == name and el.text and el.text.strip():
            return el.text.strip()
    return None


def _int(root, name):
    v = _txt(root, name)
    if v is None:
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _grp(root, name):
    for el in root.iter():
        if _local(el.tag) == name:
            return {_local(c.tag): (c.text or "").strip() for c in el}
    return {}


def _grp_int(root, name, field="TotalAmt"):
    g = _grp(root, name)
    try:
        return int(g[field])
    except (KeyError, ValueError, TypeError):
        return None


# The SAME role is spelled differently from year to year on the same return:
# this org filed "CHIEF EXECUTIVE OFFICER" for FY2024 and "CEO" for FY2025. Left
# alone that yields officer:chief_executive_officer AND officer:ceo — two live
# claims for one chair, which is precisely the two-live-truths the claim_key and
# its unique index exist to prevent. Canonicalise before slugging.
ROLE_ALIASES = {
    "ceo": "ceo", "chief executive officer": "ceo", "executive director": "ceo",
    "president and ceo": "ceo", "president ceo": "ceo", "president": "ceo",
    "cfo": "cfo", "chief financial officer": "cfo", "director of finance": "cfo",
    "vp finance": "cfo", "vice president of finance": "cfo",
    "coo": "coo", "chief operating officer": "coo",
    "cio": "cio", "chief information officer": "cio",
    "cto": "cto", "chief technology officer": "cto",
    "chro": "chro", "chief human resources officer": "chro",
    "chief program officer": "chief_program_officer",
    "chief philanthropy officer": "chief_philanthropy_officer",
    "chief development officer": "chief_development_officer",
    "chief medical officer": "chief_medical_officer",
    "chief advancement officer": "chief_advancement_officer",
    "chief administrative officer": "chief_administrative_officer",
}


def role_slug(title):
    """'CHIEF EXECUTIVE OFFICER' and 'CEO' -> 'ceo'. Parentheticals dropped so
    'BOARD MEMBER (THRU 6/4/2025)' and 'BOARD MEMBER' are ONE role, not two."""
    t = re.sub(r"\(.*?\)", " ", title or "")
    t = re.sub(r"[^A-Za-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    t = re.sub(r"^(the|interim|acting|former)\s+", "", t)
    if t in ROLE_ALIASES:
        return ROLE_ALIASES[t]
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_") or "unknown"


def parse_intel(xml_bytes):
    """Everything this ticket extracts, straight off the return. Returns None when
    the document carries no IRS990 body (a 990-EZ/PF or a malformed file)."""
    root = ET.fromstring(xml_bytes)
    if not any(_local(e.tag) == "IRS990" for e in root.iter()):
        return None

    period_end = _txt(root, "TaxPeriodEndDt")
    officers = []
    for el in root.iter():
        if _local(el.tag) != "Form990PartVIISectionAGrp":
            continue
        d = {_local(c.tag): (c.text or "").strip() for c in el}
        name, title = d.get("PersonNm"), d.get("TitleTxt")
        if not name or not title:
            continue
        try:
            comp = int(d.get("ReportableCompFromOrgAmt") or 0)
        except ValueError:
            comp = 0
        clean_title = re.sub(r"\(.*?\)", " ", title).strip()
        if comp <= 0 and GOVERNANCE_RE.match(clean_title):
            continue                      # unpaid trustee — governance, not management
        officers.append({"name": name.strip(), "title": clean_title,
                         "role": role_slug(title), "comp": comp})
    # One row per role. Two people sharing a role slug: the paid one wins, so the
    # claim_key stays unique and the kept row is the one an operator would call.
    by_role = {}
    for o in sorted(officers, key=lambda x: -x["comp"]):
        by_role.setdefault(o["role"], o)

    tot_exp = _int(root, "CYTotalExpensesAmt")
    salaries = _grp_int(root, "OtherSalariesAndWagesGrp")
    return {
        "ein": _txt(root, "EIN"),
        "tax_year": _int(root, "TaxYr"),
        "period_begin": _txt(root, "TaxPeriodBeginDt"),
        "period_end": period_end,
        "fy_end_month": int(period_end[5:7]) if period_end else None,
        "total_revenue": _int(root, "CYTotalRevenueAmt"),
        "total_expenses": tot_exp,
        "program_revenue": _int(root, "CYProgramServiceRevenueAmt"),
        "contributions": _int(root, "CYContributionsGrantsAmt"),
        "grants_paid": _int(root, "CYGrantsAndSimilarPaidAmt"),
        "salaries": salaries,
        "officer_comp_total": _grp_int(root, "CompCurrentOfcrDirectorsGrp"),
        "rental_gross": _grp_int(root, "GrossRentsGrp", "RealAmt"),
        "rental_net": _grp_int(root, "NetRentalIncomeOrLossGrp", "TotalRevenueColumnAmt"),
        "assets": _int(root, "TotalAssetsEOYAmt"),
        "liabilities": _int(root, "TotalLiabilitiesEOYAmt"),
        "net_assets": _int(root, "NetAssetsOrFundBalancesEOYAmt"),
        "tax_exempt_bonds": (_txt(root, "TaxExemptBondsInd") or "").lower() in ("true", "1"),
        "schedule_l": any(_local(e.tag) == "IRS990ScheduleL" for e in root.iter()),
        "officers": list(by_role.values()),
    }


MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def _usd(n):
    return "${:,}".format(int(n))


def _row(kind, claim_key, headline, detail, *, ein, object_id, period_end,
         suppressed=False, reason=None, category_hint=None):
    """One account_intel_findings row. evidence_state/source_tier/published_on are
    fixed together because aif_fact_needs_grade_chk rejects a 'fact' that is not
    tier A/B AND dated — a fact you cannot date is not a fact."""
    return {
        "kind": kind,
        "headline": headline[:500],
        "detail": (detail or "") + (" | IRS e-file object_id %s" % object_id),
        "source_url": PP_ORG.format(ein=ein),
        "source_publisher": PUBLISHER,
        "published_on": period_end,
        "self_published": False,
        "confidence": "confirmed",
        "evidence_state": "fact",
        "source_tier": "A",
        "category_hint": category_hint,
        "claim_key": claim_key,
        "printable": not suppressed,
        "outreach_safe": not suppressed,
        "suppressed": suppressed,
        "suppress_reason": reason,
    }


SUPPRESS_COMP = ("LAW 15.4 — individual compensation. Useful before a call, a "
                 "threat in a letter. Never printed, never sent.")
SUPPRESS_SCHED_L = ("LAW 15.4 — Schedule L related-party transactions. Naming a "
                    "prospect's insider dealings in outreach loses the meeting.")


def findings_for(parsed, *, ein, object_id, ntee=None, ntee_label=None):
    """parsed -> the rows for ONE filing. Trend rows are added by the caller,
    which is the only place that can see two filings at once."""
    p, out = parsed, []
    pe = p["period_end"]
    add = lambda *a, **k: out.append(_row(*a, ein=ein, object_id=object_id, period_end=pe, **k))

    for o in p["officers"]:
        add(KIND_PERSON, "officer:%s" % o["role"],
            "%s is %s" % (o["name"], o["title"]),
            "Form 990 Part VII, tax period ending %s." % pe)
        if o["comp"] > 0:
            add(KIND_PERSON, "officer_comp:%s" % o["role"],
                "%s (%s) reportable compensation %s" % (o["name"], o["title"], _usd(o["comp"])),
                "Form 990 Part VII reportable compensation from the organization.",
                suppressed=True, reason=SUPPRESS_COMP)

    # The Part IX aggregate, separate from the per-person rows above. An operator
    # asking "what does this org spend on its executives" wants the one number.
    if p["officer_comp_total"]:
        add(KIND_PERSON, "officer_comp:total",
            "Officer, director and key employee compensation totals %s"
            % _usd(p["officer_comp_total"]),
            "Form 990 Part IX line 5, tax period ending %s." % pe,
            suppressed=True, reason=SUPPRESS_COMP)

    if p["fy_end_month"]:
        add(KIND_OPS, "fiscal_year_end",
            "Fiscal year ends %s" % MONTHS[p["fy_end_month"] - 1],
            "Tax period %s to %s. Budget season runs into the period end."
            % (p["period_begin"], pe))

    if p["rental_gross"]:
        share = (" — %.1f%% of total revenue" % (100.0 * p["rental_gross"] / p["total_revenue"])
                 if p["total_revenue"] else "")
        add(KIND_COST, "revenue:rental",
            "Collects %s in gross rents from real property%s" % (_usd(p["rental_gross"]), share),
            "Form 990 Part VIII line 6a. Net rental income %s. A landlord carries "
            "grounds, repair and turnover cost the expense lines alone understate."
            % (_usd(p["rental_net"]) if p["rental_net"] is not None else "n/a"),
            category_hint=["Maintenance"])

    if p["salaries"] and p["total_expenses"]:
        pct = 100.0 * p["salaries"] / p["total_expenses"]
        add(KIND_COST, "cost:salary_share",
            "Salaries and wages are %.1f%% of total expenses" % pct,
            "Other salaries and wages %s of total expenses %s (Part IX line 7)."
            % (_usd(p["salaries"]), _usd(p["total_expenses"])))

    if p["assets"] is not None and p["net_assets"] is not None:
        add(KIND_SCALE, "balance_sheet",
            "Total assets %s, liabilities %s, net assets %s"
            % (_usd(p["assets"]), _usd(p["liabilities"] or 0), _usd(p["net_assets"])),
            "Form 990 Part X, end of tax period %s." % pe)

    add(KIND_CONTRACT, "debt:bond",
        "Tax-exempt bond obligations outstanding" if p["tax_exempt_bonds"]
        else "No tax-exempt bond obligations outstanding",
        "Form 990 Part IV bond indicator. Outstanding bonds bring covenants and a "
        "trustee; their absence means capital projects are cash or bank financed.")

    if p["schedule_l"]:
        add(KIND_CONTRACT, "related_party",
            "Schedule L filed — transactions with interested persons reported",
            "Form 990 Schedule L is attached to this return.",
            suppressed=True, reason=SUPPRESS_SCHED_L)

    if ntee:
        add(KIND_OPS, "ntee",
            "NTEE %s — %s" % (ntee, ntee_label or "classification on file"),
            "IRS Business Master File classification, carried alongside the filing "
            "for the tax period ending %s." % pe)

    if p["grants_paid"]:
        add(KIND_COST, "grants_paid",
            "Paid %s in grants and similar amounts" % _usd(p["grants_paid"]),
            "Form 990 Part IX line 1-3, tax period ending %s." % pe)

    if p["program_revenue"] is not None and p["contributions"] is not None:
        tot = (p["program_revenue"] or 0) + (p["contributions"] or 0)
        if tot:
            add(KIND_SCALE, "revenue_mix",
                "Earns %.0f%% of revenue from programs and %.0f%% from contributions"
                % (100.0 * p["program_revenue"] / tot, 100.0 * p["contributions"] / tot),
                "Program service revenue %s vs contributions and grants %s."
                % (_usd(p["program_revenue"]), _usd(p["contributions"])))
    return out


TREND_LINES = [("total_revenue", "total revenue"), ("total_expenses", "total expenses"),
               ("salaries", "salaries and wages"), ("rental_gross", "gross rents"),
               ("program_revenue", "program service revenue"),
               ("contributions", "contributions and grants")]


def trend_findings(newer, older, *, ein, object_id):
    """Year-over-year movement per line. Needs two filings, so it lives outside
    findings_for(). Dated to the NEWER period end — the movement is only known as
    of the later return."""
    out = []
    for key, label in TREND_LINES:
        a, b = newer.get(key), older.get(key)
        if not a or not b:
            continue
        delta = a - b
        pct = 100.0 * delta / b
        if abs(pct) < 0.05:
            continue
        out.append(_row(
            KIND_COST, "trend:%s" % key,
            "%s %s %.1f%% year over year (%s to %s)"
            % (label.capitalize(), "up" if delta > 0 else "down", abs(pct), _usd(b), _usd(a)),
            "Tax period ending %s against %s, a change of %s."
            % (newer["period_end"], older["period_end"], _usd(abs(delta))),
            ein=ein, object_id=object_id, period_end=newer["period_end"]))
    return out
