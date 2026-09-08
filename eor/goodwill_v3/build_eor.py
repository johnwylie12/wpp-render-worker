#!/usr/bin/env python3
"""
Executive Opportunity Brief — Goodwill Industries of South Florida (account_id 23895)
LOCKED 2026-09-07.  19 numbered pages, 22 sheets.

Runs standalone from the repo:   python3 eor/goodwill_v3/build_eor.py
Output path overridable:         EOR_OUT=/path/out.pdf python3 .../build_eor.py

DOES NOT touch eor/eor_engine.py — that is the superseded Coastal rebuild (settled #173).

RENDERER NOTE. WeasyPrint does not honour flex align-items / justify-content, and drops
padding-bottom on a stretched flex child. Anything that must be centred uses a table cell
with vertical-align:middle, or explicit SVG geometry. Three separate defects traced to
this during the build; do not reintroduce flex centring.

TYPE SCALE — six steps, floor 9.5pt, nothing outside this set:
  9.5 micro | 10 body | 11 lede & letter | 12 subhead | 17 page headline | 24 hero

FIXED PAGE HEIGHT. .page is height:9.72in, so content that overruns is CLIPPED or pushed
to an orphan sheet — it does not reflow. After ANY edit, re-render and check both the page
count and for short pages before believing the change worked.
"""
import os, base64, io
from weasyprint import HTML

W = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
OUT = os.environ.get("EOR_OUT", "EOR_Goodwill_v3_FULL.pdf")

def b64(p, mime="image/png"):
    return f"data:{mime};base64," + base64.b64encode(open(p, "rb").read()).decode()

ERA_WHITE = b64(os.path.join(A, "era_logo_white.png"))
VTI_WHITE = b64(os.path.join(A, "vti_white.png"))
ERA_MARK  = b64(os.path.join(W, "meeting_label/assets/era_logo.png"))
VTI_MARK  = b64(os.path.join(W, "meeting_label/assets/vti_logo.png"))
HERO      = b64(os.path.join(W, "cir/src/assets/heroes/human_services.png"))
QR        = b64(os.path.join(A, "qr_portal.png"))
QR_BOOK   = b64(os.path.join(A, "qr_booking.png"))
HEADSHOT  = b64(os.path.join(W, "closing/assets/jw_headshot.jpg"), "image/jpeg")
SIG3      = io.open(os.path.join(A, "sig3_b64.txt")).read().strip()

ORG = "Goodwill Industries of South Florida"

CSS = """
@page { size:Letter; margin:0.5in 0.62in 0.46in 0.62in }
@page cover { margin:0 }
*{box-sizing:border-box;margin:0;padding:0}
/* TYPE SCALE — six steps, floor 9.5pt. Nothing outside this set.
   9.5 micro | 10 body | 11 lede & letter | 12 subhead | 17 page headline | 24 hero */
body{font-family:'Arial Nova','Arial','Carlito','DejaVu Sans',sans-serif;color:#1B2A41;
     font-size:10pt;line-height:1.5}
.page{page-break-after:always;position:relative;height:9.72in}
.page:last-child{page-break-after:auto}
h1{font-family:'Trebuchet MS',Arial,sans-serif;font-size:17pt;color:#003A70;line-height:1.2;
   font-weight:700;letter-spacing:-.01em;margin-top:12px}
h2{font-family:'Trebuchet MS',Arial,sans-serif;font-size:12pt;color:#003A70;font-weight:700;margin-bottom:6px}
h3{font-family:'Trebuchet MS',Arial,sans-serif;font-size:11pt;color:#003A70;font-weight:700;margin-bottom:4px}
p{font-size:10pt;line-height:1.55}
p+p{margin-top:7px}
.hdr{display:flex;align-items:flex-end;justify-content:space-between;border-bottom:2px solid #003A70;padding-bottom:6px}
.hdr .l{font-size:9.5pt;letter-spacing:.13em;text-transform:uppercase;color:#003A70;font-weight:700}
.hdr .r{text-align:right;font-size:9.5pt;color:#5A6577;line-height:1.4}
.ftr{position:absolute;left:0;right:0;bottom:-0.10in;border-top:1px solid #D7DFE9;padding-top:8px;
     font-size:9.5pt;color:#5A6577;display:flex;align-items:center}
.ftr .c{margin:0 auto;color:#003A70;font-weight:700}
.ftr .p{margin-left:auto}
.lede{font-size:11pt;line-height:1.55;margin-top:8px}
.lede b{color:#003A70}
table{width:100%;border-collapse:collapse;font-size:9.5pt;margin-top:11px}
th{text-align:left;font-size:9.5pt;letter-spacing:.1em;text-transform:uppercase;color:#5A6577;
   font-weight:700;padding:0 7px 6px;border-bottom:2px solid #003A70;vertical-align:bottom}
th.n{text-align:right}
td{padding:7.5px 7px;border-bottom:1px solid #D7DFE9;vertical-align:middle}
table.tight td{padding:4.6px 7px}
td.n{text-align:right}
.cat{font-weight:700;color:#003A70}
.sub{font-size:9.5pt;color:#5A6577;margin-top:2px;line-height:1.3}
.dol{font-family:'Trebuchet MS',Arial,sans-serif;font-weight:700;color:#003A70;font-size:11pt}
tr.q td,tr.q .cat{color:#5A6577}
.totrow td{border-bottom:0;border-top:2px solid #003A70;background:#E4EBF3;padding:10px 7px}
.panel{background:#F2F5F8;border-left:3px solid #FF9C00;padding:12px 15px;margin-top:12px}
.panel.cream{background:#FEF4E2}
.panel.deep{background:#E4EBF3;border-left-color:#003A70}
.two{display:flex;gap:18px;margin-top:12px}
.two>div{flex:1}
.three{display:flex;gap:12px;margin-top:12px}
.three>div{flex:1}
.card{border:1px solid #D7DFE9;padding:11px 13px}
.card.cream{background:#FEF4E2;border-color:#F0D8A6;border-left:3px solid #FF9C00}
.card .k{font-size:9.5pt;letter-spacing:.12em;text-transform:uppercase;color:#5A6577;font-weight:700}
.card .h{font-family:'Trebuchet MS',Arial,sans-serif;font-size:11pt;color:#003A70;font-weight:700;margin:4px 0}
.card p{font-size:9.5pt}
.card .w{border-top:1px solid #D7DFE9;margin-top:6px;padding-top:5px;font-size:9.5pt;color:#5A6577}
.card .w b{color:#003A70}
table.tight td{padding:5px 7px}
table.tight th{padding:0 7px 5px}
.prov{margin-top:12px;padding-top:7px;border-top:1px solid #D7DFE9;font-size:9.5pt;color:#5A6577;line-height:1.45}
.prov b{color:#003A70}
ul{list-style:none}
li{font-size:9.5pt;line-height:1.5;padding-left:14px;position:relative;margin-bottom:6px}
li:before{content:"";position:absolute;left:0;top:.52em;width:5px;height:5px;background:#FF9C00;border-radius:1px}
.eyebrow{font-size:9.5pt;letter-spacing:.16em;text-transform:uppercase;color:#C07400;font-weight:700}
svg{display:block;margin-top:10px}
.capt{font-size:9.5pt;color:#5A6577;line-height:1.45;margin-top:7px}
.capt b{color:#003A70}
"""

P=[]
def page(n, eyebrow, inner):
    P.append(f"""<div class='page'>
      <div class='hdr'><div class='l'>{eyebrow}</div>
        <div class='r'>{ORG}<br>Form 990 FY2024</div></div>
      {inner}
      <div class='ftr'><img src='{VTI_MARK}' style='height:16px'>
        <span class='c'>{ORG}</span><span class='p'>PAGE {n} OF 19</span></div></div>""")

