#!/usr/bin/env python3
"""
ERA / WPP — meeting label, 6" W x 4" H, SIDE-BY-SIDE (vertical split at 3"):
  LEFT  (navy, 3x4)  = large QR Book-With-Me + "Let's start a conversation" + tagline
  RIGHT (white,3x4)  = ERA logo + contact + value-through-insight wordmark

Big-code variant. Best when the label lies flat (a center crease would cut the QR).
Print at 100% / Actual Size.
"""
import sys, os
import fitz
import qrcode

BOOK_URL = ("https://outlook.office.com/bookwithme/user/"
            "7aa3d169518c4b1caeb9f72a2f23f9d8@eragroup.com/"
            "meetingtype/CMjo2-07uk2-Q0n_F1MSvQ2"
            "?anonymous&ismsaljsauthenabled&ep=mcard")

NAVY  = (0x00/255, 0x3A/255, 0x70/255)
WHITE = (1, 1, 1)
GOLD  = (0xFF/255, 0x9C/255, 0x00/255)

HEADLINE = "Let's start a conversation"
TAGLINE  = "VALUE THROUGH INSIGHT"
C_NAME  = "John Wylie"
C_TITLE = "Senior Consultant, ERA Group"
C_PHONE = "703.244.9868"
C_EMAIL = "jwylie@eragroup.com"

HERE   = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
LOGO_NAVY = os.path.join(ASSETS, "era_logo.png")
LOGO_AR   = 478.0 / 1043.0
VTI_LOGO  = os.path.join(ASSETS, "vti_logo.png")
VTI_AR    = 42.0 / 360.0
VTI_WHITE = os.path.join(ASSETS, "vti_white_lockup.png")
VTI_WHITE_AR = 60.0 / 360.0

IN = 72.0
PAGE_W, PAGE_H = 6.0 * IN, 4.0 * IN
SPLIT = 3.0 * IN
BLEED = 0.125 * IN


def qr_pixmap():
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=20, border=0)
    q.add_data(BOOK_URL); q.make(fit=True)
    q.make_image(fill_color="black", back_color="white").convert("RGB").save("/tmp/_qrsbs.png")
    return fitz.Pixmap("/tmp/_qrsbs.png")


def ctext(page, cx, y, w, h, s, size, color, font="hebo"):
    box_h = max(h, size * 1.9)
    rc = page.insert_textbox(fitz.Rect(cx - w/2, y, cx + w/2, y + box_h),
                             s, fontname=font, fontsize=size, color=color,
                             align=fitz.TEXT_ALIGN_CENTER)
    if rc < 0:
        raise RuntimeError(f"overflow {s!r} by {rc:.1f}pt")
    return y + h


def build(out="JohnWylie_MeetingLabel_6x4_sidebyside.pdf"):
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    qr = qr_pixmap()

    page.draw_rect(fitz.Rect(-BLEED, -BLEED, SPLIT, PAGE_H + BLEED), color=None, fill=NAVY)
    page.draw_rect(fitz.Rect(SPLIT, -BLEED, PAGE_W + BLEED, PAGE_H + BLEED), color=None, fill=WHITE)

    # ── LEFT (navy) : big QR + headline + tagline ────────────────
    cxL = SPLIT / 2
    panel = 2.14 * IN
    px = cxL - panel/2
    py = 0.34 * IN
    page.draw_rect(fitz.Rect(px, py, px + panel, py + panel), color=None, fill=WHITE, radius=0.08)
    pad = 0.14 * IN
    page.insert_image(fitz.Rect(px+pad, py+pad, px+panel-pad, py+panel-pad), pixmap=qr)
    y = py + panel + 0.26*IN
    y = ctext(page, cxL, y, 2.7*IN, 0.28*IN, HEADLINE, 13, WHITE) + 0.20*IN
    # real white VTI lockup (white wordmark + gold underline + dot) — not text
    vw = 2.00*IN; vh = vw * VTI_WHITE_AR
    page.insert_image(fitz.Rect(cxL - vw/2, y, cxL + vw/2, y + vh),
                      filename=VTI_WHITE, keep_proportion=True)

    # ── RIGHT (white) : logo + contact + wordmark ────────────────
    cxR = SPLIT + (PAGE_W - SPLIT)/2
    # ERA logo halved (John, 2026-07-21). VTI lives only on the navy side — no duplicate here.
    lw = 0.87 * IN; lh = lw * LOGO_AR
    y = 0.92 * IN
    page.insert_image(fitz.Rect(cxR - lw/2, y, cxR + lw/2, y + lh), filename=LOGO_NAVY, keep_proportion=True)
    y += lh + 0.28*IN
    y = ctext(page, cxR, y, 2.7*IN, 0.34*IN, C_NAME, 17, NAVY) + 0.05*IN
    y = ctext(page, cxR, y, 2.7*IN, 0.24*IN, C_TITLE, 9.6, NAVY, font="helv") + 0.14*IN
    page.draw_line(fitz.Point(cxR - 0.30*IN, y), fitz.Point(cxR + 0.30*IN, y), color=GOLD, width=1.1)
    y += 0.16*IN
    y = ctext(page, cxR, y, 2.7*IN, 0.24*IN, C_PHONE, 10.8, NAVY, font="helv") + 0.04*IN
    ctext(page, cxR, y, 2.7*IN, 0.24*IN, C_EMAIL, 10.0, NAVY, font="helv")

    doc.save(out)
    return out


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else "JohnWylie_MeetingLabel_6x4_sidebyside.pdf"))
