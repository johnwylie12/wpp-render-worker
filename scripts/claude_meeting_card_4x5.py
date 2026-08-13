#!/usr/bin/env python3
"""
ERA / WPP — 4" x 5" two-side meeting card.

Split down the middle (vertical fold at 2"):
  LEFT  panel (navy)  = ERA logo + "Let's start a conversation" QR (Book-With-Me)
                        + gold rule + VALUE THROUGH INSIGHT
  RIGHT panel (white) = ERA logo + John Wylie contact block + gold rule
                        + value through insight wordmark

Prints flat as one 4x5; fold at the seam -> a 2x5 card, QR front / contact back.

Usage:  python3 meeting_card_4x5.py out.pdf
"""
import sys
import fitz
import qrcode
from wpp_assets import logo   # canonical brand-mark resolver; see asset_sources

# ── LOCKED brand ──────────────────────────────────────────────────────────────
BOOK_URL = ("https://outlook.office.com/bookwithme/user/"
            "7aa3d169518c4b1caeb9f72a2f23f9d8@eragroup.com/"
            "meetingtype/CMjo2-07uk2-Q0n_F1MSvQ2"
            "?anonymous&ismsaljsauthenabled&ep=mcard")

NAVY  = (0x00/255, 0x3A/255, 0x70/255)   # #003A70 Daybreak Blue
WHITE = (1, 1, 1)
GOLD  = (0xFF/255, 0x9C/255, 0x00/255)   # #FF9C00 Sunrise Yellow

HEADLINE = "Let's start a conversation"
TAGLINE  = "VALUE THROUGH INSIGHT"

# Contact. Title is Senior Advisor - settled canon, do not change.
C_NAME  = "John Wylie"
C_TITLE = "Senior Advisor, ERA Group"
C_PHONE = "703.244.9868"
C_EMAIL = "jwylie@eragroup.com"

LOGO_WHITE = logo('era_group', 'mono_white')   # for navy panel
LOGO_NAVY  = logo('era_group', 'light')         # for white panel

IN = 72.0
PAGE_W, PAGE_H = 4.0 * IN, 5.0 * IN
SPLIT   = 2.0 * IN
BLEED   = 0.125 * IN
LOGO_AR = 478.0 / 1043.0   # h/w of the ERA mark


def qr_pixmap() -> fitz.Pixmap:
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=20, border=0)
    q.add_data(BOOK_URL); q.make(fit=True)
    q.make_image(fill_color="black", back_color="white").convert("RGB").save("/tmp/_qrcard.png")
    return fitz.Pixmap("/tmp/_qrcard.png")


def place_logo(page, path, cx, top, w):
    h = w * LOGO_AR
    page.insert_image(fitz.Rect(cx - w/2, top, cx + w/2, top + h), filename=path, keep_proportion=True)
    return top + h


def ctext(page, cx, y, w, h, s, size, color, font="hebo"):
    rc = page.insert_textbox(fitz.Rect(cx - w/2, y, cx + w/2, y + h),
                             s, fontname=font, fontsize=size, color=color,
                             align=fitz.TEXT_ALIGN_CENTER)
    if rc < 0:
        raise RuntimeError(f"text overflow ({s!r}) by {rc:.1f}pt")
    return y + h


def rule_dot(page, cx, y, rule_w, weight, dot_d, rc, dot_col=GOLD):
    page.draw_line(fitz.Point(cx - rule_w/2 - dot_d*0.35, y),
                   fitz.Point(cx + rule_w/2 - dot_d*0.35, y), color=rc, width=weight)
    page.draw_circle(fitz.Point(cx + rule_w/2, y), dot_d/2, color=None, fill=dot_col)


def build(out="JohnWylie_MeetingCard_4x5.pdf"):
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    qr = qr_pixmap()

    # panels
    page.draw_rect(fitz.Rect(-BLEED, -BLEED, SPLIT, PAGE_H + BLEED), color=None, fill=NAVY)
    page.draw_rect(fitz.Rect(SPLIT, -BLEED, PAGE_W + BLEED, PAGE_H + BLEED), color=None, fill=WHITE)

    # ── LEFT (navy) ──────────────────────────────────────────────
    cxL = SPLIT / 2
    y = 0.34 * IN
    y = place_logo(page, LOGO_WHITE, cxL, y, 1.30 * IN) + 0.20 * IN
    # QR white panel
    panel = 1.46 * IN
    px = cxL - panel/2
    page.draw_rect(fitz.Rect(px, y, px + panel, y + panel), color=None, fill=WHITE, radius=0.07)
    pad = 0.12 * IN
    page.insert_image(fitz.Rect(px+pad, y+pad, px+panel-pad, y+panel-pad), pixmap=qr)
    y += panel + 0.20 * IN
    y = ctext(page, cxL, y, 1.72*IN, 0.66*IN, HEADLINE, 12.5, WHITE) + 0.02*IN
    ry = y + 0.06*IN
    rule_dot(page, cxL, ry, 0.66*IN, 1.3, 0.10*IN, WHITE)
    y = ry + 0.10*IN
    ctext(page, cxL, y, 1.80*IN, 0.28*IN, TAGLINE, 6.8, GOLD)

    # ── RIGHT (white) ────────────────────────────────────────────
    cxR = SPLIT + (PAGE_W - SPLIT)/2
    y = 0.42 * IN
    y = place_logo(page, LOGO_NAVY, cxR, y, 1.34 * IN) + 0.42 * IN
    # contact block
    y = ctext(page, cxR, y, 1.85*IN, 0.36*IN, C_NAME, 15, NAVY) + 0.10*IN
    y = ctext(page, cxR, y, 1.85*IN, 0.28*IN, C_TITLE, 9.2, NAVY, font="helv") + 0.30*IN
    y = ctext(page, cxR, y, 1.85*IN, 0.28*IN, C_PHONE, 10.5, NAVY, font="helv") + 0.08*IN
    y = ctext(page, cxR, y, 1.85*IN, 0.28*IN, C_EMAIL, 10.0, NAVY, font="helv") + 0.30*IN
    ry = y + 0.02*IN
    rule_dot(page, cxR, ry, 0.66*IN, 1.3, 0.10*IN, NAVY)
    y = ry + 0.12*IN
    ctext(page, cxR, y, 1.85*IN, 0.26*IN, "value through insight", 7.0, NAVY)

    # subtle fold ticks at the seam
    for ty in (0.0, PAGE_H - 0.14*IN):
        page.draw_line(fitz.Point(SPLIT, ty), fitz.Point(SPLIT, ty + 0.14*IN),
                       color=GOLD, width=0.6, dashes="[2] 0")

    doc.save(out)
    return out


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else "JohnWylie_MeetingCard_4x5.pdf"))