# ══════════ COVER ══════════
P.append(f"""<div class='page' style='page:cover;height:11in;padding:0'>
 <div style='position:relative;height:8.6in;background:#003A70;overflow:hidden'>
   <img src='{HERO}' style='position:absolute;right:0;top:0;height:8.6in;width:5.95in;object-fit:cover'>
   <div style='position:absolute;left:2.0in;top:-1in;width:2.55in;height:11in;background:#003A70;
        transform:skewX(-11deg);transform-origin:top left'></div>
   <div style='position:absolute;left:4.52in;top:-1in;width:0.045in;height:11in;background:#FF9C00;
        transform:skewX(-11deg);transform-origin:top left'></div>
   <div style='position:relative;padding:0.75in 0 0 0.78in;width:2.95in'>
     <img src='{ERA_WHITE}' style='height:0.62in;margin-bottom:0.62in'>
     <div style='color:#FF9C00;font-size:11pt;letter-spacing:.28em;font-weight:700'>PREPARED EXCLUSIVELY FOR</div>
     <div style='width:1.05in;height:3px;background:#FF9C00;margin:11px 0 20px'></div>
     <div style='font-family:Trebuchet MS,Arial,sans-serif;color:#fff;font-size:24pt;
          line-height:1.16;font-weight:700;letter-spacing:-.015em'>Goodwill<br>Industries of<br>South Florida</div>
     <div style='width:2.3in;height:2px;background:#FF9C00;margin:0.38in 0 14px'></div>
     <div style='color:#fff;font-size:9.5pt;letter-spacing:.11em;font-weight:700;white-space:nowrap'>EXECUTIVE OPPORTUNITY BRIEF</div>
     <div style='border-left:3px solid #FF9C00;padding-left:14px;margin-top:0.32in'>
       <div style='color:#fff;font-size:12pt;line-height:1.42'>Your next
         <span style='color:#FF9C00'>program</span> may already be hiding in your operating budget.</div></div>
     <div style='color:#FF9C00;font-size:11pt;letter-spacing:.22em;font-weight:700;margin-top:0.75in'>SEPTEMBER 7, 2026</div>
   </div>
 </div>
 <div style='height:1.85in;background:#F2F5F8;display:flex;align-items:center;padding:0 0.78in'>
   <div style='flex:1;text-align:center'>
     <svg width='0.46in' height='0.46in' viewBox='0 0 52 52' style='display:block;margin:0 auto 12px'><circle cx='26' cy='26' r='26' fill='#003A70'/><g transform='translate(8.00,9.50) scale(1.50)' fill='#FF9C00'><path d="M12 2 2 7v2h20V7L12 2zM4 10v7H3v3h18v-3h-1v-7h-2v7h-3v-7h-2v7h-2v-7H9v7H6v-7H4z"/></g></svg>
     <div style='color:#1B2A41;font-size:9.5pt;letter-spacing:.07em;font-weight:700'>OUTSIDE-IN ANALYSIS</div>
     <div style='color:#97999B;font-size:9.5pt;margin-top:6px;letter-spacing:.03em'>INFORMED PERSPECTIVE</div>
     <div style='color:#5A6577;font-size:9.5pt;font-weight:700;letter-spacing:.03em'>BEFORE ANY MEETING</div></div>
   <div style='width:2px;height:0.92in;background:#FF9C00;opacity:.85'></div>
   <div style='flex:1;text-align:center'>
     <svg width='0.46in' height='0.46in' viewBox='0 0 52 52' style='display:block;margin:0 auto 12px'><circle cx='26' cy='26' r='26' fill='#003A70'/><g transform='translate(10.40,11.05) scale(1.28)' fill='#FF9C00'><path d="M12 1 3 5v6c0 5 3.8 9.7 9 11 5.2-1.3 9-6 9-11V5l-9-4zm-1.2 15L7 12.2l1.4-1.4 2.4 2.4 5-5L17.2 9l-6.4 7z"/></g></svg>
     <div style='color:#1B2A41;font-size:9.5pt;letter-spacing:.07em;font-weight:700'>MISSION FOCUSED</div>
     <div style='color:#97999B;font-size:9.5pt;margin-top:6px;letter-spacing:.03em'>STEWARDSHIP TODAY.</div>
     <div style='color:#97999B;font-size:9.5pt;letter-spacing:.03em'>STRENGTH TOMORROW.</div></div>
   <div style='width:2px;height:0.92in;background:#FF9C00;opacity:.85'></div>
   <div style='flex:1;text-align:center'>
     <svg width='0.46in' height='0.46in' viewBox='0 0 52 52' style='display:block;margin:0 auto 12px'><circle cx='26' cy='26' r='26' fill='#003A70'/><g transform='translate(2.00,-1.00) scale(2.00)' fill='#FF9C00'><path d="M4 13h3v7H4v-7zm6.5-6h3v13h-3V7zM17 10h3v10h-3V10z"/></g></svg>
     <div style='color:#1B2A41;font-size:9.5pt;letter-spacing:.07em;font-weight:700'>MEASURABLE IMPACT</div>
     <div style='color:#97999B;font-size:9.5pt;margin-top:6px;letter-spacing:.03em'>DOLLARS RECOVERED.</div>
     <div style='color:#97999B;font-size:9.5pt;letter-spacing:.03em'>OPPORTUNITIES FUNDED.</div></div>
 </div>
 <div style='height:0.55in;background:#003A70;text-align:center;line-height:0.55in'>
   <img src='{VTI_WHITE}' style='height:15px;vertical-align:middle'></div>
</div>""")

# ══════════ COVER LETTER — locked copy ══════════
P.append(f"""<div class='page' style='height:9.72in'>
 <img src='{ERA_MARK}' style='height:0.52in'>
 <div style='width:1.72in;height:4px;background:#FF9C00;margin:14px 0 5px'></div>
 <div style='height:2px;background:#003A70;margin-bottom:22px'></div>
 <div style='color:#5A6577;font-size:11pt;margin-bottom:13px'>September 7, 2026</div>
 <div style='color:#003A70;font-size:12pt;font-weight:700'>Raisa Ciobanu</div>
 <div style='font-size:11pt;line-height:1.5;margin-bottom:13px'>Chief Financial Officer<br>
   Goodwill Industries of South Florida<br>2121 NW 21st St<br>Miami, FL 33142-7317</div>
 <p style='font-size:11pt'>Dear Raisa,</p>
 <p style='font-size:11pt;margin-top:8px'>We prepared the enclosed Executive Opportunity Brief before reaching out, because a useful
   conversation should begin with evidence rather than a capability presentation. For an
   organization whose mission is helping people get and keep meaningful work, every dollar that
   does not need to remain in indirect operating expense is a dollar that can stay closer to that
   mission.</p>
 <p style='font-size:11pt'>The Brief was built from public information only. It shows what the available record suggests
   may be worth understanding, what appears less important, and — just as importantly — what the
   public record cannot tell us. We treat those patterns as questions to validate, not conclusions
   about how Goodwill Industries of South Florida is being run. <b>Across five categories your
   filing names, that question is worth about $3.0 million a year at the median of our completed
   work.</b></p>
 <p style='font-size:11pt'>ERA Group has reviewed more than $2.25 billion of indirect spend across 6,420 engagements at
   916 organizations. Our work is focused on recurring operating costs outside program delivery,
   using category specialists to test whether current arrangements remain competitive.</p>
 <p style='font-size:11pt'>If the analysis is directionally useful, we would welcome a short conversation. If your current
   arrangements are already competitive, that is a valuable answer too. Nothing changes without
   your approval, incumbent suppliers often remain, and if we do not create verified recovery,
   there is no fee.</p>
 <p style='font-size:11pt;margin-top:14px'>Best regards,</p>
 <div style='display:flex;margin-top:20px;align-items:flex-start'>
   <div style='flex:1'>
     <img src='{SIG3}' style='width:115px;margin-bottom:2px'>
     <div style='font-size:12pt;color:#003A70;font-weight:700'>John Wylie</div>
     <div style='font-size:11pt;color:#5A6577;line-height:1.5'>Consulting Partner · ERA Group<br>
       jwylie@eragroup.com · 703.244.9868</div>
   </div>
   <div style='flex:0 0 3.25in;border-left:3px solid #FF9C00;padding-left:14px'>
     <div style='color:#003A70;font-size:11pt;font-weight:700'>Your Brief is live online</div>
     <img src='{QR}' style='width:0.95in;height:0.95in;margin-top:6px'>
     <div style='font-size:9.5pt;color:#5A6577;margin-top:6px'>portal.wpp-us.com/goodwillsouthflorida-benchmark</div>
     <div style='font-size:9.5pt;color:#003A70;font-weight:700;margin-top:3px'>No code. No form. No login.</div>
   </div>
 </div>
 <div style='position:absolute;left:0;right:0;bottom:0.02in;text-align:center'>
   <img src='{VTI_MARK}' style='height:16px'></div>
</div>""")

# ══════════ 1 · EXECUTIVE SUMMARY ══════════
def toc_row(title, desc, pg, apx=False):
    c = '#5A6577' if apx else '#003A70'
    w = '600' if apx else '700'
    return (f"<tr><td style='padding:4.4px 0'>"
            f"<span style='color:{c};font-weight:{w};font-size:10pt'>{title}</span>"
            f"<span class='sub' style='margin-left:9px'>{desc}</span></td>"
            f"<td class='n' style='width:40px;padding:4.4px 0;color:{c};font-weight:700;"
            f"font-family:Trebuchet MS,Arial,sans-serif'>{pg}</td></tr>")

TOC = "".join([
 toc_row("Contents","this page","1"),
 toc_row("Executive summary","the finding, the recommendation and the first step","2"),
 toc_row("How this was built","the three inputs, and what each one supports","3"),
 toc_row("Why the value is available","how indirect spend behaves, and why it drifts","4"),
 toc_row("A bid tests the price","what a sourcing process is not designed to examine","5"),
 toc_row("What your filing shows","your nine indirect categories, and what your return names","6"),
 toc_row("How your categories compare","against filers reporting the same lines","7"),
 toc_row("Every category we identified","all fourteen, and where each one stands","8"),
 toc_row("The categories your return does not show","four more, and the $69.6M it will not separate","9"),

 toc_row("The largest line","why we hold it to a floor rather than pricing it","10"),
 toc_row("What it would involve","six steps, and what each one costs you","11"),
 toc_row("Both answers are useful","what you hold if we find nothing","12"),
 toc_row("Who else should see this","two questions only your operators can answer","13"),
 toc_row("Before we meet","what we would like to ask you","14"),
 "<tr><td colspan='2' style='font-size:9.5pt;letter-spacing:.14em;text-transform:uppercase;color:#5A6577;"
 "font-weight:700;padding:12px 0 4px;border-bottom:2px solid #003A70'>Appendices</td></tr>",
 toc_row("A \u00b7 Sector cost structure","how the floor on the materials line was set","15",True),
 toc_row("B \u00b7 Category evidence","sample, median and middle half for every category priced","16",True),
 toc_row("C \u00b7 The comparison group","how it was built, and what it cannot show","17",True),
 toc_row("D \u00b7 Every filed line","all twelve indirect lines and their disposition","18",True),
 toc_row("E \u00b7 Sources","evidence layers, filing objects and retrieval dates","19",True),
])

page(1, "Contents", f"""
<h1>What is in this document.</h1>
<p class='lede'>Thirteen short sections and five appendices. The sections set out the areas where we
  believe we may be able to help, and what each could be worth. The appendices hold how each figure
  was worked out, every source and every date.</p>
<table style='margin-top:14px'><thead><tr>
  <th>Section</th><th class='n' style='width:40px'>Page</th>
</tr></thead><tbody>{TOC}</tbody></table>
<div class='panel deep'>
  <p style='margin:0'><b>If you read three pages, read 8, 9 and 14.</b> Every category we identified,
  the ones your return does not show, and the one question we would like answered.</p></div>
""")

