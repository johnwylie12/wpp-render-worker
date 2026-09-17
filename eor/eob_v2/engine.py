"""Executive Opportunity Brief v2 -- the locked v6 design, driven by per-account content.

Content comes from fn_eob_v2_content(account_id) and is frozen into
content_briefs.params.content at enqueue; signers come from wpp_signoff /
wpp_cosignoff. This module computes nothing: it lays out what it is given and
refuses to print when something required is missing.

Styling, logos, headshot, cover engine and the next-steps page are imported from
the locked Goodwill builder (eor/eob_v6_goodwill/build.py, settled #258), so the
two can never drift apart.

    render(content, signoff, cosignoff, workdir) -> (pdf_path, pages)
"""
import os
import importlib.util
from weasyprint import HTML
from jinja2 import Template
from pypdf import PdfReader

import wpp_signatures

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "eob_v6_locked", os.path.join(HERE, "..", "eob_v6_goodwill", "build.py"))
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)

JOHN_PARTNERS = {3, 6}   # partner 6 is John's working login (settled #262)
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
         "eighteen", "nineteen", "twenty"]
MAX_ROWS = 14


class EobV2Error(Exception):
    """Raised instead of printing a Brief that is missing something it needs."""


def words(n):
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


def m(n):
    return L.m(float(n or 0))


def usd(n):
    return L.usd(float(n or 0))


def cap(s):
    return s[:1].upper() + s[1:] if s else s


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def qr_url(portal, tag):
    """What a printed QR encodes: the branded address, which resolves on its own.
    Never the access code (release gate: no printed surface may carry one)."""
    return "https://%s?s=%s" % (portal["display"], tag)


def url_html(display):
    """The portal address may break after the domain, never inside the account's
    name: a split slug reads to the release gate (and a reader) as someone else's."""
    host, _, slug = display.partition("/")
    return "%s/<wbr><span style='white-space:nowrap'>%s</span>" % (esc(host), esc(slug))


def _signer(row):
    """A wpp_signoff row -> what the pages print. Raises if no mark is registered."""
    if not row:
        return None
    pid = int(row["partner_id"])
    key = wpp_signatures.signature_for_partner(pid)
    return {
        "pid": pid, "name": row["signoff_name"], "title": row["signoff_title"],
        "firm": row["signoff_firm"], "email": row["signoff_email"], "phone": row["signoff_phone"],
        "booking": row.get("booking_url"), "sig": wpp_signatures.signature_data_uri(key),
    }


def _check(c):
    if c.get("error"):
        raise EobV2Error("content: %s" % c["error"])
    r = c.get("recipient") or {}
    if r.get("blocks_package"):
        raise EobV2Error("recipient blocks the package: %s" % r.get("blocks_reason"))
    if not r.get("name") or not r.get("addr_line1"):
        raise EobV2Error("no named recipient with a mailing address")
    if not c.get("portal"):
        raise EobV2Error("no published portal: the Brief prints its address and QR")
    if not c.get("lines"):
        raise EobV2Error("no priced lines")


# ------------------------------------------------------------------ letter ----
LETTER_CSS = """
@page{size:8.5in 11in;margin:0.45in 0.85in 0.35in;}
.top{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:2pt solid var(--navy);padding-bottom:8pt;margin-bottom:14pt;}
.top img{width:1.25in;}
.top .r{text-align:right;font-size:10pt;color:var(--slate);line-height:1.35;}
.top .r b{color:var(--navy);font-size:10.5pt;letter-spacing:.08em;}
.addr{font-size:10.5pt;line-height:1.35;margin-bottom:12pt;}
.addr b{color:var(--navy);font-weight:500;font-size:11.5pt;}
p{font-size:10.6pt;line-height:1.4;margin-bottom:7pt;}
.sum{margin:4pt 0 10pt;}
.sum .h{font-weight:500;font-size:10pt;letter-spacing:.14em;color:var(--slate);border-bottom:1.5pt solid var(--sun);padding-bottom:3pt;margin-bottom:2pt;}
.sum td{font-size:10.3pt;padding:5pt 4pt;}
.sum td.k{width:1.75in;font-weight:500;color:var(--navy);font-size:12.5pt;white-space:nowrap;}
.close{display:flex;justify-content:space-between;align-items:flex-start;gap:14pt;margin-top:4pt;}
.sigs{display:flex;gap:14pt;}
.sg .mk{height:52px;display:flex;align-items:flex-end;}
.sg .mk img{max-height:52px;max-width:1.5in;}
.who{font-size:10pt;line-height:1.3;}
.who b{color:var(--navy);font-weight:500;font-size:11pt;}
.portal{width:3.0in;border-left:3pt solid var(--sun);padding-left:10pt;}
.portal .t{font-weight:500;color:var(--navy);font-size:11pt;}
.portal .d{font-size:10pt;color:var(--slate);margin:2pt 0 5pt;line-height:1.3;}
.portal .row{display:flex;gap:8pt;align-items:center;}
.portal img{width:0.85in;height:0.85in;}
.portal .u{font-size:10pt;color:var(--ink);line-height:1.3;}
.portal .u b{color:var(--navy);display:block;margin-top:3pt;}
.portal .url{font-size:9pt;color:var(--ink);margin-top:3pt;}
.foot{text-align:center;margin-top:10pt;}
.foot img{width:1.9in;}
"""


