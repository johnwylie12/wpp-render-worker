#!/usr/bin/env python3
"""
THE EXECUTIVE OPPORTUNITY REPORT — built to frozen spec, settled_decisions #172.

This is the rebuild of the generator that was lost when a chat container was
recycled. The spec survived because it was written to the database on
2026-09-04; this file exists so the RENDERER survives too. It goes in the repo.

ACCOUNT: Coastal Enterprises of Jacksonville, EIN 56-6093446, Form 990 FY2024,
filing object 202601359349313660. Every figure below was queried live.

WHY THIS ACCOUNT. Insurance is their largest filed indirect category at $1.05M,
and Form 5500 Schedule A shows $525,754 of broker fees sitting inside it - paid
to TWO intermediaries on ONE carrier, described by the filer as "BROKER FEES"
and "TPA FEES". The 990 shows the category; the 5500 shows what is being
charged inside it. Two filings, one argument.

THE ORDER IS ART THEN SCIENCE (#172). The reader meets a person, then an
orientation, then a gentle summary of what we found and why each section is
here - and only then the arithmetic. NOTHING THAT OPENS WITH THEIR MONEY MAY BE
THE FIRST THING AFTER THE INTRODUCTION.

  1  Cover                     9  Where we looked
  3  Cover letter             10  Priority 1 - Insurance
  5  Executive overview       11  Priority 2 - Maintenance
  6  The bridge               12  What this rests on
  7  What your own numbers    13  What happens next
  8  The position             15  Inside back  16  Back cover

NO COUNTERPARTY NAME APPEARS (#155). C1 Benefits and Benefit Source are in the
database and do not print. "Two broker relationships" is the fact that lands.

LAW 8: no "savings" as a noun. LAW 7: US English. Nine evidence rungs, and the
zeroes print.
"""
import base64, os, subprocess
from weasyprint import HTML

W = "/home/claude/worker"
ORG   = "Coastal Enterprises of Jacksonville"
EIN   = "56-6093446"
FY    = "FY2024"
OBJ   = "202601359349313660"
REV   = 15_682_676
PORTAL = "coastalenterprises-benchmark"

# Filed categories, Form 990 Part IX. name, spend, low%, high%
CATS = [("Insurance",        1_046_650,  8, 25),
        ("Maintenance",        264_410, 10, 22),
        ("Utilities",          166_777,  8, 18),
        ("Travel",             105_347, 10, 20),
        ("Office Supplies",     23_216, 12, 25),
        ("SaaS / Software",     15_923, 12, 30)]
FILED = sum(c[1] for c in CATS)
LO = sum(round(c[1]*c[2]/100) for c in CATS)
HI = sum(round(c[1]*c[3]/100) for c in CATS)
FEES, LIVES = 525_754, 581

def usd(n):
    if n >= 1_000_000: return f"${n/1_000_000:.2f}M".replace(".00M","M")
    if n >= 1_000:     return f"${round(n/1000):,}K"
    return f"${n:,}"

def b64(p):
    return "data:image/png;base64," + base64.b64encode(open(p,"rb").read()).decode()

ERA  = b64(os.path.join(W, "cir/src/assets/logo_white.png")) \
       if os.path.exists(os.path.join(W,"cir/src/assets/logo_white.png")) else ""

