"""ERA proposal COVER PAGE renderer (worker piece).

Same premium cover across all collateral; only the fields change, driven by the
account's `org` block. `title` is a first-class variable so one cover fronts a
Snapshot, a CIR, or a full package. Hero is resolved per-vertical from the SAME
library the CIR uses (cir/src/assets/heroes/<vertical>.png). Fonts are embedded
(base64) because the worker container only ships Liberation.
"""
import os, base64, datetime
from jinja2 import Template

HERE = os.path.dirname(os.path.abspath(__file__))
CIR_ASSETS = os.path.join(os.path.dirname(HERE), "cir", "src", "assets")

def _b64_img(path):
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()

def hero_uri(org):
    """Per-vertical hero photo as a base64 data URI (no overlay). Empty if none."""
    vert = (org or {}).get("vertical")
    if vert:
        p = os.path.join(CIR_ASSETS, "heroes", str(vert) + ".png")
        if os.path.isfile(p):
            return _b64_img(p)
    return ""

# Default centered title per doc_type — app can override via params.
TITLE_DEFAULTS = {
    "opportunity_snapshot": "EXECUTIVE OPPORTUNITY SNAPSHOT",
    "vertical_deepdive":    "STRATEGIC SPEND REVIEW",
    "package":              "EXECUTIVE OPPORTUNITY BRIEF",
    "cover_page":           "EXECUTIVE OPPORTUNITY BRIEF",
}

# Per-vertical supporting statement: (lead, gold_word, tail).
STATEMENTS = {
    "healthcare":             ("Your next ", "clinical hire",    " may already be hiding in your operating budget."),
    "community_health":       ("Your next ", "clinician",        " may already be hiding in your operating budget."),
    "private_university":     ("Your next ", "scholarship",      " may already be hiding in your operating budget."),
    "senior_living":          ("Your next ", "resident program", " may already be hiding in your operating budget."),
    "private_club":           ("Your next ", "capital project",  " may already be hiding in your operating budget."),
    "construction":           ("Your next ", "project margin",   " may already be hiding in your operating budget."),
    "wholesale_distribution": ("Your next ", "margin point",     " may already be hiding in your operating budget."),
    "business_services":      ("Your next ", "growth hire",      " may already be hiding in your operating budget."),
    "health_system":          ("Your next ", "service line",     " may already be hiding in your operating budget."),
    "human_services":         ("Your next ", "program",          " may already be hiding in your operating budget."),
    "hospice_living":         ("Your next ", "care team",        " may already be hiding in your operating budget."),
}
DEFAULT_STMT = ("Your next ", "opportunity", " may already be hiding in your operating budget.")

def _esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build(org, *, title=None, subtitle=None, statement=None, date_str=None, doc_type="cover_page"):
    org = org or {}
    vert = org.get("vertical")
    name = org.get("name") or "Organization"
    title = title or TITLE_DEFAULTS.get(doc_type, TITLE_DEFAULTS["cover_page"])
    subtitle = (subtitle or (org.get("vertical_label") or "")).upper()
    if statement:
        stmt_html = _esc(statement)
    else:
        lead, gold, tail = STATEMENTS.get(vert, DEFAULT_STMT)
        stmt_html = "%s<span class='g'>%s</span>%s" % (_esc(lead), _esc(gold), _esc(tail))
    if not date_str:
        d = datetime.date.today()
        date_str = "%s %d, %d" % (d.strftime("%B").upper(), d.day, d.year)
    else:
        date_str = date_str.upper()
    words = name.split()
    longest = max((len(w) for w in words), default=6)
    if len(words) >= 4 or len(name) > 26:
        name_size = 34
    elif longest <= 9:
        name_size = 53
    elif longest <= 12:
        name_size = 44
    else:
        name_size = 38
    return {
        "hero_uri":  hero_uri(org),
        "hero_pos":  "70% 50%" if vert == "community_health" else "52% 50%",
        "org_name":  _esc(name),
        "title":     _esc(title),
        "subtitle":  _esc(subtitle),
        "statement_html": stmt_html,
        "date_str":  _esc(date_str),
        "name_size": name_size,
    }

def render(org, out_pdf, **kw):
    from weasyprint import HTML
    ctx = build(org, **kw)
    tpl = Template(open(os.path.join(HERE, "cover_page_template.html")).read())
    HTML(string=tpl.render(**ctx)).write_pdf(out_pdf)
    return out_pdf

if __name__ == "__main__":
    gardner = {"name": "Gardner Health Services", "vertical": "community_health",
               "vertical_label": "Community Health"}
    render(gardner, "/tmp/cover_package.pdf", doc_type="package")            # EXECUTIVE OPPORTUNITY BRIEF
    render(gardner, "/tmp/cover_snapshot.pdf", doc_type="opportunity_snapshot")  # EXECUTIVE OPPORTUNITY SNAPSHOT
    print("rendered /tmp/cover_package.pdf + /tmp/cover_snapshot.pdf")