def _sig_block(s):
    return ("<div class='sg'><div class='mk'><img src='%s'></div><div class='who'><b>%s</b><br>%s<br>%s<br>%s</div></div>"
            % (s["sig"], esc(s["name"]), esc(s["title"]), esc(s["firm"]), esc(s["email"])))


def letter(c, signers, workdir):
    o, r, t, pt = c["org"], c["recipient"], c["totals"], c["portal"]
    n_cats = len({ln["category"] for ln in c["lines"]})
    unsized_note = ("mostly " + " and ".join(u["label"].split(",")[0].lower() for u in c["unsized"][:2])
                    + ". Your ledger splits them; your return does not.") if c["unsized"] else \
                   "lines a filing cannot split. Your ledger can."
    addr = "<br>".join(esc(x) for x in [r["name"], r.get("title"), o["legal"], r["addr_line1"], r.get("addr_line2")] if x)
    html = """<html><head><style>%s%s</style></head><body>
<div class="top"><img src="%s"><div class="r"><b>EXECUTIVE OPPORTUNITY BRIEF</b><br>%s</div></div>
<div class="addr"><b>%s</b></div>
<p>Dear %s,</p>
<p>We prepared the enclosed Executive Opportunity Brief for %s before contacting you. It is built entirely from your %s Form 990 and from what ERA Group's completed work has actually returned in the same categories. For an organization whose mission is %s, every dollar that does not have to stay in indirect operating expense is a dollar that can go back to that work.</p>
<div class="sum"><div class="h">IN SHORT</div><table>
<tr><td class="k">%s</td><td>of indirect operating expense on your return, across %s lines. Every one of them is accounted for inside.</td></tr>
<tr><td class="k">%s</td><td>of that we could size from outside, across %s categories ERA works.</td></tr>
<tr><td class="k">%s&ndash;%s</td><td>a year recoverable on that sized spend, from the low end to the median of ERA's completed work. <b>An estimate, not a forecast.</b></td></tr>
%s
</table></div>
<p>Every figure in it is a question to validate, not a conclusion about how %s is run. Some of it will be wrong, and we would rather hear which part than have you agree politely. If your current arrangements are already competitive, that is a useful answer too.</p>
<p>If the analysis is directionally useful, we would welcome a short conversation. Nothing changes without your approval, incumbent suppliers often remain, and ERA is paid only out of value that is actually recovered. If we recover nothing, there is no fee.</p>
<p style="margin-bottom:2pt">Best regards,</p>
<div class="close">
 <div class="sigs">%s</div>
 <div class="portal"><div class="t">Your complete analysis is online</div>
  <div class="d">Every line, where it sits on your return, and how it compares.</div>
  <div class="row"><img src="%s"><div class="u">Scan with your phone camera.<b>No code. No form. No login.</b></div></div><div class="url">%s</div></div>
</div>
<div class="foot"><img src="%s"></div>
</body></html>""" % (
        L.BASE_CSS, LETTER_CSS, L.LOGO, esc(c["month"]), addr,
        esc(r["first_name"]), esc(o["display"]), esc(o["fy"]), esc(o["mission"]),
        usd(t["filed_indirect"]), words(int(t["filed_lines"])),
        usd(t["sized"]), words(n_cats),
        m(t["low"]), m(t["median"]),
        ("<tr><td class='k'>%s</td><td>not yet sized: %s</td></tr>" % (usd(t["not_sized"]), unsized_note))
        if float(t["not_sized"] or 0) > 0 else "",
        esc(o["display"]),
        "".join(_sig_block(s) for s in signers),
        L.qr_plain(qr_url(pt, "letter")), url_html(pt["display"]), L.VTI)
    p = os.path.join(workdir, "eob_v2_letter.pdf")
    HTML(string=html).write_pdf(p)
    return p


