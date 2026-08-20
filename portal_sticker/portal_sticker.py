#!/usr/bin/env python3
"""
ERA / WPP — package insert sticker, 6" W x 4" H, TWO PAGES (duplex = two-sided):
  SIDE A (navy)  = book-a-meeting QR (the existing pattern from meeting_label) +
                   "Let's start a conversation" + contact block.
  SIDE B (white) = PORTAL QR carrying the full coded URL, plus the ACCESS CODE
                   in large readable type as the typeable fallback.

NOT bound into the package (2026-08-19). The EOP ends on the closing page; the
quarter-sheet portal label goes loose in the folder instead. This module stays
so the pattern below is what any future card component copies.

Access-code contract
--------------------
`prospect_portals.code` is the INTERNAL record id (e.g. LJ6HXUE) and must NEVER
be printed. `prospect_portals.access_code` (e.g. DQJ3KQK) is what a prospect
types to get in. 169 of 169 portals carry two different values, so printing
`code` locks the reader out every single time. This module takes access_code and
has no parameter that could carry `code`.

Signoff title comes from brand_canon (wpp_canon.signoff), never a literal.

QR via reportlab's bundled QrCodeWidget — no new dependency. Print at 100% /
Actual Size on sticker stock.
"""
import os
import sys

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wpp_canon import signoff, signoff_title_org  # noqa: E402

NAVY = (0x00 / 255, 0x3A / 255, 0x70 / 255)
GOLD = (0xFF / 255, 0x9C / 255, 0x00 / 255)
WHITE = (1, 1, 1)

BOOK_URL = ("https://outlook.office.com/bookwithme/user/"
            "7aa3d169518c4b1caeb9f72a2f23f9d8@eragroup.com/"
            "meetingtype/CMjo2-07uk2-Q0n_F1MSvQ2"
            "?anonymous&ismsaljsauthenabled&ep=mcard")

PORTAL_HOST = "portal.wpp-us.com"

PAGE_W, PAGE_H = 6.0 * inch, 4.0 * inch

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "meeting_label", "assets", "era_logo.png")


def _qr(c, url, x, y, size):
    w = QrCodeWidget(url, barLevel="M")   # black modules on the white quiet zone
    b = w.getBounds()
    d = Drawing(size, size, transform=[size / (b[2] - b[0]), 0, 0, size / (b[3] - b[1]), 0, 0])
    d.add(w)
    renderPDF.draw(d, c, x, y)


def _portal_lines(portal_url, access_code, subdomain=None):
    """(printed_url, access_code) for side B.

    The QR encodes the full coded URL so a scan opens straight in; the printed
    line is the clean shared-domain form from the rev-5 URL canon
    (portal.wpp-us.com/{slug}) with the ACCESS CODE beneath it. Never `code`.
    """
    url = (portal_url or "").strip()
    sub = (subdomain or "").strip()
    if not sub and url:
        host_path = url.split("://", 1)[-1].split("?", 1)[0].rstrip("/")
        if "/" in host_path:            # shared host: portal.wpp-us.com/{slug}
            sub = host_path.split("/", 1)[1]
        else:                            # legacy: {slug}.wpp-us.com
            sub = host_path.split(".", 1)[0]
    printed = "%s/%s" % (PORTAL_HOST, sub) if sub else PORTAL_HOST
    return printed, access_code


def render_sticker(portal_url: str, access_code: str, out_pdf: str,
                   subdomain: str = None) -> str:
    """Two 6x4 pages: side A = book-a-meeting, side B = portal QR + access code.

    access_code is `prospect_portals.access_code` — what the prospect types.
    Passing `prospect_portals.code` here prints a code that does not open the
    portal; there is deliberately no parameter for it.
    """
    if not portal_url or not access_code:
        raise ValueError("portal sticker requires portal_url and access_code")
    so = signoff()
    c = canvas.Canvas(out_pdf, pagesize=(PAGE_W, PAGE_H))

    # ---- SIDE A — navy, book-a-meeting (existing QR pattern) ----
    c.setFillColorRGB(*NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    qr_size = 2.1 * inch
    pad = (PAGE_H - qr_size) / 2.0
    c.setFillColorRGB(*WHITE)
    c.rect(0.45 * inch, pad, qr_size + 0.3 * inch, qr_size + 0.0 * inch, stroke=0, fill=1)
    _qr(c, BOOK_URL, 0.6 * inch, pad + 0.0 * inch, qr_size)
    tx = 3.15 * inch
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(tx, PAGE_H - 1.1 * inch, "Let's start a")
    c.drawString(tx, PAGE_H - 1.35 * inch, "conversation")
    c.setFont("Helvetica", 10)
    c.drawString(tx, PAGE_H - 1.85 * inch, so["name"])
    c.drawString(tx, PAGE_H - 2.05 * inch, signoff_title_org())
    c.drawString(tx, PAGE_H - 2.25 * inch, so["phone"])
    c.drawString(tx, PAGE_H - 2.45 * inch, so["email"])
    c.setFillColorRGB(*GOLD)
    c.setFont("Helvetica-BoldOblique", 9)
    c.drawString(tx, 0.55 * inch, "VALUE THROUGH INSIGHT\u2122")
    c.showPage()

    # ---- SIDE B — white, the portal QR + typeable ACCESS CODE ----
    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColorRGB(*NAVY)
    c.rect(0, PAGE_H - 0.55 * inch, PAGE_W, 0.55 * inch, stroke=0, fill=1)
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(0.45 * inch, PAGE_H - 0.38 * inch, "Your numbers, online")
    c.setFillColorRGB(*GOLD)
    c.setFont("Helvetica-BoldOblique", 8)
    c.drawRightString(PAGE_W - 0.45 * inch, PAGE_H - 0.38 * inch, "VALUE THROUGH INSIGHT\u2122")

    printed_url, typed = _portal_lines(portal_url, access_code, subdomain)
    qr_size_b = 2.0 * inch
    _qr(c, portal_url, 0.55 * inch, 0.75 * inch, qr_size_b)
    txb = 2.95 * inch
    c.setFillColorRGB(*NAVY)
    c.setFont("Helvetica", 10.5)
    c.drawString(txb, 2.55 * inch, "Scan for the full benchmark \u2014")
    c.drawString(txb, 2.36 * inch, "shareable with your CFO.")
    c.setFont("Helvetica", 9.5)
    c.drawString(txb, 1.95 * inch, "Or type the access code:")
    c.setFont("Courier-Bold", 26)
    c.drawString(txb, 1.5 * inch, typed)
    c.setFont("Helvetica", 9.5)
    c.drawString(txb, 1.12 * inch, printed_url)
    if os.path.exists(LOGO):
        try:
            c.drawImage(LOGO, txb, 0.5 * inch, width=1.1 * inch,
                        height=1.1 * inch * (478.0 / 1043.0), mask="auto")
        except Exception:
            pass
    c.showPage()
    c.save()
    return out_pdf


if __name__ == "__main__":
    render_sticker(sys.argv[1] if len(sys.argv) > 1 else "https://portal.wpp-us.com/demo-benchmark?c=HAC3E9T",
                   sys.argv[2] if len(sys.argv) > 2 else "HAC3E9T",
                   sys.argv[3] if len(sys.argv) > 3 else "/tmp/portal_sticker.pdf")
    print("ok")
