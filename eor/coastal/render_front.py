#!/usr/bin/env python3
"""Rebuild the COVER and the COVER LETTER of the Coastal Enterprises Report.

    python eor/coastal/render_front.py --src <reading.pdf> --out <fixed.pdf>

John, 2026-09-07: "This is not perfect. But it is the format that works. Use the
format." So the format is kept exactly — same geometry, same order, same copy —
and only what is BROKEN inside it is repaired. Pages 2 and 4-16 are copied
through untouched, byte for byte.

WHAT WAS BROKEN, AND HOW IT WAS ESTABLISHED

  Colour. The cover was printed in #F2A900 and #0A2E4F. brand_tokens names
    #F2A900 forbidden in as many words — "NOT #F2A900 ... (WPP golds)" — and the
    ERA navy is Daybreak Blue #003A70, not #0A2E4F. Both are near misses, which
    is the exact failure the token table exists to prevent, on the first page a
    CFO sees.
  Typeface. DejaVu Serif and Carlito. Neither is an ERA face; both are
    substitution artefacts. Paralucent is the primary, Trebuchet the secondary.
  The date collided with the statement. "SEPTEMBER 4, 2026" was set at y=466.7
    while the statement block ran y=448-510, so it printed straight through the
    orange rail and the second line of the sentence.
  No ERA mark anywhere on the cover. The identity goes on white per
    brand_tokens, so it sits in the white band the format already has at the
    foot, rather than on a plate bolted onto the navy.
  VALUE THROUGH INSIGHT was typed as letterspaced characters on both pages.
    LAW 23 / settled #175: it is a registered lockup and must be the asset.
  The letter had no letterhead, no signature and no QR.
  "Dear Colleague," — settled #174: no validated name means we address the
    OFFICE. "Dear Colleague" reads as a circular on a document that claims to be
    prepared exclusively.
  670 engagements. era_projects holds 6,389 engagements totalling $2.253B of
    spend and $616.1M returned. The letter's own $2.25B and $600M are the
    all-rows totals, so 670 is the same set counted wrong — by a factor of ten,
    against ERA.

WHAT WAS ADDED: one sentence giving the ask a size. Every figure in it is this
Report's own, framed the way the Report frames them. This document publishes no
completed-work median and no recovery estimate — deliberately; page 9 says "these
are the same disclosure expressed against two denominators" — so none is invented
here either.
"""
import argparse, base64, io, os, re, sys

import pymupdf
import segno
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
from wpp_signatures import signature_data_uri  # noqa: E402

FONTS = os.path.join(REPO, "fonts").replace(" ", "%20")

# brand_tokens, not sampled off a raster and not remembered
NAVY    = "#003A70"      # Daybreak Blue
SUNRISE = "#FF9C00"      # Sunrise Yellow
INK     = "#1B2A41"
SLATE   = "#5A6577"
MIST    = "#F2F5F8"
HAIR    = "#D7DFE9"

ACCOUNT = dict(
    org_name="Coastal Enterprises of Jacksonville",
    addr_city_state="Jacksonville, North Carolina",
    recipient_title="Chief Financial Officer",
    vertical_label="EMPLOYMENT SERVICES",
    doc_title="EXECUTIVE OPPORTUNITY REPORT",
    date="September 4, 2026",
    portal="portal.wpp-us.com/coastalenterprises-benchmark",
    portal_url="https://portal.wpp-us.com/coastalenterprises-benchmark",
    statement_a="What a filing shows about how you buy",
    statement_b="before we ever asked for your time.",
    signoff_name="John Wylie", signoff_title="Consulting Partner",
    signoff_firm="ERA Group", signoff_email="jwylie@eragroup.com",
    signoff_phone="703.244.9868",
)

STRIP = (("OUTSIDE-IN ANALYSIS", "INFORMED PERSPECTIVE", "BEFORE ANY MEETING"),
         ("MISSION FOCUSED", "STEWARDSHIP TODAY.", "STRENGTH TOMORROW."),
         ("MEASURABLE IMPACT", "DOLLARS RECOVERED.", "OPPORTUNITIES FUNDED."))

