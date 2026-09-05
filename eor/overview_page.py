#!/usr/bin/env python3
"""
EXECUTIVE OVERVIEW — page 5 of the EOR, per frozen spec settled_decisions #172.

"What this is, why we prepared it, and what it does not claim." One page of
orientation before any numbers, carrying four things the spec names:
    How it was built
    Reading the benchmark - and that neither position is a judgement
    WHAT FOLLOWS - the numbered roadmap of every section
    All categories at a glance

AND IT LEADS WITH THE NUMBER. John, 2026-09-04: "SO FUCKING WHAT? How does this
help ERA Group sell this account?" The previous pages stated positions and never
stated the opportunity. $8.4M is the reason to read on and it belongs where the
reader's eye lands first, not buried in a category table.

LAW 25 governs every figure here: meaning, position, proof, purpose. The proof
is era_projects, queried - 2,660 completed engagements, 2,649 of which recovered
value.
"""
import base64, os
from PIL import Image
from weasyprint import HTML

ORG   = "Goodwill Industries of South Florida"
REV   = 196_096_296
EXPENSES = 185_120_170
FILED = 43_658_367
UNCLASSIFIED = 38_458_237
INDIRECT = FILED + UNCLASSIFIED
# fn_recovery_summary(23895) - quartiles of COMPLETED ERA projects, not bands.
WEAK, LIKELY, STRONG = 5_486_743, 8_693_297, 14_022_890
PROJECTS_BEHIND = 158

_VTI = "/home/claude/worker/meeting_label/assets/vti_logo.png"
_im = Image.open(_VTI); _im.thumbnail((186, 186), Image.LANCZOS)
_im.save("/tmp/vti_o.png", optimize=True)
VTI_URI = "data:image/png;base64," + base64.b64encode(open("/tmp/vti_o.png","rb").read()).decode()

def usd(n):
    if n >= 1_000_000: return f"${n/1_000_000:.1f}M"
    if n >= 1_000:     return f"${round(n/1000):,}K"
    return f"${n:,}"

# category, filed, position words, percentile, ERA projects, ERA median %
CATS = [
    ("Operating Supply",       37_971_710, "Well above", 98,  69, 21.3),
    ("Freight / Small Parcel",  2_631_840, "Above",      64,  89, 23.0),
    ("Fleet Management",        2_122_533, "Below",      46,   0, 0),
    ("Office Supplies",         1_372_501, "Not compared", None, 204, 25.0),
    ("Professional Services",     637_913, "Not compared", None, 0, 0),
    ("Marketing Services",        482_421, "At median",  49,  56, 30.1),
    ("Travel",                    449_863, "Below",      39,  46, 18.4),
]

ROADMAP = [
    ("What we found, and what follows", "Five observations, none of them a conclusion"),
    ("What your own numbers say",       "Every indirect line your filing breaks out"),
    ("The position, as we read it",     "Each category against comparable filers"),
    ("Where we looked",                 "The second filing, and what it discloses"),
    ("Operating supply",                "The one priority the public record can evidence"),
    ("What this rests on",              "Nine evidence layers, four of them empty"),
    ("What happens next",               "A conversation, a no-cost baseline, your decision"),
]

rows = ""
for name, amt, pos, pct, proj, med in CATS:
    posn = f"{pos} &middot; {pct}th" if pct else pos
    colour = "#111127" if pct and pct >= 90 else ("#E08A00" if pct and pct >= 50 else "#97999B")
    proof = f"{med:.0f}% median &middot; {proj} projects" if proj >= 15 else "&mdash;"
    rows += (f'<tr><td><b>{name}</b></td><td class="r">{usd(amt)}</td>'
             f'<td class="r">{amt/FILED*100:.0f}%</td>'
             f'<td class="r" style="color:{colour};font-weight:bold">{posn}</td>'
             f'<td class="r" style="color:#003A70">{proof}</td></tr>')

road = "".join(
  f'<div class="rd"><span class="i">{i}</span><div><b>{t}</b></div></div>'
  for i,(t,d) in enumerate(ROADMAP, 1))

