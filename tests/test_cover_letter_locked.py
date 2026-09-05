"""The cover letter is LOCKED. These tests are the lock.

Every assertion here corresponds to a defect that reached a rendered PDF and had
to be corrected by John rather than caught by the build. They run against the
RENDERED PDF, never against the HTML, because every one of these bugs looked
correct in the CSS.
"""
import os, sys
import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "cover"))

pytest.importorskip("weasyprint")
from pypdf import PdfReader                      # noqa: E402
import cover_engine                              # noqa: E402

SIGNOFF = {
    "partner_id": 3, "signoff_name": "John Wylie",
    "signoff_title": "Consulting Partner", "firm": "ERA Group",
    "email": "jwylie@eragroup.com", "phone": "703.244.9868",
    "signature_key": "3",
}


@pytest.fixture(scope="module")
def letter(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("cl") / "letter.pdf")
    c = cover_engine.build_cover(
        {"recipient": {"name": "Chief Financial Officer",
                       "title": "Chief Financial Officer",
                       "company": "Coastal Enterprises of Jacksonville",
                       "address_lines": ["4915 Western Blvd",
                                         "Jacksonville, NC 28546"]},
         "sector": "employment services",
         "portal": {"slug": "coastalenterprises-benchmark"},
         "signoff": SIGNOFF},
        None, "Coastal Enterprises of Jacksonville", date_str="September 4, 2026")
    c["first_name"] = "Chief Financial Officer"
    cover_engine.render_cover(c, out, page_size="letter")
    r = PdfReader(out)
    return r, (r.pages[0].extract_text() or "")


def test_exactly_one_page(letter):
    """An EMPTY second page is what overflow looks like here, and it shipped
    twice while page one was being inspected in isolation."""
    r, _ = letter
    assert len(r.pages) == 1, f"letter must be one page, got {len(r.pages)}"


def test_signature_renders(letter):
    """Every render came out unsigned for an entire session because
    allow_unsigned was passed instead of partner_id + signature_key. Three
    images is the signal: ERA logo, signature, QR."""
    r, _ = letter
    assert len(r.pages[0].images) == 3, "expected logo, signature and QR"


def test_no_access_code_anywhere(letter):
    """LAW 9 / settled #86. The guard used to REQUIRE a code and drop the whole
    portal block without one, enforcing the opposite of the law."""
    _, t = letter
    low = t.lower()
    assert "access code" not in low
    assert "?c=" not in t
    assert "no code. no form. no login." in low


def test_recipient_title_not_duplicated(letter):
    """recipient_name falls back to the title when no name is validated, so the
    title printed on both lines of the address block."""
    _, t = letter
    assert t.count("Chief Financial Officer") <= 2


def test_no_invented_or_generic_salutation(letter):
    """No validated name means we address the OFFICE. We never invent a person,
    and 'Dear Colleague' reads as a circular on a document that claims to be
    prepared exclusively."""
    _, t = letter
    assert "Dear Chief Financial Officer," in t
    assert "Dear Colleague" not in t


def test_portal_url_is_clean_and_unbroken(letter):
    """The URL must be one readable line with no wrap and no hidden character."""
    _, t = letter
    assert "portal.wpp-us.com/coastalenterprises-benchmark" in t


def test_four_body_paragraphs(letter):
    """Four, not five. It is an executive note, not a mini-report."""
    _, t = letter
    for opener in ("We prepared the enclosed", "The Report was built",
                   "ERA Group has reviewed", "If the analysis is directionally"):
        assert opener in t, f"missing paragraph: {opener}"


def test_voice(letter):
    """WE, never I. And no banned vocabulary (LAW 8)."""
    _, t = letter
    assert "I would welcome" not in t
    assert "We work in one thing" not in t
    low = t.lower()
    assert "savings" not in low
    assert "Consulting Partner" in t and "Senior Consultant" not in t


def test_no_unrendered_placeholders(letter):
    _, t = letter
    assert "{{" not in t and "[Name" not in t