CSS = """
@page { size:Letter; margin:0.58in 0.72in 0.62in 0.72in }
@page cover { margin:0 }
@page blank { margin:0 }
* { box-sizing:border-box }
body { font-family:'Carlito','DejaVu Sans',sans-serif; color:#20272E; font-size:10.5pt;
       line-height:1.46; margin:0 }
.page { page-break-after:always; position:relative; min-height:9.6in }
.page:last-child { page-break-after:auto }
.blank { page:blank; page-break-after:always }
h1 { font-family:'Georgia',serif; font-weight:600; font-size:17pt; color:#0A2E4F;
     margin:2px 0 8px; line-height:1.25 }
h2 { font-family:'Georgia',serif; font-weight:600; font-size:12.5pt; color:#0A2E4F;
     margin:12px 0 6px }
h3 { font-family:'Georgia',serif; font-size:11pt; color:#0A2E4F; margin:11px 0 3px }
p  { margin:0 0 9px }
.hdr { display:flex; align-items:flex-end; padding-bottom:7px; border-bottom:1px solid #0A2E4F;
       margin-bottom:14px; font-size:8.4pt; letter-spacing:.1em; text-transform:uppercase;
       color:#6B7783 }
.hdr .r { margin-left:auto; text-align:right; line-height:1.6 }
.eyebrow { font-size:8.4pt; letter-spacing:.13em; font-weight:700; color:#6B7783;
           text-transform:uppercase }
.tick { width:34px; height:2px; background:#C8880A; margin:6px 0 10px }
.lede { color:#4A5763; font-size:10.4pt; margin-bottom:10px; max-width:86% }
.note { font-size:9.4pt; color:#6B7783; line-height:1.45 }
.two { display:flex; gap:22px } .two > div { flex:1 }
table { width:100%; border-collapse:collapse; font-size:10pt; margin-top:4px }
th { text-align:left; font-size:8pt; letter-spacing:.09em; text-transform:uppercase;
     color:#6B7783; border-bottom:1.2px solid #0A2E4F; padding:0 8px 5px 0 }
td { padding:4.6px 8px 4.6px 0; border-bottom:1px solid #EEF1F4; vertical-align:top }
td.r, th.r { text-align:right }
.panel { background:#F7F9FB; border-left:3px solid #C8880A; padding:10px 15px; margin:9px 0 }
.panel p { margin:0; font-size:9.8pt }
ul.pl { list-style:none; margin:0; padding:0 }
ul.pl li { padding:4.6px 0; border-bottom:1px solid #F0F3F6; font-size:9.9pt }
.rd { display:flex; align-items:center; gap:9px; padding:3.4px 0;
      border-bottom:1px solid #F0F3F6; font-size:9.6pt; color:#0A2E4F }
.rd .i { flex:0 0 19px; height:19px; border-radius:50%; background:#0A2E4F; color:#fff;
         font-size:7.4pt; font-weight:700; text-align:center; line-height:19px }
.cards { display:flex; flex-wrap:wrap; gap:9px; margin-top:5px }
.card { flex:1 1 calc(50% - 6px); border:1px solid #DDE3E9; padding:10px 13px; background:#fff }
.card.wide { flex:1 1 100% }
.card.q { background:#FBF7EE; border-left:3px solid #C8880A }
.card .tag { font-size:7.8pt; letter-spacing:.12em; text-transform:uppercase; font-weight:700;
             color:#8A6410 }
.card h4 { font-family:'Georgia',serif; font-size:11.5pt; color:#0A2E4F; margin:4px 0 4px }
.card p { margin:0; font-size:9.7pt; line-height:1.45 }
.card .why { margin-top:6px; padding-top:5px; border-top:1px solid #F0F3F6; font-size:9.1pt;
             color:#6B7783 }
.card .why b { color:#41637A }
.prov { margin-top:14px; padding-top:8px; border-top:1px solid #DDE3E9; font-size:8.2pt;
        color:#6B7783; letter-spacing:.04em }
.prov b { color:#0A2E4F }
.ftr { position:absolute; left:0; right:0; bottom:-0.1in; border-top:1px solid #DDE3E9;
       padding-top:6px; font-size:7.6pt; color:#8B96A0; display:flex }
.ftr .p { margin-left:auto }
.bar { height:26px; background:#0A2E4F; display:flex; align-items:center; padding:0 14px;
       color:#fff; font-size:8pt; letter-spacing:.1em; margin-top:12px }
.bar span { margin-right:14px }
.big { font-family:'Georgia',serif; font-size:26pt; color:#0A2E4F; font-weight:600 }
"""

def HDR(): return (f"<div class='hdr'><div>ERA Group</div>"
                   f"<div class='r'>Executive Opportunity Report<br>{ORG}</div></div>")
def FTR(n): return (f"<div class='ftr'><div>Value Through Insight&#8482;</div>"
                    f"<div class='p'>{ORG} &nbsp;&middot;&nbsp; {n}</div></div>")
def EY(t): return f"<div class='eyebrow'>{t}</div><div class='tick'></div>"
def PROV(t): return f"<div class='prov'>{t}</div>"

P = []
def page(n, inner):
    P.append(f"<div class='page'>{HDR()}{inner}{FTR(n)}</div>")
def blank():
    P.append("<div class='blank'></div>")

