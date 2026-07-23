#!/usr/bin/env python3
"""ERA Executive Opportunity Snapshot — one-page cover / standalone leave-behind.

Reads the SAME prospect JSON as the CIR (single source of truth). Dollar figures
derive from `opportunity`. The vertical-native "equivalent" framing, headline,
intro, and horizon label are chosen automatically from `org.vertical` (with a
PE override on `org.type`), so a new prospect needs NO snapshot copy. Anything
under a `snapshot` block in the JSON overrides the vertical default.

Three equivalent modes:
  count   savings / value_per_unit  -> a headcount/dues/scholarship figure
  revenue savings / margin_pct      -> the margin on $X of new sales never chased
  ebitda  savings * multiple        -> enterprise value created (savings = EBITDA)

Divisors below (loaded salary, net margin %, EBITDA multiple) are general
business benchmarks, NOT ERA savings claims. Override per prospect in the JSON.

Usage:  python3 src/snapshot_engine.py content/<prospect>.json build/<prospect>_Snapshot.pdf
Preview: WeasyPrint. Production: same HTML via headless Chromium.
"""
import json, sys, os, base64
from datetime import date
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))

# Bundled fonts.conf maps Trebuchet/Arial/Paralucent -> Liberation Sans for
# pixel parity with the CIR + cover letter. Set defensively (matches cover_engine).
_FONTS = os.path.join(HERE, "..", "cir", "build", "fonts.conf")
if os.path.exists(_FONTS):
    os.environ.setdefault("FONTCONFIG_FILE", os.path.abspath(_FONTS))

DEFAULT_AGG = {"clients": 916, "spend": "$2.25B", "projects": "6,420",
               "with_savings": "2,656", "wtd_avg": "27.5%"}

# ---- intro variants (swap the noun the reader self-identifies with) --------
INTRO = {
    "club": ("The opportunities most clubs miss are not the ones anyone is hiding. They are the "
             "recurring, unglamorous line items leadership assumes are already handled \u2014 priced under agreements "
             "few ever re-test. In clubs this size, those categories tend to drift above "
             "market quietly, year over year, rarely surfacing in the numbers leadership reviews."),
    "company": ("The opportunities most companies miss are not the ones anyone is hiding. They are the "
                "recurring, unglamorous line items leadership assumes are already handled \u2014 priced under agreements "
                "few ever re-test. In operations this size, those categories tend to drift "
                "above market quietly, year over year, rarely surfacing in the numbers leadership reviews."),
    "care": ("The opportunities most organizations miss are not the ones anyone is hiding. They are the "
             "recurring, unglamorous line items leadership assumes are already handled \u2014 priced under agreements "
             "few ever re-test. In organizations this size, those categories tend to drift "
             "above market quietly, year over year \u2014 dollars that could fund care, staffing, or "
             "reinvestment instead leaking out through contracts that go untested."),
    "university": ("The opportunities most institutions miss are not the ones anyone is hiding. They are the "
                   "recurring, unglamorous line items leadership assumes are already handled \u2014 priced under agreements "
                   "few ever re-test. In institutions this size, those categories tend to drift "
                   "above market quietly, year over year \u2014 dollars that could fund aid, faculty, or "
                   "facilities instead leaking out through contracts that go untested."),
}

