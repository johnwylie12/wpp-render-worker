"""Executive Opportunity Brief v6 -- LOCKED RESEARCH PROOF, Goodwill Industries of South Florida.

Account 23895, FY2024 Form 990 (filing object 202523219349308832). Locked 2026-09-16
by John pending external feedback. Settled decision records the lock and the output
fingerprints. Do not edit in place: copy to a new version folder.

Run from anywhere:  python eor/eob_v6_goodwill/build.py
Outputs go to eor/eob_v6_goodwill/out/ :
  EOB_v6_Goodwill_Brief_8pp_print.pdf   8 pages: cover, cover letter, 6 interior
  EOB_v6_Goodwill_CoverLetter.pdf       the letter alone (bound as page 2)
  EOB_v6_Goodwill_NoteCard_5x7.pdf      loose card, separate file, not in the package

Every figure was queried from Supabase ouzrrkskrfcvtnmhlycd on 2026-09-16:
  account_financials (primary FY2024), account_contractors (Part VII-B services; names never read here),
  category_outcome_evidence (refreshed 2026-09-09), era_projects Complete/Monitoring (rates the evidence
  table no longer carries: fleet, marketing, travel), fn_portal_payload(23895) (peer shares), partner_signature.

Rules this build satisfies: full category book priced (every indirect line, basis stated); no starting
category or set (settled #257); cover letter in "we", month-only date; no counterparty names; no access
code; no per-category engagement counts; LAW 7 / LAW 8; release_gate.py passes clean.
"""
import os, io, sys, base64, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.abspath(os.path.join(HERE, "..", ".."))       # repo root
sys.path.insert(0, W)
sys.path.insert(0, os.path.join(W, "cover"))
import qrcode
from PIL import Image
from jinja2 import Template
from weasyprint import HTML
from pypdf import PdfReader, PdfWriter
import wpp_signatures
import cover_page_engine as cpe

OUT = os.path.join(HERE, "out")
FONTS = W + "/fonts"
BOOK_URL = "https://calendly.com/john_wylie/30min"   # partner_signature.booking_url, partner 3

# ------------------------------------------------------------------- data ----

ORG = dict(legal="Goodwill Industries of South Florida, Inc.",
           display="Goodwill Industries of South Florida",
           short="Goodwill South Florida",
           fy="FY2024", filing_object="202523219349308832", retrieved="2026-09-07",
           mission="helping people get and keep meaningful work",
           cover_noun="job-training program", industry_group="Employment services")
RECIP = dict(name="Raisa Ciobanu", title="Chief Financial Officer",
             addr=["2121 NW 21st Street", "Miami, FL 33142-7317"], salutation="Raisa")
DATE = "September 16, 2026"
LETTER_MONTH = "September 2026"   # letters print in advance: month only
PORTAL = "portal.wpp-us.com/goodwillsouthflorida-benchmark"

# Every indirect Part IX line (LAW 26). compensation/payroll tax/pension/benefits,
# interest and depreciation are excluded as non-vendor or non-cash.
FILED_LINES = [
    ("Materials and supplies", "24", 37971710),
    ("Occupancy", "16", 24376137),
    ("Fees for services, other", "11g", 8082654),
    ("Freight and postage", "24", 2631840),
    ("Service charges", "24", 2423261),
    ("Fleet and transportation", "24", 2122533),
    ("All other expenses", "24e", 1502571),
    ("Office expenses", "13", 1372501),
    ("Fees for services, legal", "11b", 637913),
    ("Advertising and promotion", "12", 482421),
    ("Travel", "17", 449863),
    ("Fees for services, lobbying", "11d", 63200),
]
FILED_TOTAL = sum(x[2] for x in FILED_LINES)          # 82,116,604

# Full-book pricing. Rates: category_outcome_evidence unless marked ep (era_projects).
R = {  # category: (p25, med, p75, source)
 "Small parcels and packages": (13.2, 22.8, 36.5, "coe"),
 "Uniforms, workwear and linens": (18.9, 28.2, 40.2, "coe"),
 "Payroll and HR administration": (17.9, 32.3, 47.5, "coe"),
 "Office supplies": (16.1, 22.1, 32.7, "coe"),
 "Fleet management": (8.7, 32.5, 84.1, "ep"),
 "Professional services": (19.8, 28.6, 42.5, "coe"),
 "Banking and financial services": (1.5, 13.1, 45.6, "coe"),
 "Marketing services": (13.8, 25.4, 42.6, "ep"),
 "Travel management": (2.5, 16.9, 16.9, "ep, top quarter held at median"),
 "Miscellaneous indirect": (7.3, 14.4, 22.0, "coe"),
 "Operating supply": (13.5, 19.6, 27.9, "coe"),
 "Facility and property management": (13.9, 20.9, 33.0, "coe"),
 "Information technology": (7.9, 12.8, 19.0, "coe"),
 "Insurance": (8.1, 13.9, 24.8, "coe"),
}
REV = 196096296
VIIB = 1518596 + 476232 + 558228 + 1645458
LINES = [  # (tier, what it is on the return, amount priced, category, basis note)
 ("filed", "Freight and postage · 24", 2631840, "Small parcels and packages", "filed amount"),
 ("filed", "Fleet and transport · 24", 2122533, "Fleet management", "filed amount"),
 ("filed", "Service charges · 24", 2423261, "Banking and financial services", "filed amount"),
 ("filed", "Consulting, 2 contracts · VII-B", 1645458, "Professional services", "named service"),
 ("filed", "Laundry distribution · VII-B", 1518596, "Uniforms, workwear and linens", "named service"),
 ("filed", "All other expenses · 24e", 1502571, "Miscellaneous indirect", "filed amount"),
 ("filed", "Office expenses · 13", 1372501, "Office supplies", "filed amount"),
 ("filed", "Third-party admin · VII-B", 558228, "Payroll and HR administration", "named service"),
 ("filed", "Advertising · 12", 482421, "Marketing services", "filed amount"),
 ("filed", "Payroll services · VII-B", 476232, "Payroll and HR administration", "named service"),
 ("filed", "Travel · 17", 449863, "Travel management", "filed amount"),
 ("filed", "Fees for services, other · 11g", 8082654 - VIIB, "Miscellaneous indirect", "filed less Part VII-B"),
 ("blended", "Materials and supplies · consumed share", round(REV * 0.0218), "Operating supply", "2.18% of revenue, the peer median"),
 ("blended", "Occupancy · maintenance share", 1960963, "Facility and property management", "what comparable filers report"),
 ("implied", "IT hardware and services", 2000182, "Information technology", "what comparable filers report"),
 ("implied", "Insurance", 960872, "Insurance", "what comparable filers report"),
]