# ------------------------------------------------------------------- cover ----
def cover(c, workdir):
    o = c["org"]
    ctx = L.cpe.build({"org": {"name": o["display"], "vertical": "human_services"}},
                      hero_lookup=lambda v: o.get("hero_file") or "heroes/human_services.png",
                      title="EXECUTIVE OPPORTUNITY BRIEF", subtitle=o["fy"] + " FORM 990",
                      date_str=c["month"], doc_type="package")
    ctx["statement_html"] = ("Your next <span class='g'>%s</span> may already be sitting "
                             "in your operating budget.") % esc(o["cover_noun"])
    tpl = Template(open(os.path.join(L.W, "cover", "cover_page_template.html")).read())
    p = os.path.join(workdir, "eob_v2_cover.pdf")
    HTML(string=tpl.render(**ctx)).write_pdf(p)
    return p


# ---------------------------------------------------------------- interior ----
def p2(c):
    o, t = c["org"], c["totals"]
    n_cats = len({ln["category"] for ln in c["lines"]})
    surplus = float(t.get("surplus") or 0)
    fund = ""
    if surplus > 0:
        share = float(t["low"]) / surplus
        if 0.05 <= share <= 3:
            fund = (" At the low end it equals about %d%% of your %s operating surplus."
                    % (round(share * 100 / 5) * 5, esc(o["fy"])))
    gap = ""
    if float(t["not_sized"] or 0) > 0:
        where = ", ".join(u["label"].split(",")[0].lower() for u in c["unsized"][:2]) or "lines a filing cannot split"
        gap = ("<div class='gap2'><b>The other %s is not priced yet.</b> It sits mostly in %s, which your return "
               "reports as single figures. Your ledger splits them. A filing cannot.</div>" % (m(t["not_sized"]), esc(where)))
    return """<section class="pg">
<div class="eyebrow">Executive summary</div>
<h1>Your %s return, and what it points to</h1>
<div class="chain">
 <div class="c"><div class="lab">You file</div><div class="big">%s</div><div class="d">of indirect expense on %s lines of your Form 990</div></div>
 <div class="arr">&rarr;</div>
 <div class="c"><div class="lab">We could size</div><div class="big">%s</div><div class="d">of it from outside, across %s categories we work</div></div>
 <div class="arr">&rarr;</div>
 <div class="c c3"><div class="lab">Recoverable, a year</div><div class="big">%s&ndash;%s</div><div class="d">low end to median of ERA's completed work, on that %s</div></div>
</div>
%s
<div class="two quiet">
 <div><div class="sub">What it would fund</div><p>Every dollar that does not have to be spent on indirect expense is a dollar available for %s. It recurs and it is unrestricted.%s</p></div>
 <div><div class="sub">Why it holds up</div><p>Your own filed figures, and rates from work ERA has finished in the same categories, including engagements that recovered nothing. That work has recovered %s for %s organizations.</p></div>
</div>
<div class="big-quote">A starting point rather than a conclusion, and never a verdict on how you are run.</div>
<p class="src">ESTIMATE. Our completed record applied to your filed figures, not a forecast. Exact: %s low end, %s median, %s strongest quarter, on %s.</p>
</section>""" % (esc(o["fy"]), m(t["filed_indirect"]), words(int(t["filed_lines"])),
                 m(t["sized"]), words(n_cats), m(t["low"]), m(t["median"]), m(t["sized"]),
                 gap, esc(o["mission"]), fund, c["firm"]["recovered"], c["firm"]["orgs"],
                 usd(t["low"]), usd(t["median"]), usd(t["high"]), usd(t["sized"]))


def _rows(lines):
    return "".join(
        "<tr class='r'><td><b>%s</b></td><td class='cat'>%s</td><td class='n'>%s</td><td class='n rec'>%s&ndash;%s</td></tr>"
        % (esc(cap(x["display"])), esc(x["category"]), usd(x["amount"]), m(x["low"]), m(x["median"])) for x in lines)