PARAGRAPHS = [
    "We are sending the enclosed Executive Opportunity Report because we believe "
    "that every dollar that does not have to be spent on indirect expense is a "
    "dollar available for the people you place in work.",

    "We prepared it before reaching out to you, from public information only. Its "
    "purpose is to present where the available evidence suggests opportunity, and "
    "where it does not. We treat these patterns as starting points of discussion "
    "rather than conclusions.",

    # ADDED. The ask had no size on it. Every figure is this Report's own.
    "Your FY2024 filing breaks out <b>$1.62 million</b> of indirect spend across "
    "six categories. Insurance is <b>$1.05 million</b> of that, and your plan&rsquo;s "
    "Form 5500 Schedule A discloses <b>$526 thousand</b> of intermediary "
    "compensation inside that one category. That disclosure is why the Report "
    "starts there.",

    # CORRECTED: 670 -> 6,389. era_projects, all rows, the same set the $2.25B
    # and $600M come from.
    "ERA Group has reviewed more than $2.25 billion of indirect spend across 6,389 "
    "engagements and returned over $600 million to the organizations we work with. "
    "We are specialists in one thing: the recurring operating costs that sit "
    "outside your program delivery.",

    "If any of it is directionally useful, we would welcome a short conversation. "
    "If the current arrangements are already competitive, that is a valuable "
    "conclusion as well &mdash; and it costs you nothing to establish.",

    "Nothing about the way we work commits you to anything. No supplier changes "
    "without your approval, incumbent suppliers frequently remain, and if we do "
    "not create verified recovery there is no fee.",
]


def uri(path, mime="image/png"):
    with open(path, "rb") as fh:
        return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()


FACE = f"""
@font-face{{font-family:'Paralucent';font-weight:500;
  src:url('file://{FONTS}/fonnts.com-Paralucent_Medium.otf') format('opentype')}}
@font-face{{font-family:'Paralucent';font-weight:300;
  src:url('file://{FONTS}/fonnts.com-Paralucent_Light.otf') format('opentype')}}
@font-face{{font-family:'Trebuchet MS';font-weight:400;
  src:url('file://{FONTS}/Trebuchet%20MS.ttf') format('truetype')}}
@font-face{{font-family:'Trebuchet MS';font-weight:700;
  src:url('file://{FONTS}/Trebuchet%20MS%20Bold.ttf') format('truetype')}}
"""

TOKENS = {"__NAVY__": NAVY, "__SUNRISE__": SUNRISE, "__MIST__": MIST,
          "__INK__": INK, "__SLATE__": SLATE, "__HAIR__": HAIR}


def paint(css):
    """CSS is full of per-cent signs, so Python's % formatting cannot be used on
    it — the first `width:26%` is read as a conversion and the string blows up.
    Tokens instead."""
    for k, v in TOKENS.items():
        css = css.replace(k, v)
    return css