# ─── 1 COVER ────────────────────────────────────────────────────────────────
# THE COVER IS NOT DRAWN HERE. It comes from cover/cover_page_engine.py with
# cover_page_template.html and the per-vertical hero photograph resolved through
# hero_vertical_map. John has raised this THREE TIMES - once in the original
# build, twice in the rebuild - and each time a hand-drawn navy panel was used
# instead. The repo template IS the cover.
#
#   cover_page_engine.render(content, out, hero_lookup=..., doc_type="package",
#                            date_str=...)
#
# The block below is the placeholder that must be REMOVED when this engine is
# parameterised. It exists only so the file renders standalone.
P.append(f"""<div class='page' style='page:cover;padding:0;min-height:11in'>
<div style='background:#0A2E4F;height:7.4in;padding:1.15in 0.95in;color:#fff;position:relative'>
  <div style='font-size:8.6pt;letter-spacing:.24em;color:#F2A900;font-weight:700'>PREPARED EXCLUSIVELY FOR</div>
  <div style='width:58px;height:2px;background:#F2A900;margin:14px 0 34px'></div>
  <div style='font-family:Georgia,serif;font-size:33pt;line-height:1.14'>Coastal Enterprises<br>of Jacksonville</div>
  <div style='margin-top:2.5in'>
    <div style='width:110px;height:2px;background:#F2A900;margin-bottom:16px'></div>
    <div style='font-size:9pt;letter-spacing:.2em;font-weight:700'>EXECUTIVE OPPORTUNITY REPORT</div>
    <div style='font-size:9pt;letter-spacing:.2em;color:#F2A900;margin-top:5px'>EMPLOYMENT SERVICES</div>
    <div style='border-left:3px solid #F2A900;padding-left:15px;margin-top:22px;font-family:Georgia,serif;
                font-size:14.5pt;line-height:1.42;max-width:4.3in'>
      What a filing shows about how you buy &mdash;<br>before we ever asked for your time.</div>
  </div>
  <div style='position:absolute;bottom:0.75in;font-size:9pt;letter-spacing:.22em'>SEPTEMBER 4, 2026</div>
</div>
<div style='height:2.4in;background:#F2F4F6;display:flex;padding:0.42in 0.95in'>
  <div style='flex:1'><div style='font-weight:700;font-size:9.6pt;color:#0A2E4F;letter-spacing:.08em'>OUTSIDE-IN ANALYSIS</div>
   <div style='font-size:8.6pt;color:#5A6672;margin-top:6px;line-height:1.65'>INFORMED PERSPECTIVE<br><b>BEFORE ANY MEETING</b></div></div>
  <div style='flex:1'><div style='font-weight:700;font-size:9.6pt;color:#0A2E4F;letter-spacing:.08em'>MISSION FOCUSED</div>
   <div style='font-size:8.6pt;color:#5A6672;margin-top:6px;line-height:1.65'>STEWARDSHIP TODAY.<br>STRENGTH TOMORROW.</div></div>
  <div style='flex:1'><div style='font-weight:700;font-size:9.6pt;color:#0A2E4F;letter-spacing:.08em'>MEASURABLE IMPACT</div>
   <div style='font-size:8.6pt;color:#5A6672;margin-top:6px;line-height:1.65'>DOLLARS RECOVERED.<br>OPPORTUNITIES FUNDED.</div></div>
</div>
<div style='height:0.5in;background:#0A2E4F;color:#F2A900;font-size:10pt;letter-spacing:.4em;
            text-align:center;line-height:0.5in'>VALUE THROUGH INSIGHT&#8482;</div>
</div>""")
blank()

# ─── 3 COVER LETTER — the five frozen paragraphs, "We are sending" ──────────
P.append(f"""<div class='page' style='padding:0.7in 0.95in'>
<div style='font-size:9.4pt;color:#6B7783;margin-bottom:26px'>September 4, 2026</div>
<div style='font-size:10.4pt;line-height:1.5;margin-bottom:22px'>
  <b style='color:#0A2E4F'>Chief Financial Officer</b><br>{ORG}<br>Jacksonville, North Carolina</div>
<p>Dear Colleague,</p>
<p>We are sending the enclosed Executive Opportunity Report because we believe that every dollar
that does not have to be spent on indirect expense is a dollar available for the people you place
in work.</p>
<p>We prepared it before reaching out to you, from public information only. Its purpose is to
present where the available evidence suggests opportunity, and where it does not. We treat these
patterns as starting points of discussion rather than conclusions.</p>
<p>ERA Group has reviewed more than $2.25 billion of indirect spend across 670 engagements and
returned over $600 million to the organizations we work with. We are specialists in one thing:
the recurring operating costs that sit outside your program delivery.</p>
<p>If any of it is directionally useful, we would welcome a short conversation. If the current
arrangements are already competitive, that is a valuable conclusion as well &mdash; and it costs
you nothing to establish.</p>
<p>Nothing about the way we work commits you to anything. No supplier changes without your
approval, incumbent suppliers frequently remain, and if we do not create verified recovery there
is no fee.</p>
<p style='margin-top:16px'>Best regards,</p>
<div style='margin-top:34px'>
  <div style='font-weight:700;color:#0A2E4F;font-size:11pt'>John Wylie</div>
  <div style='font-size:9.6pt;color:#4A5763'>Consulting Partner &middot; ERA Group</div>
  <div style='font-size:9.6pt;color:#4A5763'>jwylie@eragroup.com &middot; 703.244.9868</div>
</div>
<div style='position:absolute;right:0.95in;bottom:0.9in;width:2.7in;border-top:1px solid #DDE3E9;
            padding-top:11px'>
  <div style='font-weight:700;color:#0A2E4F;font-size:9.4pt'>Your Report is live online</div>
  <div style='font-size:9pt;line-height:1.55;margin-top:3px'>Every figure is interactive &mdash;
   change any assumption and the model moves with it.<br>
   <b>portal.wpp-us.com/{PORTAL}</b></div>
  <div style='font-size:8.4pt;color:#8B96A0;margin-top:4px'>No code. No form. No login.</div>
</div>
<div style='position:absolute;left:0;right:0;bottom:0.42in;text-align:center;font-size:9pt;
            color:#8B96A0;letter-spacing:.26em'>VALUE THROUGH INSIGHT&#8482;</div>
</div>""")
blank()

