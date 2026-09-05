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
OPP_LOW, OPP_HIGH, OPP_MID = 4_366_000, 12_504_000, 8_434_775

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
    ("Operating Supply",       37_971_710, "Well above", 98,  89, 27),
    ("Freight / Small Parcel",  2_631_840, "Above",      64, 112, 29),
    ("Fleet Management",        2_122_533, "Below",      46,  17, 18),
    ("Office Supplies",         1_372_501, "Not compared", None, 227, 27),
    ("Professional Services",     637_913, "Not compared", None, 0, 0),
    ("Marketing Services",        482_421, "At median",  49,   0, 0),
    ("Travel",                    449_863, "Below",      39,   0, 0),
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
    proof = f"{med}% median &middot; {proj} projects" if proj >= 5 else "&mdash;"
    rows += (f'<tr><td><b>{name}</b></td><td class="r">{usd(amt)}</td>'
             f'<td class="r">{amt/FILED*100:.0f}%</td>'
             f'<td class="r" style="color:{colour};font-weight:bold">{posn}</td>'
             f'<td class="r" style="color:#003A70">{proof}</td></tr>')

road = "".join(
  f'<div class="rd"><span class="i">{i}</span><div><b>{t}</b>'
  f'<div class="sub">{d}</div></div></div>'
  for i,(t,d) in enumerate(ROADMAP, 1))

DOC = f"""<html><head><meta charset="utf-8"><style>
@page {{ size: Letter; margin: 0.38in 0.85in 0.62in 0.85in;
  @bottom-left  {{ content:url("{VTI_URI}"); vertical-align:top; padding-top:5px; }}
  @bottom-center{{ content:"{ORG}"; font-size:8pt; font-weight:bold; color:#16243F;
                   vertical-align:top; padding-top:6px; }}
  @bottom-right {{ content:"PAGE " counter(page) " OF 16"; font-size:7pt; color:#6C7686;
                   letter-spacing:.04em; vertical-align:top; padding-top:6px; }} }}
* {{ font-family:'Liberation Sans','Trebuchet MS',Arial,sans-serif; }}
body {{ color:#3C4658; font-size:10.2pt; line-height:1.44; }}
.hd {{ display:flex; align-items:flex-end; border-bottom:2px solid #003A70;
      padding-bottom:6px; margin-bottom:14px; }}
.hd .l {{ font-size:8.2pt; letter-spacing:.14em; color:#6C7686; text-transform:uppercase; }}
.hd .r {{ margin-left:auto; text-align:right; font-size:8.2pt; color:#6C7686; }}
h1 {{ font-size:16pt; color:#003A70; margin:0 0 6px; line-height:1.22; font-weight:bold; }}
.lede {{ color:#3C4658; margin:0 0 12px; max-width:92%; }}
/* THE NUMBER LEADS. It is the reason to read on and it belongs where the eye
   lands, not buried in a category table. */
.hero {{ display:flex; align-items:center; gap:18px; background:#003A70; color:#fff;
        padding:14px 18px; margin:0 0 13px; }}
.hero .big {{ font-size:25pt; font-weight:bold; line-height:1; white-space:nowrap; }}
.hero .k {{ font-size:7.8pt; letter-spacing:.13em; text-transform:uppercase; color:#FF9C00;
           font-weight:bold; }}
.hero .s {{ font-size:9.2pt; color:#DCE7F5; margin-top:4px; line-height:1.45; }}
h2 {{ font-size:11.5pt; color:#003A70; margin:12px 0 5px; }}
.two {{ display:flex; gap:20px; }} .two > div {{ flex:1; }}
ul.pl {{ list-style:none; margin:0; padding:0; }}
ul.pl li {{ padding:4px 0; border-bottom:1px solid #DCE3ED; font-size:9.4pt; }}
ul.pl li:last-child {{ border-bottom:none; }}
.rd {{ display:flex; gap:9px; padding:3.4px 0; border-bottom:1px solid #DCE3ED;
      font-size:9.4pt; color:#003A70; align-items:flex-start; }}
.rd:last-child {{ border-bottom:none; }}
.rd .i {{ flex:0 0 17px; height:17px; border-radius:50%; background:#003A70; color:#fff;
         font-size:7pt; font-weight:bold; text-align:center; line-height:17px; margin-top:1px; }}
.rd .sub {{ font-size:8.4pt; color:#6C7686; font-weight:normal; }}
table {{ width:100%; border-collapse:collapse; font-size:9.4pt; margin-top:3px; }}
th {{ text-align:left; font-size:7.8pt; letter-spacing:.09em; text-transform:uppercase;
     color:#6C7686; border-bottom:1.4px solid #003A70; padding:0 7px 4px 0; }}
td {{ padding:3.2px 7px 3.2px 0; border-bottom:1px solid #DCE3ED; }}
td.r, th.r {{ text-align:right; }}
.note {{ font-size:8.2pt; color:#6C7686; margin-top:6px; line-height:1.5; }}
</style></head><body>

<div class="hd"><div class="l">Executive Overview</div>
  <div class="r">{ORG}<br>Form 990 FY2024</div></div>

<h1>What this is, why we prepared it, and what it does not claim.</h1>
<div class="lede">One page of orientation before any numbers. We built this from your public filings
before contacting you, because a useful conversation should begin with evidence rather than a
capability presentation.</div>

<div class="hero">
  <div><div class="k">What an outside-in review points to</div>
    <div class="big">{usd(OPP_LOW)} &ndash; {usd(OPP_HIGH)}</div></div>
  <div class="s">a year in recoverable indirect cost, against the {usd(FILED)} your filing names by
  category. Directional, from public information only &mdash; and validated, or ruled out, in a
  no-cost baseline. Across <b>2,660 completed ERA engagements, 2,649 recovered value</b>.</div>
</div>

<div class="two">
  <div>
    <h2>How it was built</h2>
    <ul class="pl">
      <li><b>Your public filing.</b> Nineteen expense lines from your FY2024 Form 990; seven map to
        categories we work.</li>
      <li><b>A peer comparison.</b> Each category against every nonprofit filer that breaks it out
        separately, as a share of revenue.</li>
      <li><b>Our own completed work.</b> What ERA has actually recovered in each of those
        categories, not a projection.</li>
    </ul>
    <h2>Reading the position</h2>
    <ul class="pl">
      <li><b>Above the median</b> is a question, not a verdict. Categories sit high for sound
        reasons, and your model is one of them.</li>
      <li><b>At or below the median</b> is not proof of competitive buying. The median is drawn
        from organizations that have mostly never tested these categories either.</li>
    </ul>
  </div>
  <div>
    <h2>What follows</h2>
    {road}
  </div>
</div>

<h2>All seven categories at a glance</h2>
<table>
  <tr><th>Category</th><th class="r">Filed</th><th class="r">Share</th>
      <th class="r">Position</th><th class="r">What ERA has recovered here</th></tr>
  {rows}
</table>
<div class="note">A further {usd(UNCLASSIFIED)} of indirect spend sits in lines your filing does not
name &mdash; occupancy, fees for services, service charges. None of it is in the range above. ERA
benchmarks 55 categories; the baseline covers every one that applies to you.</div>

</body></html>"""

out = "/mnt/user-data/outputs/EOR_Overview_Goodwill.pdf"
HTML(string=DOC).write_pdf(out)
from pypdf import PdfReader
r = PdfReader(out); print("pages:", len(r.pages))
t = r.pages[0].extract_text() or ""
for bad in ("savings", "Senior Consultant"):
    print(("FAIL " if bad.lower() in t.lower() else "clean "), bad)
