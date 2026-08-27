#!/usr/bin/env python3
"""
WPP Portal Label — the LOCKED generator, 4-up.

THIS IS A PORT, NOT A DESIGN. The original is
`WPP-Prospecting-App/code-copies/claude_WPP_portal_label_generator_LOCKED.py`,
locked 2026-08-04 after what its spec calls "a long, painful calibration"
(working-docs-b/claude_WPP_PORTAL_LABEL_spec_and_print_workflow_2026-08-03.md).
Every number below -- page size, padding, point sizes, the 0.10 cell inset, the
rotate=90 -- is copied from it. Do not re-derive any of them.

  Stock : Spartan Industrial 4x6 individual labels, 4-up on 8.5x11, 2x2.
  Label : designed landscape 5.5in x 4.25in, rotated 90 into a 4.25 x 5.5 cell,
          scaled to 80% of the cell and centred (full bleed ran off the die-cut
          edges; 90% still touched them; 80% is the lock).
  Print : 100% / Actual Size, never fit-to-page.

WHAT CHANGED FROM THE ORIGINAL, AND ONLY THIS:
  * Assets. The original read two PNGs from a chat-upload directory that no
    longer exists. The same two logos are in the app repo at
    public/portal/era-group-logo.png and public/portal/vti-blue.png.
  * Input. It read a fixed /tmp/labels_data.json; this takes a records list.
  * Output. It wrote one fixed filename; this takes a path.

The URL is rev 6 (2026-08-27, John): https://portal.wpp-us.com/{sub}, with NO
access code. This supersedes rev 5 (2026-08-08), which appended ?c={code}. The
printed line under the QR was ALREADY the bare slug under rev 5, so the QR and
the words beneath it pointed at two different addresses; rev 6 makes them one.

The ACCESS CODE block stays on the label. It is how a prospect who types the
address rather than scanning it gets in, and it is still what proves the portal
is provisioned at all.

Already-printed labels are unaffected -- the coded form keeps resolving.
"""
import base64, io, os, re
from PIL import Image, ImageChops
import segno, fitz
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "..", "..", "WPP-Prospecting-App", "public", "portal")
ERA_DEFAULT = os.path.join(APP, "era-group-logo.png")
VTI_DEFAULT = os.path.join(APP, "vti-blue.png")

HEAD = 'Your Brief, live — open every number.'
B1 = ('The analysis in your hands, interactive: your indirect-spend opportunity '
      'line by line — tap any figure for its source and how confident we are.')
B2 = ('Your working room, too — the categories, the results behind them, and a '
      'direct line to me. No form, no ask.')

CSS = '''@page{size:5.5in 4.25in;margin:0;}*{box-sizing:border-box;margin:0;padding:0;}
html,body{font-family:"Trebuchet MS","DejaVu Sans",Verdana,sans-serif;}
.label{width:5.5in;height:4.25in;padding:0.26in 0.30in;display:flex;flex-direction:column;overflow:hidden;page-break-after:always;}
.hdr{display:flex;align-items:center;justify-content:space-between;flex:0 0 auto;}
.era{height:0.44in;} .eyebrow{color:#F2A900;font-weight:bold;font-size:8pt;letter-spacing:2px;text-align:right;line-height:1.25;}
.org{color:#003A70;font-weight:bold;font-size:14.5pt;line-height:1.05;margin-top:0.10in;}
.head{color:#1C5DA8;font-weight:bold;font-size:11.5pt;margin-top:0.04in;}
.mid{display:flex;flex:1 1 auto;min-height:0;margin-top:0.08in;gap:0.18in;}
.body{flex:1;display:flex;flex-direction:column;justify-content:center;}
.body p{color:#4a5867;font-size:10.5pt;line-height:1.45;margin-bottom:0.09in;}
.qrbox{flex:0 0 auto;display:flex;flex-direction:column;align-items:center;justify-content:center;width:1.35in;}
.qr{width:1.25in;height:1.25in;} .aclabel{color:#8794a3;font-size:6.5pt;letter-spacing:1.5px;margin-top:0.05in;}
.accode{color:#003A70;font-weight:bold;font-size:12.5pt;letter-spacing:1px;}
.foot{flex:0 0 auto;display:flex;align-items:center;justify-content:space-between;margin-top:0.05in;}
.scan{color:#3a4a5c;font-size:9pt;} .scan b{color:#003A70;} .vti{height:0.27in;}'''