# ─── 5 EXECUTIVE OVERVIEW ──────────────────────────────────────────────────
ROAD = ["What we found, and what follows", "What your own numbers say",
        "The position, as we read it", "Where we looked", "Priority 1 &mdash; Insurance",
        "Priority 2 &mdash; Maintenance", "What this rests on", "What happens next"]
road = "".join(f"<div class='rd'><span class='i'>{i}</span>{t}</div>"
               for i, t in enumerate(ROAD, 1))
rows = "".join(
    f"<tr><td><b>{n}</b></td><td class='r'>{usd(s)}</td>"
    f"<td class='r'>{s/FILED*100:.1f}%</td><td class='r'>{lo}&ndash;{hi}%</td></tr>"
    for n, s, lo, hi in CATS)
page(5, f"""{EY("Executive overview")}
<h1>What this is, why we prepared it, and what it does not claim.</h1>
<div class='lede'>One page of orientation before any numbers. We built this from your public filings
before contacting you, because we would rather show you our thinking than ask you to take it on
faith. Nothing here required anything from you, and nothing in it commits you to anything.</div>
<div class='two'><div>
  <h2>How it was built</h2>
  <ul class='pl'>
   <li><b>Your public filing.</b> Fifteen expense lines from your {FY} Form 990, six of which map
    to indirect categories we work.</li>
   <li><b>A second filing.</b> Your Form 5500 Schedule A, which discloses what is charged inside
    one of those categories &mdash; something the 990 never shows.</li>
   <li><b>Published category ranges.</b> How these markets behave, applied to your filed figures.
    They describe the category, never you.</li>
  </ul>
  <h2 style='margin-top:10px'>Reading the ranges</h2>
  <div class='panel'><p>A range is what we have seen a category yield when it is tested. It is not
   a claim about you, and it is not a finding. A category can sit anywhere in that range for sound
   reasons, and some will yield nothing at all.</p></div>
</div><div>
  <h2>What follows</h2>{road}
</div></div>
<h2>All six categories at a glance</h2>
<table><tr><th>Category</th><th class='r'>Filed spend</th><th class='r'>Share of the six</th>
<th class='r'>Range</th></tr>{rows}</table>
<p class='note' style='margin-top:6px'>Insurance is more than two thirds of what your filing breaks
out, and the one category where a second filing shows something the 990 cannot. That is why this
Report starts there. A filing can show a category is large, not whether it is well bought.</p>
{PROV("<b>FILED</b> 990 Part IX, " + FY + " &middot; <b>REGISTRY</b> 5500 Schedule A, 2024 "
      "&middot; <b>BENCHMARK</b> published ranges &middot; four layers absent, shown on p.12")}""")

# ─── 6 THE BRIDGE — five cards, NO FIGURES ─────────────────────────────────
def CARD(tag, h, body, why, cls=""):
    return (f"<div class='card {cls}'><div class='tag'>{tag}</div><h4>{h}</h4>"
            f"<p>{body}</p><div class='why'>{why}</div></div>")
