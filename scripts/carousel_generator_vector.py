#!/usr/bin/env python3
"""Vector-only ERA carousel. No raster = tiny file. Base64-able through SQL."""
import os, math, random, base64, sys
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from wpp_assets import logo   # canonical brand-mark resolver; see asset_sources
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

W, H = 1080, 1350
F = "/usr/share/fonts/truetype/dejavu/"

MID = (0x11/255, 0x11/255, 0x27/255)
DAY = (0x00/255, 0x2A/255, 0x52/255)
SEA = (0x3C/255, 0xDB/255, 0xC0/255)
ORN = (0xFF/255, 0x9C/255, 0x00/255)
GRY = (0xB4/255, 0xBC/255, 0xC6/255)
M = 100


def wrap(c, t, f, s, mw):
    c.setFont(f, s); out, line = [], ""
    for w in t.split():
        x = (line + " " + w).strip()
        if c.stringWidth(x, f, s) <= mw: line = x
        else:
            if line: out.append(line)
            line = w
    if line: out.append(line)
    return out


def page(c, seed, base, head, rows=None, sub=None, accent=None, kicker=None, foot=None, hs=56):
    bg = MID if base == "mid" else DAY
    c.setFillColorRGB(*bg); c.rect(0, 0, W, H, fill=1, stroke=0)

    # soft band behind the network
    c.setFillColorRGB(*SEA); c.setFillAlpha(0.05)
    c.circle(W*0.78, H*0.74, W*0.44, fill=1, stroke=0); c.setFillAlpha(1)

    rnd = random.Random(seed)
    pts = [(rnd.uniform(W*0.30, W*1.02), rnd.uniform(H*0.52, H*1.02)) for _ in range(26)]
    c.setStrokeColorRGB(*SEA); c.setLineWidth(0.9); c.setStrokeAlpha(0.30)
    for p in pts:
        for q in sorted(pts, key=lambda q: (q[0]-p[0])**2+(q[1]-p[1])**2)[1:3]:
            if (q[0]-p[0])**2+(q[1]-p[1])**2 < (W*0.20)**2:
                c.line(p[0], p[1], q[0], q[1])
    c.setStrokeAlpha(1); c.setFillColorRGB(*SEA)
    for p in pts:
        c.setFillAlpha(rnd.uniform(0.35, 0.75)); c.circle(p[0], p[1], rnd.uniform(3, 9), fill=1, stroke=0)
    c.setFillAlpha(1)

    # APPROVED ERA dark-field lockup (white wordmark + Sunrise Yellow arc),
    # resolved from brand_assets — never from scratch, never derived.
    from reportlab.lib.utils import ImageReader
    _lw = 186; _lh = int(_lw * 237/520)
    c.drawImage(ImageReader(logo('era_group', 'dark')), M, H-64-_lh, _lw, _lh, mask='auto')
    # Value Through Insight lockup, bottom right
    _vw = 176; _vh = int(_vw * 59/520)
    c.drawImage(ImageReader(logo('value_through_insight', 'dark')), W-M-_vw, 84, _vw, _vh, mask='auto')

    blocks = []
    hl = wrap(c, head, "Helvetica-Bold", hs, W-2*M)
    blocks.append(("h", hl, hs, int(hs*1.20)))
    if rows: blocks.append(("r", rows, 0, 62))
    if sub: blocks.append(("s", wrap(c, sub, "Helvetica", 28, W-2*M), 28, 40))
    if accent: blocks.append(("a", wrap(c, accent, "Helvetica-Bold", 31, W-2*M), 31, 44))
    total = sum(len(b[1])*b[3] + (34 if b[0] != "h" else 0) for b in blocks)
    y = 300 + total

    if kicker:
        c.setFillColorRGB(*ORN); c.setFont("Helvetica-Bold", 24)
        c.drawString(M, y + 46, kicker.upper())

    for kind, lines, size, lead in blocks:
        if kind != "h": y -= 34
        if kind == "h":
            c.setFillColorRGB(1, 1, 1)
            for ln in lines: c.setFont("Helvetica-Bold", size); c.drawString(M, y, ln); y -= lead
        elif kind == "s":
            c.setFillColorRGB(*GRY)
            for ln in lines: c.setFont("Helvetica", size); c.drawString(M, y, ln); y -= lead
        elif kind == "a":
            c.setFillColorRGB(*ORN)
            for ln in lines: c.setFont("Helvetica-Bold", size); c.drawString(M, y, ln); y -= lead
        elif kind == "r":
            for label, val, hi in lines:
                c.setFillColorRGB(*(ORN if hi else GRY)); c.setFont("Helvetica", 26)
                c.drawString(M, y, label)
                c.setFillColorRGB(*(ORN if hi else (1, 1, 1))); c.setFont("Courier-Bold", 36)
                c.drawRightString(W-M, y-4, val)
                c.setStrokeColorRGB(*GRY); c.setStrokeAlpha(0.20); c.setLineWidth(0.8)
                c.line(M, y-22, W-M, y-22); c.setStrokeAlpha(1)
                y -= 62
    if foot:
        c.setFillColorRGB(*GRY); c.setFillAlpha(0.7); c.setFont("Helvetica", 21)
        c.drawString(M, 92, foot); c.setFillAlpha(1)
    c.showPage()


def build(path, slides, seed0=11, base="mid"):
    c = canvas.Canvas(path, pagesize=(W, H))
    c.setTitle("ERA Group")
    for i, s in enumerate(slides):
        page(c, seed0 + i*17, base, **s)
    c.save()
    return path
