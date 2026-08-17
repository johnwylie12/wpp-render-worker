#!/usr/bin/env python3
"""
ERA / WPP — package insert sticker, 6" W x 4" H, TWO PAGES (duplex = two-sided):
  SIDE A (navy)  = book-a-meeting QR (the existing pattern from meeting_label) +
                   "Let's start a conversation" + contact block.
  SIDE B (white) = PORTAL QR carrying the branded portal URL, plus the typeable
                   access code and the display URL as the human-readable fallback.

URL SCHEME (rev-5, 2026-08-08 — matches src/lib/portalCode.ts and the cover
letter): the portal lives at

    https://portal.wpp-us.com/{subdomain}?c={access_code}

The QR encodes that exact URL. The printed text shows the display URL
(portal.wpp-us.com/{subdomain}) and the access code that the ?c= param carries —
so the code you TYPE and the code in the URL are the SAME. Both are derived from
the one portal_url the QR uses, so the label can never drift from the link again.
(The old template rebuilt a "/p/<code>" URL by hand; when the scheme moved to
rev-5 that produced a doubled, overflowing line that clipped the access code.)

Rendered INTO the package build (appended after the closing page, footer-exempt)
so a package can never ship without its portal code. QR via reportlab's bundled
QrCodeWidget — no new dependency. Print at 100% / Actual Size on sticker stock.

BATCH PRINTING: render_sticker_bundle() lays many accounts' stickers into ONE
PDF for a single print run (see its docstring for the duplex note).
"""
import os
from urllib.parse import urlsplit, parse_qs

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

NAVY = (0x00 / 255, 0x3A / 255, 0x70 / 255)
GOLD = (0xFF / 255, 0x9C / 255, 0x00 / 255)
WHITE = (1, 1, 1)

BOOK_URL = ("https://outlook.office.com/bookwithme/user/"
            "7aa3d169518c4b1caeb9f72a2f23f9d8@eragroup.com/"
            "meetingtype/CMjo2-07uk2-Q0n_F1MSvQ2"
            "?anonymous&ismsaljsauthenabled&ep=mcard")

# John's title is CONSULTING PARTNER (settled canon — never Senior Consultant).
C_NAME, C_TITLE = "John Wylie", "Consulting Partner, ERA Group"
C_PHONE, C_EMAIL = "703.244.9868", "jwylie@eragroup.com"

PAGE_W, PAGE_H = 6.0 * inch, 4.0 * inch

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "meeting_label", "assets", "era_logo.png")


def _qr(c, url, x, y, size):
    w = QrCodeWidget(url, barLevel="M")   # black modules on the white quiet zone
    b = w.getBounds()
    d = Drawing(size, size, transform=[size / (b[2] - b[0]), 0, 0, size / (b[3] - b[1]), 0, 0])
    d.add(w)
    renderPDF.draw(d, c, x, y)


def _display_and_code(portal_url: str, fallback_code: str):
    """Derive the human-readable URL + the typeable code from the ONE portal_url
    the QR encodes, so text and link can never disagree. For the rev-5 branded
    form the code is the ?c= access code; if a legacy /p/<code> URL is passed the
    caller's short code is used instead."""
    p = urlsplit(portal_url)
    display = (p.netloc + p.path).rstrip("/") or portal_url
    access = (parse_qs(p.query).get("c") or [None])[0]
    return display, (access or fallback_code)


def _draw_fit(c, x, y, text, font, size, max_w, min_size=6.5):
    """Draw text left-anchored at (x, y), shrinking the font until it fits max_w
    so a long subdomain can never overrun the 6-inch label edge."""
    while size > min_size and c.stringWidth(text, font, size) > max_w:
        size -= 0.5
    c.setFont(font, size)
    c.drawString(x, y, text)