def _fold(lines):
    """Keep the table on one page: the smallest lines roll into one row."""
    if len(lines) <= MAX_ROWS:
        return lines
    keep, rest = lines[:MAX_ROWS - 1], lines[MAX_ROWS - 1:]
    return keep + [{"display": "%s smaller lines" % words(len(rest)), "category": "Several",
                    "amount": sum(float(x["amount"]) for x in rest),
                    "low": sum(float(x["low"]) for x in rest),
                    "median": sum(float(x["median"]) for x in rest)}]


def p3(c):
    t = c["totals"]
    filed = _fold([x for x in c["lines"] if x["tier"] == "filed"])
    blend = [x for x in c["lines"] if x["tier"] == "blended"]
    s = lambda rows, k: sum(float(x[k]) for x in rows)
    blend_html = ""
    if blend:
        blend_html = ("<tr class='g'><td colspan='4'>Blended lines, the share comparable filers report</td></tr>%s"
                      "<tr class='sub'><td colspan='2'>Blended lines, total</td><td class='n'>%s</td><td class='n'>%s&ndash;%s</td></tr>"
                      % (_rows(blend), usd(s(blend, "amount")), m(s(blend, "low")), m(s(blend, "median"))))
    return """<section class="pg">
<div class="eyebrow">Category by category</div>
<h1>Every line we could size, and what it is worth</h1>
<table class="bkt"><thead><tr><th style="width:40%%">On your return</th><th style="width:24%%">Priced as</th><th class="n" style="width:16%%">Spend</th><th class="n" style="width:20%%">Recoverable<br>each year</th></tr></thead><tbody>
<tr class="g"><td colspan="4">Filed lines</td></tr>%s
<tr class="sub"><td colspan="2">Filed lines, total</td><td class="n">%s</td><td class="n">%s&ndash;%s</td></tr>
%s
</tbody></table>
<div class="totalbar"><div class="blk"><div class="k">Spend sized from your return</div><div class="v">%s</div></div><div class="blk rt"><div class="k">Recoverable each year</div><div class="v big">%s&ndash;%s</div></div></div>
<p class="src" style="margin-top:6pt">Recoverable each year: low end to median of ERA's completed and monitored work in each category.</p>
<div class="panel methx"><b class="navy">How each figure was built.</b> <b>Filed lines:</b> your amount at the line named. <b>Blended lines:</b> only the share comparable filers report. <b>Rates:</b> ERA's completed and monitored work in each category, including engagements that recovered nothing. <b>Comparison:</b> %s.</div>
</section>""" % (_rows(filed), usd(s(filed, "amount")), m(s(filed, "low")), m(s(filed, "median")),
                 blend_html, usd(t["sized"]), m(t["low"]), m(t["median"]), esc(c["org"]["peer_label"]))


def p5(c):
    rows = "".join("<tr><td><b>%s</b></td><td class='n'>%s</td><td>%s</td></tr>"
                   % (esc(u["label"]), m(u["amount"]), esc(u["why"])) for u in c["unsized"])
    rows += "".join("<tr><td><b>%s</b> <span class='muted'>&middot; not on return</span></td><td class='n'>%s</td>"
                    "<td>Comparable filers report it; we keep it out of page 4.</td></tr>"
                    % (esc(cap(x["display"])), m(x["amount"])) for x in c["implied"][:3])
    qs = c["questions"][:3]
    cards = "".join("<div class='q'><div class='qq'>%s</div><div class='w'>%s</div><div class='who'>%s</div></div>"
                    % (esc(q["q"]), esc(q["why"]), esc(q["who"])) for q in qs)
    n = len(qs) + 1
    return """<section class="pg">
<div class="eyebrow">What a filing cannot tell us</div>
<h1>What is still unsized, and the %s questions that matter most</h1>
<table class="dec"><thead><tr><th style="width:38%%">What remains</th><th class="n" style="width:10%%">Spend</th><th>Why it is not in the figure yet</th></tr></thead><tbody>%s</tbody></table>
<div class="hq" style="margin-top:14pt"><div class="k">The question that could change the answer</div>
<div class="q">When were these agreements last tested against the market, and against what?</div>
<p style="margin:0">No filing can answer it. If the answer is recent and the terms held, we will say so and stop.</p></div>
<div class="qs3">%s</div>
<p class="more"><b>Your return raises more than %s.</b> The rest, line by line, are in your Insight Center: <b class="navy">%s</b></p>
</section>""" % (words(n), rows, cards, words(n), url_html(c["portal"]["display"]))


