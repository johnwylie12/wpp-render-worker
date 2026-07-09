#!/usr/bin/env python3
"""ERA executive cover letter renderer.

Standalone — does NOT touch the frozen CIR engine/template. Produces a single
US-Letter page that gets merged in FRONT of the Cost Intelligence Report.

Public API:
    render_cover(cover: dict, out_pdf: str) -> out_pdf
    build_cover(params_cover, recipient, company, *, date_str=None) -> dict

`cover` dict shape (all optional except recipient is recommended):
    {
      "date_str":  "June 29, 2026",
      "recipient": {"name","title","company","address_lines":[...]},
      "salutation":"Dear Mr. Jacobi,",
      "body_paras":["...", "..."],
      "ps":        "optional postscript",
      "signoff":   {"name","title","org","email","phone","tagline"}
    }
Anything missing is filled from the ERA canon below.
"""
import os, datetime
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))

# Bundled fonts.conf maps Trebuchet -> Liberation Sans (CIR parity). Set it
# defensively so the letter renders in the same typeface even if the worker
# forgot to export it.
_FONTS = os.path.join(HERE, "..", "cir", "build", "fonts.conf")
if os.path.exists(_FONTS):
    os.environ.setdefault("FONTCONFIG_FILE", os.path.abspath(_FONTS))

# ERA canon signoff (mirrors content_contracts._shared.signoff_constant + tagline).
SIGNOFF_CANON = {
    "name":  "John Wylie",
    "title": "Senior Advisor",
    "org":   "ERA Group",
    "email": "jwylie@eragroup.com",
    "phone": "703.244.9868",
    "tagline": "Value Through Insight\u2122",
}

with open(os.path.join(HERE, "logo_b64.txt")) as fh:
    LOGO_B64 = fh.read().strip()
with open(os.path.join(HERE, "cover_letter.html")) as fh:
    _TPL = Template(fh.read())


def _honorific_salutation(name: str, title: str | None) -> str:
    """Conservative default salutation. We do NOT guess gendered honorifics —
    fall back to full name, which is always safe."""
    n = (name or "").strip()
    return f"Dear {n}," if n else "Dear Sir or Madam,"


def build_cover(params_cover: dict | None,
                recipient: dict | None,
                company: str | None,
                *, date_str: str | None = None) -> dict:
    """Merge an enqueued cover_letter block (if any) with the resolved recipient
    (from contact_id) and the ERA canon. Enqueued values win; canon fills gaps."""
    pc = dict(params_cover or {})
    rc = dict(recipient or {})

    # recipient: prefer explicit enqueued recipient, else the resolved contact
    r = dict(pc.get("recipient") or {})
    name    = r.get("name")    or rc.get("name")    or pc.get("addressee_name")
    title   = r.get("title")   or rc.get("title")   or pc.get("addressee_title")
    org     = r.get("company") or rc.get("company") or company
    address = r.get("address_lines") or rc.get("address_lines") or []

    salutation = pc.get("salutation")
    if not salutation or salutation.strip() in ("Dear ___,", "Dear ___"):
        salutation = _honorific_salutation(name, title)

    body = pc.get("body_paras") or pc.get("body")
    if not body:
        co = org or "your organization"
        # Paragraph 1 is the enqueued `opening` hook when the frontend supplies
        # one (built with the account's provenance), else a safe generic opener.
        # Paragraphs 2-3 are LOCKED CANON and live ONLY here, so ERA's promises
        # can't drift or be model-fabricated.
        opening = pc.get("opening")
        generic_opener = (
            f"I have put together a short, no-obligation cost intelligence read on "
            f"where indirect spend may be drifting across {co} \u2014 the categories "
            f"most finance teams rarely re-test, and a sized, outside-in estimate of what "
            f"a baseline could recover."
        )
        para1 = opening.strip() if isinstance(opening, str) and opening.strip() else generic_opener
        body = [
            para1,
            "ERA works strictly on contingency: a share of verified savings, with no "
            "fee if there are none and no upfront cost. Nothing changes without your "
            "approval \u2014 every recommendation is yours to accept or decline.",
            "The attached report lays out the opportunity. If it is useful, I would "
            "welcome a brief call to confirm which categories are worth a no-cost "
            "baseline.",
        ]

    signoff = {**SIGNOFF_CANON, **(pc.get("signoff") or {})}

    return {
        "date_str": date_str or datetime.date.today().strftime("%B %-d, %Y"),
        "recipient": {"name": name, "title": title, "company": org,
                      "address_lines": address},
        "salutation": salutation,
        "body_paras": body,
        "ps": pc.get("ps"),
        "signoff": signoff,
        # True -> render logo-free with a cleared top for printing on physical
        # ERA letterhead stock. Set via params.cover.letter.letterhead_paper.
        "letterhead_paper": bool(pc.get("letterhead_paper")),
    }


# Selectable cover-letter paper sizes (name -> CSS @page size token).
# Accepts a preset key (case-insensitive) OR a raw CSS size string like "8.5in 11in".
COVER_PAGE_SIZES = {
    "letter":      "Letter",            # 8.5 x 11 in  (matches the CIR; required for bundled)
    "legal":       "Legal",             # 8.5 x 14 in
    "a4":          "A4",
    "a5":          "A5",
    "half-letter": "5.5in 8.5in",       # statement / half sheet
    "monarch":     "7.25in 10.5in",     # executive letterhead
    "executive":   "7.25in 10.5in",
    "6x9":         "6in 9in",
    "note-a2":     "4.25in 5.5in",      # folded note card
}

def resolve_page_size(page_size: str | None) -> str:
    if not page_size:
        return "Letter"
    key = str(page_size).strip().lower()
    if key in COVER_PAGE_SIZES:
        return COVER_PAGE_SIZES[key]
    return str(page_size).strip()  # treat as a raw CSS size token


def render_cover(cover: dict, out_pdf: str, page_size: str | None = "Letter") -> str:
    ctx = {
        "logo_b64": LOGO_B64,
        "date_str": cover.get("date_str", ""),
        "recipient": cover.get("recipient", {}),
        "salutation": cover.get("salutation", "Dear Sir or Madam,"),
        "body_paras": cover.get("body_paras", []),
        "ps": cover.get("ps"),
        "signoff": {**SIGNOFF_CANON, **(cover.get("signoff") or {})},
        "page_css": resolve_page_size(page_size),
        "letterhead_paper": bool(cover.get("letterhead_paper")),
    }
    HTML(string=_TPL.render(**ctx)).write_pdf(out_pdf)
    return out_pdf


if __name__ == "__main__":
    # self-test
    c = build_cover(None, {"name": "Nick Jacobi", "title": "General Manager"},
                    "Stonebridge Golf Club")
    render_cover(c, "/tmp/cover_test.pdf")
    print("rendered /tmp/cover_test.pdf")
