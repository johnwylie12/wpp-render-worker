#!/usr/bin/env python3
"""
Personalized 5x7 intro note — the loose card that rides on top of the Executive
Opening Package. Clean single column: centered ERA logo, "Dear <first>," greeting,
the approved note copy, "Warm regards," signoff, and the "value through insight"
wordmark. Mirrors the closing / case_study engine pattern (Poppins + logo base64-
embedded), and reuses the shared case_study brand assets, so this engine ships as
TEXT ONLY (engine + template) — no new binaries to commit.

Usage
-----
    python note_card/note_card_engine.py [out_dir]
    from note_card_engine import render
    render({"recipient_first": "Sue", "org": "Carolina Health Centers"}, "/tmp/card.pdf")

Data (personalize with recipient_first + org)
    recipient_first   first name ONLY, e.g. "Sue"        (default "there")
    org               organization name                  (default "your organization")
    body              list of paragraph strings          (default below; {org} substituted)
    signoff{name,role,contact}                            signoff overrides
"""
import base64, os, sys
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.join(os.path.dirname(HERE), "case_study", "assets")
FONTS = os.path.join(SHARED, "fonts")
BRAND_FONTS = os.path.join(os.path.dirname(HERE), "fonts")  # repo-root brand fonts (Trebuchet)


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _img_uri(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "png"
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{_b64(path)}"


DEFAULT_BODY = [
    "Enclosed is a complimentary Executive Opportunity Brief we prepared for {org} — an "
    "independent, outside-in look at where indirect spending may be running above market, "
    "and what that could return to your mission.",
    "Nothing here is a bill, and nothing changes without your approval. If the range is "
    "worth confirming, a no-cost 30-day baseline tests it against your actual contracts. "
    "No savings, no fee.",
    "I’d welcome a brief conversation.",
]
DEFAULT_SIGNOFF = {
    "name": "John Wylie",
    "role": "Senior Advisor, ERA Group",
    "contact": "703.244.9868 | jwylie@eragroup.com",
}


VTI_B64 = "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"


def render(data, out_pdf):
    data = data or {}
    first = (data.get("recipient_first") or "there").strip() or "there"
    org = (data.get("org") or "your organization").strip() or "your organization"
    body = data.get("body")
    if not body:
        body = [ln.replace("{org}", org) for ln in DEFAULT_BODY]
    signoff = {**DEFAULT_SIGNOFF, **(data.get("signoff") or {})}
    ctx = {
        "logo_uri": _img_uri(os.path.join(SHARED, "era_logo.png")),
        "vti_uri": f"data:image/png;base64,{VTI_B64}",
        # Brand fonts per ERA playbook: Trebuchet MS body (Arial Nova fallback).
        "tre_r_b64": _b64(os.path.join(BRAND_FONTS, "Trebuchet MS.ttf")),
        "tre_b_b64": _b64(os.path.join(BRAND_FONTS, "Trebuchet MS Bold.ttf")),
        "first": first,
        "body": body,
        "signoff": signoff,
    }
    tpl = Template(open(os.path.join(HERE, "note_card_template.html"), encoding="utf-8").read())
    HTML(string=tpl.render(**ctx), base_url=HERE).write_pdf(out_pdf)
    return out_pdf


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    p = os.path.join(out_dir, "Note_Card.pdf")
    render({"recipient_first": "Sue", "org": "Carolina Health Centers"}, p)
    print("wrote", p)
