"""The v4 VALUE-SELLING cover letter is LOCKED. These tests are the lock.

WHY A SECOND LOCK FILE. test_cover_letter_locked.py locks the v2 partner-signoff
template through cover_engine. That is a different template from the one this
document actually ships — v4, rendered by eor/question_led/render_letter.py — and
it was covered by nothing at all. Every defect corrected in v4 today (Liberation
Sans winning the font stack, an 8.4pt proof strip, a two-page overflow) would
have shipped again with the v2 lock passing.

They run against the RENDERED PDF, never the HTML, because every one of these
bugs looked correct in the CSS.

REV-6, 2026-09-06. The portal URL and the access line were 9pt inside a block
marked LOCKED. brand_tokens row 12 makes Arial Nova mandatory below 10pt and
Arial Nova is not in this repo, so those two spans were quiet non-compliance
sitting under a lock. John amended the lock to 10pt. test_nothing_is_below_the
_type_floor is the assertion that makes the amended value test true instead of
merely reading true in a comment — and test_portal_url_is_one_unbroken_line is
what stops the wider URL wrapping in its 2.6in column without anyone noticing.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "eor", "question_led"))

pytest.importorskip("weasyprint")
pymupdf = pytest.importorskip("pymupdf")

import render_letter                                  # noqa: E402

FLOOR = 10.0                    # brand_tokens row 12
ERA_FACES = {"Paralucent", "Trebuchet"}


@pytest.fixture(scope="module")
def letter(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("v4") / "letter.pdf")
    render_letter.render(render_letter.GOODWILL, out)
    doc = pymupdf.open(out)
    return doc, " ".join(p.get_text() for p in doc)


def spans(doc):
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if span["text"].strip():
                        yield page, span


def test_exactly_one_page(letter):
    """An EMPTY second page is what overflow looks like here, and it shipped
    twice while page one was being inspected in isolation. Putting the real
    Trebuchet in front of Liberation Sans widened the text and did it again."""
    doc, _ = letter
    assert doc.page_count == 1, f"letter must be one page, got {doc.page_count}"


def test_logo_signature_and_qr_all_render(letter):
    doc, _ = letter
    assert len(doc[0].get_images()) >= 3, "expected ERA logo, signature and QR"


def test_nothing_is_below_the_type_floor(letter):
    """REV-6. brand_tokens row 12: below 10pt no face but Arial Nova is
    permitted, and Arial Nova is not in this repo."""
    doc, _ = letter
    small = [(round(s["size"], 1), s["text"][:40]) for _, s in spans(doc)
             if round(s["size"], 1) < FLOOR]
    assert not small, f"{len(small)} span(s) below the {FLOOR}pt floor: {small[:6]}"


def test_only_era_typefaces(letter):
    """Liberation Sans was listed FIRST in the stack, so the real Trebuchet
    sitting in fonts/ was never reached and no test noticed."""
    doc, _ = letter
    families = {s["font"].split("+")[-1].split("-")[0].split(" ")[0] for _, s in spans(doc)}
    assert families <= ERA_FACES, f"non-ERA typeface in the letter: {families}"


def test_portal_url_is_one_unbroken_line(letter):
    """At 10pt the URL is wider than it was at 9pt. It must still be a single
    span on one line, inside the page margin, not wrapped and not overhanging."""
    doc, text = letter
    slug = render_letter.GOODWILL["portal_subdomain"]
    assert f"portal.wpp-us.com/{slug}" in text
    hits = [(p, s) for p, s in spans(doc) if "portal.wpp-us.com" in s["text"]]
    assert len(hits) == 1, f"the URL is split across {len(hits)} spans — it wrapped"
    page, span = hits[0]
    assert span["text"].strip() == f"portal.wpp-us.com/{slug}"
    assert span["bbox"][2] <= page.rect.width - 56, "the URL runs into the right margin"


def test_no_access_code_anywhere(letter):
    """LAW 9 / settled #86. The guard used to REQUIRE a code and drop the whole
    portal block without one, enforcing the opposite of the law."""
    _, text = letter
    low = text.lower()
    assert "access code" not in low
    assert "?c=" not in text
    assert "no code. no form. no login." in low


def test_four_body_paragraphs(letter):
    """Four, not five. It is an executive note, not a mini-report."""
    _, text = letter
    for opener in ("We prepared the enclosed", "The Report was built",
                   "ERA Group has reviewed", "This Report identifies"):
        assert opener in text, f"missing paragraph: {opener}"


def test_voice(letter):
    """WE, never I. And no banned vocabulary (LAW 8)."""
    _, text = letter
    assert "I would welcome" not in text
    assert "savings" not in text.lower()
    assert "Consulting Partner" in text and "Senior Consultant" not in text


def test_salutation_is_the_validated_person(letter):
    _, text = letter
    assert f"Dear {render_letter.GOODWILL['first_name']}," in text
    assert "Dear Colleague" not in text


def test_no_unrendered_placeholders(letter):
    _, text = letter
    assert "{{" not in text and "[Name" not in text