# ══════════ 2 · WHY IT IS AVAILABLE ══════════
page(2, "Executive summary", f"""
<h1 style='font-size:17pt;margin-top:7px'>We believe we can recover about $2.5 million<br>a year for you. Here is the basis, and the first step.</h1>

<table style='width:100%;border-collapse:collapse;margin-top:10px'>
 <tr>
  <td style='width:30%;background:#003A70;color:#fff;padding:14px;vertical-align:middle;border:0'>
    <div style='font-family:Trebuchet MS,Arial,sans-serif;font-size:24pt;font-weight:700;line-height:1;letter-spacing:-.02em'>$2.51M</div>
    <div style='font-size:9.5pt;color:#DCE7F5;margin-top:7px;line-height:1.4'>a year, recovered from
      what you already pay suppliers, across five categories your filing names</div>
    <div style='font-size:9.5pt;color:#FF9C00;margin-top:8px;font-weight:700'>A floor, not a range.</div>
  </td>
  <td style='background:#FEF4E2;padding:14px 16px;vertical-align:middle;border:0;border-left:3px solid #FF9C00'>
    <p style='font-size:10pt;margin:0'><b style='color:#003A70'>How we would work it.</b> We take
      your spend across every category we work — not only the ones a filing happens to show — and
      come back with an options report for each. What each arrangement costs today, what it could
      cost, and what changing it would involve.</p>
    <p style='font-size:10pt;margin-top:7px'><b style='color:#003A70'>You decide what to act on,
      category by category.</b> Nothing is committed by looking, and an arrangement that is already
      competitive comes back saying so.</p>
  </td>
 </tr>
</table>

<h2 style='margin-top:8px'>Situation</h2>
<p><b style='color:#003A70'>Your return names officers for apparel manufacturing, a commercial
  laundry, donated goods and service contracts.</b> Four distinct operating environments under one
  organization, which tends to spread ownership of a category across several people. Against
  $196.1M of revenue, the categories outside program and payroll come to $82.1M — every line set
  out in Appendix D.</p>

<h2 style='margin-top:7px'>Complication</h2>
<p><b style='color:#003A70'>Indirect spend is distributed by design, which is why it drifts.</b>
  Twelve indirect lines appear on your FY2024 return. Each is too small alone to justify continuous
  market testing, and they renew on their own schedule while the markets underneath them move.</p>
<p><b style='color:#003A70'>A competitive bid tests the price. It does not read the agreement.</b>
  Term, minimums, usage bands, ancillary charges, renewal mechanics, and what is billed against what
  was agreed — in our completed work the value sits there more often than in the rate.</p>

<h2 style='margin-top:7px'>What we would expect to find</h2>
<p><b style='color:#003A70'>Agreements carried forward on their original structure.</b> Terms are
  usually set once and rolled at renewal — minimums, usage bands, replacement practice and ancillary
  charges rarely reopened even when the price is.</p>
<p><b style='color:#003A70'>Billing that has drifted from what was agreed.</b> Most of what we
  recover sits in the gap between the contract and the invoice, which is why a recent bid does not
  settle it.</p>



<h2 style='margin-top:7px'>We are paid out of the recovery, not for the advice</h2>
<p><b style='color:#003A70'>We take a share of what is actually recovered, and nothing else.</b>
  No fee for this Brief, no retainer, no hourly rate. And we do the work rather than hand over a
  report — our specialists negotiate the agreement, we implement only what you approve, and the
  result is verified with your finance team before anything is invoiced. If we recover nothing, we
  earn nothing.</p>

<p style='margin-top:8px'><b style='color:#003A70'>Next step — twenty minutes and one question.</b>
  When were these arrangements last tested, and against what? No public filing can tell us that.</p>
""")

page(3, "How this was built", """
<h1>How it was built, and what it does not claim.</h1>
<p class='lede'>Three inputs, and a clear line around what each one can and cannot support.</p>
<div class='three' style='margin-top:14px'>
  <div class='card'><div class='k'>Input one</div><div class='h'>Your return, line by line</div>
    <p>Nineteen expense lines. Twelve are indirect rather than people or non-cash, and all twelve
      appear in this document with a stated disposition.</p></div>
  <div class='card'><div class='k'>Input two</div><div class='h'>The relationships you name</div>
    <p>Part VII Section B states the service and the amount for each. Three fall in categories we
      work. The counterparties are named on your return and are not reprinted here.</p></div>
  <div class='card'><div class='k'>Input three</div><div class='h'>Our completed work</div>
    <p>Every percentage is the median of engagements ERA has finished in that same category. No
      published market range is used anywhere in this document.</p></div>
</div>
<h2 style='margin-top:14px'>Nine layers of evidence, and the five we could fill</h2>
<p>Every claim in this document sits on one of nine layers. Where a layer is empty for your
  organization we show it empty rather than filling it with something general.</p>
<div style='display:flex;margin-top:11px;background:#003A70;color:#fff'>
  <div style='flex:0 0 1.5in;padding:10px 0 10px 14px;border-right:1px solid rgba(255,255,255,.25)'>
    <div style='font-size:9.5pt;letter-spacing:.13em;color:#FF9C00;font-weight:700'>PRESENT</div>
    <div style='font-size:10pt;color:#DCE7F5;margin-top:2px'>five of nine</div></div>
  <div style='flex:1;display:flex;text-align:center'>
    <div style='flex:1;padding:10px 0'><div style='font-size:9.5pt;letter-spacing:.06em'>FILED</div></div>
    <div style='flex:1;padding:10px 0'><div style='font-size:9.5pt;letter-spacing:.06em'>REGISTRY</div></div>
    <div style='flex:1;padding:10px 0'><div style='font-size:9.5pt;letter-spacing:.06em'>OPERATING</div></div>
    <div style='flex:1;padding:10px 0'><div style='font-size:9.5pt;letter-spacing:.06em'>BENCHMARK</div></div>
    <div style='flex:1;padding:10px 0'><div style='font-size:9.5pt;letter-spacing:.06em'>DERIVED</div></div>
  </div>
</div>
<div style='display:flex;background:#F2F5F8;border:1px solid #D7DFE9;border-top:0'>
  <div style='flex:0 0 1.5in;padding:10px 0 10px 14px;border-right:1px solid #D7DFE9'>
    <div style='font-size:9.5pt;letter-spacing:.13em;color:#5A6577;font-weight:700'>ABSENT</div>
    <div style='font-size:10pt;color:#5A6577;margin-top:2px'>four of nine</div></div>
  <div style='flex:1;display:flex;text-align:center;color:#5A6577'>
    <div style='flex:1;padding:10px 0'><div style='font-size:9.5pt;letter-spacing:.06em'>RETRIEVED</div></div>
    <div style='flex:1;padding:10px 0'><div style='font-size:9.5pt;letter-spacing:.06em'>ECOSYSTEM</div></div>
    <div style='flex:1;padding:10px 0'><div style='font-size:9.5pt;letter-spacing:.06em'>ENGAGEMENT</div></div>
    <div style='flex:1;padding:10px 0'><div style='font-size:9.5pt;letter-spacing:.06em'>VERIFIED</div></div>
    <div style='flex:1;padding:10px 0'></div>
  </div>
</div>
<p style='margin-top:10px'><b style='color:#003A70'>What the five gave us.</b> Your return,
  nineteen lines. The service relationships your return names. The officer roles that identify the
  operations behind the spend. Our completed engagements by category. And arithmetic on filed
  figures only.</p>
<p><b style='color:#003A70'>What the four would need.</b> Retrieved and Ecosystem require verified
  material published by you, and we found none close enough to print. Engagement exists only after a
  conversation. Verified means checked against a contract, an invoice or a schedule of rates — which
  is the whole of what a first meeting is for.</p>
<div class='panel deep'>
  <p style='margin:0'><b>Four empty layers is the honest state of an outside-in read.</b> Every
    figure in this document could move once those layers are filled, and the direction they move is
    the reason the conversation is worth twenty minutes.</p></div>
""")