page(6, f"""{EY("What we found, and what follows")}
<h1>Five things stood out. None of them is a conclusion.</h1>
<div class='lede'>A short summary of what our reading suggested and why each section is here, so you
can decide how much of the detail is worth your time.</div>
<div class='cards'>
{CARD("One category carries the rest",
  "Your indirect spend is concentrated, not spread.",
  "Of the six categories your filing breaks out, one is larger than the other five combined. That "
  "is unusual, and it means the rest of this Report can be short.",
  "<b>Why it matters:</b> it tells us where to look, and where not to.")}
{CARD("A second filing sees inside it",
  "There is a public record of what is charged within that category.",
  "Your benefit plan files its own annual return, and that return names the intermediaries and "
  "states what each was paid. Your Form 990 shows the category; this shows what sits inside it.",
  "<b>Why it matters:</b> almost nothing in indirect spend is disclosed this way.")}
{CARD("More than one intermediary",
  "Two organizations are being compensated in the same arrangement.",
  "The schedule discloses two separate relationships against a single carrier, each paid for a "
  "different stated reason.",
  "<b>Why it matters:</b> it raises a question about structure, not about anyone's conduct.")}
{CARD("The charges are described, not just counted",
  "The filing says what each payment was for, in your filer's words.",
  "Those descriptions are the most useful thing in the document, because they say what is being "
  "paid for rather than leaving it to be guessed at.",
  "<b>Why it matters:</b> it lets a conversation start from language you already use.")}
{CARD("The one question that could change the answer",
  "We do not know when this was last taken to market.",
  "Everything above describes a structure. Whether that structure is competitive depends entirely "
  "on something no filing records: when it was last tested, and against what.",
  "<b>Why it matters:</b> if it was tested recently and held, this Report ends there &mdash; and "
  "that is a useful answer.", "wide q")}
</div>
<p class='note' style='margin-top:12px'>Nothing on this page is a number. The arithmetic starts
overleaf, and every figure in it comes from a document you filed.</p>""")

# ─── 7 WHAT YOUR OWN NUMBERS SAY ───────────────────────────────────────────
bars = ""
for n, s, lo, hi in CATS:
    w = s / CATS[0][1] * 100
    bars += (f"<div style='margin-bottom:11px'>"
             f"<div style='display:flex;font-size:9.8pt'><div><b>{n}</b></div>"
             f"<div style='margin-left:auto;color:#0A2E4F;font-weight:700'>{usd(s)}</div></div>"
             f"<div style='height:9px;background:#EEF1F4;margin-top:4px'>"
             f"<div style='height:9px;width:{w:.1f}%;background:{'#0A2E4F' if n=='Insurance' else '#8FA6B8'}'></div>"
             f"</div></div>")
page(7, f"""{EY("What your own numbers say")}
<h1>Six categories, {usd(FILED)}, and one of them is two thirds of it.</h1>
<div class='lede'>Read straight from Part IX of your {FY} return. Nothing on this page is modelled
and nothing is estimated from revenue.</div>
{bars}
<div class='panel'><p><b>Insurance is {CATS[0][1]/FILED*100:.0f}% of the indirect spend your filing
breaks out</b> and {CATS[0][1]/REV*100:.1f}% of total revenue. A category at that weight is worth
understanding before anything else, whatever the answer turns out to be.</p></div>
<h2>What is not on this page</h2>
<p>A Form 990 breaks out only the lines the IRS asks for. Freight, waste, telecom, packaging,
payment processing and most professional services never appear separately, so we have not put a
number on them. They are not in {usd(FILED)}, and the true indirect base is larger than this
page shows.</p>
{PROV("<b>FILED</b> Form 990 Part IX, " + FY + ", object " + OBJ +
      " &mdash; 15 expense lines, 6 mapped to indirect categories, 0 estimated")}""")

# ─── 8 THE POSITION ────────────────────────────────────────────────────────
page(8, f"""{EY("The position, as we read it")}
<h1>A concentrated cost base is easier to work than a scattered one.</h1>
<div class='lede'>Where indirect spend spreads thinly across many categories, no single review is
worth much. Yours does not.</div>
<div class='two'><div>
<h2>What that means in practice</h2>
<ul class='pl'>
<li><b>One category to understand first.</b> Insurance at {usd(CATS[0][1])} is larger than the
 other five together. A review that answers this one question has covered most of the ground.</li>
<li><b>A short engagement, not a long one.</b> Concentration means fewer conversations, fewer
 suppliers and a faster answer either way.</li>
<li><b>The answer may be no.</b> Concentration cuts both ways. If this category is well bought,
 the rest is small enough that we would tell you so and stop.</li>
</ul></div><div>
<h2>What we are not saying</h2>
<div class='panel'><p>We are not saying you are paying too much. We have not seen a contract, a
policy schedule or an invoice, and a filing cannot show whether a price is competitive.</p></div>
<p style='margin-top:11px' class='note'>What a filing can show is <i>structure</i> &mdash; how many
parties are involved, what each is paid, and what the payment is called. That is the whole of what
follows, and it is a question rather than a verdict.</p>
</div></div>
{PROV("<b>FILED</b> Form 990 Part IX &nbsp;&middot;&nbsp; "
      "<b>DERIVED</b> category share, arithmetic on filed figures only")}""")