COVER = """<html><head><meta charset="utf-8"><style>
""" + FACE + """
@page{ size:Letter; margin:0 }
*{ margin:0; padding:0; box-sizing:border-box }
body{ font-family:'Trebuchet MS',Arial,sans-serif; }
.pg{ position:relative; width:612pt; height:792pt; }
/* the format's own bands, to the point */
.navy { position:absolute; left:0; right:0; top:0;      height:532.8pt; background:__NAVY__ }
.grey { position:absolute; left:0; right:0; top:532.8pt;height:172.8pt; background:__MIST__ }
.bar  { position:absolute; left:0; right:0; top:705.6pt;height:36pt;   background:__NAVY__ }
.L{ position:absolute; left:68.4pt }
.kick{ top:76pt; color:__SUNRISE__; font-weight:bold; font-size:10pt; letter-spacing:.26em }
.krule{ top:105.9pt; width:43.5pt; height:2pt; background:__SUNRISE__ }
.name{ top:118pt; font-family:'Paralucent',sans-serif; font-weight:500; font-size:34pt;
       line-height:1.14; color:#fff; letter-spacing:-.3px; max-width:64% }
.date{ top:232pt; color:#9FB6CE; font-size:10pt; letter-spacing:.22em; font-weight:bold }
.nrule{ top:388.1pt; width:82.5pt; height:2pt; background:__SUNRISE__ }
.doct{ top:398pt; color:#fff; font-weight:bold; font-size:10pt; letter-spacing:.20em }
.vert{ top:415pt; color:__SUNRISE__; font-size:10pt; letter-spacing:.20em }
/* the statement, on its rail. The date used to be printed through it. */
.stmt{ top:448pt; padding-left:20pt; border-left:3pt solid __SUNRISE__;
       font-family:'Paralucent',sans-serif; font-weight:300; font-size:16.5pt;
       line-height:1.42; color:#fff; max-width:58% }
.stmt em{ font-style:normal; color:__SUNRISE__ }
.col{ position:absolute; top:560pt; width:26% }
.c1{left:68.4pt} .c2{left:226.8pt} .c3{left:385.2pt}
.ct{ color:__INK__; font-weight:bold; font-size:10pt; letter-spacing:.10em }
.cs{ color:__SLATE__; font-size:10pt; line-height:1.62; margin-top:7pt }
.cs b{ color:__INK__ }
.vti{ position:absolute; left:0; right:0; top:714pt; text-align:center }
.vti img{ height:19pt }
/* the identity goes on WHITE (brand_tokens), so it sits in the white band the
   format already has at the foot rather than on a plate over the navy. */
.era{ position:absolute; left:68.4pt; top:752pt }
.era img{ height:26pt }
</style></head><body><div class="pg">
  <div class="navy"></div><div class="grey"></div><div class="bar"></div>
  <div class="L kick">PREPARED EXCLUSIVELY FOR</div>
  <div class="L krule"></div>
  <div class="L name">{{ org_name }}</div>
  <div class="L date">{{ date_caps }}</div>
  <div class="L nrule"></div>
  <div class="L doct">{{ doc_title }}</div>
  <div class="L vert">{{ vertical_label }}</div>
  <div class="L stmt">{{ statement_a }}<br><em>{{ statement_b }}</em></div>
  {% for t, a, b in strip %}
  <div class="col c{{ loop.index }}"><div class="ct">{{ t }}</div>
    <div class="cs">{{ a }}<br><b>{{ b }}</b></div></div>
  {% endfor %}
  <div class="vti"><img src="{{ vti_white }}" alt="Value Through Insight"></div>
  <div class="era"><img src="{{ era_logo }}" alt="ERA Group"></div>
</div></body></html>"""

LETTER = """<html><head><meta charset="utf-8"><style>
""" + FACE + """
@page{ size:Letter; margin:0.5in 0.92in 0.38in 0.92in }
*{ margin:0; padding:0; box-sizing:border-box }
body{ font-family:'Trebuchet MS',Arial,sans-serif; font-size:10.5pt;
      line-height:1.40; color:__INK__ }
.hd img{ height:38pt; display:block; margin-bottom:7pt }
.hd .o{ width:150pt; height:3pt; background:__SUNRISE__ }
.hd .n{ height:1.6pt; background:__NAVY__; margin-top:7pt }
.date{ margin:11pt 0 10pt; color:__SLATE__; font-size:10pt }
.addr{ line-height:1.40; margin-bottom:10pt }
.addr .t{ color:__NAVY__; font-weight:bold }
.sal{ margin-bottom:8pt }
p{ margin-bottom:7pt }
.vale{ margin-top:9pt }
.close{ display:flex; gap:0.3in; margin-top:9pt; align-items:flex-start }
.sig{ flex:1 }
.sig img{ width:112pt; display:block; margin:2pt 0 3pt }
.sig .nm{ font-weight:bold; color:__NAVY__ }
.sig .tl,.sig .ct{ font-size:10pt; color:__SLATE__ }
/* 3.4in, because the URL needs 234pt at the 10pt floor and a 2.55in column
   wrapped it onto two lines. Settled #174: the portal URL is one readable
   line with no wrap and no hidden character. nowrap makes a future overflow
   visible instead of silently hyphenating it again. */
.portal{ flex:0 0 3.4in; border-top:1pt solid __HAIR__; padding-top:9pt }
.portal .h{ color:__NAVY__; font-weight:bold; font-size:10pt }
.portal p{ font-size:10pt; color:__SLATE__; margin:5pt 0 0 }
.portal img{ width:0.82in; height:0.82in; display:block; margin:7pt 0 6pt }
.portal .u{ font-size:10pt; font-weight:bold; color:__NAVY__; white-space:nowrap }
.portal .n{ font-size:10pt; color:__SLATE__; margin-top:3pt }
.foot{ margin-top:11pt; text-align:center }
.foot img{ height:17pt }
</style></head><body>
  <div class="hd"><img src="{{ era_logo }}" alt="ERA Group">
    <div class="o"></div><div class="n"></div></div>
  <div class="date">{{ date }}</div>
  <div class="addr"><span class="t">{{ recipient_title }}</span><br>
    {{ org_name }}<br>{{ addr_city_state }}</div>
  <div class="sal">Dear {{ recipient_title }},</div>
  {% for p in paragraphs %}<p>{{ p }}</p>{% endfor %}
  <div class="vale">Best regards,</div>
  <div class="close">
    <div class="sig">
      <img src="{{ signature }}" alt="{{ signoff_name }}">
      <div class="nm">{{ signoff_name }}</div>
      <div class="tl">{{ signoff_title }} &middot; {{ signoff_firm }}</div>
      <div class="ct">{{ signoff_email }} &middot; {{ signoff_phone }}</div>
    </div>
    <div class="portal">
      <div class="h">Your Report is live online</div>
      <p>Every figure is interactive &mdash; change any assumption and the model moves with it.</p>
      <img src="{{ qr }}" alt="Scan for your Report">
      <div class="u">{{ portal }}</div>
      <div class="n">No code. No form. No login.</div>
    </div>
  </div>
  <div class="foot"><img src="{{ vti_blue }}" alt="Value Through Insight"></div>
</body></html>"""