# ══════════ CONTENTS ══════════
page(4, "Why the value is available", """
<h1>Direct spend is managed. Indirect spend is<br>distributed — and that is why it drifts.</h1>
<p class='lede'>Nothing on this page is about your organization. It describes how indirect spend
  behaves everywhere, and it is the reason a category can be well run and still be worth reading.</p>

<svg viewBox="0 0 620 150" width="100%" height="150">
  <g font-family="Arial" font-size="9.5">
    <text x="0" y="12" fill="#003A70" font-weight="bold" font-size="10.5">DIRECT SPEND</text>
    <rect x="0" y="20" width="480" height="26" fill="#003A70"/>
    <rect x="480" y="20" width="120" height="26" fill="#E4EBF3"/>
    <text x="12" y="37" fill="#fff" font-weight="bold">80% of the dollars</text>
    <text x="492" y="37" fill="#5A6577">20% of vendors</text>
    <text x="0" y="60" fill="#5A6577">Concentrated, visible, closely managed. Someone owns each relationship.</text>

    <text x="0" y="92" fill="#C07400" font-weight="bold" font-size="10.5">INDIRECT SPEND</text>
    <rect x="0" y="100" width="120" height="26" fill="#FF9C00"/>
    <rect x="120" y="100" width="480" height="26" fill="#F2F5F8" stroke="#D7DFE9"/>
    <text x="12" y="117" fill="#412402" font-weight="bold">20%</text>
    <g fill="#97999B">
      <rect x="128" y="104" width="14" height="18"/><rect x="148" y="104" width="14" height="18"/>
      <rect x="168" y="104" width="14" height="18"/><rect x="188" y="104" width="14" height="18"/>
      <rect x="208" y="104" width="14" height="18"/><rect x="228" y="104" width="14" height="18"/>
      <rect x="248" y="104" width="14" height="18"/><rect x="268" y="104" width="14" height="18"/>
      <rect x="288" y="104" width="14" height="18"/><rect x="308" y="104" width="14" height="18"/>
      <rect x="328" y="104" width="14" height="18"/><rect x="348" y="104" width="14" height="18"/>
      <rect x="368" y="104" width="14" height="18"/><rect x="388" y="104" width="14" height="18"/>
      <rect x="408" y="104" width="14" height="18"/><rect x="428" y="104" width="14" height="18"/>
      <rect x="448" y="104" width="14" height="18"/><rect x="468" y="104" width="14" height="18"/>
      <rect x="488" y="104" width="14" height="18"/><rect x="508" y="104" width="14" height="18"/>
      <rect x="528" y="104" width="14" height="18"/><rect x="548" y="104" width="14" height="18"/>
      <rect x="568" y="104" width="14" height="18"/>
    </g>
    <text x="0" y="140" fill="#5A6577">Spread across 80% of the vendors. Each one too small on its own to justify testing.</text>
  </g>
</svg>
<p class='capt'><b>That asymmetry is the whole of it.</b> A category worth $400,000 does not earn a
  dedicated review, so it renews. Twenty of them together do.</p>

<div class='three'>
  <div class='card'><div class='k'>It is distributed</div>
    <p>Agreements are held by different people in different places. Finance sees the invoices; no
      single system holds the aggregate.</p></div>
  <div class='card'><div class='k'>It renews quietly</div>
    <p>Most indirect agreements roll over on their own terms. A renewal is rarely a decision — it
      is the absence of one.</p></div>
  <div class='card'><div class='k'>The market moves anyway</div>
    <p>The Bureau of Labor Statistics maintains price indices so long-term agreements can be
      escalated objectively. The index moves whether or not the contract is re-read.</p></div>
</div>
<div class='panel deep'>
  <p style='margin:0'><b>This is structural, and it is true of every organization we work with.</b>
    It is not a management failure and we do not present it as one. It is simply what happens to
    spend that is individually small, individually justified, and collectively large.</p></div>
<div class='prov'><b>BLS</b> Producer Price Index, <i>PPI Guide for Price Adjustment</i>, bls.gov &middot;
  the 80/20 split is a characteristic of indirect spend generally, not a measurement of your organization</div>""")

# ══════════ 5 · A BID TESTS THE PRICE ══════════
page(5, "Two different questions", """
<h1>A bid tests the price.<br>It does not read the agreement.</h1>
<p class='lede'>Most organizations have tested most of these categories at some point, and a
  competitive process is a real test. It answers one question well.</p>
<div class='panel'>
  <p style='margin-bottom:7px'>A bid establishes what the market will quote today, against the
    specification you put in front of it. <b>What it does not examine is the agreement underneath —
    the term, the minimums, the usage bands, the ancillary charges, the renewal mechanics, and what
    is actually billed against what was agreed.</b></p>
  <p style='margin:0'>In our completed work the value more often sits in that structure than in the
    quoted rate. Which is why a category can have been bid, renewed, brokered and reviewed, and
    still be worth an expert second look.</p></div>

<h2 style='margin-top:14px'>Three examples, from categories on your return</h2>
<div class='three'>
  <div class='card'><div class='k'>Small parcels</div><div class='h'>The rate is not the cost</div>
    <p>Agreements carry earned discount tiers, a dimensional weight divisor and a long list of
      accessorials. They are rarely negotiated together, and the divisor alone can move the
      effective rate more than the headline discount.</p></div>
  <div class='card'><div class='k'>Office supplies</div><div class='h'>The basket erodes</div>
    <p>Contracts are priced on a core list. Over time off-list buying grows and the negotiated items
      stop matching what is actually ordered — so the agreed price is right and the invoice is not.</p></div>
  <div class='card'><div class='k'>Uniforms and linens</div><div class='h'>Structure over rate</div>
    <p>Value sits in replacement practice, inventory treatment, minimums and what happens on
      rollover. Our completed work here ranges from 16% to 42% of category spend, and the spread is
      that wide because the answer depends on the agreement.</p></div>
</div>
<div class='panel cream'>
  <p style='margin:0'><b>None of this says anything about how you buy.</b> It describes what a
    sourcing process is built to do and what it is not. If these agreements were read closely at the
    last renewal, the answer is no and it costs nothing to establish.</p></div>
<div class='prov'><b>CATEGORY MECHANICS</b> drawn from ERA engagements completed in each category
  &middot; percentages are the middle half of finished work, not a published market range</div>""")

# ══════════ 4 · WHAT YOUR FILING SHOWS ══════════
page(6, "What your filing shows", """
<h1>Ten indirect categories,<br>and the relationships you name yourself.</h1>
<p class='lede'>Everything on this page is your filed figure or your filing's own wording. Nothing on
  it is compared to anything.</p>
<table>
  <thead><tr><th style='width:44%'>Category</th><th style='width:34%'>The line it comes from</th>
    <th class='n' style='width:22%'>FY2024</th></tr></thead>
  <tbody>
    <tr><td class='cat'>Operating Supply</td><td class='sub'>MATERIALS AND SUPPLIES · 24</td><td class='n'>$37,971,710</td></tr>
    <tr><td class='cat'>Small Parcels</td><td class='sub'>FREIGHT AND POSTAGE · 24</td><td class='n'>$2,631,840</td></tr>
    <tr><td class='cat'>Fleet Management</td><td class='sub'>FLEET AND TRANSPORTATION · 24</td><td class='n'>$2,122,533</td></tr>
    <tr><td class='cat'>Uniforms, Workwear &amp; Linens</td><td class='sub'>Part VII B — service stated on your return</td><td class='n'>$1,518,596</td></tr>
    <tr><td class='cat'>Office Supplies</td><td class='sub'>Office expenses · 13</td><td class='n'>$1,372,501</td></tr>
    <tr><td class='cat'>Professional Services</td><td class='sub'>Fees for services — Legal · 11b</td><td class='n'>$637,913</td></tr>
    <tr><td class='cat'>Benefits Administration</td><td class='sub'>Part VII B — service stated on your return</td><td class='n'>$558,228</td></tr>
    <tr><td class='cat'>Payroll &amp; HR administration</td><td class='sub'>Part VII B — service stated on your return</td><td class='n'>$476,232</td></tr>
    <tr><td class='cat'>Marketing Services</td><td class='sub'>Advertising and promotion · 12</td><td class='n'>$482,421</td></tr>
    <tr><td class='cat'>Travel</td><td class='sub'>Travel · 17</td><td class='n'>$449,863</td></tr>
  </tbody></table>
<div class='two'>
  <div><h2>Your filing names the service</h2>
    <p>Part VII Section B asks for the highest-paid contractors, what each was engaged to do and what
      each was paid. Yours describes the service, which is more than most filings do — and three of
      the four sit in categories where we hold deep completed work.</p>
    <p>It means we can ask about a specific arrangement rather than about a category in general.
      The counterparties are named on your return and are not reprinted here.</p></div>
  <div><h2>All of these were FY2024 relationships</h2>
    <p>Each was in place for the year the filing covers. Agreements of this kind usually carry an
      annual term, so most will have renewed at least once since.</p>
    <p>In several categories a renewal is the only moment the structure is genuinely open — which
      is why the timing question matters as much as the number.</p></div>
</div>
<div class='prov'><b>FILED</b> Form 990 Part IX and Part VII Section B, FY2024, filing object
  202523219349308832 &middot; nineteen expense lines, twelve indirect, none estimated</div>""")