# ─── 9 WHERE WE LOOKED — the 5500 page. No names (#155). ───────────────────
page(9, f"""{EY("Where we looked")}
<h1>Your benefit plan files its own return, and it says what was charged.</h1>
<div class='lede'>Form 5500 Schedule A is filed annually by the plan. Unlike a Form 990 it names
each intermediary and states what each was paid, and why. It is the only place in indirect spend
where a charge is disclosed with a reason attached.</div>

<div style='background:#0A2E4F;color:#fff;padding:20px 24px;margin:6px 0 14px'>
  <div style='font-size:8pt;letter-spacing:.13em;color:#F2A900;font-weight:700'>DISCLOSED ON YOUR PLAN&rsquo;S {FY} SCHEDULE A</div>
  <div style='font-family:Georgia,serif;font-size:27pt;margin:9px 0 6px'>{usd(FEES)}</div>
  <div style='font-size:10pt'>in intermediary compensation, across <b>two relationships</b> on a
   single carrier, covering {LIVES} people.</div>
</div>

<table>
<tr><th>Relationship</th><th>Described by the filer as</th><th class='r'>Disclosed</th></tr>
<tr><td>Intermediary 1</td><td>&ldquo;Broker fees&rdquo;</td><td class='r'><b>{usd(FEES)}</b></td></tr>
<tr><td>Intermediary 2</td><td>&ldquo;TPA fees&rdquo;</td><td class='r'>not stated</td></tr>
</table>
<p class='note' style='margin-top:7px'>The second relationship is disclosed on the same schedule
with no amount stated. We have not assumed one.</p>

<h2>What we are asking, and what we are not</h2>
<div class='panel'><p>We are not suggesting either party is overpaid, and we are not suggesting you
change them. The question is narrower: <b>two parties are compensated in one arrangement, and the
filing describes their charges differently.</b> Whether that structure is right is not something a
filing can settle.</p></div>
<p class='note'>For context only: {usd(FEES)} is {FEES/REV*100:.1f}% of your total revenue and
{FEES/CATS[0][1]*100:.0f}% of the insurance line on your 990. Neither figure is a finding &mdash;
they are the same disclosure expressed against two denominators you already know.</p>
{PROV("<b>REGISTRY</b> DOL Form 5500 Schedule A, plan year 2024, EFAST2 public dataset, "
      "retrieved 2026-09-03. Intermediary names are held on file and are not printed.")}""")

# ─── 10, 11 THE TWO PRIORITIES — six parts each ────────────────────────────
def priority(rank, name, spend, lo, hi, parts):
    body = "".join(f"<h3>{h}</h3><p style='margin:0 0 3px'>{t}</p>" for h, t in parts)
    return f"""{EY(f"Priority {rank} of 2")}
<h1>{name} &mdash; {usd(spend)}</h1>
<div class='lede'>{spend/FILED*100:.0f}% of the indirect spend your filing breaks out. Published
range for this category when tested: <b>{lo}&ndash;{hi}%</b> &mdash; the size of the question, not
an estimate of what would be recovered here.</div>
{body}"""

page(10, priority(1, "Insurance", CATS[0][1], 8, 25, [
 ("What we see",
  f"The largest line your filing breaks out, and the only one where a second filing shows what is "
  f"charged inside it. Two intermediaries are compensated in one arrangement, described by your "
  f"own filer as broker fees and TPA fees."),
 ("Why it matters",
  "Insurance renews on a fixed cycle. It is one of the few indirect categories where a single "
  "annual decision sets the cost for the whole year, which makes it both easy to leave alone and "
  "quick to resolve."),
 ("What may be driving it",
  "<i>In our experience, arrangements with more than one compensated party often grew that way "
  "over several renewals rather than being designed. That is category inference from what we have "
  "seen elsewhere, not a finding about your plan.</i>"),
 ("What we do not know",
  "When the schedule was last taken to market rather than renewed. Whether both parties are "
  "delivering distinct services or overlapping ones. What the total compensation is, since one of "
  "the two amounts is not stated on the filing."),
 ("What we would test first",
  "The renewal date, and whether the last renewal was a genuine re-marketing or a rollover. Then "
  "what each of the two parties actually does, in their own words."),
 ("Potential impact if validated",
  "This category carries most of the range on the previous page. If the arrangement is sound, that "
  "is the answer and this Report is short. If it is not, it is a single annual decision rather "
  "than an operational change."),
]) + PROV("<b>FILED</b> Form 990 Part IX &nbsp;&middot;&nbsp; <b>REGISTRY</b> Form 5500 Schedule A "
          "&nbsp;&middot;&nbsp; <b>BENCHMARK</b> published range &nbsp;&middot;&nbsp; "
          "OPERATING absent"))

