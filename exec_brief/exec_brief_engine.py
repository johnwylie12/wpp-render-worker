#!/usr/bin/env python3
"""ERA Executive Opportunity Brief — the Tier-3 flagship 5-7pp deliverable.

IFCJ-style personalized opportunity analysis for ONE account. Reads the
`common_core` param family (company / categories / opportunity / cannot_know /
hero) PLUS the exec_brief-specific fields (why_now, proof_stats,
decision_makers, next_step, model). Renders a multi-page branded PDF with the
same navy/gold system as the CIR + snapshot (palette #003A70 / #FF9C00, signoff
"Senior Consultant", "value through insight" lockup).

Params are the FLAT object shown in content_contracts.example_params (the PPSAT
reference artifact) — NOT wrapped in a `content` block. `render()` also accepts
a `{ "content": {...} }` wrapper defensively.

Usage:  python3 exec_brief/exec_brief_engine.py <params.json> <out.pdf>
Preview + production: WeasyPrint (same fonts.conf as the CIR).
"""
import json, sys, os, base64, datetime
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))

# Bundled fonts.conf maps Trebuchet/Arial -> the installed brand fonts for pixel
# parity with the CIR + snapshot. Set defensively (matches snapshot_engine).
_FONTS = os.path.join(HERE, "..", "cir", "build", "fonts.conf")
if os.path.exists(_FONTS):
    os.environ.setdefault("FONTCONFIG_FILE", os.path.abspath(_FONTS))

# Bundled heroes live with the CIR engine (per-vertical photo library).
_HERO_DIR = os.path.join(HERE, "..", "cir", "src", "assets", "heroes")
_LOGO_WHITE = os.path.join(HERE, "..", "cir", "src", "assets", "logo_white.png")
_LOGO_B64 = os.path.join(HERE, "..", "snapshot", "logo_b64.txt")

NAVY = "#003A70"
GOLD = "#FF9C00"
NAVY_OVERLAY = ("linear-gradient(105deg, rgba(0,40,81,0.92) 0%, "
                "rgba(0,52,100,0.62) 46%, rgba(10,74,134,0.28) 100%)")
NAVY_GRADIENT = "linear-gradient(100deg,#002851 0%,#003A70 55%,#0a4a86 100%)"

DEFAULT_SIGNOFF = {"name": "John Wylie", "title": "Senior Consultant",
                   "org": "ERA Group", "email": "jwylie@eragroup.com",
                   "phone": "703.244.9868"}
DEFAULT_CONTINGENCY = ("Contingency-based — a share of verified savings. "
                       "No savings, no fee.")


def money(n):
    """600000 -> $600K ; 1400000 -> $1.4M ; 3050000 -> $3.05M ; 3000000 -> $3M"""
    n = float(n)
    if n >= 1_000_000:
        s = f"{n/1_000_000:.2f}".rstrip("0").rstrip(".")
        return f"${s}M"
    return f"${int(round(n/1000))}K"


def money_range(lo, hi):
    return f"{money(lo)}–{money(hi)}"


def pct(v):
    """1.0 -> 1% ; 2.4 -> 2.4% ; 18 -> 18%"""
    v = float(v)
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return f"{s}%"


def _hero_bg(content):
    """Resolve the hero band background: bundled per-name photo (from hero.url
    basename or company vertical), else a remote hero.url, else the navy
    gradient. Always returns a CSS background-image value with the navy overlay."""
    hero = content.get("hero") or {}
    url = hero.get("url") or ""
    # Try to resolve a bundled local hero by the URL basename (e.g. healthcare.png).
    if url:
        base = os.path.basename(url.split("?")[0])
        local = os.path.join(_HERO_DIR, base)
        if os.path.isfile(local):
            uri = "data:image/png;base64," + base64.b64encode(open(local, "rb").read()).decode()
            return NAVY_OVERLAY + ", url('" + uri + "')"
    # Fall back to a vertical-named bundled hero if the company carries one.
    vert = (content.get("company") or {}).get("vertical")
    if vert:
        local = os.path.join(_HERO_DIR, str(vert) + ".png")
        if os.path.isfile(local):
            uri = "data:image/png;base64," + base64.b64encode(open(local, "rb").read()).decode()
            return NAVY_OVERLAY + ", url('" + uri + "')"
    # Remote hero URL, embedded as a link (WeasyPrint fetches it) if present.
    if url and url.startswith("http"):
        return NAVY_OVERLAY + ", url('" + url + "')"
    return NAVY_GRADIENT


