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

# --- dynamic cover-name sizing --------------------------------------------
# Pick the LARGEST Paralucent size at which the org name wraps cleanly inside
# the name box (max-width 46% of 8.5in; height from .name top to the gold rule).
# Measures real Paralucent metrics when available; falls back to an average-
# width estimate otherwise. Replaces the old fixed length-bucket tiers, which
# made long names small and could overflow the rule.
_PARA_CANDIDATES = [
    os.path.join(HERE, "Paralucent-Medium.otf"),
    os.path.join(os.path.dirname(HERE), "fonts", "fonnts.com-Paralucent_Medium.otf"),
]
_PARA_WIDTHS = None      # codepoint -> advance width in em
_PARA_AVG = 0.52

def _load_para_metrics():
    global _PARA_WIDTHS, _PARA_AVG
    if _PARA_WIDTHS is not None:
        return
    _PARA_WIDTHS = {}
    try:
        from fontTools.ttLib import TTFont
        path = next((p for p in _PARA_CANDIDATES if os.path.exists(p)), None)
        if path:
            f = TTFont(path, lazy=True)
            upm = f["head"].unitsPerEm
            hmtx = f["hmtx"]
            for cp, gname in f.getBestCmap().items():
                try:
                    _PARA_WIDTHS[cp] = hmtx[gname][0] / upm
                except Exception:
                    pass
            if _PARA_WIDTHS:
                _PARA_AVG = sum(_PARA_WIDTHS.values()) / len(_PARA_WIDTHS)
    except Exception:
        pass  # graceful fallback to average-width estimate

def _text_w(text, size, ls_pt=-0.375):
    _load_para_metrics()
    return sum(_PARA_WIDTHS.get(ord(ch), _PARA_AVG) * size + ls_pt for ch in text)

def _wrap_lines(words, size, box_w):
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if not cur or _text_w(trial, size) <= box_w:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines

# Cover geometry (viewBox 816x1056). The navy panel's right edge is the diagonal
# from (522,0) to (343,845); the name text starts at .pad left 7.4% (~60px) and
# top 25.6% (~270px). Available width at a given line drops as the diagonal moves
# left. We keep a safety gap so the name never kisses the gold rule.
_VB_W, _VB_H = 816.0, 1056.0
_PT_PER_PX = 612.0 / _VB_W          # 8.5in*72pt / 816px  -> px -> pt
_DIAG_TOP_X, _DIAG_TOP_Y = 522.0, 0.0
_DIAG_BOT_X, _DIAG_BOT_Y = 343.0, 845.0
_PAD_LEFT_PX = 0.074 * _VB_W        # name left edge
_NAME_TOP_PX = 0.256 * _VB_H        # first baseline-ish top
_DIAG_GAP_PX = 26.0                 # safety gap from the diagonal

def _line_width_pt(line_index, size, line_height):
    # y (px) of this line's baseline region, measured down from the name top
    y_px = _NAME_TOP_PX + (line_index + 0.85) * (size * line_height) / _PT_PER_PX
    frac = max(0.0, min(1.0, (y_px - _DIAG_TOP_Y) / (_DIAG_BOT_Y - _DIAG_TOP_Y)))
    diag_x = _DIAG_TOP_X + frac * (_DIAG_BOT_X - _DIAG_TOP_X)
    avail_px = diag_x - _DIAG_GAP_PX - _PAD_LEFT_PX
    return max(40.0, avail_px * _PT_PER_PX)

def autofit_name_size(name, box_h=150.0, max_pt=54, min_pt=28, line_height=1.06):
    words = name.split() or [name]
    for size in range(int(max_pt), int(min_pt) - 1, -1):
        # greedy-wrap using each line's OWN diagonal-limited width
        lines, cur, idx, ok = [], "", 0, True
        for w in words:
            limit = _line_width_pt(idx, size, line_height)
            if _text_w(w, size) > limit:          # a single word overflows its line
                ok = False; break
            trial = (cur + " " + w).strip()
            if not cur or _text_w(trial, size) <= limit:
                cur = trial
            else:
                lines.append(cur); cur = w; idx += 1
        if cur:
            lines.append(cur)
        if not ok:
            continue
        if len(lines) * size * line_height <= box_h:
            return size
    return int(min_pt)


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
    name_size = autofit_name_size(name)
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