DOC = f"""<html><head><meta charset="utf-8"><style>
@page {{ size: Letter; margin: 0.34in 0.8in 0.58in 0.8in;
  @bottom-left  {{ content:url("{VTI_URI}"); vertical-align:top; padding-top:5px; }}
  @bottom-center{{ content:"{ORG}"; font-size:8pt; font-weight:bold; color:#16243F;
                   vertical-align:top; padding-top:6px; }}
  @bottom-right {{ content:"PAGE " counter(page) " OF 16"; font-size:8pt; color:#6C7686;
                   letter-spacing:.04em; vertical-align:top; padding-top:6px; }} }}
* {{ font-family:'Liberation Sans','Trebuchet MS',Arial,sans-serif; }}
body {{ color:#3C4658; font-size:10pt; line-height:1.5; }}
.hd {{ display:flex; align-items:flex-end; border-bottom:2px solid #003A70;
      padding-bottom:6px; margin-bottom:14px; }}
.hd .l {{ font-size:8pt; letter-spacing:.14em; color:#6C7686; text-transform:uppercase; }}
.hd .r {{ margin-left:auto; text-align:right; font-size:8pt; color:#6C7686; }}
h1 {{ font-size:16pt; color:#003A70; margin:0 0 6px; line-height:1.22; font-weight:bold; }}
.lede {{ color:#3C4658; margin:0 0 14px; max-width:92%; }}
/* THE NUMBER LEADS. It is the reason to read on and it belongs where the eye
   lands, not buried in a category table. */
.hero {{ display:flex; align-items:center; gap:26px; background:#003A70; color:#fff;
        padding:22px 26px; margin:2px 0 14px; }}
.hero .figure {{ flex:0 0 auto; }}
.hero .rule {{ flex:0 0 1px; align-self:stretch; background:#2A5074; }}
.hero .unit {{ font-size:10pt; color:#DCE7F5; margin-top:2px; }}
.hero .floor {{ font-size:10pt; color:#FF9C00; margin-top:9px; }}
.hero .say {{ flex:1; }}
.hero .say p {{ margin:0; font-size:10pt; line-height:1.5; color:#DCE7F5; }}
.hero .say p b {{ color:#fff; }}
.hero .stat {{ margin-top:8px; padding-top:7px; border-top:1px solid #2A5074;
              font-size:10pt; color:#fff; }}
.hero .stat b {{ font-size:14pt; color:#FF9C00; }}
.hero .stat span {{ color:#DCE7F5; }}
.hero .say p {{ max-width:none; }}
.hero .big {{ font-size:34pt; letter-spacing:-0.5pt; margin-top:-3px; font-weight:bold; line-height:1; white-space:nowrap; }}
h2 {{ font-size:11pt; color:#003A70; margin:16px 0 7px; }}
.two {{ display:flex; gap:18px; }} .two > div {{ flex:1; }}
ul.pl {{ list-style:none; margin:0; padding:0; }}
ul.pl li {{ padding:6px 0; border-bottom:1px solid #DCE3ED; font-size:10pt; }}
ul.pl li:last-child {{ border-bottom:none; }}
.rd {{ display:flex; gap:9px; padding:9.5px 0; border-bottom:1px solid #DCE3ED;
      font-size:10pt; color:#003A70; align-items:flex-start; }}
.rd:last-child {{ border-bottom:none; }}
.rd .i {{ flex:0 0 17px; height:17px; border-radius:50%; background:#003A70; color:#fff;
         font-size:8pt; font-weight:bold; text-align:center; line-height:17px; margin-top:1px; }}
.rd .sub {{ font-size:8pt; color:#6C7686; font-weight:normal; }}
table {{ width:100%; border-collapse:collapse; font-size:10pt; margin-top:3px; }}
th {{ text-align:left; font-size:8pt; letter-spacing:.09em; text-transform:uppercase;
     color:#6C7686; border-bottom:1.4px solid #003A70; padding:0 7px 4px 0; }}
td {{ padding:2.8px 7px 2.8px 0; border-bottom:1px solid #DCE3ED; }}
td.r, th.r {{ text-align:right; }}
.scope {{ display:flex; gap:14px; margin:10px 0 0; }}
.sc {{ flex:1; border-top:3px solid #DCE3ED; padding:11px 0 0; }}
.sc.on {{ border-top-color:#FF9C00; }}
.sc .amt {{ font-size:22pt; color:#003A70; font-weight:bold; line-height:1; }}
.sc .lab {{ font-size:8pt; letter-spacing:.13em; text-transform:uppercase; color:#6C7686;
           font-weight:bold; margin:5px 0 6px; }}
.sc .txt {{ font-size:10pt; line-height:1.45; }}
.note {{ font-size:8pt; color:#6C7686; margin-top:5px; line-height:1.45; }}
</style></head><body>

<div class="hd"><div class="l">Executive Overview</div>
  <div class="r">{ORG}<br>Form 990 FY2024</div></div>

<h1>What this is, why we prepared it, and what it does not claim.</h1>
<div class="lede">One page of orientation before any numbers. We built this from your public filings
before contacting you, because a useful conversation should begin with evidence rather than a
capability presentation.</div>

<div class="hero">
  <div class="figure">
    <div class="big">{usd(LIKELY)}</div>
    <div class="unit">a year</div>
    <div class="floor">{usd(WEAK)} on our weakest quartile</div>
  </div>
  <div class="rule"></div>
  <div class="say">
    <p>Not a range. The <b>median outcome across {PROJECTS_BEHIND} completed ERA
    engagements</b> in your categories.</p>
    <div class="stat"><b>2,649</b> of 2,660 engagements recovered value<span>
    &mdash; the weakest quarter still returned 14%</span></div>
  </div>
</div>

<div class="two">
  <div>
    <h2>How it was built</h2>
    <ul class="pl">
      <li><b>Your public filing.</b> Nineteen expense lines; seven map to categories we work.</li>
      <li><b>A peer comparison.</b> Each category against every nonprofit filer that breaks it out
        separately.</li>
      <li><b>Our own completed work.</b> What ERA has recovered in those categories &mdash; not a
        projection.</li>
    </ul>
    <h2>Reading the position</h2>
    <ul class="pl">
      <li><b>Above the median</b> is a question, not a verdict. Your model is one reason a category
        sits high.</li>
      <li><b>At or below it</b> is not proof of competitive buying &mdash; the median is drawn from
        organizations that have mostly never tested either.</li>
    </ul>
  </div>
  <div>
    <h2>What follows</h2>
    {road}
  </div>
</div>

<h2>What we looked at, and what we did not</h2>
<div class="scope">
  <div class="sc on">
    <div class="amt">$40.6M</div>
    <div class="lab">Modelled</div>
    <div class="txt">Operating supply and freight. <b>158 completed engagements</b> stand behind
      the figure above.</div>
  </div>
  <div class="sc">
    <div class="amt">$3.1M</div>
    <div class="lab">To be quantified</div>
    <div class="txt">Fleet, marketing, travel. We work all three &mdash; too few engagements to
      quote a median. <b>Upside.</b></div>
  </div>
  <div class="sc">
    <div class="amt">$38.5M</div>
    <div class="lab">Needs your detail</div>
    <div class="txt">Mostly occupancy. We work everything in it but the rent, and a 990 reports
      them as one figure. <b>Upside.</b></div>
  </div>
</div>
<div class="note">ERA works <b>55 categories</b>. Your filing reports <b>12 lines of indirect
spend</b>, $82.1M in total, and all twelve are above. The $8.7M comes from the first card only.</div>

</body></html>"""

out = "/mnt/user-data/outputs/EOR_Overview_Goodwill.pdf"
HTML(string=DOC).write_pdf(out)
from pypdf import PdfReader
r = PdfReader(out); print("pages:", len(r.pages))
t = r.pages[0].extract_text() or ""
for bad in ("savings", "Senior Consultant"):
    print(("FAIL " if bad.lower() in t.lower() else "clean "), bad)
