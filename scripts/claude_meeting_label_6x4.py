#!/usr/bin/env python3
"""
ERA / WPP — meeting label, 6" wide x 4" tall (landscape), sits on the folder's
bottom fold. Horizontal seam at the CENTER (2"):

  TOP half (navy, 6x2)   = QR Book-With-Me (left)  +  "Let's start a conversation"
                           + gold rule + VALUE THROUGH INSIGHT (right)
  BOTTOM half (white,6x2) = ERA logo + wordmark (left)  +  John Wylie contact (right)

Wide format gives each element its own horizontal lane, so it aligns across the
fold instead of crowding the crease. Print at 100% / Actual Size.

Usage:  python3 meeting_label_6x4.py out.pdf
"""
import sys
import fitz
import qrcode
from wpp_assets import logo   # canonical brand-mark resolver; see asset_sources

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
C_TITLE = "Senior Advisor, ERA Group"
C_PHONE = "703.244.9868"
C_EMAIL = "jwylie@eragroup.com"

LOGO_NAVY = logo('era_group', 'light')
LOGO_AR   = 478.0 / 1043.0

IN = 72.0
PAGE_W, PAGE_H = 6.0 * IN, 4.0 * IN
FOLD  = 2.0 * IN
BLEED = 0.125 * IN
GUTTER = 0.22 * IN     # clear space kept off the crease, each side


def qr_pixmap():
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=20, border=0)
    q.add_data(BOOK_URL); q.make(fit=True)
    q.make_image(fill_color="black", back_color="white").convert("RGB").save("/tmp/_qr6x4.png")
    return fitz.Pixmap("/tmp/_qr6x4.png")


def tbox(page, x0, y, x1, h, s, size, color, font="hebo", align=fitz.TEXT_ALIGN_LEFT):
    box_h = max(h, size * 1.9)
    rc = page.insert_textbox(fitz.Rect(x0, y, x1, y + box_h), s, fontname=font,
                             fontsize=size, color=color, align=align)
    if rc < 0:
        raise RuntimeError(f"overflow {s!r} by {rc:.1f}pt")
    return y + h


def build(out="JohnWylie_MeetingLabel_6x4.pdf"):
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    qr = qr_pixmap()

    page.draw_rect(fitz.Rect(-BLEED, -BLEED, PAGE_W + BLEED, FOLD), color=None, fill=NAVY)
    page.draw_rect(fitz.Rect(-BLEED, FOLD, PAGE_W + BLEED, PAGE_H + BLEED), color=None, fill=WHITE)

    # ── TOP (navy) : QR left, headline+tagline right ─────────────
    usable_top = FOLD - GUTTER               # keep content above this
    qp = 1.55 * IN
    qx = 0.34 * IN
    qy = (usable_top - qp) / 2               # centered in the clear top zone
    page.draw_rect(fitz.Rect(qx, qy, qx + qp, qy + qp), color=None, fill=WHITE, radius=0.07)
    pad = 0.12 * IN
    page.insert_image(fitz.Rect(qx+pad, qy+pad, qx+qp-pad, qy+qp-pad), pixmap=qr)

    rx0 = qx + qp + 0.34*IN
    rx1 = PAGE_W - 0.34*IN
    stack_h = 0.52*IN + 0.18*IN + 0.24*IN
    ty = (usable_top - stack_h) / 2
    ty = tbox(page, rx0, ty, rx1, 0.52*IN, HEADLINE, 19, WHITE)
    ry = ty + 0.10*IN
    rw = 0.80*IN; dot = 0.11*IN
    page.draw_line(fitz.Point(rx0, ry), fitz.Point(rx0 + rw, ry), color=WHITE, width=1.4)
    page.draw_circle(fitz.Point(rx0 + rw + dot*0.6, ry), dot/2, color=None, fill=GOLD)
    tbox(page, rx0, ry + 0.11*IN, rx1, 0.24*IN, TAGLINE, 8.0, GOLD)

    # ── BOTTOM (white) : logo+wordmark left, contact right ───────
    base = FOLD + GUTTER
    lw = 1.66 * IN
    lh = lw * LOGO_AR
    lx = 0.40 * IN
    lcy = base + (PAGE_H - base)/2 - 0.08*IN
    page.insert_image(fitz.Rect(lx, lcy - lh/2, lx + lw, lcy + lh/2),
                      filename=LOGO_NAVY, keep_proportion=True)
    tbox(page, lx - 0.05*IN, lcy + lh/2 + 0.04*IN, lx + lw + 0.10*IN, 0.20*IN,
         "value through insight", 8.0, NAVY, align=fitz.TEXT_ALIGN_CENTER)

    cx0 = lx + lw + 0.42*IN
    cx1 = PAGE_W - 0.34*IN
    block_h = 0.34*IN + 0.24*IN + 0.20*IN + 0.24*IN + 0.24*IN
    cy = base + ((PAGE_H - base) - block_h)/2
    cy = tbox(page, cx0, cy, cx1, 0.34*IN, C_NAME, 18, NAVY) + 0.06*IN
    cy = tbox(page, cx0, cy, cx1, 0.24*IN, C_TITLE, 10.5, NAVY, font="helv") + 0.16*IN
    page.draw_line(fitz.Point(cx0, cy), fitz.Point(cx0 + 0.60*IN, cy), color=GOLD, width=1.2)
    cy += 0.14*IN
    cy = tbox(page, cx0, cy, cx1, 0.24*IN, C_PHONE, 11.5, NAVY, font="helv") + 0.05*IN
    tbox(page, cx0, cy, cx1, 0.24*IN, C_EMAIL, 10.5, NAVY, font="helv")

    # fold guide across the seam
    page.draw_line(fitz.Point(0.10*IN, FOLD), fitz.Point(PAGE_W - 0.10*IN, FOLD),
                   color=GOLD, width=0.5, dashes="[2 3] 0")

    doc.save(out)
    return out


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else "JohnWylie_MeetingLabel_6x4.pdf"))
