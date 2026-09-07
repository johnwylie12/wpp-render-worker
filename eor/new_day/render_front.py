#!/usr/bin/env python3
"""Cover, cover letter and back cover for the New Day Brief.

GATE 2: the cover is the APPROVED ERA asset rendered through cover_page_engine.
It is never a hand-drawn navy panel — the brief records that error as having been
made four times already. The hero is named explicitly rather than looked up, and
which image it is was established by pixel-matching the one already shipping.

The letter obeys settled #174: nothing on it is position:absolute or
position:fixed, and it is asserted against the rendered PDF.
"""
import argparse, base64, io, os, sys

import pymupdf
import segno
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "cover"))
sys.path.insert(0, HERE)
import cover_page_engine as cpe            # noqa: E402
import data_goodwill as D                  # noqa: E402
from wpp_signatures import signature_data_uri  # noqa: E402

FONTS = os.path.join(REPO, "fonts").replace(" ", "%20")
NAVY, SUNRISE, INK, SLATE, HAIR = "#003A70", "#FF9C00", "#1B2A41", "#5A6577", "#D7DFE9"
MIDNIGHT = "#111127"

COVER_TPL = os.path.join(REPO, "cover", "cover_page_template_v2.html")
# Four lines plus a two-line quiet note grew the block down into the date, which
# sits at 74.6% in the shared template. The copy gives, not the template — the
# template is used by two other builds.
STATEMENT = ('Forty Goodwill affiliates break out this line. '
             '<span class="g">Thirty-nine spend less than you.</span>'
             '<span class="quiet">Public filings only.</span>')

CONTENT = {"org": {"name": D.SUBJECT["name"].replace(" Inc", ""),
                   "vertical": "human_services",
                   "vertical_label": "Employment Services"},
           "assets": {"hero": "heroes/human_services.png"}}


def uri(path):
    with open(path, "rb") as fh:
        return "data:image/png;base64," + base64.b64encode(fh.read()).decode()


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

