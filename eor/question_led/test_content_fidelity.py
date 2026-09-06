"""The guard that should have existed a week ago.

Every complaint that "Claude fucked up the EOR" has the same shape: the document
was regenerated, and copy that John had spent days improving did not come back.
Nothing in the build noticed, because nothing was watching the words.

This test watches the words. It reads the recovered original — the PDF John
identified as the best output yet, committed byte-for-byte in recovered/ — and
asserts that every sentence of it still reaches the rendered page.

It deliberately does NOT check the layout. The look is meant to change; that is
the whole point of the visual work. What must never change silently is the copy.

    python -m pytest eor/question_led/test_content_fidelity.py
"""
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
RECOVERED = os.path.join(HERE, "recovered", "EOR_QUESTION_LED_extracted.json")
CONTENT = os.path.join(HERE, "content_goodwill.json")
OUT = os.path.join(HERE, "out", "interior.pdf")

# Sheets 1-4 and 14 of the original are the cover, the letter and the blanks.
# They are rendered by their own locked engines and are not this engine's copy.
INTERIOR_SHEETS = set(range(5, 14)) | {15}

# Fragments that legitimately do not survive: running furniture the original
# baked into every page, and the page number, which is now a CSS counter.
FURNITURE = re.compile(
    r"^(PAGE \d+ OF \d+|Goodwill Industries of South Florida|Form 990 FY\d+)$"
)


def normalise(s):
    """Compare words, not whitespace. The original was a fixed-position PDF and
    broke its lines mid-sentence; the rebuild reflows. A sentence that survived
    reflow is a sentence that survived."""
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("—", "—").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def original_phrases():
    doc = json.load(open(RECOVERED))
    out = []
    for sheet in doc["sheets"]:
        if sheet["sheet"] not in INTERIOR_SHEETS:
            continue
        for span in sheet["spans"]:
            t = normalise(span["text"])
            # A span is a fragment of a line. Only assert on ones long enough to
            # be a real phrase — short ones are figures and column heads that
            # legitimately move between cells.
            if len(t) >= 40 and not FURNITURE.match(t):
                out.append((sheet["sheet"], t))
    return out


@pytest.fixture(scope="module")
def rendered():
    if not os.path.exists(OUT):
        subprocess.run(
            [sys.executable, os.path.join(HERE, "engine.py"), CONTENT, "--mode", "plain"],
            check=True, cwd=os.path.dirname(os.path.dirname(HERE)),
        )
    import fitz
    doc = fitz.open(OUT)
    return normalise(" ".join(page.get_text() for page in doc))


def test_every_phrase_of_the_original_still_reaches_the_page(rendered):
    """No sentence of John's copy may be dropped by a rebuild."""
    missing = [(sheet, t) for sheet, t in original_phrases() if t not in rendered]
    if missing:
        report = "\n".join(f"  sheet {s}: {t[:96]}" for s, t in missing[:25])
        pytest.fail(
            f"{len(missing)} phrase(s) from the recovered original are not in the "
            f"render. This is the failure mode the EOR keeps having.\n{report}"
        )


def test_the_type_floor_holds(rendered):
    """brand_tokens makes Arial Nova mandatory below 10pt and Arial Nova is not
    in this repo, so nothing may be set below 10pt. The original had 112 spans
    under 9.5pt, down to 7.4."""
    import fitz
    doc = fitz.open(OUT)
    small = []
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if round(span["size"], 1) < 10.0 and span["text"].strip():
                        small.append((round(span["size"], 1), span["text"][:40]))
    assert not small, f"{len(small)} span(s) below the 10pt floor: {small[:8]}"


def test_only_brand_tokens_are_used(rendered):
    """A near-miss brand colour is the specific failure the tokens exist to
    prevent. The original used 15 colours that are not tokens."""
    sys.path.insert(0, HERE)
    from tokens_generated import TOKENS
    import fitz
    allowed = {h.upper() for h in TOKENS.values()}
    doc = fitz.open(OUT)
    stray = set()
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    if span["text"].strip():
                        hexcode = "#%06X" % span["color"]
                        if hexcode not in allowed:
                            stray.add(hexcode)
    assert not stray, f"text colours that are not brand_tokens: {sorted(stray)}"


def test_only_era_typefaces_are_used(rendered):
    """The original was set in Poppins on the cover and Liberation Sans
    everywhere else. Neither is an ERA face."""
    import fitz
    doc = fitz.open(OUT)
    families = set()
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    families.add(span["font"].split("+")[-1].split("-")[0])
    assert families <= {"Paralucent", "Trebuchet"}, f"non-ERA typeface in output: {families}"
