#!/usr/bin/env python3
"""
Portal QR label — the LOCKED 6x4 side-by-side design, carrying the account's
portal instead of a booking link.

THE TEMPLATE IS meeting_label/ (LOCKED by John, 2026-07-20/21). Its geometry is
reproduced here exactly:

  6" W x 4" H, vertical split at 3".
  LEFT  (navy #003A70) : white QR panel 2.14" at y 0.34", headline at 13pt white,
                         then the white VTI lockup 2.00" wide. ONE VTI, here only.
  RIGHT (white)        : ERA logo 0.87" wide at y 0.92" (the halved size John
                         chose), then 17pt navy, 9.6pt helv, gold hairline
                         0.60" wide, 10.8pt, 10.0pt.

Only the CONTENT of those slots changes, never their positions:
  headline  "Let's start a conversation"   -> "Your numbers, online"
  QR        Book-With-Me                   -> this account's portal URL
  name      John Wylie                     -> the account's name
  title     Senior Consultant, ERA Group   -> "Executive Opportunity Brief"
  phone     703.244.9868                   -> the typeable access code
  email     jwylie@eragroup.com            -> the same portal address in text

PARTNER-NEUTRAL. A portal label carries the ACCOUNT's address and nothing about
who mailed it, so one sheet is correct for any partner. The booking QR is the
partner-identity piece and stays in meeting_label / portal_sticker, where it
refuses to print without that partner's own booking_url.

THE ADDRESS IS NOT BUILT HERE. url and code arrive from the database
(portal_alias_url / portal_url_for). This file concatenates no host.
"""
import os
import fitz
import qrcode

NAVY = (0x00/255, 0x3A/255, 0x70/255)
WHITE = (1, 1, 1)
GOLD = (0xFF/255, 0x9C/255, 0x00/255)

HEADLINE = "Your numbers, online"
SUBTITLE = "Executive Opportunity Brief"

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "meeting_label", "assets")
LOGO_NAVY = os.path.join(ASSETS, "era_logo.png")
LOGO_AR = 478.0 / 1043.0
VTI_WHITE = os.path.join(ASSETS, "vti_white_lockup.png")
VTI_WHITE_AR = 60.0 / 360.0

IN = 72.0
PAGE_W, PAGE_H = 6.0 * IN, 4.0 * IN
SPLIT = 3.0 * IN
BLEED = 0.125 * IN


def _qr_pixmap(url, tmpdir):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                      box_size=20, border=0)
    q.add_data(url)
    q.make(fit=True)
    p = os.path.join(tmpdir, "_qr.png")
    q.make_image(fill_color="black", back_color="white").convert("RGB").save(p)
    return fitz.Pixmap(p)


def _ctext(page, cx, y, w, h, s, size, color, font="hebo"):
    """meeting_label.ctext, unchanged: the box is grown to size*1.9 to dodge
    PyMuPDF's silent text-drop when a box is a hair short. Long account names
    are stepped down rather than allowed to overflow -- an overflow here is a
    label that silently prints without its account name."""
    while size > 6.0:
        box_h = max(h, size * 1.9)
        rc = page.insert_textbox(fitz.Rect(cx - w/2, y, cx + w/2, y + box_h),
                                 s, fontname=font, fontsize=size, color=color,
                                 align=fitz.TEXT_ALIGN_CENTER)
        if rc >= 0:
            return y + h
        size -= 0.5
    raise RuntimeError("cannot fit %r on the label" % (s,))


def draw_label(page, url, code, org_name, display, tmpdir):
    qr = _qr_pixmap(url, tmpdir)
    page.draw_rect(fitz.Rect(-BLEED, -BLEED, SPLIT, PAGE_H + BLEED), color=None, fill=NAVY)
    page.draw_rect(fitz.Rect(SPLIT, -BLEED, PAGE_W + BLEED, PAGE_H + BLEED), color=None, fill=WHITE)

    # ---- LEFT (navy): big QR + headline + white VTI lockup
    cxL = SPLIT / 2
    panel = 2.14 * IN
    px, py = cxL - panel/2, 0.34 * IN
    page.draw_rect(fitz.Rect(px, py, px + panel, py + panel), color=None, fill=WHITE, radius=0.08)
    pad = 0.14 * IN
    page.insert_image(fitz.Rect(px+pad, py+pad, px+panel-pad, py+panel-pad), pixmap=qr)
    y = py + panel + 0.26*IN
    y = _ctext(page, cxL, y, 2.7*IN, 0.28*IN, HEADLINE, 13, WHITE) + 0.20*IN
    vw = 2.00*IN; vh = vw * VTI_WHITE_AR
    page.insert_image(fitz.Rect(cxL - vw/2, y, cxL + vw/2, y + vh),
                      filename=VTI_WHITE, keep_proportion=True)

    # ---- RIGHT (white): ERA logo + the account and its code
    cxR = SPLIT + (PAGE_W - SPLIT)/2
    lw = 0.87 * IN; lh = lw * LOGO_AR
    y = 0.92 * IN
    page.insert_image(fitz.Rect(cxR - lw/2, y, cxR + lw/2, y + lh), filename=LOGO_NAVY, keep_proportion=True)
    y += lh + 0.28*IN
    y = _ctext(page, cxR, y, 2.7*IN, 0.34*IN, org_name or "", 17, NAVY) + 0.05*IN
    y = _ctext(page, cxR, y, 2.7*IN, 0.24*IN, SUBTITLE, 9.6, NAVY, font="helv") + 0.14*IN
    page.draw_line(fitz.Point(cxR - 0.30*IN, y), fitz.Point(cxR + 0.30*IN, y), color=GOLD, width=1.1)
    y += 0.16*IN
    y = _ctext(page, cxR, y, 2.7*IN, 0.24*IN, code, 10.8, NAVY, font="cobo") + 0.04*IN
    _ctext(page, cxR, y, 2.7*IN, 0.24*IN, display or "", 10.0, NAVY, font="helv")


def render_labels(labels, out_pdf, tmpdir):
    """One 6x4 page per label, in the order given. Returns (path, n)."""
    rows = list(labels)
    if not rows:
        raise ValueError("no labels to render")
    for i, r in enumerate(rows, 1):
        if not (r.get("url") or "").strip() or not (r.get("code") or "").strip():
            raise ValueError("label %d (%s) has no portal url/code -- refusing to "
                             "print a label that leads nowhere" % (i, r.get("name") or "?"))
    doc = fitz.open()
    for r in rows:
        page = doc.new_page(width=PAGE_W, height=PAGE_H)
        draw_label(page, r["url"], r["code"], r.get("name"), r.get("display"), tmpdir)
    doc.save(out_pdf)
    return out_pdf, len(rows)