def _trim(p):
    im = Image.open(p).convert("RGBA")
    w = Image.new("RGBA", im.size, (255, 255, 255, 255))
    diff = ImageChops.difference(Image.alpha_composite(w, im).convert("RGB"),
                                 Image.new("RGB", im.size, (255, 255, 255)))
    bb = diff.getbbox()
    return im.crop(bb) if bb else im


def _uri(im):
    b = io.BytesIO(); im.save(b, format="PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def _qr(t):
    q = segno.make(t, error='m'); b = io.BytesIO()
    q.save(b, kind='png', scale=12, border=1, dark='#003A70', light='#fff')
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def _clean(n):
    n = n.strip()
    for _ in range(3):
        n = re.sub(r'[ ,]+(Inc\.?|Incorporated|Foundation)\s*$', '', n).strip()
    return n


def render(records, out_pdf, workdir, era_png=None, vti_png=None):
    """records: [{name, sub, code}] in print order. Returns (out_pdf, sheets, labels)."""
    if not records:
        raise ValueError("no records")
    for i, r in enumerate(records, 1):
        if not str(r.get("sub") or "").strip() or not str(r.get("code") or "").strip():
            raise ValueError("label %d (%s) has no subdomain/access code -- refusing "
                             "to print a label that leads nowhere" % (i, r.get("name") or "?"))
    era = _uri(_trim(era_png or ERA_DEFAULT))
    vti = _uri(_trim(vti_png or VTI_DEFAULT))

    def label(r):
        n, sub, code = _clean(r['name']), r['sub'], r['code']
        return f'''<div class="label">
  <div class="hdr"><img class="era" src="{era}"/><div class="eyebrow">PREPARED<br/>PRIVATELY FOR</div></div>
  <div class="org">{n}</div><div class="head">{HEAD}</div>
  <div class="mid"><div class="body"><p>{B1}</p><p>{B2}</p></div>
    <div class="qrbox"><img class="qr" src="{_qr(f'https://portal.wpp-us.com/{sub}')}"/>
      <div class="aclabel">ACCESS CODE</div><div class="accode">{code}</div></div></div>
  <div class="foot"><div class="scan">Scan, or visit <b>portal.wpp-us.com/{sub}</b></div><img class="vti" src="{vti}"/></div>
</div>'''

    html = ('<!doctype html><html><head><meta charset="utf-8"><style>' + CSS +
            '</style></head><body>' + "".join(label(r) for r in records) + '</body></html>')
    hp = os.path.join(workdir, "labels.html")
    np_ = os.path.join(workdir, "labels_natural.pdf")
    open(hp, "w").write(html)
    # This image ships Chromium at a pinned build that the pip-installed
    # playwright does not expect, and "playwright install" is not allowed here.
    # Point it at the browser that is actually present instead.
    exe = os.environ.get("CHROMIUM_PATH")
    if not exe:
        for cand in ("/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
                     "/opt/pw-browsers/chromium/chrome-linux/chrome",
                     "/usr/bin/chromium"):
            if os.path.exists(cand):
                exe = cand
                break
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        pg = b.new_page()
        pg.goto("file://" + hp); pg.wait_for_timeout(500)
        pg.pdf(path=np_, prefer_css_page_size=True, print_background=True)
        b.close()

    # composite: 8.5x11, four quarter-sheet cells, each label rotated 90 into its
    # cell. CSS transforms and PIL both failed to rotate reliably; fitz works.
    src = fitz.open(np_); out = fitz.open()
    PW, PH = 8.5 * 72, 11 * 72
    cw, ch = 4.25 * 72, 5.5 * 72
    mx, my = 0.10 * cw, 0.10 * ch
    cells = [fitz.Rect(mx, my, cw - mx, ch - my),
             fitz.Rect(cw + mx, my, PW - mx, ch - my),
             fitz.Rect(mx, ch + my, cw - mx, PH - my),
             fitz.Rect(cw + mx, ch + my, PW - mx, PH - my)]
    for i in range(0, src.page_count, 4):
        pg = out.new_page(width=PW, height=PH)
        for j, r in enumerate(cells):
            if i + j < src.page_count:
                pg.show_pdf_page(r, src, i + j, rotate=90)
    out.save(out_pdf)
    sheets, labels = out.page_count, src.page_count
    out.close(); src.close()
    return out_pdf, sheets, labels