def _draw_side_a(c):
    """SIDE A — navy, book-a-meeting (existing QR pattern)."""
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
    c.drawString(tx, PAGE_H - 1.85 * inch, C_NAME)
    c.drawString(tx, PAGE_H - 2.05 * inch, C_TITLE)
    c.drawString(tx, PAGE_H - 2.25 * inch, C_PHONE)
    c.drawString(tx, PAGE_H - 2.45 * inch, C_EMAIL)
    c.setFillColorRGB(*GOLD)
    c.setFont("Helvetica-BoldOblique", 9)
    c.drawString(tx, 0.55 * inch, "VALUE THROUGH INSIGHT™")


def _draw_side_b(c, portal_url, code):
    """SIDE B — white, the portal QR + typeable code + branded display URL."""
    display_url, type_code = _display_and_code(portal_url, code)
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
    _qr(c, portal_url, 0.55 * inch, 0.75 * inch, qr_size_b)   # QR = the branded portal_url
    txb = 2.95 * inch
    c.setFillColorRGB(*NAVY)
    c.setFont("Helvetica", 10.5)
    c.drawString(txb, 2.55 * inch, "Scan for the full benchmark —")
    c.drawString(txb, 2.36 * inch, "shareable with your CFO.")
    c.setFont("Helvetica", 9.5)
    c.drawString(txb, 1.95 * inch, "Or type the code:")
    c.setFont("Courier-Bold", 26)
    c.drawString(txb, 1.5 * inch, type_code)
    # Display URL — the SAME link the QR carries, width-fit so it never runs off
    # the label. max width = the column from txb to the right margin.
    _draw_fit(c, txb, 1.12 * inch, display_url, "Helvetica", 9.5,
              max_w=PAGE_W - txb - 0.3 * inch)
    if os.path.exists(LOGO):
        try:
            c.drawImage(LOGO, txb, 0.5 * inch, width=1.1 * inch,
                        height=1.1 * inch * (478.0 / 1043.0), mask="auto")
        except Exception:
            pass


def render_sticker(portal_url: str, code: str, out_pdf: str) -> str:
    """Two 6x4 pages: side A = book-a-meeting, side B = portal QR + code."""
    if not portal_url or not code:
        raise ValueError("portal sticker requires portal_url and code")
    c = canvas.Canvas(out_pdf, pagesize=(PAGE_W, PAGE_H))
    _draw_side_a(c)
    c.showPage()
    _draw_side_b(c, portal_url, code)
    c.showPage()
    c.save()
    return out_pdf


def render_sticker_bundle(items, out_pdf: str, side: str = "both") -> str:
    """Many stickers, ONE PDF, for a single print run.

    items : iterable of (portal_url, code) — one per account.
    side  : 'both' (default) = A then B for each account, so a duplex print
            (flip on the SHORT edge) puts book-a-meeting on the back of each
            portal card; 'b' = the portal side only, one per page, for plain
            sticker stock; 'a' = the meeting side only.

    Incomplete rows (missing url or code) are skipped, never fatal, so one bad
    account can't sink the whole batch. Returns out_pdf; raises if nothing
    renderable was supplied.
    """
    if side not in ("both", "a", "b"):
        raise ValueError("side must be 'both', 'a', or 'b'")
    c = canvas.Canvas(out_pdf, pagesize=(PAGE_W, PAGE_H))
    n = 0
    for portal_url, code in items:
        if not portal_url or not code:
            continue
        if side in ("both", "a"):
            _draw_side_a(c)
            c.showPage()
        if side in ("both", "b"):
            _draw_side_b(c, portal_url, code)
            c.showPage()
        n += 1
    if n == 0:
        raise ValueError("no renderable stickers (every item missing url or code)")
    c.save()
    return out_pdf


if __name__ == "__main__":
    import sys
    render_sticker(sys.argv[1] if len(sys.argv) > 1 else "https://portal.wpp-us.com/example-benchmark?c=K7M2Q9R",
                   sys.argv[2] if len(sys.argv) > 2 else "K7M2Q9R",
                   sys.argv[3] if len(sys.argv) > 3 else "/tmp/portal_sticker.pdf")
    print("ok")
