#!/usr/bin/env python3
"""The question-led Executive Opportunity Brief.

  python eor/question_led/engine.py content_goodwill.json --mode plain
  python eor/question_led/engine.py content_goodwill.json --mode stitched
  python eor/question_led/engine.py content_goodwill.json --mode both

WHAT THIS IS. A generator for the version of the document John identified on
2026-09-06 as the best output yet, which until that day existed only as a single
PDF and had been lost to a chat container twice before (open_findings #195 and
#212, and the postmortem inside settled #172). The recovered original and its
full extracted structure sit in recovered/ and are the thing to diff against.

THE PAGE COUNT IS NOT FROZEN. John, 2026-09-06: "We do not have to freeze the
number of the pages. For the 15th time. The purpose is to get the best product
out the door. If it takes a few more pages, then great as long as they are
delivering value." So content decides the length, and this file computes
everything that depends on it:

  * "PAGE n OF m" is derived from the number of content sheets actually
    rendered. The measured original said "OF 16" and delivered 10.
  * The saddle-stitch blanks are computed, not written into the content. A
    stitched booklet needs a multiple of four leaves; add a page and the padding
    re-solves itself.

TWO IMPOSITIONS, ONE CONTENT SET.
  plain     cover, letter, content, back cover. No blanks. This is the version
            for ordinary duplex or for reading on screen.
  stitched  the same sheets with blank versos inserted so the cover and the
            letter each start on a recto and the total is a multiple of four.
            For the saddle-stitch production John has not nailed down yet.
Neither is more canonical than the other. They are the same document imposed
two ways, and both are rendered from this one call so they cannot drift.

WHAT THIS FILE DOES NOT DO. It does not draw the cover and it does not lay out
the cover letter. Both already exist, both are locked, and re-implementing them
is the specific mistake settled #172 records twice ("THE REPO TEMPLATE IS THE
COVER. Do not draw one.") and settled #174 guards with nine assertions. They are
rendered by their own engines and merged in here.
"""
import argparse, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
FONTS = os.path.join(REPO, "fonts")

sys.path.insert(0, HERE)
from tokens_generated import TOKENS, FORBIDDEN_HEXES  # noqa: E402
import charts  # noqa: E402


# ── the stylesheet, with the palette poured in from the generated tokens ─────
def stylesheet():
    css = open(os.path.join(HERE, "styles.css")).read()
    variables = "\n  ".join(
        f"--{name.lower().replace(' ', '-')}: {hex_};" for name, hex_ in TOKENS.items()
    )
    css = css.replace("TOKENS_HERE", variables)
    css = css.replace("FONTS/", "file://" + FONTS.replace(" ", "%20") + "/")
    return css


def assert_no_forbidden_colour(css, html):
    """A near-miss brand colour is the failure the tokens exist to prevent, and
    six hexes are named as forbidden. Catch them at build time, not in print."""
    found = set()
    for blob in (css, html):
        for hexcode in re.findall(r"#[0-9A-Fa-f]{6}", blob):
            if hexcode.upper() in FORBIDDEN_HEXES:
                found.add(hexcode.upper())
    if found:
        raise SystemExit(
            "FORBIDDEN COLOUR IN OUTPUT: " + ", ".join(sorted(found)) +
            "\nThese are named as forbidden in brand_tokens. Use the token."
        )


# ── blocks. Each returns HTML. Every visual decision lives in styles.css; these
#    only choose which component a piece of content is. ──────────────────────
def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if s is not None else "")


import re as _re

def rich(s):
    """Content may carry <b>, <i>, <br> and HTML entities, and nothing else.
    Headlines break where the writer breaks them (settled #169), so <br> has to
    survive. Entities have to survive too: escaping the ampersand in &nbsp;
    prints the entity as literal text, which is what the first v2 render did."""
    out = esc(s)
    for tag in ("b", "i"):
        out = out.replace(f"&lt;{tag}&gt;", f"<{tag}>").replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    out = out.replace("&lt;br&gt;", "<br>")
    # put back any entity the author wrote deliberately (&nbsp; &mdash; &amp; ...)
    return _re.sub(r"&amp;(#?\w{1,8});", r"&\1;", out)


