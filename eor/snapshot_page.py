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
    fn_peer_band(20605)                 474 peers, $7.8M-$31.4M revenue
    account_benefit_broker              Form 5500 Schedule A
"""
import os
from weasyprint import HTML

ORG   = "Coastal Enterprises of Jacksonville"

# The registered lockup, from the brand asset. NEVER retyped in CSS.
_VTI = "/home/claude/worker/meeting_label/assets/vti_logo.png"
import base64 as _b64
from PIL import Image as _Img
_im = _Img.open(_VTI)
_im.thumbnail((150, 150))          # ~0.52in wide in print; rule and dot stay legible
_im.save("/tmp/vti_footer.png")
VTI_URI = "data:image/png;base64," + _b64.b64encode(
    open("/tmp/vti_footer.png", "rb").read()).decode()
REV   = 15_682_676
FILED = 1_622_323
FEES, LIVES = 525_754, 581

# category, filed, their % of revenue, peer median %, percentile, peers
ROWS = [
    ("Insurance",       1_046_650, 6.67, 1.04, 99, 10_953),
    ("Maintenance",       264_410, 1.69, 1.00, 67,  4_831),
    ("Travel",            105_347, 0.67, 0.37, 65,  8_769),
    ("Utilities",         166_777, 1.06, 1.86, 26,    434),
    ("SaaS / Software",    15_923, 0.10, 0.36, 17,  1_155),
]
NO_PEER = [("Office Supplies", 23_216)]

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
      <td class="r" style="color:#6C7686">No comparable cohort</td>
    </tr>"""

HTMLDOC = f"""<html><head><meta charset="utf-8"><style>
@page {{
  size: Letter; margin: 0.38in 0.85in 0.62in 0.85in;
  @bottom-left  {{ content:url("{VTI_URI}"); vertical-align:top;
                   padding-top:5px; }}
  @bottom-center{{ content:"Prepared exclusively for {ORG}"; font-size:8pt;
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
.kpi > div {{ flex:1; border:1px solid #DCE3ED; padding:7px 9px; }}
.kpi .n {{ font-size:18pt; color:#003A70; font-weight:bold; line-height:1.1; }}
.kpi .k {{ font-size:7.8pt; letter-spacing:.1em; text-transform:uppercase;
          color:#6C7686; margin-top:3px; }}
.kpi .s {{ font-size:8.4pt; color:#6C7686; margin-top:4px; line-height:1.35; }}
.kpi .hi {{ border-color:#FF9C00; border-left-width:3px; }}
.note {{ font-size:8.4pt; color:#6C7686; margin:6px 0 9px; }}
h2 {{ font-size:12pt; color:#003A70; margin:11px 0 4px; }}
table {{ width:100%; border-collapse:collapse; font-size:9.8pt; }}
th {{ text-align:left; font-size:7.8pt; letter-spacing:.09em; text-transform:uppercase;
     color:#6C7686; border-bottom:1.4px solid #003A70; padding:0 7px 5px 0; }}
td {{ padding:3.4px 7px 3.4px 0; border-bottom:1px solid #DCE3ED; }}
td.r, th.r {{ text-align:right; }}

.split {{ display:flex; gap:14px; margin-top:10px; }}
.split > div {{ flex:1; }}
.box {{ border-left:3px solid #FF9C00; background:#F5F7FB; padding:7px 10px; }}
.box.g {{ border-left-color:#003A70; }}
.box h3 {{ margin:0 0 5px; font-size:10.4pt; color:#003A70; }}
.box p {{ margin:0; font-size:9.4pt; line-height:1.45; }}
.prov {{ margin-top:7px; padding-top:6px; border-top:1px solid #DCE3ED;
        font-size:8pt; color:#6C7686; }}
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

<h1>Six categories examined. Two look worth a conversation.<br>Two look well bought.</h1>
<div class="lede">Every indirect category your filing breaks out, compared against organizations of
comparable size and type. Position is a starting point for a question, never a verdict on how you
are run.</div>

<div class="kpi">
  <div><div class="n">{EXAMINED}</div><div class="k">Categories examined</div>
       <div class="s">Every indirect line your filing breaks out, not a selection.</div></div>
  <div><div class="n">{usd(FILED)}</div><div class="k">Addressable, as filed</div>
       <div class="s">{FILED/REV*100:.1f}% of total revenue. The true base is larger.</div></div>
  <div><div class="n">{ABOVE}</div><div class="k">Above peer median</div>
       <div class="s">{BELOW} sit below it, and one has no comparable cohort.</div></div>
  <div class="hi"><div class="n">{PRIORITIES}</div><div class="k">Evidence-supported priority</div>
       <div class="s">Earned on a second evidence layer, not on size.</div></div>
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
<div class="note">Peer cohort: nonprofit organizations with revenue between $7.8M and $31.4M, the
same filing methodology and the same denominator. Cohort size differs by category because not
every organization breaks out every line.</div>

<div class="split">
  <div class="box">
    <h3>Why insurance, and not simply because it is largest</h3>
    <p>It sits at the <b>99th percentile of 10,953 comparable filers</b> &mdash; six times the peer
    median as a share of revenue. It is also the one category where a second filing shows something
    a Form 990 cannot: your plan&rsquo;s Schedule A discloses <b>{usd(FEES)}</b> of intermediary
    compensation across two relationships, covering {LIVES} people. Two independent layers on one
    category is what earns it a page.</p>
  </div>
  <div class="box g">
    <h3>Where you appear to be buying well</h3>
    <p><b>Utilities sits at the 26th percentile and software at the 17th</b> &mdash; both below the
    peer median as a share of revenue. On the public record these look competitively bought, and we
    would not start there. If a review happened, it should say so.</p>
  </div>
</div>

<div class="prov">
  <b>FILED</b> Form 990 Part IX, FY2024, object 202601359349313660 &nbsp;&middot;&nbsp;
  <b>BENCHMARK</b> peer cohort of 474 organizations by revenue band; per-category cohorts as shown
  &nbsp;&middot;&nbsp; <b>REGISTRY</b> DOL Form 5500 Schedule A, plan year 2024
  &nbsp;&middot;&nbsp; <b>DERIVED</b> percentages and positions, arithmetic on filed figures only
  &nbsp;&middot;&nbsp; OPERATING, RETRIEVED, ENGAGEMENT, VERIFIED &mdash; absent
</div>

</body></html>"""

out = "/mnt/user-data/outputs/EOR_Snapshot_Coastal.pdf"
HTML(string=HTMLDOC).write_pdf(out)
from pypdf import PdfReader
r = PdfReader(out)
print("PAGES:", len(r.pages))
t = r.pages[0].extract_text() or ""
for bad in ("savings", "Senior Consultant"):
    print(f"  {'FAIL' if bad.lower() in t.lower() else 'clean'}: {bad}")