def p7(c, lead):
    prom = [("I will tell you when you already have a good deal.", "By category, in writing."),
            ("Incumbents stay whenever they are the best choice.", "The goal is better terms, not new suppliers."),
            ("Every recommendation comes with its evidence.", "You see the data first."),
            ("You stay in control.", "Nothing changes without your approval."),
            ("My success depends on yours.", "If we recover nothing, there is no fee.")]
    pr = "".join("<div><b>%s</b>%s</div>" % p for p in prom)
    photo = "<img class='ph' src='%s'>" % L.PHOTO if lead["pid"] in JOHN_PARTNERS else ""
    book = ""
    if lead.get("booking"):
        shown = lead["booking"].split("://", 1)[-1]
        book = ("<div class='q7 bk mt'><img src='%s'><div><div class='t'>Pick a time to talk with me</div>"
                "<div class='u'>%s</div><div class='nc'>Or call %s &middot; %s</div></div></div>"
                % (L.qr_plain(lead["booking"]), esc(shown), esc(lead["phone"]), esc(lead["email"])))
    return """<section class="pg">
<div class="eyebrow">Before we meet</div>
<div class="p7top">%s<div>
 <h1 style="margin:0 0 10pt">Prepared before we spoke, and some of it will be wrong</h1>
 <div class="nm">%s</div><div class="tt">%s · %s</div>
 <div class="ct">%s · %s</div></div></div>
<div class="note">
<p>That is not a disclaimer. It is the reason for the conversation.</p>
<p>This Brief is not here to prove an estimate. It is here to find out, from your own contracts and invoices, whether the opportunity is real, and to tell you plainly when it is not. So the question I would most like to ask you is a simple one: <b>what have we got wrong?</b></p>
<img class="sg" src="%s">
</div>
<div class="sub" style="margin-top:10pt">What you can expect from me</div>
<div class="prom" style="margin-top:4pt">%s</div>
%s
</section>""" % (photo, esc(lead["name"]), esc(lead["title"]).upper(), esc(lead["firm"]).upper(),
                 esc(lead["email"]), esc(lead["phone"]), lead["sig"], pr, book)


def p8(c, lead):
    pt = c["portal"]
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
<div class="ft"><div>%s · %s · %s<br>%s · %s</div><img src="%s"></div>
</div></section>""" % (L.LOGO_W, L.qr_plain(qr_url(pt, "back")), url_html(pt["display"]),
                       esc(lead["name"]), esc(lead["title"]), esc(lead["firm"]),
                       esc(lead["email"]), esc(lead["phone"]), L.VTI_W)


def interior(c, lead, workdir):
    css = L.page_css().replace(L.ORG["display"], esc(c["org"]["display"]))
    html = "<html><head><style>%s%s%s</style></head><body>%s%s%s%s%s%s</body></html>" % (
        L.BASE_CSS, css, L.CSS, p2(c), p3(c), p5(c), L.p6(), p7(c, lead), p8(c, lead))
    p = os.path.join(workdir, "eob_v2_interior.pdf")
    HTML(string=html).write_pdf(p)
    return p


def qr_payloads(content):
    """Every URL a printed QR in this Brief encodes, for the release gate."""
    pt = content["portal"]
    return [qr_url(pt, "letter"), qr_url(pt, "back")]


def render(content, signoff, cosignoff, workdir):
    """-> (booklet_pdf, page_count). The co-signer, when present, leads."""
    _check(content)
    signer = _signer(signoff)
    if not signer:
        raise EobV2Error("no signoff resolved for this account")
    co = _signer(cosignoff)
    signers = [co, signer] if co else [signer]
    lead = signers[0]
    os.makedirs(workdir, exist_ok=True)
    cv = cover(content, workdir)
    lt = letter(content, signers, workdir)
    if len(PdfReader(lt).pages) != 1:
        raise EobV2Error("the cover letter ran past one page")
    it = interior(content, lead, workdir)
    n = len(PdfReader(it).pages)
    if n != 6:
        raise EobV2Error("interior ran to %d pages; the Brief is cover + letter + 6" % n)
    out = L.merge([cv, lt, it], os.path.join(workdir, "eob_v2_brief.pdf"))
    return out, len(PdfReader(out).pages)
