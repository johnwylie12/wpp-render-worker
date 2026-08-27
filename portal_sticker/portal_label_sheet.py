#!/usr/bin/env python3
"""
Portal QR labels, FOUR PER SHEET on US Letter.

WHY THIS EXISTS SEPARATELY FROM portal_sticker.py
-------------------------------------------------
portal_sticker renders ONE 6x4 label per page, to be printed on 6x4 sticker
stock and bound into a package. That is the right shape when the worker is
assembling a single package. It is the wrong shape for a print run: 45 accounts
means 45 pages of single labels and 45 sheets of expensive stock.

This lays the SAME information out as a 2x2 grid of quarter-sheet (4.25 x 5.5)
cells on plain Letter, with cut lines on the cell boundaries. Cut on the lines
and you have four labels; run it on full-sheet label stock and you have four
stickers. No label-stock SKU is assumed, because guessing one wrong wastes the
whole run.

PARTNER-NEUTRAL BY CONSTRUCTION. A portal label carries the ACCOUNT's address
and code and nothing about who mailed it, so one sheet is correct for any
partner. The book-a-meeting label is the partner-identity piece and lives in
portal_sticker._draw_meeting_side, which refuses to print without that
partner's own booking_url.

THE ADDRESS IS NOT BUILT HERE. url and code both come from the database
(portal_for_account -> portal_url_for). This module concatenates no host, adds
no path, and appends no query. Per CLAUDE.md a portal address has exactly one
author and it is not this file.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

NAVY = (0x00 / 255, 0x3A / 255, 0x70 / 255)
GOLD = (0xFF / 255, 0x9C / 255, 0x00 / 255)
WHITE = (1, 1, 1)
HAIR = (0.72, 0.72, 0.72)

PAGE_W, PAGE_H = letter                 # 612 x 792 pt
COLS, ROWS = 2, 2
# Consumer laser and inkjet printers cannot print to the sheet edge -- roughly a
# quarter inch is mechanically unreachable. A full-bleed quarter-sheet grid would
# put the navy header band of the top row and the logo of the bottom row inside
# that dead zone and they would come out clipped, on every sheet, at every one of
# these printers. So the grid is inset and the cells are slightly under quarter
# sheet. Cutting still yields four identical labels.
MARGIN = 0.25 * inch
GRID_W, GRID_H = PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN
CELL_W, CELL_H = GRID_W / COLS, GRID_H / ROWS
PER_SHEET = COLS * ROWS

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "meeting_label", "assets", "era_logo.png")


def _qr(c, url, x, y, size):
    w = QrCodeWidget(url, barLevel="M")
    b = w.getBounds()
    d = Drawing(size, size,
                transform=[size / (b[2] - b[0]), 0, 0, size / (b[3] - b[1]), 0, 0])
    d.add(w)
    renderPDF.draw(d, c, x, y)


def _fit(c, text, font, size, max_w, min_size=6.0):
    """Shrink until it fits. An account name is not allowed to run off its label."""
    while size > min_size and c.stringWidth(text, font, size) > max_w:
        size -= 0.5
    return size


def _draw_label(c, x, y, url, code, org_name, display):
    """One quarter-sheet label with its origin at (x, y)."""
    pad = 0.32 * inch
    inner_w = CELL_W - 2 * pad

    # header band
    band_h = 0.46 * inch
    c.setFillColorRGB(*NAVY)
    c.rect(x, y + CELL_H - band_h, CELL_W, band_h, stroke=0, fill=1)
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(x + pad, y + CELL_H - 0.30 * inch, "Your numbers, online")
    c.setFillColorRGB(*GOLD)
    c.setFont("Helvetica-BoldOblique", 6.5)
    c.drawRightString(x + CELL_W - pad, y + CELL_H - 0.30 * inch, "VALUE THROUGH INSIGHT™")

    # who this label belongs to -- the collator's only way to match label to package
    c.setFillColorRGB(*NAVY)
    name = (org_name or "").strip()
    if name:
        size = _fit(c, name, "Helvetica-Bold", 9.5, inner_w)
        c.setFont("Helvetica-Bold", size)
        c.drawString(x + pad, y + CELL_H - band_h - 0.24 * inch, name)

    # QR, centred
    qr = 2.05 * inch
    qr_y = y + CELL_H - band_h - 0.42 * inch - qr
    _qr(c, url, x + (CELL_W - qr) / 2.0, qr_y, qr)

    # typeable fallback
    ty = qr_y - 0.30 * inch
    c.setFillColorRGB(*NAVY)
    c.setFont("Helvetica", 9)
    c.drawCentredString(x + CELL_W / 2.0, ty, "Scan for the full benchmark — shareable with your CFO.")
    ty -= 0.34 * inch
    c.setFont("Helvetica", 8)
    c.drawCentredString(x + CELL_W / 2.0, ty, "Or type the code:")
    ty -= 0.30 * inch
    c.setFont("Courier-Bold", 19)
    c.drawCentredString(x + CELL_W / 2.0, ty, code)
    if display:
        ty -= 0.24 * inch
        size = _fit(c, display, "Helvetica", 7.5, inner_w)
        c.setFont("Helvetica", size)
        c.drawCentredString(x + CELL_W / 2.0, ty, display)

    if os.path.exists(LOGO):
        try:
            c.drawImage(LOGO, x + pad, y + 0.26 * inch, width=0.95 * inch,
                        height=0.95 * inch * (478.0 / 1043.0), mask="auto")
        except Exception:
            pass


def _cut_lines(c):
    """Drawn AFTER the labels. Drawn before, the navy header bands paint over
    them and the guide vanishes exactly where the blade needs it."""
    c.setStrokeColorRGB(*HAIR)
    c.setLineWidth(0.4)
    c.setDash(3, 3)
    c.line(MARGIN + CELL_W, MARGIN, MARGIN + CELL_W, MARGIN + GRID_H)
    c.line(MARGIN, MARGIN + CELL_H, MARGIN + GRID_W, MARGIN + CELL_H)
    c.setDash()


def render_label_sheets(labels, out_pdf):
    """labels: [{url, code, name}] in print order. Returns (out_pdf, n_pages).

    An entry missing url or code RAISES. A blank label is worse than a missing
    one: it looks like a label, gets stuffed in an envelope, and leads the
    prospect nowhere. Provision the portal first.
    """
    rows = list(labels)
    if not rows:
        raise ValueError("no labels to render")
    for i, r in enumerate(rows, 1):
        if not (r.get("url") or "").strip() or not (r.get("code") or "").strip():
            raise ValueError(
                "label %d (%s) has no portal url/code -- refusing to print a "
                "label that leads nowhere" % (i, r.get("name") or "?"))

    c = canvas.Canvas(out_pdf, pagesize=letter)
    pages = 0
    for start in range(0, len(rows), PER_SHEET):
        chunk = rows[start:start + PER_SHEET]
        for slot, r in enumerate(chunk):
            col, row = slot % COLS, slot // COLS
            x = MARGIN + col * CELL_W
            # fill top-left, top-right, then down -- reading order, so the print
            # order on the collation sheet is the order they come off the stack
            y = MARGIN + GRID_H - (row + 1) * CELL_H
            _draw_label(c, x, y, r["url"], r["code"], r.get("name"), r.get("display"))
        _cut_lines(c)
        c.showPage()
        pages += 1
    c.save()
    return out_pdf, pages