def block(b):
    kind = b["type"]

    if kind == "lede":
        return f'<div class="lede">{rich(b["text"])}</div>'

    if kind == "para":
        return f'<p>{rich(b["text"])}</p>'

    if kind == "h2":
        return f'<div class="h2">{rich(b["text"])}</div>'

    if kind == "eyebrow":
        return f'<div class="eyebrow">{rich(b["text"])}</div>'

    if kind == "panel":
        # ground says what the panel MEANS: evidence, decision, or nested.
        cls = ["panel", f'panel--{b.get("ground", "evidence")}']
        if b.get("rail") == "sunrise":
            cls.append("panel--rail")
        elif b.get("rail") == "navy":
            cls.append("panel--rail-quiet")
        inner = ""
        if b.get("label"):
            inner += f'<div class="panel--label">{rich(b["label"])}</div>'
        if b.get("heading"):
            inner += f'<div class="h2">{rich(b["heading"])}</div>'
        for p in b.get("paras", []):
            inner += f"<p>{rich(p)}</p>"
        return f'<div class="{" ".join(cls)}">{inner}</div>'

    if kind == "cards":
        out = ['<div class="cards">']
        for c in b["items"]:
            cls = "card card--set-apart" if c.get("set_apart") else "card"
            inner = ""
            if c.get("eyebrow"):
                inner += f'<div class="eyebrow">{rich(c["eyebrow"])}</div>'
            if c.get("heading"):
                inner += f'<div class="h2">{rich(c["heading"])}</div>'
            for p in c.get("paras", []):
                inner += f"<p>{rich(p)}</p>"
            # A finding that stops at "why it matters" tells the reader something
            # is true and nothing about what we would do. The second footer is
            # the whole point of the value-selling pass.
            if c.get("why") and c.get("how"):
                inner += ('<div class="foot2">'
                          f'<div><div class="lbl">Why it matters</div>{rich(c["why"])}</div>'
                          f'<div><div class="lbl">How ERA helps</div>{rich(c["how"])}</div>'
                          '</div>')
            elif c.get("why"):
                inner += f'<div class="why"><b>Why it matters:</b> {rich(c["why"])}</div>'
            out.append(f'<div class="{cls}">{inner}</div>')
        out.append("</div>")
        return "".join(out)

    if kind == "stats":
        out = ['<div class="stats">']
        for s in b["items"]:
            cls = "stat stat--lead" if s.get("lead") else "stat"
            out.append(
                f'<div class="{cls}"><div class="fig">{rich(s["figure"])}</div>'
                f'<div class="lab">{rich(s["label"])}</div>'
                f'<div class="note">{rich(s.get("note", ""))}</div></div>'
            )
        out.append("</div>")
        return "".join(out)

    if kind == "table":
        # Explicit widths. Left to itself the browser algorithm starves the
        # category column — the one the reader anchors on — and lets the
        # numeric columns sprawl. The review is explicit that the category name
        # is the visual anchor and figures are tabular.
        cols_ = "".join(
            f'<col style="width:{c["width"]}">' if c.get("width") else "<col>"
            for c in b["columns"]
        )
        head = "".join(
            f'<th{" class=num" if c.get("num") else ""}>{rich(c["label"])}</th>'
            for c in b["columns"]
        )
        body = ""
        for r in b["rows"]:
            rcls = " ".join(filter(None, [r.get("emphasis")]))
            cells = ""
            for c, v in zip(b["columns"], r["cells"]):
                cls = []
                if c.get("num"):
                    cls.append("num")
                if isinstance(v, dict):
                    cls.append(v.get("class", ""))
                    text = rich(v.get("text", ""))
                else:
                    text = rich(v)
                if c.get("anchor"):
                    cls.append("cat")
                    if r.get("sub"):
                        text += f'<span class="sub">{rich(r["sub"])}</span>'
                cells += f'<td class="{" ".join(filter(None, cls))}">{text}</td>'
            body += f'<tr class="{rcls}">{cells}</tr>'
        return (f"<table><colgroup>{cols_}</colgroup>"
                f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")

    if kind == "cols":
        inner = "".join(
            "<div>" + "".join(block(x) for x in col) + "</div>" for col in b["columns"]
        )
        return f'<div class="cols">{inner}</div>'

    if kind == "rows":
        items = "".join(f'<div class="row">{rich(r)}</div>' for r in b["items"])
        return f'<div class="rows">{items}</div>'

    if kind == "closing":
        inner = ""
        if b.get("heading"):
            inner += f'<div class="h2">{rich(b["heading"])}</div>'
        for p in b.get("paras", []):
            inner += f"<p>{rich(p)}</p>"
        return f'<div class="closing">{inner}</div>'

    if kind == "prov":
        return f'<div class="prov">{rich(b["text"])}</div>'

    if kind == "chart":
        # Every chart carries a sentence-level takeaway above it and a source or
        # calculation note beneath, per the whitespace plan. A chart without a
        # takeaway is decoration, and decoration is what fills a page instead of
        # answering the question the copy left open.
        fn = getattr(charts, b["chart"])
        svg = fn(**b.get("args", {}))
        out = '<div class="fig-wrap">'
        if b.get("takeaway"):
            out += f'<div class="fig-take">{rich(b["takeaway"])}</div>'
        out += svg
        if b.get("note"):
            out += f'<div class="fig-note">{rich(b["note"])}</div>'
        return out + "</div>"

    raise SystemExit(f"unknown block type {kind!r} — add it to block() in engine.py")


def sheet_html(s, org, vti_src, density=1.0):
    """One content sheet. Its header and foot are running elements: they become
    this page's furniture and stay correct if the content flows to a second page."""
    head = (
        f'<div class="hdr"><div class="who">{esc(org)}</div>'
        f'<div class="what">{esc(s["title"])}</div>'
        f'<div class="from">{esc(s.get("source", ""))}</div></div>'
    )
    body = ""
    if s.get("headline"):
        body += f'<div class="h1">{rich(s["headline"])}</div>'
    body += "".join(block(b) for b in s["blocks"])
    # The page number is a CSS counter, not a value computed here: the physical
    # page count is only known at layout time, and a sheet is allowed to run
    # onto a second page. The measured original printed "PAGE 3 OF 16" on a
    # document that delivered ten numbered pages, which is what happens when
    # the total is written down instead of counted.
    foot = (
        f'<div class="ftr"><img src="{vti_src}" alt="Value Through Insight">'
        f'<div class="who">{esc(org)}</div>'
        f'<div class="pg"></div></div>'
    )
    return f'<div class="sheet" style="--rh:{density}">{head}{foot}{body}</div>'


def _document(html_body, css):
    return (f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{css}</style>"
            f"</head><body>{html_body}</body></html>")


def _measure(html_body, css):
    """Pages, and how full the EMPTIEST of them is.

    The first cut measured the last page only, and optimised it to 87% by pushing
    air onto the pages in front — which just moves the hole. What a reader calls
    white space is the emptiest page in the sheet, so that is the number to
    maximise. Every sheet carries break-after:page, so a sheet paginates the same
    alone as it does in the document; that is what makes fitting one sheet at a
    time sound rather than a guess about its neighbours."""
    import io

    import pymupdf
    from weasyprint import HTML

    buf = io.BytesIO()
    HTML(string=_document(html_body, css), base_url=REPO).write_pdf(buf)
    doc = pymupdf.open(stream=buf.getvalue(), filetype="pdf")
    fills = []
    for page in doc:
        limit = page.rect.height - 40                   # above the running footer
        ink = [b[3] for b in page.get_text("blocks") if b[4].strip()]
        ink += [d["rect"].y1 for d in page.get_drawings()]
        ink = [y for y in ink if y < limit]
        fills.append((max(ink) if ink else 0) / limit)
    return doc.page_count, min(fills)


def fit(sheet, org, vti, css, floor=0.82):
    """Choose this sheet's rhythm. Nothing here touches a word or a type size.

    Two moves, in this order:
      1. TIGHTEN, only if the sheet spills. A sheet that runs 15pt past its page
         costs a whole further page, and that page comes back 40% full.
      2. LOOSEN otherwise — including a ONE-page sheet that ends at 40%. The
         first cut of this returned early on any single-page sheet, on the
         reasoning that there is no break to move. There isn't; but there is a
         page to fill, and a one-page sheet ending at 40% is exactly the white
         space being complained about. v1 is seventeen one-page sheets, so that
         early return skipped the entire document.
    A sheet already full enough is left at --rh:1 exactly."""
    base, pages, fill = _try(sheet, org, vti, css, 1.0)
    if fill >= floor:
        return base, pages, fill, None

    if pages > 1:
        for rh in (0.94, 0.88, 0.82, 0.76, 0.70):
            html, n, f = _try(sheet, org, vti, css, rh)
            if n < pages:
                return html, n, f, rh

    best = (base, pages, fill, None)
    for rh in (1.08, 1.16, 1.24, 1.32, 1.40, 1.45):   # 1.45 is the cap: past it the
        # rhythm of one sheet stops matching the rest of the document, and John
        # asked for components that read the same throughout.
        html, n, f = _try(sheet, org, vti, css, rh)
        if n > pages:
            break                      # past the point where it costs a page
        if f > best[2]:
            best = (html, n, f, rh)
    return best


def _try(sheet, org, vti, css, rh):
    html = sheet_html(sheet, org, vti, rh)
    n, f = _measure(html, css)
    return html, n, f


def render_interior(content, out_pdf, fit_pass=True):
    from weasyprint import HTML

    org = content["organization"]
    vti = "file://" + os.path.join(REPO, content["vti_lockup"]).replace(" ", "%20")
    sheets = content["sheets"]
    css = stylesheet()

    parts, report = [], []
    for i, sheet in enumerate(sheets, 1):
        if fit_pass:
            html, pages, fill, density = fit(sheet, org, vti, css)
        else:
            html = sheet_html(sheet, org, vti)
            pages, fill = _measure(html, css)
            density = None
        parts.append(html)
        report.append((i, pages, fill, density))

    html_body = "".join(parts)
    assert_no_forbidden_colour(css, html_body)
    HTML(string=_document(html_body, css), base_url=REPO).write_pdf(out_pdf)
    for i, pages, fill, density in report:
        if density or pages > 1:
            print(f"  sheet {i:>2}: {pages}pp, emptiest page {fill*100:.0f}% full"
                  + (f"  [rhythm x{density}]" if density else ""))
    return len(sheets)


# ── imposition. Computed from the rendered length, both ways, same content. ──
def impose(cover, letter, interior, back, mode, out_pdf):
    from pypdf import PdfReader, PdfWriter

    w = PdfWriter()

    def add(path):
        if not path or not os.path.exists(path):
            return 0
        r = PdfReader(path)
        for p in r.pages:
            w.add_page(p)
        return len(r.pages)

    def blank():
        # a real blank leaf, the same trim size as the rest
        r = PdfReader(interior)
        w.add_blank_page(width=r.pages[0].mediabox.width,
                         height=r.pages[0].mediabox.height)

    if mode == "stitched":
        # cover and letter each open on a recto, so each gets a blank verso.
        add(cover);  blank()
        add(letter); blank()
        n = add(interior)
        # the back cover is the last leaf; pad before it so the whole booklet is
        # a multiple of four. Solved from the real length, not written down.
        used = 4 + n + 1
        pad = (-used) % 4
        for _ in range(pad):
            blank()
        add(back)
    else:
        add(cover); add(letter); add(interior); add(back)

    with open(out_pdf, "wb") as fh:
        w.write(fh)
    return len(w.pages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("--mode", choices=["plain", "stitched", "both"], default="both")
    ap.add_argument("--outdir", default=os.path.join(HERE, "out"))
    ap.add_argument("--cover", help="pre-rendered cover PDF from cover/cover_page_engine.py")
    ap.add_argument("--letter", help="pre-rendered letter PDF from cover/cover_engine.py")
    ap.add_argument("--back", help="pre-rendered back cover PDF")
    a = ap.parse_args()

    content = json.load(open(a.content if os.path.isabs(a.content)
                             else os.path.join(HERE, a.content)))
    os.makedirs(a.outdir, exist_ok=True)
    interior = os.path.join(a.outdir, "interior.pdf")
    n = render_interior(content, interior)
    print(f"interior: {n} content sheets")

    modes = ["plain", "stitched"] if a.mode == "both" else [a.mode]
    for mode in modes:
        out = os.path.join(a.outdir, f"EOR_{content['slug']}_{mode}.pdf")
        total = impose(a.cover, a.letter, interior, a.back, mode, out)
        print(f"{mode:>8}: {total} leaves -> {out}")


if __name__ == "__main__":
    main()
