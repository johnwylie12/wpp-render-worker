#!/usr/bin/env python3
"""
Put 6x4 labels onto letter sheets.

FOUR 6x4 LABELS DO NOT FIT A LETTER SHEET AT 100%. Four of them need 12" x 8"
of area; a letter sheet is 8.5 x 11 and its printable area is smaller still. So
there are exactly two honest answers and this module produces both rather than
silently scaling a LOCKED design and calling it 4-up:

  four_up  -> letter LANDSCAPE, 2x2, each label scaled to fit its cell. The
              scale factor is returned so it can be stated, not hidden.
  two_up   -> letter PORTRAIT, 1x2, each label at EXACT 6x4. True size, which
              is what a locked print asset and a reliably-scanning QR want.

Both draw cut lines and both keep a quarter-inch margin, because consumer
printers cannot reach the sheet edge.
"""
import fitz

IN = 72.0
LETTER_W, LETTER_H = 8.5 * IN, 11.0 * IN
LABEL_W, LABEL_H = 6.0 * IN, 4.0 * IN
MARGIN = 0.25 * IN
HAIR = (0.72, 0.72, 0.72)


def _cut(page, xs, ys, x0, y0, x1, y1):
    for x in xs:
        page.draw_line(fitz.Point(x, y0), fitz.Point(x, y1),
                       color=HAIR, width=0.4, dashes="[3 3] 0")
    for y in ys:
        page.draw_line(fitz.Point(x0, y), fitz.Point(x1, y),
                       color=HAIR, width=0.4, dashes="[3 3] 0")


def _impose(src_path, out_pdf, page_w, page_h, cols, rows, max_scale=None):
    src = fitz.open(src_path)
    grid_w, grid_h = page_w - 2 * MARGIN, page_h - 2 * MARGIN
    cell_w, cell_h = grid_w / cols, grid_h / rows
    scale = min(cell_w / LABEL_W, cell_h / LABEL_H)
    # Never ENLARGE. A 6x4 in a taller cell would otherwise be blown up past
    # true size, which for a locked print asset is as wrong as shrinking it.
    if max_scale is not None:
        scale = min(scale, max_scale)
    w, h = LABEL_W * scale, LABEL_H * scale
    per = cols * rows
    out = fitz.open()
    for start in range(0, src.page_count, per):
        page = out.new_page(width=page_w, height=page_h)
        n = 0
        for slot in range(per):
            idx = start + slot
            if idx >= src.page_count:
                break
            c, r = slot % cols, slot // cols
            # centre each label in its cell so the cut lines have even bleed
            x = MARGIN + c * cell_w + (cell_w - w) / 2
            y = MARGIN + r * cell_h + (cell_h - h) / 2
            page.show_pdf_page(fitz.Rect(x, y, x + w, y + h), src, idx)
            n += 1
        _cut(page,
             [MARGIN + i * cell_w for i in range(1, cols)],
             [MARGIN + i * cell_h for i in range(1, rows)],
             MARGIN, MARGIN, MARGIN + grid_w, MARGIN + grid_h)
    out.save(out_pdf)
    pages = out.page_count
    out.close(); src.close()
    return out_pdf, pages, scale


def four_up(src_path, out_pdf):
    """Letter landscape, 2x2. Scaled -- the factor is returned, state it."""
    return _impose(src_path, out_pdf, LETTER_H, LETTER_W, 2, 2)


def two_up(src_path, out_pdf):
    """Letter portrait, 1x2, at exact 6x4."""
    return _impose(src_path, out_pdf, LETTER_W, LETTER_H, 1, 2, max_scale=1.0)