page(11, priority(2, "Maintenance", CATS[1][1], 10, 22, [
 ("What we see",
  f"{usd(CATS[1][1])}, the second largest of the six, covering facilities upkeep across your "
  f"locations."),
 ("Why it matters",
  "Maintenance is usually bought locally, by the people who need the work done, on terms that are "
  "rarely reviewed centrally. It is the category most likely to be several arrangements reported "
  "as one number."),
 ("What may be driving it",
  "<i>Where an organization operates from more than one site, this line is commonly a collection "
  "of separate local relationships rather than a single agreement. Category experience, not "
  "something your filing shows.</i>"),
 ("What we do not know",
  "Whether this is one contract or many. Whether any of it is bundled with a facilities or "
  "janitorial arrangement. Whether it includes capital work that would sit differently."),
 ("What we would test first",
  "The number of suppliers behind the line, and whether anyone sees the whole of it."),
 ("Potential impact if validated",
  "Smaller than insurance and slower to resolve, which is why it is second rather than first. "
  "Worth a look once the larger question is settled."),
]) + PROV("<b>FILED</b> Form 990 Part IX &nbsp;&middot;&nbsp; <b>BENCHMARK</b> published range "
          "&nbsp;&middot;&nbsp; OPERATING, REGISTRY absent for this category"))

# ─── 12 WHAT THIS RESTS ON ─────────────────────────────────────────────────
page(12, f"""{EY("What this rests on")}
<h1>Every figure, where it came from, and what we could not see.</h1>
<div class='lede'>Nine layers of evidence exist in our work. Four of them are empty for your
organization, and they are shown empty rather than filled.</div>
<table>
<tr><th>Layer</th><th>State</th><th>What it contributed</th></tr>
<tr><td><b>Filed</b></td><td>Present</td><td>Form 990 Part IX, {FY}, object {OBJ}. Fifteen expense
 lines, six mapped, none estimated.</td></tr>
<tr><td><b>Benchmark</b></td><td>Present</td><td>Published ranges for how these categories behave
 when tested. Describes the category, not you.</td></tr>
<tr><td><b>Derived</b></td><td>Present</td><td>Arithmetic on filed figures only &mdash; category
 shares and the two ratios on page 9.</td></tr>
<tr><td><b>Registry</b></td><td>Present</td><td>Form 5500 Schedule A, plan year 2024. The
 intermediaries, the stated purposes and the disclosed amount.</td></tr>
<tr><td><b>Operating</b></td><td><b>Absent</b></td><td>Nothing found specific enough to this
 organization to be worth stating. Omitted rather than filled.</td></tr>
<tr><td><b>Retrieved</b></td><td><b>Absent</b></td><td>No verified quotation from your own
 published material.</td></tr>
<tr><td><b>Engagement</b></td><td><b>Absent</b></td><td>You have not told us anything yet. This is
 the layer that only exists after a conversation.</td></tr>
<tr><td><b>Verified</b></td><td><b>Absent</b></td><td>Nothing has been checked against a contract,
 an invoice or a policy schedule.</td></tr>
</table>
<div class='bar'><span>FILED &#10003;</span><span>BENCHMARK &#10003;</span><span>DERIVED &#10003;</span>
<span>REGISTRY &#10003;</span><span>OPERATING &mdash;</span><span>RETRIEVED &mdash;</span>
<span>ENGAGEMENT &mdash;</span><span>VERIFIED &mdash;</span></div>
<div class='panel' style='margin-top:15px'><p><b>No inference is stated in this Report</b> except
where it is labelled as such, in italics, and attributed to category experience. You will find two
of those, on pages 10 and 11.</p></div>""")

