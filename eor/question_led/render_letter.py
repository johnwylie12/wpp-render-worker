#!/usr/bin/env python3
"""Render the question-led cover letter.

The letter is locked by settled #174 — nine assertions against the RENDERED PDF.
This does not re-implement it: it renders cover/WPP_EOP_CoverLetter_TEMPLATE_v3_
QUESTION_LED.html, which is the v2 partner-signoff template with four rewritten
body paragraphs and nothing else moved. v2 itself is untouched.

The rewrite answers, in order, the questions John set on 2026-09-06:
  who we are · what we are writing about · why we are writing · where we got it
  · when · what it should mean to you · how we get you to the desired state
The previous Goodwill letter answered four of those seven. It never said who ERA
is (the firm appeared only in the sign-off), never gave a date, and had drifted
off all four paragraph openers #174 requires — including "ERA Group has
reviewed", which IS the credentials paragraph.

    python eor/question_led/render_letter.py --out letter.pdf
"""
import argparse, base64, io, os, sys

import segno
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
from wpp_signatures import signature_data_uri  # noqa: E402

TEMPLATE = os.path.join(REPO, "cover", "WPP_EOP_CoverLetter_TEMPLATE_v4_VALUE_SELLING.html")


def data_uri(path, mime="image/png"):
    with open(path, "rb") as fh:
        return f"data:{mime};base64," + base64.b64encode(fh.read()).decode()


def render(account, out_pdf, signature="3"):
    qr = segno.make(f"https://portal.wpp-us.com/{account['portal_subdomain']}", error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=10, border=0)

    html = Template(open(TEMPLATE).read()).render(
        era_logo_uri=data_uri(os.path.join(REPO, "case_study/assets/era_logo.png")),
        vti_uri=data_uri(os.path.join(REPO, "meeting_label/assets/vti_logo.png")),
        # The signature comes from wpp_signatures, never from an image lifted out
        # of a rendered PDF: the mark in the PDF carries a soft mask, and a naive
        # extraction composites it onto black and prints a black box.
        signature_uri=signature_data_uri(signature),
        signature_width_px=115,
        qr_uri="data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
        **account,
    )
    HTML(string=html, base_url=REPO).write_pdf(out_pdf)
    return out_pdf


GOODWILL = dict(
    first_name="Raisa", recipient_name="Raisa Ciobanu",
    recipient_title="Chief Financial Officer",
    org_name="Goodwill Industries of South Florida",
    addr_line1="2121 NW 21st St", addr_city_state_zip="Miami, FL 33142-7317",
    sector="Employment Services", date="September 6, 2026",
    portal_subdomain="goodwillsouthflorida-benchmark",
    signoff_name="John Wylie", signoff_title="Consulting Partner",
    signoff_firm="ERA Group", signoff_email="jwylie@eragroup.com",
    signoff_phone="703.244.9868",
)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "letter.pdf"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    print("wrote", render(GOODWILL, a.out))