# ---- per-vertical defaults -------------------------------------------------
# horizon_label describes the 5x cumulative-savings figure (same in every mode).
VERTICAL_DEFAULTS = {
    "private_club": {
        "intro": "club",
        "headline": "Your next capital project may already be hiding in your operating budget.",
        "horizon_label": "toward capital projects over five years, with no new member assessment",
        "equivalent": {"mode": "count", "value_per_unit": 27400,
                       "label": "full golf memberships in equivalent annual dues",
                       "qualifier": "without adding a member"},
    },
    "private_university": {
        "intro": "university",
        "headline": "Your next scholarship may already be hiding in your operating budget.",
        "horizon_label": "toward financial aid and facilities over five years",
        "equivalent": {"mode": "count", "value_per_unit": 40000,
                       "label": "full-tuition scholarships funded for a year",
                       "qualifier": "without touching the endowment or raising tuition"},
    },
    "healthcare": {
        "intro": "care",
        "headline": "Your next clinical hire may already be hiding in your operating budget.",
        "horizon_label": "toward staffing and capital over five years",
        "equivalent": {"mode": "count", "value_per_unit": 100000,
                       "label": "full-time nurses funded for a year",
                       "qualifier": "without adding to the clinical budget"},
    },
    "community_health": {
        "intro": "care",
        "headline": "Your next clinician may already be hiding in your operating budget.",
        "horizon_label": "toward patient care and community programs over five years",
        "equivalent": {"mode": "count", "value_per_unit": 90000,
                       "label": "full-time clinicians funded for a year",
                       "qualifier": "without adding to the care budget"},
    },
    "human_services": {
        "intro": "care",
        "headline": "Your next program may already be hiding in your operating budget.",
        "horizon_label": "toward the programs and people you serve over five years",
        "equivalent": {"mode": "count", "value_per_unit": 55000,
                       "label": "full-time direct-support staff funded for a year",
                       "qualifier": "without cutting a single program"},
    },
    "senior_living": {
        "intro": "care",
        "headline": "Your next community upgrade may already be hiding in your operating budget.",
        "horizon_label": "toward care and community reinvestment over five years",
        "equivalent": {"mode": "count", "value_per_unit": 45000,
                       "label": "full-time caregivers funded for a year",
                       "qualifier": "without raising a resident's monthly fee"},
    },
    "manufacturing": {
        "intro": "company",
        "headline": "Your next margin point may already be hiding in your indirect spend.",
        "horizon_label": "in cumulative bottom-line savings over five years",
        "equivalent": {"mode": "revenue", "margin_pct": 8,
                       "label": "in equivalent new sales at your current margin",
                       "qualifier": "without raising a price or adding a line"},
    },
    "wholesale_distribution": {
        "intro": "company",
        "headline": "Your next margin point may already be hiding in your indirect spend.",
        "horizon_label": "in cumulative bottom-line savings over five years",
        "equivalent": {"mode": "revenue", "margin_pct": 4,
                       "label": "in equivalent new sales at your current margin",
                       "qualifier": "without signing a single new account"},
    },
    "construction": {
        "intro": "company",
        "headline": "Your next piece of equipment may already be hiding in your overhead.",
        "horizon_label": "in cumulative bottom-line savings over five years",
        "equivalent": {"mode": "revenue", "margin_pct": 4,
                       "label": "in equivalent contract revenue at your current margin",
                       "qualifier": "without winning a single extra bid"},
    },
    "hvac_plumbing_electrical": {
        "intro": "company",
        "headline": "Your next crew may already be hiding in your overhead.",
        "horizon_label": "in cumulative bottom-line savings over five years",
        "equivalent": {"mode": "revenue", "margin_pct": 8,
                       "label": "in equivalent service revenue at your current margin",
                       "qualifier": "without raising a single invoice"},
    },
    "business_services": {
        "intro": "company",
        "headline": "Your next margin point may already be hiding in your indirect spend.",
        "horizon_label": "in cumulative bottom-line savings over five years",
        "equivalent": {"mode": "revenue", "margin_pct": 10,
                       "label": "in equivalent new revenue at your current margin",
                       "qualifier": "without signing a single new client"},
    },
    "multi_site_services": {
        "intro": "company",
        "headline": "Your next margin point may already be hiding in your indirect spend.",
        "horizon_label": "in cumulative bottom-line savings over five years",
        "equivalent": {"mode": "revenue", "margin_pct": 8,
                       "label": "in equivalent new revenue at your current margin",
                       "qualifier": "without opening a single new site"},
    },
    "roll_ups": {
        "intro": "company",
        "headline": "Your next point of EBITDA may already be hiding in your operating budget.",
        "horizon_label": "in cumulative savings over five years, on top of the value above",
        "equivalent": {"mode": "ebitda", "multiple": 7,
                       "label": "in enterprise value at exit",
                       "qualifier": "from EBITDA that drops straight to the bottom line"},
    },
    "pe_backed_services": {
        "intro": "company",
        "headline": "Your next point of EBITDA may already be hiding in your operating budget.",
        "horizon_label": "in cumulative savings over five years, on top of the value above",
        "equivalent": {"mode": "ebitda", "multiple": 7,
                       "label": "in enterprise value at exit",
                       "qualifier": "from EBITDA that drops straight to the bottom line"},
    },
}
GENERIC_DEFAULT = {
    "intro": "company",
    "headline": "Your next margin point may already be hiding in your indirect spend.",
    "horizon_label": "in cumulative bottom-line savings over five years",
    "equivalent": {"mode": "revenue", "margin_pct": 8,
                   "label": "in equivalent new sales at your current margin",
                   "qualifier": "without raising a price or winning a new bid"},
}
# org.type == "pe_backed" forces the EBITDA framing regardless of vertical.
PE_OVERRIDE = {
    "headline": "Your next point of EBITDA may already be hiding in your operating budget.",
    "horizon_label": "in cumulative savings over five years, on top of the value above",
    "equivalent": {"mode": "ebitda", "multiple": 7,
                   "label": "in enterprise value at exit",
                   "qualifier": "from EBITDA that drops straight to the bottom line"},
}


def money(n):
    """610000 -> $610K ; 1370000 -> $1.37M ; 3050000 -> $3.05M ; 3000000 -> $3M"""
    if n >= 1_000_000:
        s = f"{n/1_000_000:.2f}".rstrip("0").rstrip(".")
        return f"${s}M"
    return f"${int(round(n/1000))}K"


def money_range(lo, hi):
    return f"{money(lo)} \u2013 {money(hi)}"


