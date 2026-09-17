"""Every partner's mark must FIT its block and stay READABLE, in both documents.

This is the test that was missing. Jodi Wiktor signs her full name, so her mark
is 640x122 - aspect 5.25 - where John's initials are 640x472, aspect 1.36. Both
templates pinned WIDTH and let height follow, so one number produced:

    John  115x85 on the cover, 96x77 on the note card
    Jodi  330x63 on the cover, 192x37 on the note card

37px tall on a 5x7 card is not a signature, it is a smudge. The failure is silent
- nothing errors, the PDF renders, and it only shows up when someone looks at the
printed card.

The assertions deliberately do NOT restate the expected pixel sizes for every
partner. A test that retypes the answer is a second copy of it. Instead each mark
is rendered through the REAL template and measured against its own containing
block: it must not exceed it, and it must clear a legibility floor.
"""
import base64
import os
import re
import struct
import sys

import jinja2
import pytest
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from wpp_signatures import PARTNER_SIGNATURE, signature_b64  # noqa: E402

COVER = os.path.join(ROOT, "cover", "WPP_EOP_CoverLetter_TEMPLATE_v2_PARTNER_SIGNOFF.html")
CARD = os.path.join(ROOT, "note_card", "note_card_template.html")

# A mark shorter than this cannot be read as a signature at print size. John's
# marks land at 85 (cover) and 77 (card); this floor is well under both, so it
# only fires on a mark that has been squeezed by an aspect-ratio mismatch.
MIN_LEGIBLE_PX = 60


def _png_dims(b64_text):
    raw = base64.b64decode(re.sub(r"\s+", "", b64_text))
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "signature is not a PNG"
    return struct.unpack(">II", raw[16:24])


def _uri(key):
    return "data:image/png;base64," + signature_b64(key)


def _render(path, ctx):
    with open(path, encoding="utf-8") as fh:
        tpl = jinja2.Environment(undefined=jinja2.Undefined).from_string(fh.read())
    return HTML(string=tpl.render(**ctx)).render().pages[0]._page_box


def _mark_and_container(page_box, predicate):
    """The signature box, and the width of the block that is supposed to hold it."""
    found = None
    stack = [(page_box, None)]
    while stack:
        box, parent = stack.pop()
        if getattr(box, "element_tag", None) == "img" and predicate(box):
            found = (box, parent)
        for child in getattr(box, "children", ()) or ():
            stack.append((child, box))
    return found


def _cover_page(key, name):
    return _render(COVER, dict(
        signature_uri=_uri(key), signoff_name=name, cosigner=None,
        signoff_title="Consulting Partner", signoff_firm="ERA Group",
        signoff_email="x@eragroup.com", signoff_phone="703.000.0000",
        era_logo_uri="", vti_uri="", first_name="Dana", org_name="Test Org",
        sector="health care", date_str="September 17, 2026",
        recipient_name="Dana Lee", recipient_title="CFO", addr_lines=[],
        portal_url="", portal_qr_uri="", access_code="ABC123", subdomain="test",
    ))


def _card_page(key, name):
    return _render(CARD, dict(
        sig_uri=_uri(key), logo_uri="", vti_uri="", tre_r_b64="", tre_b_b64="",
        first="Dana", body=["One.", "Two."],
        signoff={"name": name, "role": "Consulting Partner", "contact": "x@eragroup.com"},
    ))


PARTNERS = sorted(PARTNER_SIGNATURE.items())


@pytest.mark.parametrize("partner_id,key", PARTNERS)
def test_cover_signature_fits_and_is_legible(partner_id, key):
    page = _cover_page(key, "Test Partner")
    hit = _mark_and_container(
        page, lambda b: (b.element.get("src") or "").startswith("data:image/png"))
    assert hit, f"partner {partner_id}: no signature rendered on the cover"
    mark, parent = hit
    assert mark.width <= parent.width + 0.5, (
        f"partner {partner_id} ({key}): mark {mark.width:.0f}px overflows its "
        f"{parent.width:.0f}px block on the cover letter")
    assert mark.height >= MIN_LEGIBLE_PX, (
        f"partner {partner_id} ({key}): mark renders {mark.height:.0f}px tall on "
        f"the cover letter, under the {MIN_LEGIBLE_PX}px legibility floor")


@pytest.mark.parametrize("partner_id,key", PARTNERS)
def test_note_card_signature_fits_and_is_legible(partner_id, key):
    page = _card_page(key, "Test Partner")
    hit = _mark_and_container(
        page, lambda b: "mark" in (b.element.get("class") or ""))
    assert hit, f"partner {partner_id}: no signature rendered on the note card"
    mark, parent = hit
    assert mark.width <= parent.width + 0.5, (
        f"partner {partner_id} ({key}): mark {mark.width:.0f}px overflows the "
        f"{parent.width:.0f}px card measure")
    assert mark.height >= MIN_LEGIBLE_PX, (
        f"partner {partner_id} ({key}): mark renders {mark.height:.0f}px tall on "
        f"the 5x7 card, under the {MIN_LEGIBLE_PX}px legibility floor")


def test_the_marks_really_do_have_very_different_shapes():
    """If this ever stops being true the fix above is no longer load-bearing."""
    aspects = {}
    for _pid, key in PARTNERS:
        w, h = _png_dims(signature_b64(key))
        aspects[key] = w / h
    assert max(aspects.values()) / min(aspects.values()) > 2.0, (
        "partner marks now have similar aspect ratios; re-read whether the "
        f"height-led sizing is still needed: {aspects}")
