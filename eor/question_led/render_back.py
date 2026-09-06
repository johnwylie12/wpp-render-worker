#!/usr/bin/env python3
"""Render the back cover.

    python eor/question_led/render_back.py --out covers/back_value_selling.pdf

WHY THIS FILE EXISTS. The back cover was John's artwork and it lived only inside
a rendered PDF. It was rebuilt once, by hand, in a chat container — which is the
exact failure open_findings #195 and #212 record: an artefact with no source, so
every "improvement" is a fresh act of drawing rather than an edit. The source is
now baseline/BEST_SO_FAR_2026-09-06.pdf plus this script, and the two together
reproduce the page byte-for-byte on any machine.

WHAT IT CHANGES, AND WHAT IT LEAVES ALONE.
  * The 990-mechanics paragraph is replaced with the value-selling close. John
    asked for that copy; the words below are his and Chat's, not mine.
  * The four contact lines are RESET, not rewritten. They arrived in Carlito —
    LibreOffice's Calibri clone, not an ERA face and not a face John chose; it is
    what a substitution engine reached for. Same words, same sizes, same colours,
    same baselines, in Paralucent. The ground behind them is flat #003A70, so a
    per-line redaction is safe here in a way it was NOT on the front cover, where
    the fill sampled text colour over a diagonal photograph and wrecked the page.
  * Nothing else on the page is touched.
"""
import argparse, os, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BASELINE = os.path.join(HERE, "baseline", "BEST_SO_FAR_2026-09-06.pdf")
BACK_PAGE = 15                                   # 0-indexed; the last leaf
NAVY = (0x00 / 255, 0x3A / 255, 0x70 / 255)      # ERA Navy, the flat ground here

MEDIUM = os.path.join(REPO, "fonts", "fonnts.com-Paralucent_Medium.otf")
LIGHT = os.path.join(REPO, "fonts", "fonnts.com-Paralucent_Light.otf")

HEADLINE = "What the filing reveals is only the beginning."
BODY = (
    "A Form 990 shows selected expense lines. ERA brings the category specialists, "
    "contract and invoice analysis, market knowledge, implementation support and "
    "measurement needed to examine the full indirect-spend portfolio.",
    "Across every applicable category, the objective is the same: validate what is "
    "already working, recover value where the evidence supports it, and return more "
    "dollars to mission.",
)
STRIP = "55 categories  ·  one evidence-led process  ·  results measured after implementation"

# lines of the ORIGINAL that the new close replaces
KILL_EXACT = {"What we could see is", "the smaller half."}
KILL_PREFIX = ("A Form 990 breaks out", "actually buys never", "processing. The categories")


def wrap(font, text, size, width):
    out, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if font.text_length(trial, size) > width and line:
            out.append(line); line = word
        else:
            line = trial
    if line:
        out.append(line)
    return out


def render(out_pdf):
    src = pymupdf.open(BASELINE)
    page = src[BACK_PAGE]
    fm = pymupdf.Font(fontfile=MEDIUM)
    fl = pymupdf.Font(fontfile=LIGHT)

    # ── 1. lift the contact block off the page, remembering exactly how it sat ──
    # Carlito alone is NOT the filter. The paragraph being REPLACED is set in
    # Carlito too, so filtering on the face swept it up and re-typeset the very
    # lines the redactions had just removed — the old copy came back, in a new
    # font, under the new copy. The contact block is the material below the
    # strip line at y=452; that is what makes it the contact block.
    CONTACT_TOP = 465
    contact = []
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            for sp in ln["spans"]:
                if "Carlito" in sp["font"] and sp["bbox"][1] >= CONTACT_TOP:
                    contact.append(dict(
                        text=sp["text"], size=sp["size"], origin=sp["origin"],
                        bold="Bold" in sp["font"],
                        colour=tuple(((sp["color"] >> s) & 255) / 255 for s in (16, 8, 0)),
                        bbox=sp["bbox"]))

    # ── 2. redactions: the replaced paragraph, and the contact lines ───────────
    for blk in page.get_text("dict")["blocks"]:
        for ln in blk.get("lines", []):
            t = "".join(s["text"] for s in ln["spans"]).strip()
            if t in KILL_EXACT or t.startswith(KILL_PREFIX):
                r = pymupdf.Rect(ln["bbox"])
                page.add_redact_annot(pymupdf.Rect(r.x0 - 2, r.y0 - 3, r.x1 + 4, r.y1 + 4), fill=NAVY)
    for c in contact:
        x0, y0, x1, y1 = c["bbox"]
        page.add_redact_annot(pymupdf.Rect(x0 - 2, y0 - 1.5, x1 + 3, y1 + 1.5), fill=NAVY)
    page.apply_redactions()

    page.insert_font(fontname="PLM", fontfile=MEDIUM)
    page.insert_font(fontname="PLL", fontfile=LIGHT)

    # ── 3. the value-selling close ────────────────────────────────────────────
    x, y = 68.4, 180
    for line in wrap(fm, HEADLINE, 22, 420):
        page.insert_text((x, y), line, fontname="PLM", fontsize=22, color=(1, 1, 1)); y += 29
    y += 22
    for para in BODY:
        for line in wrap(fl, para, 10.4, 430):
            page.insert_text((x, y), line, fontname="PLL", fontsize=10.4,
                             color=(0.86, 0.90, 0.96)); y += 16.8
        y += 12
    page.insert_text((x, 452), STRIP, fontname="PLL", fontsize=9, color=(0.62, 0.70, 0.82))

    # ── 4. the contact block back, same words, on an ERA face ─────────────────
    for c in contact:
        page.insert_text(c["origin"], c["text"], fontsize=c["size"], color=c["colour"],
                         fontname="PLM" if c["bold"] else "PLL")

    out = pymupdf.open()
    out.insert_pdf(src, from_page=BACK_PAGE, to_page=BACK_PAGE)
    out.save(out_pdf)
    return out_pdf


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "covers", "back_value_selling.pdf"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    print("wrote", render(a.out))
