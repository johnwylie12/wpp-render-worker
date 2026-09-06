#!/usr/bin/env python3
"""Render the Brief's cover — from the repo template, never drawn by hand.

Settled #172 says it twice: "THE REPO TEMPLATE IS THE COVER. Do not draw one."
This renders cover/cover_page_template_v2.html through the existing cover engine's
context builder, so the hero image, the diagonal, the ERA logo, the benefit strip
and the name autofit all stay exactly where they are.

What the CFO rebuild changes, and nothing else:
  * the second explanatory sentence is GONE. "We identify where to look, validate
    what is real, and help capture the value across every applicable category."
    made the cover read like instructions.
  * the hero statement is larger and has room: 14pt -> 19pt.
  * only "returned to mission" is orange.
  * one quiet supporting line underneath, at reading size.
"""
import argparse, os, sys

from jinja2 import Template

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "cover"))
import cover_page_engine as cpe  # noqa: E402

TEMPLATE = os.path.join(REPO, "cover", "cover_page_template_v2.html")

STATEMENT = ('Your operating budget may contain dollars that can be '
             '<span class="g">returned to mission</span>.'
             '<span class="quiet">An outside-in view of where the evidence '
             'says to look first.</span>')


def render(content, out_pdf, date_str, title="Executive Opportunity Brief"):
    from weasyprint import HTML
    ctx = cpe.build(content, title=title, date_str=date_str)
    # build() escapes a plain `statement`; this one carries the two spans the
    # spec asks for, so it goes in after the escaping rather than through it.
    ctx["statement_html"] = STATEMENT
    HTML(string=Template(open(TEMPLATE).read()).render(**ctx),
         base_url=REPO).write_pdf(out_pdf)
    cpe._assert_not_blank(out_pdf, ctx["org_name"])
    return ctx["hero_rel"]


# The hero is named EXPLICITLY, not looked up. The spec says KEEP the current
# photograph, and "current" was established by pixel-matching the image embedded
# in the shipped cover against every file in cir/src/assets/heroes — an exact
# match, mean absolute difference 0.0, on human_services.png. A vertical lookup
# would have gone hunting for "employment_services" and either failed or found a
# different picture, and the wrong photograph is worse than no cover: it mails.
GOODWILL = {"org": {"name": "Goodwill Industries of South Florida",
                    "vertical": "human_services",
                    "vertical_label": "Employment Services"},
            "assets": {"hero": "heroes/human_services.png"}}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "covers", "cover_cfo.pdf"))
    ap.add_argument("--date", default="September 6, 2026")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    print("wrote", a.out, "hero:", render(GOODWILL, a.out, a.date))
