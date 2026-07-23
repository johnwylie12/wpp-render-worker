#!/usr/bin/env python3
"""
"Before We Meet" executive closing page — final page of the Executive
Opportunity Brief (portrait, WPP package house style).

Mirrors the case_study / cover_page engine pattern: Lora + Poppins and the
headshot are base64-embedded so the container needs no system fonts or network.
The page is essentially static (the letter and the five commitments are the same
for every prospect); only the footer vertical label and the headshot ever change,
and both are overridable via the `data` dict.

Voice: a genuine personal letter (shareholder-letter cadence), not marketing
collateral. The right column is five personal commitments. The contact block is
deliberately minimal — the package already carries the cover letter, card, and
full contact details, so this page leads with the person, not the coordinates.

Usage
-----
    python closing/closing_engine.py [out_dir]          # -> Closing_BeforeWeMeet.pdf
    from closing_engine import render
    render({"footer_left_b": "Senior Care"}, "/tmp/close.pdf")

Overrides (all optional; sensible defaults below)
    photo_uri / photo_path   headshot (data-URI/URL or file); default ./assets/jw_headshot.jpg
    signature_uri            a SCANNED handwritten signature (data-URI/URL); falls
                             back to a typeset script of signature_name when absent
    footer_left_b            vertical label in the footer (default "Human Services")
    person{...}, headline, letter[...], commitments[...], ...
"""
import base64, os, sys, copy
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
_LOCAL_FONTS = os.path.join(ASSETS, "fonts")
_CS_FONTS = os.path.join(os.path.dirname(HERE), "case_study", "assets", "fonts")
# Prefer this piece's own bundled fonts so closing/ is fully self-contained;
# fall back to the case-study copy if the local folder isn't present.
CS_FONTS = _LOCAL_FONTS if os.path.isdir(_LOCAL_FONTS) else _CS_FONTS


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _img_uri(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "jpeg"
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{_b64(path)}"


# --- brand icons (24x24 gold strokes, drawn on the navy circle by the template) ---
_IC = {
    "shield":  '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="#FF9C00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.4-3 8-7 10-4-2-7-5.6-7-10V6l7-3z"/><path d="M9 12l2.2 2.2L15.2 10"/></svg>',
    "people":  '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FF9C00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="9" r="3.1"/><path d="M3.6 18.8c.7-3 3-4.7 5.4-4.7s4.7 1.7 5.4 4.7"/><path d="M15.6 6.5a3 3 0 0 1 0 5.1"/><path d="M17.2 14.3c1.9.6 3.2 2.1 3.7 4.5"/></svg>',
    "scale":   '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="#FF9C00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v16M7.5 20.5h9"/><path d="M12 6.2 6 8m6-1.8L18 8"/><path d="M6 8 3.4 13a2.6 2.6 0 0 0 5.2 0L6 8z"/><path d="M18 8l-2.6 5a2.6 2.6 0 0 0 5.2 0L18 8z"/></svg>',
    "check":   '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="#FF9C00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8.3 12.4l2.6 2.6 4.8-5.2"/></svg>',
    "compass": '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="#FF9C00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M15.6 8.4l-2.1 5.1-5.1 2.1 2.1-5.1 5.1-2.1z"/></svg>',
}

# --------------------------------------------------------------- default content
DEFAULT = {
    "eyebrow":  "Before We Meet\u2026",
    "headline": "Everything you\u2019ve just read was prepared before we ever spoke.",
    # p.cls: '' normal · 'tight' short line, small gap below · 'lift' quiet navy beat
    "letter": [
        {"cls": "tight", "html": "Some of it may prove to be accurate."},
        {"cls": "tight", "html": "Some of it may not."},
        {"cls": "lift",  "html": "That isn\u2019t the point."},
        {"cls": "tight", "html": "The purpose of this brief isn\u2019t to prove an estimate."},
        {"cls": "",      "html": "It\u2019s to determine\u2014using your own contracts and data\u2014whether "
                                 "opportunities truly exist, and to tell you honestly when they don\u2019t."},
        {"cls": "tight", "html": "Over the past thirty years I\u2019ve learned that the strongest client "
                                 "relationships don\u2019t begin with a proposal."},
        {"cls": "lift",  "html": "They begin with trust."},
        {"cls": "",      "html": "Sometimes that means confirming there isn\u2019t an opportunity at all."},
        {"cls": "",      "html": "Whether we ultimately work together or not, I hope this briefing reflects "
                                 "the level of preparation, curiosity, and respect I bring before asking for "
                                 "even a few minutes of your time."},
        {"cls": "",      "html": "If, after reviewing it, you believe the conversation is worthwhile, I\u2019d "
                                 "welcome the opportunity to learn more about your organization."},
    ],

    "signature_uri":  "",              # drop in a scanned signature PNG/URL here
    "signature_name": "John Wylie",
    "signature_role": "Senior Consultant",

    "right_title": "What You Can Expect From Me",
    "commitments": [
        {"icon": _IC["shield"],
         "h": "I\u2019ll tell you when you\u2019re already getting a good deal.",
         "s": "If your contracts are already competitive, that\u2019s exactly what I\u2019ll tell you."},
        {"icon": _IC["people"],
         "h": "I\u2019ll recommend keeping incumbent suppliers whenever they\u2019re the best choice.",
         "s": "The objective isn\u2019t changing vendors. It\u2019s improving outcomes."},
        {"icon": _IC["scale"],
         "h": "Every recommendation will be supported by evidence.",
         "s": "You\u2019ll see the data before making any decision."},
        {"icon": _IC["check"],
         "h": "You remain in complete control.",
         "s": "Nothing changes without your approval. Ever."},
        {"icon": _IC["compass"],
         "h": "My success depends on yours.",
         "s": "If we don\u2019t create verified savings, there is no fee."},
    ],

    "person": {
        "name": "John Wylie",
        "role": "Senior Consultant",
        "org":  "ERA Group",
        "email": "jwylie@eragroup.com",
        "phone": "703.244.9868",
    },

    "footer_left_a": "Executive Opportunity Brief",
    "footer_left_b": "Human Services",
    "footer_right":  "Value Through Insight\u2122",
}

_TPL = Template(open(os.path.join(HERE, "closing_template.html")).read())
_FONTS = {
    "lora_b64":    _b64(os.path.join(CS_FONTS, "Lora.ttf")),
    "lora_it_b64": _b64(os.path.join(CS_FONTS, "Lora.ttf")),   # faux-italic for the signature
    "pop_r_b64":   _b64(os.path.join(CS_FONTS, "Poppins-Regular.ttf")),
    "pop_sb_b64":  _b64(os.path.join(CS_FONTS, "Poppins-SemiBold.ttf")),
    "pop_b_b64":   _b64(os.path.join(CS_FONTS, "Poppins-Bold.ttf")),
}


_LOGO_URI = _img_uri(os.path.join(ASSETS, "era_logo.png"))


def _resolve_photo(data):
    if data.get("photo_uri"):
        return data["photo_uri"]
    path = data.get("photo_path") or os.path.join(ASSETS, "jw_headshot.jpg")
    return _img_uri(path)


def build_ctx(data=None):
    ctx = copy.deepcopy(DEFAULT)
    if data:
        person = {**ctx["person"], **(data.get("person") or {})}
        ctx.update({k: v for k, v in data.items() if k not in ("person", "photo_path", "photo_uri")})
        ctx["person"] = person
    ctx["photo_uri"] = _resolve_photo(data or {})
    ctx["logo_uri"] = data.get("logo_uri") if (data or {}).get("logo_uri") else _LOGO_URI
    ctx.update(_FONTS)
    return ctx


def render(data, out_pdf):
    html = _TPL.render(**build_ctx(data or {}))
    HTML(string=html).write_pdf(out_pdf)
    return out_pdf


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "Closing_BeforeWeMeet.pdf")
    render({}, p)
    print("wrote", p)