def _tier(t):
    rows = []
    for tier, lab, amt, cat, basis in LINES:
        if tier == t:
            p25, med, p75, src = R[cat]
            rows.append(dict(lab=lab, amt=amt, cat=cat, basis=basis, med=med, src=src,
                             lo=round(amt*p25/100), md=round(amt*med/100), hi=round(amt*p75/100)))
    return rows

T_FILED, T_BLEND, T_IMPL = _tier("filed"), _tier("blended"), _tier("implied")
def _sum(rows, k): return sum(x[k] for x in rows)
FB = T_FILED + T_BLEND
B_SPEND, B_LOW, B_MED, B_HI = _sum(FB, "amt"), _sum(FB, "lo"), _sum(FB, "md"), _sum(FB, "hi")
I_SPEND, I_LOW, I_MED = _sum(T_IMPL, "amt"), _sum(T_IMPL, "lo"), _sum(T_IMPL, "md")
assert (B_SPEND, B_LOW, B_MED, B_HI) == (25303506, 2908106, 5365598, 9407081)
SURPLUS = 196096296 - 185120170
MAT_REST = 37971710 - T_BLEND[0]["amt"]
OCC_REST = 24376137 - T_BLEND[1]["amt"]

FIRM = dict(recovered="$425 million", orgs="825", nfp="$24.5 million", zero="About one in five")

def usd(n): return "${:,.0f}".format(n)

# --------------------------------------------------------------- assets ----
def b64(path, mime):
    return "data:%s;base64,%s" % (mime, base64.b64encode(open(path, "rb").read()).decode())

