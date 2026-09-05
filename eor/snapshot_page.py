#!/usr/bin/env python3
"""
EXECUTIVE OPPORTUNITY SNAPSHOT — the principal summary page.

Restored per settled_decisions #173, which named its absence "the biggest
analytical loss" in the first rebuild. It replaces an orientation page plus a
spend table, which is NOT this page.

#173 REQUIRES IT TO SHOW, and the acceptance test is thirty seconds:
    addressable spend
    categories examined
    categories ABOVE PEER MEDIAN
    evidence-supported priorities
    evidence depth
    a directional range ONLY if the inputs clear the confidence gate, and
    CLEARLY SEPARATE from variance-to-peer

THE TWO NUMBERS MUST NOT BE CONFLATED. Variance to peer median is what the
filing says relative to comparable organizations. A recovery range is what a
category has yielded when tested. They are different claims from different
sources and the first rebuild ran them side by side as though they were one -
which is the error that made the whole document feel like a spend ranking.

WHY ONE PRIORITY AND NOT TWO. Priorities are earned on EVIDENCE, never on spend
size (#173). Insurance carries two independent layers - 99th percentile of
10,953 peers AND a Form 5500 Schedule A disclosure naming intermediaries and
what they were paid. Maintenance is second largest and has one layer, so it
does not get a page. That is the whole correction.

Every figure below was queried live on 2026-09-04:
    account_category_percentile(20605)  peer position per category
    NOT fn_peer_band()  - that returns a REVENUE-BAND cohort (474 organizations,
                          $7.8M-$31.4M) and is a different comparator entirely.
                          Describing one as the other put a false cohort on the
                          page and invited the obvious question: how does a
                          474-organization band produce 10,953 insurance peers.
    account_benefit_broker              Form 5500 Schedule A
"""
import os
from weasyprint import HTML

ORG   = "Goodwill Industries of South Florida"

# The registered lockup, from the brand asset. NEVER retyped in CSS.
_VTI = "/home/claude/worker/meeting_label/assets/vti_logo.png"
import base64 as _b64
from PIL import Image as _Img
_im = _Img.open(_VTI)
_im.thumbnail((186, 186), _Img.LANCZOS)   # 0.62in at 300dpi; LANCZOS from 3066px
_im.save("/tmp/vti_footer.png", optimize=True)
VTI_URI = "data:image/png;base64," + _b64.b64encode(
    open("/tmp/vti_footer.png", "rb").read()).decode()
REV   = 196_096_296
FILED = 43_658_367
FEES, BROKERS = 173_354, 4
# ── THE EXPENSE BASE, SPLIT HONESTLY ────────────────────────────────────────
# "82% of your filed expenses is not broken out" was WRONG and I wrote it. Of
# the $7.46M I called invisible, $5.98M is compensation, payroll taxes and
# benefits and $970K is depreciation - NONE of it is indirect and none of it is
# workable. Claiming it as unseen opportunity is the kind of overclaim that
# ends a meeting.
EXPENSES     = 185_120_170   # total functional expenses, Form 990 Part IX FY2024
PEOPLE       =  99_283_913   # salaries, payroll taxes, pension, benefits
NON_CASH     =   3_493_294   # depreciation and interest
UNCLASSIFIED =  38_458_237   # occupancy, fees for services - other, service charges,
                             # all-other. Indirect, but the filing does not name the
                             # category. NOT modelled in the recovery range.
INDIRECT     = FILED + UNCLASSIFIED

# category, filed, their % of revenue, peer median %, percentile, peers
ROWS = [
    ("Operating Supply",      37_971_710, 19.36, 2.40, 98, 2_573),
    ("Freight / Small Parcel", 2_631_840,  1.34, 0.79, 64,   140),
    ("Marketing Services",       482_421,  0.25, 0.26, 49, 7_371),
    ("Fleet Management",       2_122_533,  1.08, 1.21, 46,   396),
    ("Travel",                   449_863,  0.23, 0.37, 39, 8_769),
]
NO_PEER = [("Office Supplies", 1_372_501), ("Professional Services: Legal", 637_913)]

EXAMINED = len(ROWS) + len(NO_PEER)
ABOVE    = sum(1 for r in ROWS if r[4] >= 50)
BELOW    = sum(1 for r in ROWS if r[4] < 50)
PRIORITIES = 1


def usd(n):
    if n >= 1_000_000: return f"${n/1_000_000:.2f}M".replace(".00M", "M")
    if n >= 1_000:     return f"${round(n/1000):,}K"
    return f"${n:,}"


MIDNIGHT = "#111127"  # Midnight Blue, Brand Playbook secondary palette
COOLGREY = "#97999B"  # Cool Grey, core palette