# ══════════ 5 · WHAT EACH COULD RETURN ══════════
page(7, "How your categories compare", f"""
<h1>Where your filed lines sit against<br>organizations that report the same lines.</h1>
<p class='lede'>Your share of total operating expense against the midpoint of comparable filers.
  <b>A difference is a reason to ask a better question, never a verdict on how you are run</b> —
  and the midpoint is drawn from organizations that have mostly never tested these lines either.</p>

<table class='tight' style='margin-top:12px'>
  <thead><tr><th style='width:27%'>Category</th><th class='n' style='width:12%'>FY2024</th>
    <th class='n' style='width:13%'>Comparable filers</th><th class='n' style='width:10%'>You</th>
    <th class='n' style='width:11%'>Difference, bps</th><th style='width:27%'>What it means</th></tr></thead>
  <tbody>
    <tr style='background:#F2F5F8'><td><div class='cat'>Operating Supply</div><div class='sub'>480 filers report this line</div></td>
      <td class='n'>$37.97M</td><td class='n'>2.06%</td>
      <td class='n'><span style='color:#C07400;font-weight:700;font-size:10.5pt'>20.51%</span></td>
      <td class='n'>+1845</td>
      <td><span style='color:#003A70;font-weight:700'>Ask about this first</span><div class='sub'>A filing cannot explain it</div></td></tr>
    <tr><td><div class='cat'>Small Parcels</div><div class='sub'>33 filers report this line</div></td>
      <td class='n'>$2.63M</td><td class='n'>1.36%</td>
      <td class='n'><span style='color:#003A70;font-weight:700;font-size:10.5pt'>1.42%</span></td>
      <td class='n'>+6</td>
      <td><span style='color:#003A70;font-weight:700'>At the midpoint</span><div class='sub'>Typical, not tested</div></td></tr>
    <tr><td><div class='cat'>Fleet Management</div><div class='sub'>68 filers report this line</div></td>
      <td class='n'>$2.12M</td><td class='n'>1.07%</td>
      <td class='n'><span style='color:#003A70;font-weight:700;font-size:10.5pt'>1.15%</span></td>
      <td class='n'>+8</td>
      <td><span style='color:#003A70;font-weight:700'>At the midpoint</span><div class='sub'>Typical, not tested</div></td></tr>
    <tr><td><div class='cat'>Marketing Services</div><div class='sub'>1,617 filers report this line</div></td>
      <td class='n'>$482K</td><td class='n'>0.20%</td>
      <td class='n'><span style='color:#003A70;font-weight:700;font-size:10.5pt'>0.26%</span></td>
      <td class='n'>+6</td>
      <td><span style='color:#003A70;font-weight:700'>At the midpoint</span><div class='sub'>Typical, not tested</div></td></tr>
    <tr><td><div class='cat'>Professional Services</div><div class='sub'>1,878 filers report this line</div></td>
      <td class='n'>$638K</td><td class='n'>0.30%</td>
      <td class='n'><span style='color:#003A70;font-weight:700;font-size:10.5pt'>0.34%</span></td>
      <td class='n'>+4</td>
      <td><span style='color:#003A70;font-weight:700'>At the midpoint</span><div class='sub'>Typical, not tested</div></td></tr>
    <tr><td><div class='cat'>Travel</div><div class='sub'>1,917 filers report this line</div></td>
      <td class='n'>$450K</td><td class='n'>0.25%</td>
      <td class='n'><span style='color:#5A6577;font-weight:700;font-size:10.5pt'>0.24%</span></td>
      <td class='n'>-1</td>
      <td><span style='color:#003A70;font-weight:700'>Below the midpoint</span><div class='sub'>No question here</div></td></tr>
    <tr><td><div class='cat'>Office Supplies</div><div class='sub'>1,984 filers report this line</div></td>
      <td class='n'>$1.37M</td><td class='n'>1.07%</td>
      <td class='n'><span style='color:#5A6577;font-weight:700;font-size:10.5pt'>0.74%</span></td>
      <td class='n'>-33</td>
      <td><span style='color:#003A70;font-weight:700'>Below the midpoint</span><div class='sub'>No question here</div></td></tr>
  </tbody></table>
<p class='capt'>Share of total operating expense. Uniforms and payroll administration are named in
  Part VII Section B and have no comparable filed cohort.</p>

<div class='panel cream'>
  <p style='margin:0'><b>Five of these seven sit within a few basis points of the midpoint, and that
    is the point worth making.</b> The midpoint describes what is normal, not what is available.
    Organizations that test these categories usually find room whether they started above the
    midpoint or below it — which is why we do not lead with the line that shows the largest
    difference.</p></div>

<div class='prov'><b>FILED</b> Form 990 Part IX, FY2024, as a share of total operating expense
  &middot; <b>COMPARISON</b> filers of comparable size and type that report the same line separately,
  count shown per category &middot; uniforms and payroll administration are named in Part VII B and
  have no comparable filed cohort &middot; method in Appendix C</div>
""")

page(8, "Every category we identified", """
<h1>Fourteen categories identified.<br>Five of them carry $2.51 million a year.</h1>
<p class='lede'>Fourteen of the fifty-five categories ERA works are visible in your situation.
  <b>The right-hand column is what we would expect to recover for you</b>, at the median of
  engagements we have completed in that same category.</p>

<table class='tight' style='margin-top:10px'>
  <thead><tr><th style='width:29%'>Category</th><th class='n' style='width:15%'>Spend basis</th>
    <th class='n' style='width:11%'>Median</th><th class='n' style='width:16%'>What we could recover</th>
    <th style='width:29%'>Status</th></tr></thead>
  <tbody>
    <tr><td colspan='5' style='background:#003A70;color:#fff;padding:6px 7px;font-size:9.5pt;
        letter-spacing:.12em;font-weight:700'>PRICED FROM YOUR RETURN &middot; five categories</td></tr>
    <tr><td class='cat'>Operating Supply</td><td class='n'>$4,775,636<div class='sub'>floored</div></td>
      <td class='n'>21.3%</td><td class='n'><span class='dol'>$1,017,210</span></td>
      <td>Held to what comparable filers report; page 10.</td></tr>
    <tr><td class='cat'>Small Parcels</td><td class='n'>$2,631,840</td><td class='n'>23.0%</td>
      <td class='n'><span class='dol'>$605,323</span></td><td>Filed cleanly. Ready to open.</td></tr>
    <tr><td class='cat'>Uniforms &amp; Linens</td><td class='n'>$1,518,596</td><td class='n'>28.1%</td>
      <td class='n'><span class='dol'>$426,725</span></td><td>Named on your return with the service stated.</td></tr>
    <tr><td class='cat'>Fleet Management</td><td class='n'>$2,122,533</td><td class='n'>14.8%</td>
      <td class='n'><span class='dol'>$314,135</span></td><td>Thirteen completed engagements behind it.</td></tr>
    <tr><td class='cat'>Payroll &amp; HR administration</td><td class='n'>$476,232</td><td class='n'>31.0%</td>
      <td class='n'><span class='dol'>$147,632</span></td><td>Named on your return with the service stated.</td></tr>
    <tr class='totrow'><td class='cat'>Five categories</td><td class='n'>$11,524,837</td><td class='n'>21.8%</td>
      <td class='n'><span class='dol'>$2,511,025</span></td>
      <td><b>What we believe we can recover, a year.</b></td></tr>

    <tr><td colspan='5' style='background:#E4EBF3;color:#003A70;padding:6px 7px;font-size:9.5pt;
        letter-spacing:.12em;font-weight:700'>ON YOUR RETURN, NOT YET PRICED &middot; five categories</td></tr>
    <tr class='q'><td class='cat'>Office Supplies</td><td class='n'>$1,372,501</td>
      <td class='n' colspan='2'>204 completed engagements</td>
      <td>Blends consumables with equipment.</td></tr>
    <tr class='q'><td class='cat'>Professional Services</td><td class='n'>$637,913</td>
      <td class='n' colspan='2'>10 completed engagements</td>
      <td>Filed legal fees are a fiduciary appointment.</td></tr>
    <tr class='q'><td class='cat'>Benefits Administration</td><td class='n'>$558,228</td>
      <td class='n' colspan='2'>10 completed engagements</td>
      <td>At our evidence threshold. Workable, not quotable.</td></tr>
    <tr class='q'><td class='cat'>Marketing Services</td><td class='n'>$482,421</td>
      <td class='n' colspan='2'>below threshold</td>
      <td>Too few finished engagements to place a median.</td></tr>
    <tr class='q'><td class='cat'>Travel</td><td class='n'>$449,863</td>
      <td class='n' colspan='2'>below threshold</td>
      <td>As above.</td></tr>
    <tr class='totrow'><td class='cat'>Five more categories</td><td class='n'>$3,500,926</td>
      <td class='n' colspan='2'>not yet quotable</td>
      <td>Spend we work. A filing will not price it; your contracts will.</td></tr>
  </tbody></table>
<div class='prov'><b>FILED</b> Form 990, FY2024 &middot; <b>MEDIAN</b> completed ERA engagements
  &middot; quartiles in Appendix B</div>
""")

page(9, "The categories your return does not show", """
<h1>Four more categories we work,<br>and $69.6M your return will not separate.</h1>
<p class='lede'>The ten on the previous page are the ones a Form 990 happens to break out. They are
  not the whole of what you buy, and they are not the whole of where we work.</p>

<table>
  <thead><tr><th style='width:29%'>Category</th><th class='n' style='width:18%'>Implied spend</th>
    <th class='n' style='width:11%'>Median</th><th class='n' style='width:16%'>What we could recover</th>
    <th style='width:26%'>Basis</th></tr></thead>
  <tbody>
    <tr><td colspan='5' style='background:#E4EBF3;color:#003A70;padding:6px 7px;font-size:9.5pt;
        letter-spacing:.12em;font-weight:700'>NOT ON YOUR RETURN &middot; sized from comparable filers</td></tr>
    <tr><td class='cat'>Maintenance</td><td class='n'>$2,274,717</td><td class='n'>21.5%</td>
      <td class='n'>$489,064</td><td>What filers of your size and type report</td></tr>
    <tr><td class='cat'>IT Hardware &amp; Services</td><td class='n'>$2,000,182</td><td class='n'>11.9%</td>
      <td class='n'>$238,022</td><td>As above</td></tr>
    <tr><td class='cat'>Insurance</td><td class='n'>$1,000,091</td><td class='n'>15.1%</td>
      <td class='n'>$151,014</td><td>As above</td></tr>
    <tr><td class='cat'>Telecommunications</td><td class='n'>$803,995</td><td class='n'>36.2%</td>
      <td class='n'>$291,046</td><td>As above</td></tr>
    <tr class='totrow'><td class='cat'>Four categories</td><td class='n'>$6,078,985</td>
      <td class='n'>19.2%</td><td class='n'><span class='dol'>$1,169,146</span></td>
      <td>Implication, not finding</td></tr>
  </tbody></table>
<p class='capt'><b>Implications, not findings.</b> Your return contains no figure for any of them,
  which is why none of it is in the $2.51M.</p>

<h2 style='margin-top:14px'>And $69.6M your return reports as single figures</h2>
<table>
  <thead><tr><th style='width:34%'>Filed line</th><th class='n' style='width:16%'>FY2024</th>
    <th style='width:50%'>What sits inside it</th></tr></thead>
  <tbody>
    <tr><td class='cat'>Materials above the floor</td><td class='n'>$33,196,074</td>
      <td>Production input, resale or consumed supply.</td></tr>
    <tr><td class='cat'>Occupancy · 16</td><td class='n'>$24,376,137</td>
      <td>Rent with utilities, maintenance and janitorial as one figure.</td></tr>
    <tr><td class='cat'>Fees for services — Other · 11g</td><td class='n'>$8,082,654</td>
      <td>Itemized only in part. We will not guess at the remainder.</td></tr>
    <tr><td class='cat'>Service charges · 24</td><td class='n'>$2,423,261</td>
      <td>A description we cannot read from outside.</td></tr>
    <tr><td class='cat'>All other expenses · 24e</td><td class='n'>$1,502,571</td>
      <td>The catch-all. By definition it holds what did not fit anywhere else.</td></tr>
  </tbody></table>
<div class='panel deep'>
  <p style='margin:0'><b>This is the larger half of your indirect spend, and none of it is priced
    here.</b> Not because it is out of scope — occupancy alone holds three categories we work — but
    because a Form 990 reports it in a way we cannot separate. Most of it resolves in one
    conversation with your controller.</p></div>
<div class='prov'><b>IMPLIED</b> median share reported by comparable filers &middot; Appendix C</div>

""")

