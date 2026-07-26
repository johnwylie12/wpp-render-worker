#!/usr/bin/env python3
"""ERA executive cover letter renderer — LOCKED template (2026-07-25).

Renders the single US-Letter EOP cover letter from the locked copy-of-record
(cover/cover_letter.html) using the shared signature + letterhead modules. The
body copy, valediction ("Best regards,") and signoff are LOCKED IN THE TEMPLATE —
this engine only supplies merge fields (recipient, org, address, date, the natural-
reading sector phrase) and the embedded assets. Nothing is rebuilt per run.

Letter = Signature 3 (wpp_signatures). Standalone — does NOT touch the frozen CIR
engine or the bound CIR cover page (cover_page_engine.py / cover_page_template.html).

Public API (unchanged for worker.py):
    build_cover(params_cover, recipient, company, *, date_str=None, industry_group=None) -> dict
    render_cover(cover: dict, out_pdf: str, page_size="Letter") -> out_pdf
"""
import os, sys, datetime
from jinja2 import Template

# Repo root on path so the shared modules resolve (worker.py inserts the engine
# dirs; be defensive for the self-test / direct import).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from wpp_signatures import signature_data_uri
from wpp_letterhead_assets import era_logo_uri, vti_uri

HERE = os.path.dirname(os.path.abspath(__file__))

# fonts.conf maps Trebuchet -> Liberation Sans (CIR parity) so the letter paginates
# the same way in the worker; set defensively.
_FONTS = os.path.join(HERE, "..", "cir", "build", "fonts.conf")
if os.path.exists(_FONTS):
    os.environ.setdefault("FONTCONFIG_FILE", os.path.abspath(_FONTS))

# Kept for API compatibility; the locked template hardcodes the signoff.
SIGNOFF_CANON = {
    "name": "John Wylie", "title": "Senior Consultant", "org": "ERA Group",
    "email": "jwylie@eragroup.com", "phone": "703.244.9868",
    "tagline": "Value Through Insight™",
}

# Natural-reading sector phrase from accounts.industry_group. Unmapped / None -> the
# template drops the sector clause (null-safe). null / 'Education' are the ICP-gate
# excludes, enforced at WAVE ASSEMBLY (out of scope for this render).
_SECTOR = {
    "Healthcare": "healthcare",
    "Nonprofit": "the nonprofit sector",
    "Senior Care / Retirement": "senior care and retirement",
    "Business / Professional Services": "business and professional services",
    "Construction": "construction",
}

with open(os.path.join(HERE, "cover_letter.html")) as fh:
    _TPL = Template(fh.read())

# Cover-letter paper sizes (name -> CSS @page size). The locked letter is Letter;
# these preserve the legacy "separate" print path at other sizes.
COVER_PAGE_SIZES = {
    "letter": "Letter", "legal": "Legal", "a4": "A4", "a5": "A5",
    "half-letter": "5.5in 8.5in", "monarch": "7.25in 10.5in",
    "executive": "7.25in 10.5in", "6x9": "6in 9in", "note-a2": "4.25in 5.5in",
}


def resolve_page_size(page_size):
    if not page_size:
        return "Letter"
    key = str(page_size).strip().lower()
    return COVER_PAGE_SIZES.get(key, str(page_size).strip())


def build_cover(params_cover, recipient, company, *, date_str=None, industry_group=None):
    """Resolve merge fields for the locked letter. Enqueued values win; body /
    valediction / signoff are fixed in the template, so they are ignored here."""
    pc = dict(params_cover or {})
    rc = dict(recipient or {})
    r = dict(pc.get("recipient") or {})
    name = r.get("name") or rc.get("name") or pc.get("addressee_name")
    title = r.get("title") or rc.get("title") or pc.get("addressee_title")
    org = r.get("company") or rc.get("company") or company
    address = r.get("address_lines") or rc.get("address_lines") or []
    # sector: explicit block override wins; else map from industry_group.
    ig = pc.get("industry_group") or industry_group
    sector_phrase = pc.get("sector_phrase") or _SECTOR.get((ig or "").strip())
    return {
        "date_str": date_str or datetime.date.today().strftime("%B %-d, %Y"),
        "recipient": {"name": name, "title": title, "company": org,
                      "address_lines": list(address)},
        "sector_phrase": sector_phrase,
        "letterhead_paper": bool(pc.get("letterhead_paper")),
    }


def _split_address(lines):
    """recipient.address_lines (list) -> (line1, line2|None, city_state_zip)."""
    ls = [str(x).strip() for x in (lines or []) if str(x).strip()]
    if not ls:
        return "", None, ""
    if len(ls) == 1:
        return ls[0], None, ""
    if len(ls) == 2:
        return ls[0], None, ls[1]
    return ls[0], ", ".join(ls[1:-1]), ls[-1]  # street / (middle) / city-state-zip


def build_ctx(cover: dict) -> dict:
    """Pure merge-field builder (no I/O) — the exact context the locked template
    consumes. Split out so it can be unit-tested without WeasyPrint."""
    r = cover.get("recipient", {}) or {}
    name = (r.get("name") or "").strip()
    first = name.split()[0] if name else ""
    l1, l2, csz = _split_address(r.get("address_lines"))
    return {
        "era_logo_uri": era_logo_uri(),
        "vti_uri": vti_uri(),
        "signature_uri": signature_data_uri("3"),   # LETTER = Sig 3
        "date": cover.get("date_str", ""),
        "first_name": first or "there",
        "recipient_name": name,
        "recipient_title": r.get("title") or "",
        "org_name": (r.get("company") or "").rstrip("."),
        "addr_line1": l1,
        "addr_line2": l2,
        "addr_city_state_zip": csz,
        "sector_phrase": cover.get("sector_phrase"),
        "letterhead_paper": bool(cover.get("letterhead_paper")),
    }


def render_html(cover: dict, page_size="Letter") -> str:
    """Render the locked template to an HTML string (no PDF — testable)."""
    ctx = build_ctx(cover)
    html = _TPL.render(**ctx)
    if ctx["letterhead_paper"]:
        # pre-printed ERA letterhead: template omits .hd; clear the top band (~1.8in)
        # so the body starts below it. A later @page rule cascades over the base one.
        html = html.replace("</style>", "  @page { margin-top: 1.8in; }\n</style>", 1)
    size_css = resolve_page_size(page_size)
    if size_css and size_css != "Letter":
        html = html.replace("</style>", f"  @page {{ size: {size_css}; }}\n</style>", 1)
    return html


def render_cover(cover: dict, out_pdf: str, page_size="Letter") -> str:
    from weasyprint import HTML  # lazy: keeps build_cover / render_html import-safe without WeasyPrint
    HTML(string=render_html(cover, page_size)).write_pdf(out_pdf)
    return out_pdf


if __name__ == "__main__":
    c = build_cover(
        {"letterhead_paper": False},
        {"name": "Nick Jacobi", "title": "General Manager",
         "address_lines": ["1200 Club Dr", "Suite 100", "Raleigh, NC 27601"]},
        "Stonebridge Golf Club.", date_str="July 25, 2026", industry_group="Nonprofit")
    render_cover(c, "/tmp/cover_test.pdf")
    print("rendered /tmp/cover_test.pdf")
