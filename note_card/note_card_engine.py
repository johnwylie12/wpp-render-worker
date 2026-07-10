#!/usr/bin/env python3
"""
Personalized 5x7 intro card — the loose note that rides on top of the Executive
Opening Package. First-name greeting (house preference), a short warm note, and
the WPP signoff. Mirrors the closing / case_study engine pattern: Lora + Poppins
and the ERA logo are base64-embedded so the worker container needs no system
fonts or network. Reuses the shared case_study brand assets, so this engine ships
as TEXT ONLY (engine + template) — no new binaries to commit.

Usage
-----
    python note_card/note_card_engine.py [out_dir]
    from note_card_engine import render
    render({"recipient_first": "Rob", "org": "HonorBridge"}, "/tmp/card.pdf")

Data (all optional; personalize with recipient_first + org)
    recipient_first   first name ONLY, e.g. "Rob"        (default "there")
    org               organization name                  (default "")
    seq               collation stamp, e.g. "3 of 18"    (omit for single prints)
    eyebrow           small gold kicker                  (has a default)
    body              list of paragraph strings          (has a default; {org} substituted)
    signoff{mark,name,role,tag}                           signoff overrides
"""
import base64, os, sys
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
# Reuse the shared brand assets (logo + fonts) so this engine ships as text only.
SHARED = os.path.join(os.path.dirname(HERE), "case_study", "assets")
FONTS = os.path.join(SHARED, "fonts")


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _img_uri(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "png"
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{_b64(path)}"


DEFAULT_BODY = [
    "The brief enclosed with this note was built specifically for {org} \u2014 your own "
    "figures and categories, not boilerplate.",
    "If even a line or two of it proves useful, it has done its job.",
    "I would welcome twenty minutes to walk you through what we found, and to hear where "
    "it lands with you.",
]
DEFAULT_SIGNOFF = {
    "mark": "John Wylie",
    "name": "John Wylie",
    "role": "Senior Advisor, ERA Group",
    "tag": "Value Through Insight\u2122",
}


def render(data, out_pdf):
    data = data or {}
    first = (data.get("recipient_first") or "there").strip() or "there"
    org = (data.get("org") or "").strip()
    body = data.get("body")
    if not body:
        body = [ln.replace("{org}", org or "your organization") for ln in DEFAULT_BODY]
    signoff = {**DEFAULT_SIGNOFF, **(data.get("signoff") or {})}
    ctx = {
        "logo_uri": _img_uri(os.path.join(SHARED, "era_logo.png")),
        "lora_b64": _b64(os.path.join(FONTS, "Lora.ttf")),
        "pop_r_b64": _b64(os.path.join(FONTS, "Poppins-Regular.ttf")),
        "pop_sb_b64": _b64(os.path.join(FONTS, "Poppins-SemiBold.ttf")),
        "pop_b_b64": _b64(os.path.join(FONTS, "Poppins-Bold.ttf")),
        "eyebrow": data.get("eyebrow") or "A note before you read",
        "greeting": f"{first},",
        "body": body,
        "signoff": signoff,
        "seq": str(data.get("seq") or ""),
    }
    tpl = Template(open(os.path.join(HERE, "note_card_template.html"), encoding="utf-8").read())
    HTML(string=tpl.render(**ctx), base_url=HERE).write_pdf(out_pdf)
    return out_pdf


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    p = os.path.join(out_dir, "Note_Card.pdf")
    render({"recipient_first": "Rob", "org": "HonorBridge", "seq": "3 of 18"}, p)
    print("wrote", p)