def _logo_uri():
    if os.path.isfile(_LOGO_B64):
        return "data:image/png;base64," + open(_LOGO_B64).read().strip()
    return ""


def _derive_proof_stats(content):
    """If proof_stats omitted, derive top 3 from categories + the ERA proof line."""
    stats = []
    for cat in (content.get("categories") or [])[:2]:
        lo, hi = cat.get("low_usd"), cat.get("high_usd")
        if lo is not None and hi is not None:
            stats.append({"value": money_range(lo, hi), "label": f"in {cat.get('label', 'this category')}"})
    stats.append({"value": "1,000+", "label": "ERA projects with quantified savings"})
    return stats[:4]


def render(params, out_pdf):
    # Accept the flat PPSAT-shaped object OR a { "content": {...} } wrapper.
    content = params
    if isinstance(params, dict) and isinstance(params.get("content"), dict) \
            and "company" in params["content"]:
        content = params["content"]

    company = content.get("company") or {}
    if not company.get("name"):
        raise ValueError("exec_brief requires company.name")

    opp = content.get("opportunity") or {}
    if opp.get("low_usd") is None or opp.get("high_usd") is None:
        raise ValueError("exec_brief requires opportunity.low_usd and high_usd")

    why = content.get("why_now") or {}
    model = content.get("model") or {}
    categories = content.get("categories") or []
    for cat in categories:
        lo, hi = cat.get("low_usd"), cat.get("high_usd")
        cat["_range"] = money_range(lo, hi) if lo is not None and hi is not None else ""
        if cat.get("pct_low") is not None and cat.get("pct_high") is not None:
            cat["_pct"] = f"{pct(cat['pct_low'])}–{pct(cat['pct_high'])}"
        else:
            cat["_pct"] = ""

    proof_stats = content.get("proof_stats") or _derive_proof_stats(content)

    # Decision makers: address by role when the name is withheld.
    dms = []
    for d in (content.get("decision_makers") or []):
        dms.append({
            "name": d.get("name"),
            "role": d.get("role") or "",
            "focus": d.get("focus") or "",
            "display": d.get("name") or d.get("role") or "",
        })

    signoff = {**DEFAULT_SIGNOFF, **(content.get("signoff") or {})}
    prepared_date = content.get("date") or datetime.date.today().strftime("%B %-d, %Y")

    opp_range = opp.get("display") or money_range(opp["low_usd"], opp["high_usd"])
    opp_pct = ""
    if opp.get("pct_low") is not None and opp.get("pct_high") is not None:
        opp_pct = f"{pct(opp['pct_low'])}–{pct(opp['pct_high'])} of revenue"

    revenue_line = ""
    if company.get("revenue_usd"):
        revenue_line = money(company["revenue_usd"]) + " annual revenue"

    ctx = dict(
        navy=NAVY, gold=GOLD,
        hero_bg=_hero_bg(content),
        logo_uri=_logo_uri(),
        company=company,
        industry=company.get("industry", ""),
        footprint_line=company.get("footprint_line", ""),
        revenue_line=revenue_line,
        headline=content.get("headline") or "The savings are already in your budget.",
        prepared_date=prepared_date,
        why_summary=why.get("summary", ""),
        why_signals=why.get("signals") or [],
        opp_range=opp_range, opp_pct=opp_pct,
        proof_stats=proof_stats,
        categories=categories,
        cannot_know=content.get("cannot_know") or [],
        decision_makers=dms,
        next_step=content.get("next_step", ""),
        contingency_note=model.get("contingency_note") or DEFAULT_CONTINGENCY,
        signoff=signoff,
    )
    tpl = Template(open(os.path.join(HERE, "exec_brief_template.html")).read())
    HTML(string=tpl.render(**ctx)).write_pdf(out_pdf)
    return out_pdf


if __name__ == "__main__":
    render(json.load(open(sys.argv[1])), sys.argv[2])
    print("rendered", sys.argv[2])