page(10, "The largest line", """
<h1>The largest line on your return is also<br>the one we will not price at face value.</h1>
<p class='lede'>Materials and supplies is $37,971,710 — bigger than every other indirect line
  combined. It is also the line a return cannot resolve, so we have held it to a floor.</p>

<svg viewBox="0 0 620 132" width="100%" height="132">
 <g font-family="Arial" font-size="9.5">
  <text x="0" y="10" fill="#003A70" font-weight="bold" font-size="10.5">$37,971,710 reported as materials and supplies</text>
  <rect x="0" y="20" width="75" height="34" fill="#FF9C00"/>
  <rect x="75" y="20" width="525" height="34" fill="#F2F5F8" stroke="#D7DFE9"/>
  <text x="8" y="41" fill="#412402" font-weight="bold" font-size="9">$4.78M</text>
  <text x="86" y="35" fill="#5A6577">$33,196,074 — not priced anywhere in this Brief</text>
  <text x="86" y="48" fill="#5A6577" font-size="9">production input, resale, or consumed supply. A return does not separate them.</text>
  <text x="0" y="70" fill="#C07400" font-weight="bold" font-size="9">PRICED — held to what organizations of your size and type report as operating supply</text>

  <rect x="0" y="88" width="600" height="1" fill="#D7DFE9"/>
  <text x="0" y="106" fill="#003A70" font-weight="bold">Why a floor rather than an estimate</text>
  <text x="0" y="122" fill="#5A6577">We price only the part comparable organizations would recognize as operating supply, and leave the rest for you to explain.</text>
 </g>
</svg>

<div class='two'>
  <div><h2>What we can see</h2>
    <p>An operation running apparel manufacturing, a commercial laundry and donated goods retail
      will carry production and resale material in this line as well as consumed supply. Your
      officers are named for each of those operations.</p>
    <p>Organizations of your size and type report operating supply at a level that would put roughly
      <b>$4.78M</b> of this line in our scope. That is the figure on page 5.</p></div>
  <div><h2>What we cannot see</h2>
    <p>How the $37.97M divides between what you convert, what you resell, and what you consume
      running the operation. Your return does not separate them and no filing would.</p>
    <p>The difference changes the answer materially, which is why we have priced the conservative
      part and named the rest rather than modelling it.</p></div>
</div>
<div class='panel cream'>
  <p style='margin:0'><b>So the first question we would ask is not about price.</b> It is how that
    line divides. If most of it is material you convert or resell, the floor is the right number and
    we would say so. If more of it is consumed supply than a comparable operation would carry, the
    figure on page 5 is low — and that is the more interesting answer.</p></div>
<div class='prov'><b>FILED</b> Form 990 Part IX &middot; <b>FLOOR</b> derived from what comparable
  organizations report for this category, method in Appendix A &middot; nothing above the floor is
  included in any figure in this Brief</div>""")

# ══════════ 9 · WHAT IT WOULD INVOLVE ══════════
page(11, "What it would involve", """
<h1>Your spend goes in. Options come back,<br>category by category. You decide.</h1>
<svg viewBox="0 0 620 92" width="100%" height="92">
 <g font-family="Arial" font-size="9">
  <line x1="46" y1="30" x2="566" y2="30" stroke="#D7DFE9" stroke-width="2"/>
  <circle cx="46" cy="30" r="13" fill="#FF9C00"/><text x="46" y="34" text-anchor="middle" font-weight="bold" fill="#412402">1</text>
  <circle cx="150" cy="30" r="13" fill="#FF9C00"/><text x="150" y="34" text-anchor="middle" font-weight="bold" fill="#412402">2</text>
  <circle cx="254" cy="30" r="13" fill="#003A70"/><text x="254" y="34" text-anchor="middle" font-weight="bold" fill="#fff">3</text>
  <circle cx="358" cy="30" r="13" fill="#003A70"/><text x="358" y="34" text-anchor="middle" font-weight="bold" fill="#fff">4</text>
  <circle cx="462" cy="30" r="13" fill="#003A70"/><text x="462" y="34" text-anchor="middle" font-weight="bold" fill="#fff">5</text>
  <circle cx="566" cy="30" r="13" fill="#003A70"/><text x="566" y="34" text-anchor="middle" font-weight="bold" fill="#fff">6</text>
  <text x="46" y="58" text-anchor="middle" fill="#003A70" font-weight="bold">A conversation</text>
  <text x="150" y="58" text-anchor="middle" fill="#003A70" font-weight="bold">You send it</text>
  <text x="254" y="58" text-anchor="middle" fill="#003A70" font-weight="bold">Specialists</text>
  <text x="358" y="58" text-anchor="middle" fill="#003A70" font-weight="bold">You choose</text>
  <text x="462" y="58" text-anchor="middle" fill="#003A70" font-weight="bold">Options</text>
  <text x="566" y="58" text-anchor="middle" fill="#003A70" font-weight="bold">We deliver</text>
  <text x="46" y="74" text-anchor="middle" fill="#C07400">20 minutes</text>
  <text x="150" y="74" text-anchor="middle" fill="#C07400">a data pull</text>
  <text x="254" y="74" text-anchor="middle" fill="#C07400">nothing</text>
  <text x="358" y="74" text-anchor="middle" fill="#5A6577">nothing</text>
  <text x="462" y="74" text-anchor="middle" fill="#5A6577">nothing</text>
  <text x="566" y="74" text-anchor="middle" fill="#5A6577">nothing</text>
 </g>
</svg>
<table>
  <thead><tr><th style='width:24%'>Step</th><th style='width:54%'>What happens</th>
    <th style='width:22%'>What it costs you</th></tr></thead>
  <tbody>
    <tr><td class='cat'>1 · A conversation</td><td>What you already know about these arrangements —
      what was tested recently, what is under contract, what is not worth touching.</td>
      <td>Twenty minutes</td></tr>
    <tr><td class='cat'>2 · You send the spend</td><td>Agreements and invoices across the
      categories you want examined. Redacted is fine, and the list is yours to set.</td><td>A data pull</td></tr>
    <tr><td class='cat'>3 · Specialists read it</td><td>One per category, working the terms, the
      billing and the market — not a generalist reading all of it.</td><td>Nothing</td></tr>
    <tr><td class='cat'>4 · An options report per category</td><td>What it costs today, what it could
      cost, what changing it involves, and where the answer is leave it alone.</td><td>Nothing</td></tr>
    <tr><td class='cat'>5 · You choose, line by line</td><td>Take one, take all of them, take none.
      Keeping the incumbent on better terms is a common outcome.</td><td>Nothing</td></tr>
    <tr><td class='cat'>6 · We implement and verify</td><td>Only what you approved, and the result
      is checked against your own invoices before anything is invoiced to you.</td><td>Nothing</td></tr>
  </tbody></table>
<div class='panel deep'>
  <p style='margin:0'><b>We do not ask you to choose categories up front.</b> You give us the spend
    and we come back with an options report on each one — including the ones where the answer is
    that the arrangement is already competitive. Our fee comes only out of value actually recovered,
    after you have it and after it is verified.</p></div>""")

# ══════════ 10 · NOTHING / SOMETHING ══════════
page(12, "Both answers are useful", """
<h1>If we find nothing, you still hold<br>something you did not have before.</h1>
<div class='two'>
  <div class='panel' style='margin-top:12px'>
    <h3>If we find nothing</h3>
    <ul>
      <li>Confirmation that the incumbent and your process are delivering competitive economics.</li>
      <li>Evidence that the category was independently reviewed.</li>
      <li>A record of why no change was recommended.</li>
      <li>A baseline to revisit at renewal, or when volume moves.</li>
      <li>No disruption to a supplier who is doing the job.</li>
      <li>A defensible answer if the category is questioned later.</li>
    </ul></div>
  <div class='panel cream' style='margin-top:12px'>
    <h3>If we find something</h3>
    <p>It is recurring rather than one-off. It is unrestricted. It did not come out of a program, a
      headcount or a fundraising target — and it does not depend on new contributed revenue next
      year to repeat.</p>
    <p><b>It is also a different item to bring to a board than a cut list.</b> You will have the
      working, the sources and the file, whether or not you continue with us afterwards.</p></div>
</div>
<div class='panel deep'>
  <p style='margin:0'><b>Roughly a fifth of what we open comes back with nothing worth changing.</b>
    We would rather tell you that than manufacture a finding, and it is the reason the fee sits
    where it does — we are paid out of what is recovered, so a category that is already competitive
    costs you nothing to have confirmed.</p></div>
<h2 style='margin-top:14px'>What you can expect either way</h2>
<div class='three'>
  <div class='card'><div class='h'>We will say when you are already competitive</div>
    <p>By category, in writing, with the basis stated.</p></div>
  <div class='card'><div class='h'>Incumbents stay wherever they should</div>
    <p>The objective is better terms, not new suppliers.</p></div>
  <div class='card'><div class='h'>You remain in control throughout</div>
    <p>Nothing changes without your approval, at any stage.</p></div>
</div>""")