LETTER = """<html><head><meta charset="utf-8"><style>
""" + FACE + """
@page{ size:Letter; margin:0.5in 0.92in 0.4in 0.92in }
*{ margin:0; padding:0; box-sizing:border-box }
/* settled #174: NOTHING here is position:absolute or position:fixed. */
body{ font-family:'Trebuchet MS',Arial,sans-serif; font-size:10.5pt;
      line-height:1.42; color:__INK__ }
.hd img{ height:38pt; display:block; margin-bottom:7pt }
.hd .o{ width:150pt; height:3pt; background:__SUNRISE__ }
.hd .n{ height:1.6pt; background:__NAVY__; margin-top:7pt }
.date{ margin:11pt 0 10pt; color:__SLATE__; font-size:10pt }
.addr{ line-height:1.40; margin-bottom:10pt }
.addr .rn{ color:__NAVY__; font-weight:bold; font-size:11.5pt }
.sal{ margin-bottom:8pt }
p{ margin-bottom:7pt }
.ask{ font-weight:bold; color:__NAVY__; margin:10pt 0 8pt }
.vale{ margin-top:9pt }
.close{ display:flex; gap:0.3in; margin-top:9pt; align-items:flex-start }
.sig{ flex:1 }
.sig img{ width:112pt; display:block; margin:2pt 0 3pt }
.sig .nm{ font-weight:bold; color:__NAVY__ }
.sig .tl,.sig .ct{ font-size:10pt; color:__SLATE__ }
.portal{ flex:0 0 3.4in; border-top:1pt solid __HAIR__; padding-top:9pt }
.portal .h{ color:__NAVY__; font-weight:bold; font-size:10pt }
.portal img{ width:0.82in; height:0.82in; display:block; margin:7pt 0 6pt }
.portal .u{ font-size:10pt; font-weight:bold; color:__NAVY__; white-space:nowrap }
.portal .n{ font-size:10pt; color:__SLATE__; margin-top:3pt }
.foot{ margin-top:12pt; text-align:center }
.foot img{ height:17pt }
</style></head><body>
  <div class="hd"><img src="{{ era_logo }}"><div class="o"></div><div class="n"></div></div>
  <div class="date">{{ date }}</div>
  <div class="addr"><span class="rn">{{ recipient }}</span><br>
    {{ recipient_title }}<br>{{ org }}<br>{{ addr1 }}<br>{{ addr2 }}</div>
  <div class="sal">Dear {{ first_name }},</div>
  <p>Forty Goodwill affiliates break out the same operating supply line on their
     own Form 990. Thirty-nine of them spend a smaller share of revenue on it than
     {{ org }} does &mdash; and the affiliate median, 2.44%, is the same as the
     median across all nonprofits. Running the identical donated-goods model does
     not move that ratio.</p>
  <p>We prepared the enclosed Executive Opportunity Brief before contacting you,
     from public filings only. It tests the two explanations that would settle the
     question from outside &mdash; scale and state &mdash; and both fail: the two
     largest affiliates in the comparison are larger than you and spend under a
     tenth as much.</p>
  <p>It also reads your filing a second way. Part VII Section B names five of your
     suppliers, and those same suppliers are named in other organisations' returns
     with the amounts they were paid. Two of your five appear often enough to place.</p>
  <p>We are not concluding that anyone is overpaying. Every explanation we can test
     from public data has failed, and the ones that remain &mdash; accounting
     treatment, purchasing, or both &mdash; are in your ledger rather than ours.
     That is the whole of the question.</p>
  <p class="ask">Would you give us ninety minutes, with whoever owns the general
     ledger, to establish which it is?</p>
  <p>You would leave with a written read of where your position is explained by
     treatment and where it is not, whether or not you engage ERA. Nothing changes
     without your approval, incumbent suppliers frequently remain, and if we create
     no verified recovery there is no fee.</p>
  <div class="vale">Best regards,</div>
  <div class="close">
    <div class="sig"><img src="{{ signature }}">
      <div class="nm">John Wylie</div>
      <div class="tl">Consulting Partner &middot; ERA Group</div>
      <div class="ct">jwylie@eragroup.com &middot; 703.244.9868</div></div>
    <div class="portal"><div class="h">Your Brief is live online</div>
      <img src="{{ qr }}"><div class="u">{{ portal }}</div>
      <div class="n">No code. No form. No login.</div></div>
  </div>
  <div class="foot"><img src="{{ vti }}"></div>
</body></html>"""

BACK = """<html><head><meta charset="utf-8"><style>
""" + FACE + """
@page{ size:Letter; margin:0 }
*{ margin:0; padding:0; box-sizing:border-box }
.pg{ position:relative; width:612pt; height:792pt; background:__NAVY__ }
.in{ padding:150pt 78pt 0 78pt }
.rule{ width:96pt; height:3pt; background:__SUNRISE__; margin-bottom:26pt }
h1{ font-family:'Paralucent',sans-serif; font-weight:500; font-size:25pt;
    line-height:1.24; color:#fff; max-width:74%; margin-bottom:22pt }
p{ font-family:'Trebuchet MS',Arial,sans-serif; font-size:11pt; line-height:1.55;
   color:#C6D4E4; max-width:70%; margin-bottom:12pt }
.sig{ margin-top:54pt; font-family:'Trebuchet MS',Arial,sans-serif; font-size:10pt;
      line-height:1.6; color:#9FB6CE }
.sig b{ color:#fff; font-size:11pt }
.vti{ position:absolute; left:0; right:0; bottom:44pt; text-align:center }
.vti img{ height:19pt }
</style></head><body><div class="pg"><div class="in">
  <div class="rule"></div>
  <h1>Is it how the line is recorded, or how it is bought?</h1>
  <p>Every explanation we could test from public filings has failed. Your own peer
     set does not explain the position, scale does not explain it, and neither does
     the state you operate in.</p>
  <p>What remains is a question only your ledger can answer &mdash; and answering it
     costs one conversation.</p>
  <div class="sig"><b>John Wylie</b><br>Consulting Partner, ERA Group<br>
     jwylie@eragroup.com &middot; 703.244.9868</div>
</div><div class="vti"><img src="{{ vti_white }}"></div></div></body></html>"""