def qr_uri(tag):
    img = qrcode.make("https://%s?s=%s" % (PORTAL, tag), box_size=10, border=1)
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _photo_uri():
    im = Image.open(os.path.join(W, "JW_001RTv2.jpeg"))
    im.thumbnail((500, 500))
    buf = io.BytesIO(); im.convert("RGB").save(buf, format="JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

LOGO = b64(W + "/case_study/assets/era_logo.png", "image/png")
LOGO_W = b64(W + "/eor/goodwill_v3/assets/era_logo_white.png", "image/png")
VTI = b64(W + "/meeting_label/assets/vti_logo.png", "image/png")
VTI_W = b64(W + "/eor/goodwill_v3/assets/vti_white.png", "image/png")
PHOTO = _photo_uri()
SIG = wpp_signatures.signature_data_uri(wpp_signatures.signature_for_partner(3))



def qr_plain(url):
    img = qrcode.make(url, box_size=10, border=1)
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

FONT_CSS = """
@font-face{font-family:'PL';src:url('file://%(f)s/fonnts.com-Paralucent_Light.otf');font-weight:300;}
@font-face{font-family:'PL';src:url('file://%(f)s/fonnts.com-Paralucent_Light_Italic.otf');font-weight:300;font-style:italic;}
@font-face{font-family:'PL';src:url('file://%(f)s/fonnts.com-Paralucent_Medium.otf');font-weight:500;}
@font-face{font-family:'PL';src:url('file://%(f)s/fonnts.com-Paralucent_Demi_Bold.otf');font-weight:700;}
""" % {"f": FONTS}

BASE_CSS = FONT_CSS + """
:root{--navy:#003A70;--sun:#FF9C00;--grey:#97999B;--mid:#111127;--mist:#F2F5F8;--deep:#E4EBF3;
      --cream:#FEF4E2;--edge:#F0D8A6;--ink:#1B2A41;--slate:#5A6577;--hair:#D7DFE9;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'PL','DejaVu Sans',sans-serif;font-weight:300;font-size:10.5pt;line-height:1.38;color:var(--ink);}
b,strong{font-weight:700;}
h1{font-weight:500;color:var(--navy);font-size:22pt;line-height:1.12;margin:2pt 0 7pt;}
.eyebrow{font-weight:500;color:var(--slate);font-size:10pt;letter-spacing:.16em;text-transform:uppercase;}
.lede{font-size:11pt;color:var(--ink);margin-bottom:9pt;}
.panel{background:var(--mist);padding:9pt 11pt;}
.cream{background:var(--cream);border-left:3pt solid var(--sun);padding:9pt 11pt;}
.rail{border-left:3pt solid var(--sun);padding-left:10pt;}
.src{font-size:10pt;color:var(--slate);line-height:1.3;}
table{border-collapse:collapse;width:100%;}
th{font-weight:500;font-size:10pt;letter-spacing:.06em;text-transform:uppercase;color:#fff;background:var(--navy);
   text-align:left;padding:5pt 6pt;vertical-align:bottom;}
td{font-size:10pt;padding:4.5pt 6pt;border-bottom:.6pt solid var(--hair);vertical-align:top;line-height:1.28;}
td.n,th.n{text-align:right;white-space:nowrap;}
.muted{color:var(--slate);}
"""

# --------------------------------------------------------- 1. note card ----
def note_card():
    html = """<html><head><style>%s
@page{size:5in 7in;margin:0.45in 0.5in 0.4in;}
.logo{width:1.3in;display:block;margin:0 auto 16pt;}
p{font-size:12pt;line-height:1.42;margin-bottom:9pt;}
.qr{display:flex;align-items:center;gap:10pt;margin:6pt 0 12pt;}
.qr img{width:0.9in;height:0.9in;}
.qr div{font-size:10pt;color:var(--slate);line-height:1.35;}
.qr b{color:var(--navy);font-size:10.5pt;}
.url{font-size:10pt;color:var(--navy);white-space:nowrap;margin:-6pt 0 12pt;}
.sig img{width:1.1in;}
.who{font-size:10.5pt;line-height:1.35;}
.who b{color:var(--navy);font-size:12pt;}
</style></head><body>
<img class="logo" src="%s">
<p>Dear %s,</p>
<p>Enclosed is an Executive Opportunity Brief I prepared for %s before reaching out, built from your own public filing. It shows what may be worth testing, what already looks competitive, and what a filing cannot tell us.</p>
<p>The complete line-by-line analysis is online.</p>
<div class="qr"><img src="%s"><div>Scan with your phone camera.<br><b>No code. No form. No login.</b></div></div><div class="url">%s</div>
<p style="margin-bottom:2pt">Best regards,</p>
<div class="sig"><img src="%s"></div>
<div class="who"><b>John Wylie</b><br>Consulting Partner · ERA Group<br>jwylie@eragroup.com · 703.244.9868</div>
</body></html>""" % (BASE_CSS, LOGO, RECIP["salutation"], ORG["short"], qr_uri("card"), PORTAL, SIG)
    p = OUT + "/01_note_card.pdf"; HTML(string=html).write_pdf(p); return p

# -------------------------------------------------------- 2. cover letter --
def letter():
    html = """<html><head><style>%s
@page{size:8.5in 11in;margin:0.45in 0.85in 0.35in;}
.top{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2pt solid var(--navy);padding-bottom:8pt;margin-bottom:14pt;}
.top img{width:1.25in;}
.top .r{text-align:right;font-size:10pt;color:var(--slate);line-height:1.35;}
.top .r b{color:var(--navy);font-size:10.5pt;letter-spacing:.08em;}
.addr{font-size:10.5pt;line-height:1.35;margin-bottom:12pt;}
.addr b{color:var(--navy);font-weight:500;font-size:11.5pt;}
p{font-size:10.8pt;line-height:1.42;margin-bottom:8pt;}
.sum{margin:4pt 0 10pt;}
.sum .h{font-weight:500;font-size:10pt;letter-spacing:.14em;color:var(--slate);border-bottom:1.5pt solid var(--sun);padding-bottom:3pt;margin-bottom:2pt;}
.sum td{font-size:10.3pt;padding:5pt 4pt;}
.sum td.k{width:1.75in;font-weight:500;color:var(--navy);font-size:12.5pt;white-space:nowrap;}
.close{display:flex;justify-content:space-between;align-items:flex-start;margin-top:4pt;}
.sig img{width:1.2in;margin:2pt 0 0;}
.who{font-size:10.5pt;line-height:1.35;}
.who b{color:var(--navy);font-weight:500;font-size:11.5pt;}
.portal{width:3.35in;border-left:3pt solid var(--sun);padding-left:10pt;}
.portal .t{font-weight:500;color:var(--navy);font-size:11pt;}
.portal .d{font-size:10pt;color:var(--slate);margin:2pt 0 5pt;line-height:1.3;}
.portal .row{display:flex;gap:8pt;align-items:center;}
.portal img{width:0.85in;height:0.85in;}
.portal .u{font-size:10pt;color:var(--ink);line-height:1.3;}
.portal .u b{color:var(--navy);display:block;margin-top:3pt;}
.portal .url{font-size:10pt;color:var(--ink);margin-top:4pt;white-space:nowrap;}
.foot{text-align:center;margin-top:30pt;}
.foot img{width:1.9in;}
</style></head><body>
<div class="top"><img src="%s"><div class="r"><b>EXECUTIVE OPPORTUNITY BRIEF</b><br>%s</div></div>
<div class="addr"><b>%s</b><br>%s<br>%s<br>%s<br>%s</div>
<p>Dear %s,</p>
<p>We prepared the enclosed Executive Opportunity Brief for %s before contacting you. It is built entirely from your %s Form 990 and from what ERA Group's completed work has actually returned in the same categories. For an organization whose mission is %s, every dollar that does not have to stay in indirect operating expense is a dollar that can go back to that work.</p>
<div class="sum"><div class="h">IN SHORT</div><table>
<tr><td class="k">%s</td><td>of indirect operating expense on your return, across %d lines. Every one of them is accounted for inside.</td></tr>
<tr><td class="k">%s</td><td>of that we could size from outside, across twelve categories ERA works.</td></tr>
<tr><td class="k">%s&ndash;%s</td><td>a year recoverable on that sized spend, from the low end to the median of ERA's completed work. <b>An estimate, not a forecast.</b></td></tr>
<tr><td class="k">%s</td><td>not yet sized: mostly the rest of materials and supplies and of occupancy. Your ledger splits them; your return does not.</td></tr>
</table></div>
<p>Every figure in it is a question to validate, not a conclusion about how %s is run. Some of it will be wrong, and we would rather hear which part than have you agree politely. If your current arrangements are already competitive, that is a useful answer too.</p>
<p>If the analysis is directionally useful, we would welcome a short conversation. Nothing changes without your approval, incumbent suppliers often remain, and ERA is paid only out of value that is actually recovered. If we recover nothing, there is no fee.</p>
<div class="close">
 <div><p style="margin-bottom:0">Best regards,</p><div class="sig"><img src="%s"></div>
  <div class="who"><b>John Wylie</b><br>Consulting Partner · ERA Group<br>jwylie@eragroup.com · 703.244.9868</div></div>
 <div class="portal"><div class="t">Your complete analysis is online</div>
  <div class="d">Every line, where it sits on your return, and how it compares.</div>
  <div class="row"><img src="%s"><div class="u">Scan with your phone camera.<b>No code. No form. No login.</b></div></div><div class="url">%s</div></div>
</div>
<div class="foot"><img src="%s"></div>
</body></html>""" % (BASE_CSS, LOGO, LETTER_MONTH,
        RECIP["name"], RECIP["title"], ORG["legal"], RECIP["addr"][0], RECIP["addr"][1],
        RECIP["salutation"], ORG["short"], ORG["fy"], ORG["mission"],
        usd(FILED_TOTAL), len(FILED_LINES), usd(B_SPEND), "$2.9M", "$5.4M", usd(FILED_TOTAL - B_SPEND),
        ORG["short"], SIG, qr_uri("letter"), PORTAL, VTI)
    p = OUT + "/02_cover_letter.pdf"; HTML(string=html).write_pdf(p); return p

# ------------------------------------------------------------ 3. cover -----
def cover():
    content = {"org": {"name": ORG["display"], "vertical": "human_services"}}
    ctx = cpe.build(content, hero_lookup=lambda v: "heroes/human_services.png",
                    title="EXECUTIVE OPPORTUNITY BRIEF", subtitle=ORG["fy"] + " FORM 990",
                    date_str=DATE, doc_type="package")
    ctx["statement_html"] = ("Your next <span class='g'>%s</span> may already be sitting "
                             "in your operating budget.") % ORG["cover_noun"]
    from jinja2 import Template
    tpl = Template(open(W + "/cover/cover_page_template.html").read())
    p = OUT + "/_cover.pdf"
    HTML(string=tpl.render(**ctx)).write_pdf(p)
    return p

# ------------------------------------------------------- 4. interior -------
SHORT = {"Small parcels and packages": "Small parcels", "Fleet management": "Fleet",
 "Banking and financial services": "Banking fees", "Professional services": "Professional services",
 "Uniforms, workwear and linens": "Uniforms and linens", "Miscellaneous indirect": "Miscellaneous",
 "Office supplies": "Office supplies", "Payroll and HR administration": "Payroll and HR",
 "Marketing services": "Marketing", "Travel management": "Travel", "Operating supply": "Operating supply",
 "Facility and property management": "Facilities", "Information technology": "IT", "Insurance": "Insurance"}
def merge(parts, dest):
    w = PdfWriter()
    for f in parts:
        for pg in PdfReader(f).pages:
            w.add_page(pg)
    with open(dest, "wb") as fh:
        w.write(fh)
    return dest


# ------------------------------------------------------ v6 presentation ----


def m(n):
    """Compact money: $347K, $2.9M."""
    return "$%.1fM" % (n / 1e6) if n >= 1e6 else "$%dK" % round(n / 1e3)


# ------------------------------------------------------------------ CSS ----
def page_css():
    return """
@page{size:8.5in 11in;margin:0.75in 0.8in 0.7in;
  @bottom-right{content:'Page ' counter(page) ' of 8';font-family:'PL';font-size:10pt;color:#97999B;vertical-align:top;padding-top:6pt;}
  @bottom-left{content:'Executive Opportunity Brief  ·  Prepared exclusively for %s';font-family:'PL';font-size:10pt;color:#97999B;vertical-align:top;padding-top:6pt;}
}
@page :first{counter-reset:page 3;}
@page back{margin:0;@bottom-left{content:none}@bottom-right{content:none}}
.back{page:back;}
.pg{break-after:page;}
""" % (ORG["display"],)


CSS = """
body{font-size:11pt;line-height:1.45;}
h1{font-size:25pt;line-height:1.1;margin:4pt 0 14pt;}
.eyebrow{color:var(--slate);border-left:3pt solid #FF9C00;padding-left:7pt;line-height:1;margin-bottom:10pt;}
p{margin-bottom:7pt;}
.sub{font-weight:500;color:var(--navy);font-size:12pt;margin-bottom:5pt;}
.two{display:flex;gap:22pt;} .two>div{flex:1;}
.src{font-size:10pt;color:var(--slate);}

/* HERO page 2 */
.chain{display:flex;align-items:flex-start;gap:6pt;margin:24pt 0 26pt;width:100%;}
.chain .c{flex:1;}
.chain .c3{flex:1.45;min-width:0;background:var(--navy);color:#fff;padding:12pt 12pt 14pt;margin-top:-12pt;}
.chain .arr{font-size:22pt;color:var(--grey);padding-top:22pt;}
.chain .lab{font-weight:500;font-size:10pt;letter-spacing:.14em;text-transform:uppercase;color:var(--slate);}
.chain .c3 .lab{color:#FF9C00;}
.chain .big{font-weight:500;color:var(--navy);font-size:29pt;line-height:1.08;margin:3pt 0 6pt;white-space:nowrap;}
.chain .c3 .big{color:#fff;font-size:26pt;padding-top:3pt;}
.chain .d{font-size:11pt;color:var(--slate);line-height:1.35;}
.chain .c3 .d{color:#E4EBF3;}
.gap2{border-left:3pt solid var(--sun);padding:2pt 0 2pt 12pt;font-size:13pt;line-height:1.4;margin-bottom:26pt;color:var(--ink);}
.gap2 b{color:var(--navy);font-weight:500;}
.quiet{border-top:.6pt solid var(--hair);padding-top:14pt;}
.quiet p{font-size:11pt;}
.big-quote{font-weight:500;font-size:18pt;line-height:1.3;color:var(--navy);margin:60pt 0 10pt;}

/* EVIDENCE page 3 */
table.bkt{border-collapse:collapse;width:100%;margin-top:2pt;}
.bkt th{background:none;color:var(--slate);font-weight:500;font-size:10pt;letter-spacing:.1em;border-bottom:1.5pt solid var(--navy);padding:0 6pt 5pt;}
.bkt td{font-size:10.5pt;padding:3pt 6pt;border-bottom:none;vertical-align:middle;}
.bkt tr.r:nth-of-type(even) td{background:var(--mist);}
.bkt td.n,.bkt th.n{text-align:right;white-space:nowrap;}
.bkt td.cat{color:var(--slate);}
.bkt tr.g td{border-bottom:none;padding:9pt 6pt 3pt;font-weight:500;font-size:10pt;letter-spacing:.12em;text-transform:uppercase;color:#FF9C00;}
.bkt tr.sub td{border-bottom:1pt solid var(--navy);font-weight:500;color:var(--navy);}
.bkt .rec{font-weight:500;color:var(--navy);}
.totalbar{display:flex;justify-content:space-between;align-items:center;background:var(--navy);color:#fff;padding:8pt 14pt;margin-top:9pt;}
.totalbar .k{font-weight:500;font-size:10pt;letter-spacing:.12em;text-transform:uppercase;color:#FF9C00;}
.totalbar .v{font-weight:500;font-size:18pt;margin-top:2pt;} .totalbar .v.big{font-size:22pt;} .totalbar .rt{text-align:right;}

/* EVIDENCE page 4 (v5 structure, restyled) */
.dec th{background:none;color:var(--slate);font-weight:500;font-size:10pt;letter-spacing:.1em;border-bottom:1.5pt solid var(--navy);padding:0 6pt 5pt;}
.dec td{font-size:10.5pt;padding:5pt 6pt;border-bottom:none;vertical-align:top;line-height:1.3;}
.dec tbody tr:nth-child(odd):not(.grp):not(.tot) td{background:var(--mist);}
.dec td.n,.dec th.n{text-align:right;white-space:nowrap;}
.dec tr.grp td{font-weight:500;font-size:10pt;letter-spacing:.12em;text-transform:uppercase;color:#FF9C00;background:none;border-bottom:none;padding-top:10pt;}
.dec tr.tot td{border-top:1pt solid var(--navy);font-weight:500;}
.meth .cols{columns:2;column-gap:18pt;} .meth p{break-inside:avoid;margin-bottom:5pt;font-size:10.5pt;}
.hv{display:flex;gap:10pt;margin-top:9pt;} .hv>div{flex:1;font-size:10.5pt;}
.methx{margin-top:6pt;font-size:10.5pt;line-height:1.38;}
.havenot{background:var(--cream);} .navy{color:var(--navy);}

/* HUMAN page 5 */
.hq{background:var(--cream);border-left:4pt solid var(--sun);padding:16pt 18pt;margin:6pt 0 16pt;}
.hq .k{font-weight:700;font-size:10pt;letter-spacing:.14em;color:#FF9C00;text-transform:uppercase;}
.hq .q{font-weight:500;font-size:20pt;line-height:1.2;color:var(--navy);margin:6pt 0 8pt;}
.qs3{display:flex;gap:12pt;margin-bottom:16pt;}
.qs3 .q{flex:1;border-top:3pt solid var(--navy);padding-top:8pt;}
.qs3 .qq{font-weight:500;font-size:13pt;line-height:1.25;color:var(--navy);margin-bottom:6pt;}
.qs3 .w{font-size:10.5pt;color:var(--slate);line-height:1.35;}
.qs3 .who{font-size:10pt;color:var(--slate);font-weight:500;margin-top:6pt;}
.more{border-left:3pt solid var(--sun);padding-left:10pt;margin:0 0 14pt;}
.startp{background:var(--navy);color:#fff;padding:14pt 16pt;}
.startp .k{font-weight:500;font-size:10pt;letter-spacing:.14em;color:#FF9C00;text-transform:uppercase;}
.startp .t{font-weight:500;font-size:16pt;margin:3pt 0 5pt;}
.startp p{color:#E4EBF3;margin:0;}

/* HUMAN page 6 */
.journey{display:flex;gap:0;margin:10pt 0 14pt;position:relative;}
.journey .s{flex:1;text-align:center;padding:0 4pt;position:relative;}
.journey .dot{width:30pt;height:30pt;border-radius:50%;background:var(--navy);color:#fff;font-weight:500;font-size:13pt;line-height:30pt;margin:0 auto 7pt;position:relative;z-index:2;}
.journey .s.first .dot,.journey .s.second .dot,.journey .s.third .dot{background:#FF9C00;}
.journey .line{position:absolute;top:15pt;left:8%;right:8%;height:1.5pt;background:var(--hair);z-index:1;}
.journey .t{font-weight:500;font-size:11pt;color:var(--navy);line-height:1.2;min-height:28pt;}
.journey .c{font-size:10pt;color:var(--slate);margin-top:3pt;}
.journey .c b{color:var(--ink);}
.keyline{text-align:center;font-size:12pt;color:var(--ink);margin-bottom:14pt;}
.oc{display:flex;gap:14pt;margin-bottom:14pt;}
.oc>div{flex:1;padding:14pt 16pt;}
.oc .n1{background:var(--mist);} .oc .n2{background:var(--navy);color:#fff;}
.oc .h{font-weight:500;font-size:15pt;margin-bottom:6pt;color:var(--navy);}
.oc .n2 .h{color:#fff;} .oc .n2 p{color:#E4EBF3;}
.oc ul{margin-left:13pt;} .oc li{margin-bottom:4pt;}
.bidline{border-left:3pt solid var(--navy);padding:2pt 0 2pt 12pt;margin-bottom:14pt;}
.fee{background:var(--cream);border-left:4pt solid var(--sun);padding:12pt 16pt;font-size:12pt;}
.fee b{color:var(--navy);font-weight:500;}
.ask{font-weight:500;font-size:16pt;color:var(--navy);margin-top:16pt;}

/* HUMAN page 7 */
.p7top{display:flex;gap:18pt;align-items:flex-end;margin-bottom:14pt;}
.p7top .ph{width:1.65in;height:1.7in;object-fit:cover;}
.p7top .nm{font-weight:500;font-size:22pt;color:var(--navy);line-height:1.05;}
.p7top .tt{font-weight:500;font-size:10pt;letter-spacing:.14em;color:#FF9C00;margin:4pt 0 8pt;}
.p7top .ct{font-size:11pt;color:var(--slate);}
.note{font-size:11.5pt;line-height:1.45;}
.note p{margin-bottom:8pt;}
.note .sg{width:1.1in;margin-top:0;}
.qr7{display:flex;gap:12pt;margin-top:12pt;}
.q7{display:flex;gap:14pt;align-items:center;background:var(--mist);padding:11pt 14pt;}
.q7.mt{margin-top:14pt;}
.q7.bk{background:var(--navy);color:#fff;}
.q7 img{width:1.1in;height:1.1in;background:#fff;padding:3pt;}
.q7 .t{font-weight:500;font-size:16pt;color:var(--navy);line-height:1.2;}
.q7.bk .t{color:#fff;}
.q7 .u{font-size:11pt;color:var(--slate);margin:4pt 0;white-space:nowrap;}
.q7.bk .u{color:#E4EBF3;}
.q7 .nc{font-weight:700;font-size:10pt;color:#FF9C00;margin-top:4pt;}
.prom{display:flex;flex-wrap:wrap;gap:6pt 16pt;margin-top:8pt;border-top:.6pt solid var(--hair);padding-top:8pt;}
.prom div{width:calc(50% - 8pt);font-size:10.5pt;color:var(--slate);}
.prom b{display:block;color:var(--navy);font-weight:500;font-size:11.5pt;}

/* HERO page 8 */
.bk8{background:var(--navy);color:#fff;width:8.5in;height:11in;padding:0.85in 0.9in 0.6in;position:relative;}
.bk8 .lg{width:1.3in;margin-bottom:34pt;}
.bk8 .eb{font-weight:500;font-size:10pt;letter-spacing:.16em;color:#FF9C00;}
.bk8 h1{color:#fff;font-size:34pt;margin:6pt 0 14pt;}
.bk8 .lead{font-size:13pt;line-height:1.5;color:#E4EBF3;max-width:6in;}
.cta{display:flex;gap:22pt;align-items:center;margin:30pt 0 26pt;background:#fff;color:var(--navy);padding:18pt 20pt;}
.cta img{width:1.9in;height:1.9in;}
.cta .t{font-weight:500;font-size:22pt;line-height:1.15;}
.cta .u{font-size:11pt;color:var(--slate);margin:8pt 0 4pt;}
.cta .nc{font-weight:700;font-size:12pt;color:#FF9C00;}
.bk8 ul{margin-left:14pt;font-size:11.5pt;color:#E4EBF3;} .bk8 li{margin-bottom:5pt;}
.bk8 .bq{margin-top:22pt;border-left:3pt solid #FF9C00;padding-left:12pt;font-weight:500;font-size:14pt;}
.bk8 .ft{position:absolute;left:0.9in;right:0.9in;bottom:0.55in;display:flex;justify-content:space-between;align-items:flex-end;font-size:10.5pt;color:#E4EBF3;border-top:.6pt solid #5A6577;padding-top:8pt;}
.bk8 .ft img{width:2in;}
"""


# ---------------------------------------------------------------- pages ----
def p2():
    return """<section class="pg">
<div class="eyebrow">Executive summary</div>
<h1>Your %s return, and what it points to</h1>
<div class="chain">
 <div class="c"><div class="lab">You file</div><div class="big">%s</div><div class="d">of indirect expense on twelve lines of your Form 990</div></div>
 <div class="arr">&rarr;</div>
 <div class="c"><div class="lab">We could size</div><div class="big">%s</div><div class="d">of it from outside, across twelve categories we work</div></div>
 <div class="arr">&rarr;</div>
 <div class="c c3"><div class="lab">Recoverable, a year</div><div class="big">%s&ndash;%s</div><div class="d">low end to median of ERA's completed work, on that %s</div></div>
</div>
<div class="gap2"><b>The other %s is not priced yet.</b> It sits mostly in materials and occupancy, which your return reports as single figures. Your ledger splits them. A filing cannot.</div>
<div class="two quiet">
 <div><div class="sub">What it would fund</div><p>Every dollar that does not have to be spent on indirect expense is a dollar available for %s. It recurs, it is unrestricted, and at the low end it equals about a quarter of your %s operating surplus.</p></div>
 <div><div class="sub">Why it holds up</div><p>Your own filed figures, and rates from work ERA has finished in the same categories, including engagements that recovered nothing. That work has recovered %s for %s organizations.</p></div>
</div>
<div class="big-quote">A starting point rather than a conclusion, and never a verdict on how you are run.</div>
<p class="src">ESTIMATE. Our completed record applied to your filed figures, not a forecast. Exact: %s low end, %s median, %s strongest quarter, on %s.</p>
</section>""" % (ORG["fy"], m(FILED_TOTAL), m(B_SPEND), m(B_LOW), m(B_MED), m(B_SPEND),
                m(FILED_TOTAL - B_SPEND), ORG["mission"], ORG["fy"], FIRM["recovered"], FIRM["orgs"],
                usd(B_LOW), usd(B_MED), usd(B_HI), usd(B_SPEND))


def _bk_rows(rows):
    out = ""
    for x in sorted(rows, key=lambda r: -r["amt"]):
        out += "<tr class='r'><td><b>%s</b></td><td class='cat'>%s</td><td class='n'>%s</td><td class='n rec'>%s&ndash;%s</td></tr>" % (
            x["lab"], SHORT[x["cat"]], usd(x["amt"]), m(x["lo"]), m(x["md"]))
    return out


def p3():
    return """<section class="pg">
<div class="eyebrow">Category by category</div>
<h1>Every line we could size, and what it is worth</h1>
<table class="bkt"><thead><tr><th style="width:44%%">On your return</th><th style="width:20%%">Priced as</th><th class="n" style="width:16%%">Spend</th><th class="n" style="width:20%%">Recoverable<br>each year</th></tr></thead><tbody>
<tr class="g"><td colspan="4">Filed lines and named services</td></tr>%s
<tr class="sub"><td colspan="2">Filed lines and named services, total</td><td class="n">%s</td><td class="n">%s&ndash;%s</td></tr>
<tr class="g"><td colspan="4">Blended lines, the share comparable filers report</td></tr>%s
<tr class="sub"><td colspan="2">Blended lines, total</td><td class="n">%s</td><td class="n">%s&ndash;%s</td></tr>
</tbody></table>
<div class="totalbar"><div class="blk"><div class="k">Spend sized from your return</div><div class="v">%s</div></div><div class="blk rt"><div class="k">Recoverable each year</div><div class="v big">%s&ndash;%s</div></div></div>
<p class="src" style="margin-top:6pt">Recoverable each year: low end to median. Line numbers are Part IX; VII-B services are treated as inside line 11g, so nothing is counted twice. Travel sits below what comparable filers report.</p>
<div class="panel methx"><b class="navy">How each figure was built.</b> <b>Filed lines:</b> your amount at the line named. <b>Blended lines:</b> only the share comparable filers report (2.18%% of revenue as consumed supply; their maintenance spend). <b>Rates:</b> ERA's completed and monitored work in each category, including engagements that recovered nothing. <b>Comparison:</b> employment-services filers at half to double your revenue.</div>
</section>""" % (_bk_rows(T_FILED), usd(_sum(T_FILED, "amt")), m(_sum(T_FILED, "lo")), m(_sum(T_FILED, "md")),
                 _bk_rows(T_BLEND), usd(_sum(T_BLEND, "amt")), m(_sum(T_BLEND, "lo")), m(_sum(T_BLEND, "md")),
                 usd(B_SPEND), m(B_LOW), m(B_MED))


def p4():
    return ""


def p5():
    rest = [("Materials and supplies, the rest", "line 24", MAT_REST, "Resale or converted material, or more consumed supply than peers carry."),
            ("Occupancy, the rest", "line 16", OCC_REST, "Rent, plus janitorial and utilities, which we work."),
            ("Software subscriptions", "not on return", 333364, "Peers report it; we work it. No rate from outside."),
            ("Legal and lobbying fees", "lines 11b, 11d", 637913 + 63200, "Professional appointments, not supplier spend.")]
    rows = "".join("<tr><td><b>%s</b> <span class='muted'>&middot; %s</span></td><td class='n'>%s</td><td>%s</td></tr>" % (a, b, m(c), d) for a, b, c, d in rest)
    rows += "".join("<tr><td><b>%s</b> <span class='muted'>&middot; not on return</span></td><td class='n'>%s</td><td><b class='navy'>%s&ndash;%s each year</b>, kept out of page 3.</td></tr>" % (
        x["lab"], m(x["amt"]), m(x["lo"]), m(x["md"])) for x in T_IMPL)
    qs = [
        ("How does materials and supplies divide between what you resell and what you consume?",
         "It is your largest line, and we sized only the share peers consume.", "Whoever runs those operations"),
        ("Is your laundry distribution one agreement or several, and what does it cover?",
         "Scope and renewal terms decide whether the page 4 figure is real.", "Whoever owns that relationship"),
        ("How much of your %s in occupancy is rent?" % m(24376137),
         "Janitorial and utilities, which we work, sit inside the same figure.", "Your controller or facilities lead"),
    ]
    cards = "".join("<div class='q'><div class='qq'>%s</div><div class='w'>%s</div><div class='who'>%s</div></div>" % q for q in qs)
    return """<section class="pg">
<div class="eyebrow">What a filing cannot tell us</div>
<h1>What is still unsized, and the four questions that matter most</h1>
<table class="dec"><thead><tr><th style="width:38%%">What remains</th><th class="n" style="width:10%%">Spend</th><th>Why it is not in the figure yet</th></tr></thead><tbody>%s</tbody></table>
<div class="hq" style="margin-top:14pt"><div class="k">The question that could change the answer</div>
<div class="q">When were these agreements last tested against the market, and against what?</div>
<p style="margin:0">No filing can answer it. If the answer is recent and the terms held, we will say so and stop.</p></div>
<div class="qs3">%s</div>
<p class="more"><b>Your return raises more than four.</b> What the consulting contracts cover, what sits in service charges and all other expenses, and where IT and insurance appear. Those are in your Insight Center: <b class="navy">%s</b></p>
</section>""" % (rows, cards, PORTAL)


def p6():
    steps = [("You tell us when", "An answer per line"), ("We read the agreements", "Your contracts"),
             ("We read the invoices", "An export"), ("Specialists look", "Nothing"),
             ("Options, line by line", "Nothing"), ("You decide each one", "Nothing")]
    cls = ["first", "second", "third", "", "", ""]
    js = "".join("<div class='s %s'><div class='dot'>%d</div><div class='t'>%s</div><div class='c'>Costs you<br><b>%s</b></div></div>" % (
        cls[i], i + 1, a, b) for i, (a, b) in enumerate(steps))
    return """<section class="pg">
<div class="eyebrow">What would happen next</div>
<h1>What it takes from you, and what you get either way</h1>
<div class="journey"><div class="line"></div>%s</div>
<div class="keyline">Every category runs through these steps at once. Any line tested recently that held, we say so at step one and stop.</div>
<div class="oc">
 <div class="n1"><div class="h">If we find nothing</div><ul>
  <li>Written confirmation, by category, that your arrangements are competitive</li>
  <li>A baseline to revisit at renewal</li>
  <li>No disruption to a supplier doing the job</li></ul>
  <p style="margin-top:6pt">%s of our completed reviews end here. If the current arrangements are already competitive, that is a valuable conclusion as well.</p></div>
 <div class="n2"><div class="h">If we find something</div>
  <p>It recurs and it is unrestricted. It did not come out of a program or a fundraising target.</p>
  <p>It is a different item to bring to a board than a cut list, and the working is yours either way.</p></div>
</div>
<div class="bidline"><b>You may already have bid these.</b> A bid tests the price. It does not read the agreement: the term, the minimums, the ancillary charges, what is billed against what was agreed. In our completed work, that is where the value more often sits.</div>
<div class="fee"><b>Our fee comes only out of value that is actually recovered and verified.</b> If we recover nothing, there is no fee. No supplier changes without your approval, and you can stop any line at any step.</div>
<div class="ask">If this is directionally useful, a short conversation is the next step.</div>
</section>""" % (js, FIRM["zero"])


def p7():
    prom = [("I will tell you when you already have a good deal.", "By category, in writing."),
            ("Incumbents stay whenever they are the best choice.", "The goal is better terms, not new suppliers."),
            ("Every recommendation comes with its evidence.", "You see the data first."),
            ("You stay in control.", "Nothing changes without your approval."),
            ("My success depends on yours.", "If we recover nothing, there is no fee.")]
    pr = "".join("<div><b>%s</b>%s</div>" % p for p in prom)
    return """<section class="pg">
<div class="eyebrow">Before we meet</div>
<div class="p7top"><img class="ph" src="%s"><div>
 <h1 style="margin:0 0 10pt">Prepared before we spoke, and some of it will be wrong</h1>
 <div class="nm">John Wylie</div><div class="tt">CONSULTING PARTNER · ERA GROUP</div>
 <div class="ct">jwylie@eragroup.com · 703.244.9868</div></div></div>
<div class="note">
<p>That is not a disclaimer. It is the reason for the conversation.</p>
<p>This Brief is not here to prove an estimate. It is here to find out, from your own contracts and invoices, whether the opportunity is real, and to tell you plainly when it is not. So the question I would most like to ask you is a simple one: <b>what have we got wrong?</b></p>
<img class="sg" src="%s">
</div>
<div class="sub" style="margin-top:10pt">What you can expect from me</div>
<div class="prom" style="margin-top:4pt">%s</div>
<div class="q7 bk mt"><img src="%s"><div><div class="t">Pick a time to talk with me</div><div class="u">calendly.com/john_wylie/30min</div><div class="nc">Or call 703.244.9868 &middot; jwylie@eragroup.com</div></div></div>
</section>""" % (PHOTO, SIG, pr, qr_plain(BOOK_URL))


def p8():
    return """<section class="back"><div class="bk8">
<img class="lg" src="%s">
<div class="eb">YOUR INSIGHT CENTER</div>
<h1>What we could print is the smaller half</h1>
<p class="lead">A Form 990 breaks out only the lines the form asks for. Facilities, insurance, professional services, printing and IT support usually sit inside larger lines. We work all of them. We cannot size yours from outside. You can.</p>
<div class="cta"><img src="%s"><div><div class="t">Scan for the rest of your analysis</div><div class="u">%s</div><div class="nc">No code. No form. No login.</div></div></div>
<ul><li>Every line on your return, with its exact place on the filing</li>
<li>How each line compares with organizations that file the same one</li>
<li>The categories organizations like yours report that your return does not show</li>
<li>What is moving in the markets behind your categories, updated as it happens</li></ul>
<div class="bq">The first question is still the same: when were these agreements last tested, and against what?</div>
<div class="ft"><div>John Wylie · Consulting Partner · ERA Group<br>jwylie@eragroup.com · 703.244.9868</div><img src="%s"></div>
</div></section>""" % (LOGO_W, qr_uri("back"), PORTAL, VTI_W)


def interior():
    html = "<html><head><style>%s%s%s%s</style></head><body>%s%s%s%s%s%s</body></html>" % (
        BASE_CSS, page_css(), "", CSS, p2(), p3(), p5(), p6(), p7(), p8())
    p = OUT + "/_interior_v6.pdf"
    HTML(string=html).write_pdf(p)
    return p




if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    nc, lt, cv = note_card(), letter(), cover()
    it = interior()
    n = len(PdfReader(it).pages)
    assert n == 6, "interior must be 6 pages, got %d" % n
    booklet = merge([cv, lt, it], OUT + "/EOB_v6_Goodwill_Brief_8pp_print.pdf")
    shutil.copy(booklet, OUT + "/EOB_v6_Goodwill_PACKAGE_proof.pdf")
    shutil.copy(lt, OUT + "/EOB_v6_Goodwill_CoverLetter.pdf")
    shutil.copy(nc, OUT + "/EOB_v6_Goodwill_NoteCard_5x7.pdf")
    print("booklet pages:", len(PdfReader(booklet).pages))