# ══════════ 11 · WHO ELSE ══════════
page(13, "Who else should see this", """
<h1>One page of this belongs to someone<br>other than finance.</h1>
<p class='lede'>This Brief is built from a filing, which means it is written in finance's language.
  Two of the questions in it can only be answered by the people who run the operations.</p>
<div class='two'>
  <div class='card'><div class='k'>Page 8 — the materials line</div>
    <div class='h'>Whoever runs the stores and the production floor</div>
    <p>They can tell you in one sentence how that $37.97M divides between what you convert, what you
      resell and what you consume. That answer decides whether the largest number in this document
      is worth anything at all.</p>
    <p style='margin-top:6px'>We would rather they corrected us early than agreed with us politely.</p></div>
  <div class='card'><div class='k'>Page 7 — the linen arrangement</div>
    <div class='h'>Whoever owns the laundry operation</div>
    <p>They will know when it was last tested and what the agreement actually covers — the two
      things a return cannot show and the two things that decide whether the number on page 7 is
      real.</p>
    <p style='margin-top:6px'>Twenty minutes with them is worth more than an hour with the filing.</p></div>
</div>
<div class='panel'>
  <p style='margin:0'><b>The appendices are built to be handed on.</b> They hold how each figure was
    worked out, how many completed engagements sit behind it, and every source with a date — so
    whoever you pass this to can check it without us in the room.</p></div>""")

# ══════════ 12 · THE QUESTION ══════════
page(14, "Before we meet", f"""
<h1>Everything here was prepared before we spoke.<br>Some of it will be wrong.</h1>
<p class='lede'>That is not a disclaimer. It is the reason for the conversation.</p>

<div style='display:flex;gap:20px;margin-top:14px'>
  <div style='flex:0 0 1.5in;text-align:center'>
    <img src='{HEADSHOT}' style='width:1.5in;height:1.5in;border-radius:50%'>
    <div style='font-family:Trebuchet MS,Arial,sans-serif;font-size:12pt;color:#003A70;font-weight:700;margin-top:9px'>John Wylie</div>
    <div style='font-size:9.5pt;color:#5A6577;line-height:1.5'>Consulting Partner<br>ERA Group</div>
    <div style='font-size:9.5pt;color:#003A70;margin-top:6px;line-height:1.5'>jwylie@eragroup.com<br>703.244.9868</div>
  </div>
  <div style='flex:1'>
    <div style='background:#FEF4E2;border-left:4px solid #FF9C00;padding:16px 18px'>
      <div class='eyebrow' style='margin-bottom:8px'>What we would like to ask you</div>
      <div style='font-family:Trebuchet MS,Arial,sans-serif;font-size:17pt;color:#003A70;line-height:1.32;font-weight:700'>
        What have we got wrong?</div>
      <p style='margin-top:10px'>Twenty minutes, and you tell us which part of this does not match the
        organization you actually run. We will have learned something either way, and you will have
        an independent read on categories you were going to renew anyway.</p>
      <p>If these arrangements were tested recently and held, that is a useful result and it costs
        nothing to establish.</p>
    </div>
    <div class='two' style='margin-top:12px'>
      <div style='display:flex;gap:11px;align-items:flex-start'>
        <img src='{QR_BOOK}' style='width:0.82in;height:0.82in;flex:0 0 auto'>
        <div><h3 style='margin-bottom:3px'>Put twenty minutes in the diary</h3>
          <p style='font-size:9.5pt;color:#5A6577;margin:0'>calendly.com/john_wylie/30min</p>
          <p style='font-size:9.5pt;margin-top:4px'>Pick any slot. No preparation needed.</p></div>
      </div>
      <div style='display:flex;gap:11px;align-items:flex-start'>
        <img src='{QR}' style='width:0.82in;height:0.82in;flex:0 0 auto'>
        <div><h3 style='margin-bottom:3px'>Every figure, live online</h3>
          <p style='font-size:9.5pt;color:#5A6577;margin:0'>portal.wpp-us.com/goodwillsouthflorida-benchmark</p>
          <p style='font-size:9.5pt;margin-top:4px'>No code. No form. No login.</p></div>
      </div>
    </div>
  </div>
</div>

<div class='two' style='margin-top:14px'>
  <div><h2>What we did not do</h2>
    <ul>
      <li>We did not contact anyone inside your organization.</li>
      <li>We did not use non-public information.</li>
      <li>We did not assume contract terms we cannot see.</li>
      <li>We did not model a recovery we cannot show the basis for.</li>
    </ul></div>
  <div><h2>What you can expect from us</h2>
    <ul>
      <li>We will tell you where you are already competitive, by category and in writing.</li>
      <li>Incumbent suppliers stay wherever they should. The objective is better terms.</li>
      <li>Nothing changes without your approval, at any stage.</li>
      <li>If we recover nothing, there is no fee.</li>
    </ul></div>
</div>
""")

page(15, "Appendix A · Sector cost structure", """
<h1>How the floor on the materials line was set.</h1>
<p class='lede'>Page 8 prices $4.78M of a $37.97M line. This is the whole of the derivation, so it
  can be checked or disputed.</p>
<h2 style='margin-top:14px'>The comparison group</h2>
<p>Forty organizations of the same type and operating model file a return that breaks out the same
  operating supply line. Their reported spend, as a share of total revenue:</p>
<table>
  <thead><tr><th>Statistic</th><th class='n'>Share of revenue</th><th class='n'>Applied to $196,096,296</th></tr></thead>
  <tbody>
    <tr><td>Lower quartile</td><td class='n'>1.71%</td><td class='n'>$3,353,247</td></tr>
    <tr class='totrow'><td class='cat'>Median — used as the floor</td><td class='n'>2.4354%</td><td class='n'><span class='dol'>$4,775,636</span></td></tr>
    <tr><td>Upper quartile</td><td class='n'>3.86%</td><td class='n'>$7,569,318</td></tr>
    <tr><td>90th percentile</td><td class='n'>4.90%</td><td class='n'>$9,608,718</td></tr>
  </tbody></table>
<div class='panel'>
  <p style='margin:0'><b>We used the median, not the upper quartile.</b> Had we used the upper
    quartile the figure on page 5 would be $1,612,265 rather than $1,017,210, and the headline
    $3.63M rather than $2.51M. The conservative choice is deliberate: the number should be one you
    can raise, not one you have to defend against.</p></div>
<h2 style='margin-top:13px'>What the floor assumes</h2>
<p>That an organization running manufacturing, laundry and retail operations carries production and
  resale material inside the same filed line as consumed operating supply, and that the consumed
  portion resembles what comparable organizations report. <b>Neither assumption can be tested from
  outside.</b> Both are resolved by a single answer from whoever runs the operation.</p>
<div class='prov'><b>COHORT</b> forty comparable filers, most recent return each, operating supply as
  a share of total revenue &middot; <b>SUBJECT</b> Form 990 Part IX, FY2024 &middot; arithmetic on
  filed figures only</div>""")

# ══════════ APPENDIX B ══════════
page(16, "Appendix B · Category evidence", """
<h1>Sample, median and middle half<br>for every category priced.</h1>
<p class='lede'>Every percentage in this Brief comes from engagements ERA has completed in that
  category. None is a published market range. Where fewer than ten engagements exist, no percentage
  is quoted at all.</p>
<table>
  <thead><tr><th style='width:30%'>Category</th><th class='n'>Completed</th><th class='n'>Lower quartile</th>
    <th class='n'>Median</th><th class='n'>Upper quartile</th><th class='n'>Applied to</th></tr></thead>
  <tbody>
    <tr class='q'><td class='cat'>Office Supplies</td><td class='n'>204</td><td class='n' colspan='4'>Evidence is strong; your filed line is not separable. Named, not priced.</td></tr>
    <tr><td class='cat'>Uniforms, Workwear &amp; Linens</td><td class='n'>109</td><td class='n'>16.2%</td><td class='n'><b>28.1%</b></td><td class='n'>42.2%</td><td class='n'>$1,518,596</td></tr>
    <tr><td class='cat'>Payroll &amp; HR administration</td><td class='n'>101</td><td class='n'>17.4%</td><td class='n'><b>31.0%</b></td><td class='n'>46.6%</td><td class='n'>$476,232</td></tr>
    <tr><td class='cat'>Small Parcels</td><td class='n'>89</td><td class='n'>13.7%</td><td class='n'><b>23.0%</b></td><td class='n'>36.5%</td><td class='n'>$2,631,840</td></tr>
    <tr><td class='cat'>Operating Supply</td><td class='n'>69</td><td class='n'>13.5%</td><td class='n'><b>21.3%</b></td><td class='n'>34.4%</td><td class='n'>$4,775,636 <span class='sub'>floored</span></td></tr>
    <tr><td class='cat'>Fleet Management</td><td class='n'>13</td><td class='n'>7.8%</td><td class='n'><b>14.8%</b></td><td class='n'>32.9%</td><td class='n'>$2,122,533</td></tr>
    <tr class='q'><td class='cat'>Professional Services</td><td class='n'>10</td><td class='n' colspan='4'>Your filed legal fees are a fiduciary appointment. Named, not priced.</td></tr>
    <tr class='q'><td class='cat'>Marketing Services</td><td class='n'>under 10</td><td class='n' colspan='4'>Below our evidence threshold. Named, not priced.</td></tr>
    <tr class='q'><td class='cat'>Travel</td><td class='n'>under 10</td><td class='n' colspan='4'>Below our evidence threshold. Named, not priced.</td></tr>
    <tr class='q'><td class='cat'>Benefits Administration</td><td class='n'>10</td><td class='n' colspan='4'>At the threshold. Named on page 4, not included in the $2.51M.</td></tr>
  </tbody></table>
<div class='two'>
  <div class='panel' style='margin-top:10px'><h3>Why the median and not the mean</h3>
    <p style='margin:0'>A small number of very large outcomes would pull a mean upward and describe
      none of the work. The median is the outcome most likely to describe the set.</p></div>
  <div class='panel' style='margin-top:10px'><h3>Zero results are included</h3>
    <p style='margin:0'>Engagements that recovered nothing remain in the population. Excluding them
      would raise every figure in this Brief and describe a different business.</p></div>
</div>
<div class='prov'><b>ERA RECOVERY</b> completed engagements, quartiles of category spend recovered
  &middot; ten completed engagements is the minimum before any percentage is quoted</div>""")