def build(tmpdir):
    qr = segno.make(ACCOUNT["portal_url"], error="m")
    buf = io.BytesIO(); qr.save(buf, kind="png", scale=10, border=0)
    ctx = dict(ACCOUNT,
               strip=STRIP, paragraphs=PARAGRAPHS,
               date_caps=ACCOUNT["date"].upper(),
               era_logo=uri(os.path.join(REPO, "case_study/assets/era_logo.png")),
               vti_white=uri(os.path.join(REPO, "meeting_label/assets/vti_white_lockup.png")),
               vti_blue=uri(os.path.join(REPO, "meeting_label/assets/vti_logo.png")),
               signature=signature_data_uri("3"),
               qr="data:image/png;base64," + base64.b64encode(buf.getvalue()).decode())
    cover = os.path.join(tmpdir, "cover.pdf")
    letter = os.path.join(tmpdir, "letter.pdf")
    HTML(string=Template(paint(COVER)).render(**ctx), base_url=REPO).write_pdf(cover)
    HTML(string=Template(paint(LETTER)).render(**ctx), base_url=REPO).write_pdf(letter)
    return cover, letter


def splice(src, cover, letter, out):
    """Page 1 and page 3 replaced. Everything else copied through untouched."""
    doc = pymupdf.open(src)
    new = pymupdf.open()
    for i in range(doc.page_count):
        if i == 0:
            new.insert_pdf(pymupdf.open(cover))
        elif i == 2:
            new.insert_pdf(pymupdf.open(letter))
        else:
            new.insert_pdf(doc, from_page=i, to_page=i)
    new.save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tmp = os.path.join(HERE, "out"); os.makedirs(tmp, exist_ok=True)
    cover, letter = build(tmp)
    for f, n in ((cover, "cover"), (letter, "letter")):
        pages = pymupdf.open(f).page_count
        if pages != 1:
            raise SystemExit(f"{n} rendered {pages} pages; it must be one.")

    # settled #174, asserted against the RENDERED page rather than the CSS
    doc = pymupdf.open(letter)
    spans = [sp for pg in doc for bl in pg.get_text("dict")["blocks"]
             for ln in bl.get("lines", []) for sp in ln["spans"]
             if "portal.wpp-us.com" in sp["text"]]
    if len(spans) != 1 or spans[0]["text"].strip() != ACCOUNT["portal"]:
        raise SystemExit(f"the portal URL wrapped: {[s['text'] for s in spans]}")
    small = [(round(sp["size"], 1), sp["text"][:30]) for pg in doc
             for bl in pg.get_text("dict")["blocks"] for ln in bl.get("lines", [])
             for sp in ln["spans"] if sp["text"].strip() and round(sp["size"], 1) < 10]
    if small:
        raise SystemExit(f"below the 10pt floor: {small}")
    text = " ".join(pg.get_text() for pg in doc)
    for banned in ("Dear Colleague", "670 engagements", "savings"):
        if banned in text:
            raise SystemExit(f"{banned!r} is still in the letter")
    print("letter: 1 page, URL unbroken, nothing under 10pt, no banned copy")
    print("wrote", splice(a.src, cover, letter, a.out))