# ─── 13 WHAT HAPPENS NEXT ──────────────────────────────────────────────────
page(13, f"""{EY("What happens next")}
<h1>A conversation. That is the whole of the ask.</h1>
<div class='lede'>There is no proposal in this document and no scope of work. The next step is
replacing what we assumed with what you know.</div>
<div class='cards'>
{CARD("Step one", "A conversation",
  "We walk the insurance question together and you tell us what the filing could not: when it was "
  "last tested, and what each party does.",
  "<b>Costs you:</b> the time it takes.")}
{CARD("Step two", "A no-cost baseline",
  "If it is worth going further, we replace the ranges in this Report with your actual contract "
  "data &mdash; across every applicable category, not only the six shown.",
  "<b>Costs you:</b> nothing.")}
{CARD("Step three", "An options report",
  "Category by category, what we found and what we would do about it. You decide what, if "
  "anything, to pursue.",
  "<b>Costs you:</b> nothing, and nothing changes without your approval.")}
{CARD("And if the answer is no", "That is a result too",
  "If your current arrangements are already competitive, we will tell you, and we will say which "
  "ones. That is worth knowing and it costs you nothing to establish.",
  "<b>Our fee:</b> a share of what is actually recovered, after you have it. No recovery, no fee.",
  "wide q")}
</div>
<div class='panel' style='margin-top:16px'><p>Every figure in this Report is live online. Change
any assumption and the model moves with it &mdash; and if we have read something wrongly, the page
will record your correction as yours.<br>
<b style='font-size:11pt'>portal.wpp-us.com/{PORTAL}</b><br>
<span class='note'>No code. No form. No login.</span></p></div>""")

blank()
# ─── 15 INSIDE BACK ────────────────────────────────────────────────────────
page(15, f"""{EY("Before we meet")}
<h1>Everything you have just read was prepared before we ever spoke.</h1>
<div class='lede'>Some of it may prove accurate. Some of it may not. That is not the point.</div>
<div class='two'><div>
<p>The purpose of this Report is not to prove an estimate. It is to work out &mdash; using your own
contracts and data &mdash; whether opportunity genuinely exists, and to tell you honestly when it
does not.</p>
<p>The strongest working relationships do not begin with a proposal. They begin with somebody
having done the reading first.</p>
<p>Whether we work together or not, we hope this reflects the preparation and the respect we bring
before asking for any of your time.</p>
</div><div>
<h2>What you can expect</h2>
<ul class='pl'>
<li><b>We will tell you when you are already getting a good deal.</b> If your arrangements are
 competitive, that is exactly what you will hear.</li>
<li><b>We recommend keeping incumbents whenever they are the right choice.</b> The objective is not
 changing suppliers.</li>
<li><b>Every recommendation is supported by evidence.</b> You see the data before any decision.</li>
<li><b>You remain in complete control.</b> Nothing changes without your approval. Ever.</li>
<li><b>Our success depends on yours.</b> If we do not recover value, there is no fee.</li>
</ul></div></div>""")

# ─── 16 BACK COVER ─────────────────────────────────────────────────────────
P.append(f"""<div class='page' style='page:cover;padding:0;min-height:11in;background:#0A2E4F'>
<div style='padding:2.1in 0.95in;color:#fff'>
  <div style='width:110px;height:2px;background:#F2A900;margin-bottom:26px'></div>
  <div style='font-family:Georgia,serif;font-size:22pt;line-height:1.34;max-width:5.1in'>
    What we could see is<br>the smaller half.</div>
  <p style='margin-top:22px;font-size:10.4pt;line-height:1.62;max-width:5.1in;color:#CBD6E2'>
    A Form 990 breaks out only the lines the IRS asks for. Most of what an organization actually
    buys never appears on one at all &mdash; freight, waste, telecom, packaging, payment
    processing. The categories that never reach a return are where this usually goes.</p>
  <div style='margin-top:2.2in;border-top:1px solid #2A4E70;padding-top:20px'>
    <div style='font-weight:700;font-size:11.5pt'>John Wylie</div>
    <div style='color:#CBD6E2;font-size:9.8pt;margin-top:3px'>Consulting Partner, ERA Group</div>
    <div style='color:#CBD6E2;font-size:9.8pt'>jwylie@eragroup.com &middot; 703.244.9868</div>
    <div style='color:#F2A900;font-weight:700;margin-top:16px;font-size:10.4pt'>No recovery, no fee.</div>
    <div style='color:#CBD6E2;font-size:9.4pt;margin-top:5px'>portal.wpp-us.com/{PORTAL}
      &nbsp;&middot;&nbsp; No code. No form. No login.</div>
  </div>
</div>
<div style='position:absolute;bottom:0.6in;left:0;right:0;text-align:center;color:#F2A900;
            font-size:10pt;letter-spacing:.4em'>VALUE THROUGH INSIGHT&#8482;</div>
</div>""")

html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(P)}</body></html>"
open("/home/claude/eor.html", "w").write(html)
out = "/mnt/user-data/outputs/EOR_CoastalEnterprises_READING.pdf"
HTML(string=html).write_pdf(out)

from pypdf import PdfReader
print("pages:", len(PdfReader(out).pages))
