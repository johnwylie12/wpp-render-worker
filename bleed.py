"""Add print bleed to an already-rendered PDF without touching its layout.

Each page keeps its exact vector content, trim size and position. It is placed
centred on a larger page, and the bleed ring is filled by extending the page's
own edge pixels outward. White pages get a plain larger page (nothing to
extend); cover and back pages get a thin edge-extension image under the page.

Result per page: MediaBox = BleedBox = trim + 2 * bleed, TrimBox = ArtBox = the
original page, centred. No crop marks.
"""
import io
import os

import numpy as np
import pypdfium2 as pdfium
from PIL import Image
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from pypdf.generic import RectangleObject

RASTER_DPI = 150      # only the ring's colour matters; it is trimmed away
NEAR_WHITE = 250


def _ring_image(page, bleed_px):
    """Edge-extended raster of one page, interior blanked, or None if the ring is white."""
    bitmap = page.render(scale=RASTER_DPI / 72.0)
    img = bitmap.to_pil().convert("RGB")
    arr = np.asarray(img)
    # sample one pixel inside the edge so a half-covered edge pixel never bleeds white
    inner = arr[1:-1, 1:-1]
    padded = np.pad(inner, ((bleed_px + 1, bleed_px + 1), (bleed_px + 1, bleed_px + 1), (0, 0)), mode="edge")
    padded = padded[0:arr.shape[0] + 2 * bleed_px, 0:arr.shape[1] + 2 * bleed_px]
    ring = padded.copy()
    ring[bleed_px:-bleed_px, bleed_px:-bleed_px] = 255
    mask = np.ones(ring.shape[:2], dtype=bool)
    mask[bleed_px:-bleed_px, bleed_px:-bleed_px] = False
    if ring[mask].min() >= NEAR_WHITE:
        return None
    buf = io.BytesIO()
    Image.fromarray(ring).save(buf, format="JPEG", quality=92, subsampling=0)
    buf.seek(0)
    return buf


def add_bleed(src_path, dst_path, bleed_in=0.125):
    b_pt = bleed_in * 72.0
    bleed_px = max(2, int(round(bleed_in * RASTER_DPI)))
    pdf = pdfium.PdfDocument(src_path)
    reader = PdfReader(src_path)
    writer = PdfWriter()
    try:
        for i, src_page in enumerate(reader.pages):
            w = float(src_page.mediabox.width)
            h = float(src_page.mediabox.height)
            W, H = w + 2 * b_pt, h + 2 * b_pt
            new = PageObject.create_blank_page(width=W, height=H)
            ring = _ring_image(pdf[i], bleed_px)
            if ring is not None:
                bg = io.BytesIO()
                c = canvas.Canvas(bg, pagesize=(W, H))
                c.drawImage(ImageReader(ring), 0, 0, width=W, height=H)
                c.showPage()
                c.save()
                bg.seek(0)
                new.merge_page(PdfReader(bg).pages[0])
            new.merge_transformed_page(src_page, Transformation().translate(b_pt, b_pt))
            media = RectangleObject([0, 0, W, H])
            trim = RectangleObject([b_pt, b_pt, b_pt + w, b_pt + h])
            new.mediabox = media
            new.cropbox = media
            new.bleedbox = media
            new.trimbox = trim
            new.artbox = trim
            writer.add_page(new)
    finally:
        pdf.close()
    with open(dst_path, "wb") as fh:
        writer.write(fh)
    return dst_path