def paint(css):
    for k, v in {"__NAVY__": NAVY, "__SUNRISE__": SUNRISE, "__INK__": INK,
                 "__SLATE__": SLATE, "__HAIR__": HAIR, "__MIDNIGHT__": MIDNIGHT}.items():
        css = css.replace(k, v)
    return css


def build(outdir):
    os.makedirs(outdir, exist_ok=True)
    cover = os.path.join(outdir, "cover.pdf")
    ctx = cpe.build(CONTENT, title="Executive Opportunity Brief",
                    date_str=D.SUBJECT["date"])
    ctx["statement_html"] = STATEMENT
    HTML(string=Template(open(COVER_TPL).read()).render(**ctx),
         base_url=REPO).write_pdf(cover)
    cpe._assert_not_blank(cover, ctx["org_name"])

    qr = segno.make(f"https://portal.wpp-us.com/{D.SUBJECT['portal']}", error="m")
    buf = io.BytesIO(); qr.save(buf, kind="png", scale=10, border=0)
    common = dict(
        era_logo=uri(os.path.join(REPO, "case_study/assets/era_logo.png")),
        vti=uri(os.path.join(REPO, "meeting_label/assets/vti_logo.png")),
        vti_white=uri(os.path.join(REPO, "meeting_label/assets/vti_white_lockup.png")),
        signature=signature_data_uri("3"),
        qr="data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
        date=D.SUBJECT["date"], recipient=D.SUBJECT["recipient"],
        recipient_title=D.SUBJECT["recipient_title"], org=D.SUBJECT["short"],
        addr1=D.SUBJECT["addr1"], addr2=D.SUBJECT["addr2"],
        first_name=D.SUBJECT["recipient"].split()[0],
        portal=f"portal.wpp-us.com/{D.SUBJECT['portal']}")
    letter = os.path.join(outdir, "letter.pdf")
    back = os.path.join(outdir, "back.pdf")
    HTML(string=Template(paint(LETTER)).render(**common), base_url=REPO).write_pdf(letter)
    HTML(string=Template(paint(BACK)).render(**common), base_url=REPO).write_pdf(back)
    return cover, letter, back


def assert_174(letter):
    """settled #174, run against the RENDERED page."""
    d = pymupdf.open(letter)
    t = " ".join(p.get_text() for p in d)
    spans = [s for p in d for b in p.get_text("dict")["blocks"]
             for l in b.get("lines", []) for s in l["spans"] if s["text"].strip()]
    checks = [
        ("exactly one page", d.page_count == 1),
        ("logo, signature and QR present", len(d[0].get_images()) >= 3),
        ("no 'savings' as a noun (LAW 8)", "savings" not in t.lower()),
        ("'No code. No form. No login.'", "no code. no form. no login." in t.lower()),
        ("Consulting Partner, not Senior Consultant",
         "Consulting Partner" in t and "Senior Consultant" not in t),
        ("no access code, no '?c='", "access code" not in t.lower() and "?c=" not in t),
        ("portal URL clean and unbroken",
         len([s for s in spans if "portal.wpp-us.com" in s["text"]]) == 1),
        ("no unrendered placeholders", "{{" not in t and "[Name" not in t),
        ("salutation is the validated person",
         f"Dear {D.SUBJECT['recipient'].split()[0]}," in t and "Dear Colleague" not in t),
    ]
    small = [(round(s["size"], 1), s["text"][:30]) for s in spans if round(s["size"], 1) < 9.5]
    for k, v in checks:
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"  {'PASS' if not small else 'FAIL'}  nothing below the 9.5pt floor"
          + (f" {small}" if small else ""))
    return all(v for _, v in checks) and not small


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    c, l, b = build(a.outdir)
    ok = assert_174(l)
    print(("\n  settled #174: all assertions pass" if ok else "\n  ASSERTIONS FAILED"))
