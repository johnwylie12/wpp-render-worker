#!/usr/bin/env python3
"""
ERA / WPP — 4" x 5" meeting label for Spartan Industrial R022 (4x5, 4/sheet).

Horizontal split at the CENTER (2.5") — the label sits ON the folder's bottom
fold, crease down the middle:
  TOP  half (navy, 4x2.5)  = QR Book-With-Me + "Let's start a conversation"
  BOTTOM half (white, 4x2.5) = ERA logo + value-through-insight + John contact

Prints at 100% on R022. The two-tone edge marks the fold; faint ticks align it.

Usage:  python3 meeting_label_R022.py out.pdf
"""
import sys
import fitz
import qrcode
from wpp_assets import logo   # canonical brand-mark resolver; see asset_sources

BOOK_URL = ("https://outlook.office.com/bookwithme/user/"
            "7aa3d169518c4b1caeb9f72a2f23f9d8@eragroup.com/"
            "meetingtype/CMjo2-07uk2-Q0n_F1MSvQ2"
            "?anonymous&ismsaljsauthenabled&ep=mcard")

NAVY  = (0x00/255, 0x3A/255, 0x70/255)   # #003A70
WHITE = (1, 1, 1)
GOLD  = (0xFF/255, 0x9C/255, 0x00/255)   # #FF9C00

HEADLINE = "Let's start a conversation"
TAGLINE  = "VALUE THROUGH INSIGHT"
C_NAME  = "John Wylie"
C_TITLE = "Senior Advisor, ERA Group"
C_PHONE = "703.244.9868"
C_EMAIL = "jwylie@eragroup.com"

LOGO_NAVY = logo('era_group', 'light')   # navy text + orange arc, transparent
LOGO_AR   = 478.0 / 1043.0

IN = 72.0
PAGE_W, PAGE_H = 4.0 * IN, 5.0 * IN
FOLD  = 2.5 * IN                 # horizontal center seam
BLEED = 0.125 * IN


def qr_pixmap():
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=20, border=0)
    q.add_data(BOOK_URL); q.make(fit=True)
    q.make_image(fill_color="black", back_color="white").convert("RGB").save("/tmp/_qrR022.png")
    return fitz.Pixmap("/tmp/_qrR022.png")


def tbox(page, x0, y, x1, h, s, size, color, font="hebo", align=fitz.TEXT_ALIGN_LEFT):
    # render into a box tall enough for the font (kills PyMuPDF's silent-drop
    # when h is a hair short); advance layout by the requested h.
    box_h = max(h, size * 1.9)
    rc = page.insert_textbox(fitz.Rect(x0, y, x1, y + box_h), s, fontname=font,
                             fontsize=size, color=color, align=align)
    if rc < 0:
        raise RuntimeError(f"overflow {s!r} by {rc:.1f}pt (width too narrow)")
    return y + h


def build(out="JohnWylie_MeetingLabel_R022.pdf"):
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    qr = qr_pixmap()

    # planes
    page.draw_rect(fitz.Rect(-BLEED, -BLEED, PAGE_W + BLEED, FOLD), color=None, fill=NAVY)
    page.draw_rect(fitz.Rect(-BLEED, FOLD, PAGE_W + BLEED, PAGE_H + BLEED), color=None, fill=WHITE)

    # ── TOP (navy): QR left, headline+tagline right ──────────────
    qp = 1.72 * IN
    qx = 0.30 * IN
    qy = (FOLD - qp) / 2
    page.draw_rect(fitz.Rect(qx, qy, qx + qp, qy + qp), color=None, fill=WHITE, radius=0.07)
    pad = 0.13 * IN
    page.insert_image(fitz.Rect(qx+pad, qy+pad, qx+qp-pad, qy+qp-pad), pixmap=qr)

    rx0, rx1 = qx + qp + 0.22*IN, PAGE_W - 0.20*IN
    # vertically center the headline/rule/tagline stack in the top half
    hh = 0.86*IN
    ty = (FOLD - (hh + 0.16*IN + 0.24*IN)) / 2
    ty = tbox(page, rx0, ty, rx1, hh, HEADLINE, 15, WHITE, align=fitz.TEXT_ALIGN_LEFT)
    ry = ty + 0.02*IN
    rw = 0.70*IN; dot = 0.10*IN
    page.draw_line(fitz.Point(rx0, ry), fitz.Point(rx0 + rw, ry), color=WHITE, width=1.3)
    page.draw_circle(fitz.Point(rx0 + rw + dot*0.6, ry), dot/2, color=None, fill=GOLD)
    tbox(page, rx0, ry + 0.09*IN, rx1, 0.24*IN, TAGLINE, 7.2, GOLD, align=fitz.TEXT_ALIGN_LEFT)

    # ── BOTTOM (white): logo + wordmark left, contact right ──────
    lx = 0.34 * IN
    lw = 1.46 * IN
    lh = lw * LOGO_AR
    lcy = FOLD + (PAGE_H - FOLD)/2
    page.insert_image(fitz.Rect(lx, lcy - lh/2 - 0.10*IN, lx + lw, lcy + lh/2 - 0.10*IN),
                      filename=LOGO_NAVY, keep_proportion=True)
    tbox(page, lx - 0.05*IN, lcy + lh/2 + 0.02*IN, lx + lw + 0.10*IN, 0.22*IN,
         "value through insight", 7.2, NAVY, align=fitz.TEXT_ALIGN_CENTER)

    cx0 = lx + lw + 0.24*IN
    cx1 = PAGE_W - 0.22*IN
    cy = FOLD + 0.42*IN
    cy = tbox(page, cx0, cy, cx1, 0.40*IN, C_NAME, 15.5, NAVY, align=fitz.TEXT_ALIGN_LEFT) + 0.05*IN
    cy = tbox(page, cx0, cy, cx1, 0.24*IN, C_TITLE, 9.0, NAVY, font="helv", align=fitz.TEXT_ALIGN_LEFT) + 0.22*IN
    # gold hairline separating identity from reach
    page.draw_line(fitz.Point(cx0, cy), fitz.Point(cx0 + 0.55*IN, cy), color=GOLD, width=1.1)
    cy += 0.16*IN
    cy = tbox(page, cx0, cy, cx1, 0.24*IN, C_PHONE, 10.5, NAVY, font="helv", align=fitz.TEXT_ALIGN_LEFT) + 0.06*IN
    tbox(page, cx0, cy, cx1, 0.24*IN, C_EMAIL, 9.6, NAVY, font="helv", align=fitz.TEXT_ALIGN_LEFT)

    # faint fold ticks at the seam edges
    for x in (0.0, PAGE_W - 0.16*IN):
        page.draw_line(fitz.Point(x, FOLD), fitz.Point(x + 0.16*IN, FOLD),
                       color=GOLD, width=0.6, dashes="[2] 0")

    doc.save(out)
    return out


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else "JohnWylie_MeetingLabel_R022.pdf"))