# ══════════ APPENDIX C ══════════
page(17, "Appendix C · The comparison group", """
<h1>How the comparison group was built,<br>and what it can and cannot show.</h1>
<p class='lede'>Appendix A applies a floor drawn from forty comparable filers. This is how that group
  was assembled.</p>
<div class='two'>
  <div><h2>How it was selected</h2>
    <ul>
      <li>Organizations of the same type and operating model, filing the same return.</li>
      <li>Only those that break out the same operating supply line separately. A filer that reports
        it inside another line is excluded rather than estimated.</li>
      <li>The most recent return available for each, which means filing years differ across the
        group.</li>
      <li>Compared as a share of total revenue, so size differences do not distort the comparison.</li>
    </ul></div>
  <div><h2>What it cannot show</h2>
    <ul>
      <li>Whether any organization in the group buys well. The group describes what is normal, not
        what is available.</li>
      <li>How each filer classifies material internally. Two organizations doing the same thing can
        report it in different lines.</li>
      <li>Anything about how your organization is run. A position in a distribution is a reason to
        ask a question, never a verdict.</li>
    </ul></div>
</div>
<div class='panel cream'>
  <p style='margin:0'><b>Being at the median is not the same as being competitive.</b> The group is
    drawn from organizations that have mostly never market-tested these categories either. It
    describes what is <i>normal</i>, not what is <i>available</i> — which is why the comparison sets
    a floor in this Brief and is not used to price anything.</p></div>
<div class='prov'><b>COHORT</b> forty comparable filers &middot; <b>BASIS</b> operating supply as a
  share of total revenue, most recent filing per organization &middot; a minimum of thirty filers is
  required before any position is stated</div>""")

# ══════════ APPENDIX D ══════════
page(18, "Appendix D · Every filed line", """
<h1>Every indirect line on your return,<br>and what we did with each one.</h1>
<p class='lede'>Eleven expense lines are indirect rather than people or non-cash, and your return
  separately names four service relationships. All fifteen are below — <b>a line we declined to
  price is better shown than left out.</b></p>
<table>
  <thead><tr><th style='width:31%'>Filed line</th><th class='n' style='width:14%'>Amount</th>
    <th style='width:55%'>Disposition</th></tr></thead>
  <tbody>
    <tr><td>MATERIALS AND SUPPLIES · 24</td><td class='n'>$37.97M</td><td><b>Priced to a floor</b> · $4.78M in scope</td></tr>
    <tr><td>Part VII B — service stated</td><td class='n'>$1.52M</td><td><b>Priced</b> · Uniforms, Workwear &amp; Linens</td></tr>
    <tr><td>FREIGHT AND POSTAGE · 24</td><td class='n'>$2.63M</td><td><b>Priced</b> · Small Parcels</td></tr>
    <tr class='q'><td>Office expenses · 13</td><td class='n'>$1.37M</td><td>Line 13 mixes consumables with equipment. We work the consumables, not the equipment, and the line does not separate them.</td></tr>
    <tr><td>FLEET AND TRANSPORTATION · 24</td><td class='n'>$2.12M</td><td><b>Priced</b> · Fleet Management</td></tr>
    <tr class='q'><td>Fees for services — Legal · 11b</td><td class='n'>$638K</td><td>Fiduciary appointment, as line 11d. Not vendor spend.</td></tr>
    <tr><td>Part VII B — service stated</td><td class='n'>$476K</td><td><b>Priced</b> · Payroll and HR administration</td></tr>
    <tr><td>Part VII B — service stated</td><td class='n'>$558K</td><td>Benefits Administration. At the threshold, not in the total.</td></tr>
    <tr class='q'><td>Occupancy · 16</td><td class='n'>$24.38M</td><td>Rent with utilities, maintenance and janitorial as one figure.</td></tr>
    <tr class='q'><td>Fees for services — Other · 11g</td><td class='n'>$8.08M</td><td>Itemized only in part. We will not guess at the remainder.</td></tr>
    <tr class='q'><td>SERVICE CHARGES · 24</td><td class='n'>$2.42M</td><td>A description we cannot read from outside.</td></tr>
    <tr class='q'><td>All other expenses · 24e</td><td class='n'>$1.50M</td><td>The catch-all, by definition.</td></tr>
    <tr class='q'><td>Advertising and promotion · 12</td><td class='n'>$482K</td><td>Below our evidence threshold. Named, not priced.</td></tr>
    <tr class='q'><td>Travel · 17</td><td class='n'>$450K</td><td>Below our evidence threshold. Named, not priced.</td></tr>
    <tr class='q'><td>Fees — Legal and Lobbying · 11d</td><td class='n'>$701K</td><td>Fiduciary appointments. Outside our scope.</td></tr>
  </tbody></table>
""")

# ══════════ APPENDIX E ══════════
page(19, "Appendix E · Sources", """
<h1>Every figure, where it came from,<br>and what we could not see.</h1>
<table>
  <thead><tr><th style='width:20%'>Layer</th><th style='width:14%'>State</th><th>What it contributed</th></tr></thead>
  <tbody>
    <tr><td class='cat'>Filed</td><td><b>Present</b></td><td>Form 990 Part IX, FY2024, filing object 202523219349308832. Nineteen expense lines, twelve indirect, all twelve in Appendix D.</td></tr>
    <tr><td class='cat'>Registry</td><td><b>Present</b></td><td>Form 990 Part VII Section B. Named service relationships with the service stated and the amount disclosed.</td></tr>
    <tr><td class='cat'>Operating</td><td><b>Present</b></td><td>Officer roles named on your own return, which identify the operations behind the spend.</td></tr>
    <tr><td class='cat'>Benchmark</td><td><b>Present</b></td><td>Completed ERA engagements by category, quoted as quartiles of what those engagements produced.</td></tr>
    <tr><td class='cat'>Derived</td><td><b>Present</b></td><td>The floor in Appendix A, and arithmetic on filed figures only.</td></tr>
    <tr class='q'><td class='cat'>Retrieved</td><td>Absent</td><td>No verified quotation from your own published material.</td></tr>
    <tr class='q'><td class='cat'>Ecosystem</td><td>Absent</td><td>No dated external event connected closely enough to your organization to print.</td></tr>
    <tr class='q'><td class='cat'>Engagement</td><td>Absent</td><td>You have not told us anything yet. This layer only exists after a conversation.</td></tr>
    <tr class='q'><td class='cat'>Verified</td><td>Absent</td><td>Nothing has been checked against a contract, an invoice or a schedule of rates.</td></tr>
  </tbody></table>
<h2 style='margin-top:14px'>Sources</h2>
<div style='font-size:9.5pt;line-height:1.6'>
  <p><b>1 · IRS Form 990, FY2024</b> — Goodwill Industries of South Florida, Part IX Statement of
    Functional Expenses and Part VII Section B. Filing object 202523219349308832. Retrieved
    2026-09-07.</p>
  <p><b>2 · ERA completed engagement record</b> — quartiles by category, refreshed 2026-09-05.
    Ten completed engagements minimum before any percentage is quoted; zero-result engagements
    included.</p>
  <p><b>3 · Comparable filer group</b> — forty organizations of the same type breaking out the same
    line, most recent return each. Method in Appendix C.</p>
  <p><b>4 · Bureau of Labor Statistics</b> — Producer Price Index, <i>PPI Guide for Price
    Adjustment</i>. Cited on page 4 for how long-term agreements are escalated. bls.gov.</p>
</div>
<div class='panel'>
  <p style='margin:0'><b>No inference appears in this Brief except where it is labelled as one.</b>
    No published market range is used anywhere: every percentage is the outcome of engagements ERA
    has finished.</p></div>""")

# ══════════ BACK COVER ══════════
P.append(f"""<div class='page' style='page:cover;height:11in;padding:0;background:#003A70'>
 <div style='padding:2.5in 0.95in 0'>
   <div style='width:1.4in;height:3px;background:#FF9C00;margin-bottom:0.42in'></div>
   <div style='font-family:Trebuchet MS,Arial,sans-serif;color:#fff;font-size:24pt;line-height:1.3;font-weight:700'>
     What we could price is<br>the smaller half.</div>
   <div style='color:#DCE7F5;font-size:12pt;line-height:1.6;margin-top:0.35in;max-width:5.5in'>
     A Form 990 breaks out only the lines the form asks for. Waste, telecom, packaging, payment
     processing, managed print, records and grounds never reach a return at all. We work all of
     them. We cannot size yours from outside — you can.</div>
   <div style='height:1px;background:rgba(255,255,255,.3);margin:1.35in 0 0.3in'></div>
   <div style='color:#fff;font-size:12pt;font-weight:700;font-family:Trebuchet MS,Arial,sans-serif'>John Wylie</div>
   <div style='color:#DCE7F5;font-size:11pt;line-height:1.55;margin-top:4px'>Consulting Partner, ERA Group<br>
     jwylie@eragroup.com · 703.244.9868</div>
   <div style='color:#FF9C00;font-size:12pt;font-weight:700;margin-top:0.28in'>No recovery, no fee.</div>
 </div>
 <div style='position:absolute;left:0;right:0;bottom:1.1in;text-align:center'>
   <img src='{VTI_WHITE}' style='height:17px'></div>
</div>""")

html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(P)}</body></html>"
HTML(string=html).write_pdf(OUT)
from pypdf import PdfReader
print("pages:", len(PdfReader(OUT).pages))