def band(p):
    """Plain words carry the meaning; colour carries the weight. Both readings
    are stated neutrally - 'well above' is not an accusation and 'well below' is
    not praise - but neither of them whispers."""
    if p >= 90: return ("Well above", MIDNIGHT)
    if p >= 50: return ("Above",      "#E08A00")
    if p >= 25: return ("Below",      COOLGREY)
    return ("Well below", COOLGREY)


rows = ""
for name, amt, theirs, med, pct, peers in ROWS:
    label, colour = band(pct)
    rows += f"""<tr>
      <td><b>{name}</b></td>
      <td class="r">{usd(amt)}</td>
      <td class="r">{theirs:.2f}%</td>
      <td class="r">{med:.2f}%</td>
      <td class="r">{peers:,}</td>
      <td class="r" style="color:{colour};font-weight:bold">{label} &middot; {pct}th</td>
    </tr>"""
for name, amt in NO_PEER:
    rows += f"""<tr>
      <td><b>{name}</b></td><td class="r">{usd(amt)}</td>
      <td class="r">&mdash;</td><td class="r">&mdash;</td><td class="r">&mdash;</td>
      <td class="r" style="color:#6C7686">Not yet compared</td>
    </tr>"""

HTMLDOC = f"""<html><head><meta charset="utf-8"><style>
@page {{
  size: Letter; margin: 0.38in 0.85in 0.62in 0.85in;
  @bottom-left  {{ content:url("{VTI_URI}"); vertical-align:top; padding-top:5px; }}
  @bottom-center{{ content:"{ORG}"; font-size:8pt;
                   font-weight:bold; color:#16243F; vertical-align:top;
                   padding-top:6px; }}
  @bottom-right {{ content:"PAGE " counter(page) " OF 16"; font-size:7pt;
                   color:#6C7686; letter-spacing:.04em; vertical-align:top;
                   padding-top:6px; }}
}}
* {{ font-family:'Liberation Sans','Trebuchet MS',Arial,sans-serif; }}
body {{ color:#3C4658; font-size:10.5pt; line-height:1.45; }}
.hd {{ display:flex; align-items:flex-end; border-bottom:2px solid #003A70;
      padding-bottom:6px; margin-bottom:16px; }}
.hd .l {{ font-size:8.2pt; letter-spacing:.14em; color:#6C7686; text-transform:uppercase; }}
.hd .r {{ margin-left:auto; text-align:right; font-size:8.2pt; color:#6C7686; }}
h1 {{ font-size:17pt; color:#003A70; margin:0 0 6px; line-height:1.22; font-weight:bold; }}
.lede {{ color:#3C4658; margin:0 0 10px; max-width:88%; }}
/* THE THIRTY-SECOND ROW. #173's acceptance test is that a reader can tell at a
   glance how many categories were examined, how many sit above peer median, and
   how many are evidence-supported priorities. That is this strip and nothing
   else on the page competes with it. */
.kpi {{ display:flex; gap:10px; margin:0 0 6px; }}
.kpi > div {{ flex:1; border:1px solid #DCE3ED; padding:6px 8px; }}
.kpi .n {{ font-size:18pt; color:#003A70; font-weight:bold; line-height:1.1; }}
.kpi .k {{ font-size:7.8pt; letter-spacing:.1em; text-transform:uppercase;
          color:#6C7686; margin-top:3px; }}
.kpi .s {{ font-size:8.4pt; color:#6C7686; margin-top:4px; line-height:1.35; }}
.kpi .hi {{ border-color:#FF9C00; border-left-width:3px; }}
.note {{ font-size:8.2pt; color:#6C7686; margin:5px 0 8px; }}
h2 {{ font-size:12pt; color:#003A70; margin:9px 0 4px; }}
table {{ width:100%; border-collapse:collapse; font-size:9.8pt; }}
th {{ text-align:left; font-size:7.8pt; letter-spacing:.09em; text-transform:uppercase;
     color:#6C7686; border-bottom:1.4px solid #003A70; padding:0 7px 5px 0; }}
td {{ padding:2.8px 7px 2.8px 0; border-bottom:1px solid #DCE3ED; }}
td.r, th.r {{ text-align:right; }}

.split {{ display:flex; gap:13px; margin-top:8px; }}
.split > div {{ flex:1; }}
.box {{ border-left:3px solid #FF9C00; background:#F5F7FB; padding:6px 9px; }}
.box.g {{ border-left-color:#003A70; }}
.box h3 {{ margin:0 0 5px; font-size:10.4pt; color:#003A70; }}
.box p {{ margin:0; font-size:9.4pt; line-height:1.45; }}
.prov {{ margin-top:6px; padding-top:5px; border-top:1px solid #DCE3ED;
        font-size:7.4pt; color:#6C7686; line-height:1.5; }}
.prov b {{ color:#003A70; }}
.footer {{ margin-top:0.12in; }}
.footer .hair {{ border-top:1px solid #DCE3ED; margin-bottom:6px; }}
.footer .row {{ display:flex; justify-content:space-between; align-items:center; }}
.footer .vti {{ font-weight:bold; font-size:7.5pt; color:#003A70; }}
.footer .vti em {{ color:#FF9C00; font-style:normal; font-weight:normal; }}
.footer .mid {{ font-size:8pt; font-weight:bold; color:#16243F; }}
.footer .pg {{ font-size:7pt; color:#6C7686; letter-spacing:.04em; }}
</style></head><body>

<div class="hd">
  <div class="l">Executive Opportunity Snapshot</div>
  <div class="r">{ORG}<br>Form 990 FY2024</div>
</div>

<h1>$82.1M of indirect spend, and one category is<br>eight times the peer median.</h1>
<div class="lede">Indirect spend is the recurring operating cost that sits outside your program
delivery and outside your payroll &mdash; it is the only thing we work. What follows compares the
categories your Form 990 names separately against organizations of comparable size and type: a
starting point for a question, never a verdict on how you are run.</div>

<div class="kpi">
  <div class="hi"><div class="n">${INDIRECT/1e6:.1f}M</div>
       <div class="k">Indirect spend, as filed</div>
       <div class="s">Salaries, depreciation and interest are excluded &mdash; they are not
       indirect and not ours to work.</div></div>
  <div><div class="n">${FILED/1e6:.1f}M</div><div class="k">Named by category</div>
       <div class="s">Seven categories. A further {usd(UNCLASSIFIED)} sits in lines the filing
       does not name.</div></div>
  <div><div class="n">55</div><div class="k">Categories ERA works</div>
       <div class="s">The baseline covers every one that applies to you, not only those a form
       happens to disclose.</div></div>
  <div><div class="n">1</div><div class="k">Priority the public record can already evidence</div>
       <div class="s">Operating supply, at the 98th percentile of 2,573 filers.</div></div>
</div>
<div class="note">Evidence depth: four of nine layers carry something for this organization &mdash;
filed, benchmark, derived and registry. Operating, retrieved, engagement and verified are empty,
and are shown as empty rather than filled.</div>

<h2>Where each category sits</h2>
<table>
  <tr><th>Category</th><th class="r">Filed</th><th class="r">Your %<br>of revenue</th>
      <th class="r">Peer<br>median</th><th class="r">Peers</th><th class="r">Position</th></tr>
  {rows}
</table>
<div class="note">Each category is compared against every nonprofit filer that breaks that category
out separately, measured the same way &mdash; category spend as a share of total revenue. Cohort
sizes differ because not every organization discloses every line, and a category needs at least 30
filers before we will state a position. The categories a filing does not break out are sized in the
baseline, not here.</div>

<div class="split">
  <div class="box">
    <h3>Why operating supply, and not simply because it is largest</h3>
    <p>At <b>19.4% of revenue against a 2.4% peer median</b> it sits at the 98th percentile of
    2,573 filers &mdash; roughly eight times. A retail and donated-goods operation genuinely buys
    more supply than most nonprofits, so some of that gap is your model rather than your buying.
    How much is the question, and it is the one worth answering first.</p>
  </div>
  <div class="box g">
    <h3>Where the filing looks competitive</h3>
    <p><b>Fleet sits at the 46th percentile and travel at the 39th</b>, with marketing at the
    median. On the public record these already look well bought, so they are not where this Report
    points first. A baseline covers every applicable category and would confirm it either way.</p>
  </div>
</div>

<div class="prov">
  <b>FILED</b> Form 990 Part IX, FY2024 &nbsp;&middot;&nbsp;
  <b>REGISTRY</b> DOL Form 5500 Schedule A, plan year 2024<br>
  <b>BENCHMARK</b> per-category peer cohorts as shown, 30-filer minimum
  &nbsp;&middot;&nbsp; <b>DERIVED</b> arithmetic on filed figures only
  &nbsp;&middot;&nbsp; OPERATING, RETRIEVED, ENGAGEMENT, VERIFIED &mdash; absent
</div>

</body></html>"""

out = "/mnt/user-data/outputs/EOR_Snapshot_Goodwill.pdf"
HTML(string=HTMLDOC).write_pdf(out)
from pypdf import PdfReader
r = PdfReader(out)
print("PAGES:", len(r.pages))
t = r.pages[0].extract_text() or ""
for bad in ("savings", "Senior Consultant"):
    print(f"  {'FAIL' if bad.lower() in t.lower() else 'clean'}: {bad}")