def equivalent(eq, lo, hi):
    """Return (bigfig, subhead) for the chosen mode."""
    mode = eq.get("mode", "count")
    label, qual = eq.get("label", ""), eq.get("qualifier", "")
    if mode == "revenue":
        m = eq.get("margin_pct", 8) / 100.0
        bigfig = money_range(lo / m, hi / m)
    elif mode == "ebitda":
        mult = eq.get("multiple", 7)
        bigfig = money_range(lo * mult, hi * mult)
        if not eq.get("label"):
            label = f"in enterprise value at a {mult}\u00d7 multiple"
    else:  # count
        vpu = eq.get("value_per_unit")
        if eq.get("units_display"):
            bigfig = eq["units_display"]
        elif vpu:
            bigfig = f"{int(round(lo/vpu))}\u2013{int(round(hi/vpu))}"
        else:
            bigfig = money_range(lo, hi)
    subhead = f"{label}, {qual}" if (label and qual) else (label or qual)
    return bigfig, subhead


def render(content, out_pdf):
    c = content
    org = c["org"]
    opp = c["opportunity"]
    snap = c.get("snapshot", {})
    agg = {**DEFAULT_AGG, **c.get("aggregate", {})}

    lo, hi = opp["low_usd"], opp["high_usd"]
    annual_display = opp.get("display", money_range(lo, hi))

    # ---- resolve vertical defaults, then PE override, then JSON overrides --
    base = dict(VERTICAL_DEFAULTS.get(org.get("vertical", ""), GENERIC_DEFAULT))
    if org.get("type") == "pe_backed":
        base = {**base, **PE_OVERRIDE}
    eq = {**base["equivalent"], **snap.get("equivalent", {})}
    headline = snap.get("headline", base["headline"])
    intro = snap.get("intro", INTRO.get(base["intro"], INTRO["company"]))
    horizon_label = snap.get("horizon_label", base["horizon_label"])

    bigfig, subhead = equivalent(eq, lo, hi)

    years = snap.get("horizon_years", 5)
    horizon_display = money_range(lo * years, hi * years)

    # ---- why-the-figure-is-credible (item 1 data-driven; 2 & 3 boilerplate)
    cred = snap.get("credibility")
    if not cred:
        cred = [
            (f"Built from {org['name']}'s own <b>public financial filings</b> and ERA's benchmark "
             f"database \u2014 {agg['spend']} of spend reviewed across {agg['projects']} completed "
             f"engagements at {agg['clients']} organizations."),
            ("Validation is a no-cost, 30-day baseline that replaces these outside-in estimates with your "
             "actual contract data. Nothing changes without your approval \u2014 every recommendation is yours to accept or decline. Most organizations are already competitive in some categories; the baseline identifies both the opportunities and the areas performing well."),
            ("The engagement is contingency-based: a share of verified savings only \u2014 "
             "no savings, no fee, and no upfront cost."),
        ]

    eyebrow = snap.get("eyebrow",
                       f"Executive Opportunity Snapshot \u00b7 {org.get('vertical_label', '')}")
    closing = snap.get("closing",
        ("Our outside-in analysis points to an opportunity comparable to those identified across "
         "similar organizations. The remaining question is whether the same conditions exist within "
         f"{org['name']}."))
    if snap.get("lead_in"):
        lead_in = snap["lead_in"]
    elif snap.get("package") or c.get("package"):
        lead_in = (f"What follows is a preliminary, outside-in analysis of {org['name']}, completed before "
                   f"any meeting from public filings and ERA's category benchmarks: a category-by-category "
                   f"view of where the opportunity sits, sector benchmarks showing where indirect spend "
                   f"concentrates, and a client case study of results ERA has delivered. The remaining step "
                   f"is to validate these observations against the contract data held only inside the organization.")
    else:
        lead_in = (f"The three pages that follow summarize a preliminary, outside-in analysis already completed on "
                   f"{org['name']} \u2014 before any meeting, using public filings and ERA's category benchmarks. "
                   "The remaining step is to validate those observations against information available only inside the organization.")

    so = c.get("signoff", {"name": "John Wylie", "title": "Senior Consultant", "org": "ERA Group",
                           "email": "jwylie@eragroup.com", "phone": "703.244.9868"})
    prepared_date = snap.get("date") or c.get("date") or date.today().strftime("%B %-d, %Y")

    logo_path = os.path.join(HERE, "logo_b64.txt")
    logo_uri = ("data:image/png;base64," + open(logo_path).read().strip()
                if os.path.exists(logo_path) else "")

    ctx = dict(
        org=org, eyebrow=eyebrow.upper(), headline=headline, intro=intro,
        units_display=bigfig, subhead=subhead,
        annual_line=f"\u2248 {annual_display} in estimated annual recovery \u00b7 sized in the analysis that follows",
        horizon_display=horizon_display, horizon_label=horizon_label,
        credibility=cred, lead_in=lead_in, closing=closing,
        signoff=so, prepared_date=prepared_date, logo_uri=logo_uri,
    )
    tpl = Template(open(os.path.join(HERE, "snapshot_template.html")).read())
    HTML(string=tpl.render(**ctx)).write_pdf(out_pdf)
    return out_pdf


if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
    print("rendered", sys.argv[2])
