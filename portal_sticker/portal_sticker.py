import wpp_partner as _partner
#!/usr/bin/env python3
"""
ERA / WPP — package insert sticker, 6" W x 4" H, TWO PAGES (duplex = two-sided):
  SIDE A (navy)  = book-a-meeting QR (the existing pattern from meeting_label) +
                   "Let's start a conversation" + contact block.
  SIDE B (white) = PORTAL QR carrying the full /p/<code> URL, plus the 7-character
                   code in large readable type as the typeable fallback.

Rendered INTO the package build (appended after the closing page, footer-exempt)
so a package can never ship without its portal code. QR via reportlab's bundled
QrCodeWidget — no new dependency. Print at 100% / Actual Size on sticker stock.
"""
import os
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

NAVY = (0x00 / 255, 0x3A / 255, 0x70 / 255)
GOLD = (0xFF / 255, 0x9C / 255, 0x00 / 255)
WHITE = (1, 1, 1)

# BOOK_URL / C_NAME / C_TITLE / C_PHONE / C_EMAIL used to live here, all five
# hardcoded to John. Decision #78 made them per-partner: every one now arrives
# through partner_signoff (partner_signature.booking_url + wpp_signoff). Keeping
# a copy here would be a second answer to a question the database now owns --
# the exact shape of defect this module was rewritten to remove.

PAGE_W, PAGE_H = 6.0 * inch, 4.0 * inch

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "meeting_label", "assets", "era_logo.png")


def _qr(c, url, x, y, size):
    w = QrCodeWidget(url, barLevel="M")   # black modules on the white quiet zone
    b = w.getBounds()
    d = Drawing(size, size, transform=[size / (b[2] - b[0]), 0, 0, size / (b[3] - b[1]), 0, 0])
    d.add(w)
    renderPDF.draw(d, c, x, y)


def _draw_meeting_side(c, p):
    """SIDE A — navy, book-a-meeting. Every identity field comes from the partner.

    These were module constants (C_NAME/C_TITLE/C_PHONE/C_EMAIL and BOOK_URL) all
    pointing at John. A partner mailing this unchanged sends every prospect who
    scans it to John's calendar.
    """
    c.setFillColorRGB(*NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    qr_size = 2.1 * inch
    pad = (PAGE_H - qr_size) / 2.0
    c.setFillColorRGB(*WHITE)
    c.rect(0.45 * inch, pad, qr_size + 0.3 * inch, qr_size + 0.0 * inch, stroke=0, fill=1)
    _qr(c, p["booking_url"], 0.6 * inch, pad + 0.0 * inch, qr_size)
    tx = 3.15 * inch
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(tx, PAGE_H - 1.1 * inch, "Let's start a")
    c.drawString(tx, PAGE_H - 1.35 * inch, "conversation")
    c.setFont("Helvetica", 10)
    c.drawString(tx, PAGE_H - 1.85 * inch, p["name"])
    c.drawString(tx, PAGE_H - 2.05 * inch, p["title_line"])
    c.drawString(tx, PAGE_H - 2.25 * inch, p["phone"])
    c.drawString(tx, PAGE_H - 2.45 * inch, p["email"])
    c.setFillColorRGB(*GOLD)
    c.setFont("Helvetica-BoldOblique", 9)
    c.drawString(tx, 0.55 * inch, "VALUE THROUGH INSIGHT\u2122")
    c.showPage()


def render_sticker(portal_url: str, code: str, out_pdf: str, *, partner_signoff=None,
                   include_meeting_side: bool = True) -> str:
    """Side A = book-a-meeting (partner identity), side B = portal QR + short code.

    SIDE B IS PARTNER-NEUTRAL. It carries the account's own portal QR and typeable
    code and is identical whoever mails it. Side A is entirely partner identity.

    include_meeting_side=False prints side B only -- the honest output for a
    partner not yet set up to take bookings: a portal label with no meeting page,
    rather than a meeting page belonging to someone else.
    """
    if not portal_url or not code:
        raise ValueError("portal sticker requires portal_url and code")
    c = canvas.Canvas(out_pdf, pagesize=(PAGE_W, PAGE_H))

    if include_meeting_side:
        # need_booking raises when the partner has no booking_url, so a stray
        # include_meeting_side=True can never fall back to John's link.
        _draw_meeting_side(c, _partner.normalize(partner_signoff, need_signature=False,
                                                 need_booking=True))

    # ---- SIDE B — white, the portal QR + typeable short code ----
    c.setFillColorRGB(*WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColorRGB(*NAVY)
    c.rect(0, PAGE_H - 0.55 * inch, PAGE_W, 0.55 * inch, stroke=0, fill=1)
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(0.45 * inch, PAGE_H - 0.38 * inch, "Your numbers, online")
    c.setFillColorRGB(*GOLD)
    c.setFont("Helvetica-BoldOblique", 8)
    c.drawRightString(PAGE_W - 0.45 * inch, PAGE_H - 0.38 * inch, "VALUE THROUGH INSIGHT™")

    qr_size_b = 2.0 * inch
    _qr(c, portal_url, 0.55 * inch, 0.75 * inch, qr_size_b)
    txb = 2.95 * inch
    c.setFillColorRGB(*NAVY)
    c.setFont("Helvetica", 10.5)
    c.drawString(txb, 2.55 * inch, "Scan for the full benchmark —")
    c.drawString(txb, 2.36 * inch, "shareable with your CFO.")
    c.setFont("Helvetica", 9.5)
    c.drawString(txb, 1.95 * inch, "Or type the code:")
    c.setFont("Courier-Bold", 26)
    c.drawString(txb, 1.5 * inch, code)
    c.setFont("Helvetica", 9.5)
    host = portal_url.split("/p/")[0].replace("https://", "").replace("http://", "")
    c.drawString(txb, 1.12 * inch, "%s/p/%s" % (host, code))
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
    import sys
    # Side B only: this smoke test has no partner, and side A without one is
    # exactly the unattributed print the module refuses to make.
    render_sticker(sys.argv[1] if len(sys.argv) > 1 else "https://example.com/p/K7M2Q9R",
                   sys.argv[2] if len(sys.argv) > 2 else "K7M2Q9R",
                   sys.argv[3] if len(sys.argv) > 3 else "/tmp/portal_sticker.pdf",
                   include_meeting_side=False)
    print("ok")
