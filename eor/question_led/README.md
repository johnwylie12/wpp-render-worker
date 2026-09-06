# The question-led EOR — the generator

`recovered/` holds the original and why it had to be recovered. This directory
is the thing that means it never has to be recovered again.

## Run it

    python eor/question_led/engine.py content_goodwill.json --mode both

Writes `out/EOR_<slug>_plain.pdf` and `out/EOR_<slug>_stitched.pdf`.

## The four files, and which one to open

| you want to change | open |
|---|---|
| **the words, a figure, a table row** | `content_goodwill.json` |
| how something *looks* — spacing, colour, a component | `styles.css` |
| a new kind of block that does not exist yet | `engine.py`, `block()` |
| the palette | nothing here. Change `brand_tokens`, re-run `generate_tokens.py` |

That split is the point. John, 2026-09-06: *"I am so tired of having to work
through templates over and over and over again. We are improving the content of
the EOR and Claude just fucks the entire document up."* Content and layout were
the same artifact, so every content edit was a layout risk. Now a copy change
touches one JSON file and cannot move a margin.

## The page count is not frozen

John, 2026-09-06: *"We do not have to freeze the number of the pages. For the
15th time... If it takes a few more pages, then great as long as they are
delivering value."*

Nothing here writes down a page count.

* The running foot prints `counter(page)` of `counter(pages)` — the real
  numbers. The recovered original printed "PAGE 3 OF 16" on a document that
  delivered ten numbered pages, because the total was typed rather than counted.
* The header and the foot are `@page` furniture, not content, so a sheet whose
  content runs long becomes two properly dressed pages instead of one page plus
  an orphan. The first render of this engine produced four orphans, one carrying
  nothing but a header.
* **Two impositions, one content set.** `plain` for duplex and screen;
  `stitched` inserts blank versos and pads to a multiple of four for the
  saddle-stitch production that is not nailed down yet. Add a sheet and the
  padding re-solves itself. Neither version is more canonical than the other and
  both are written by one call so they cannot drift.

## What is enforced, and where

`test_content_fidelity.py` is the guard that did not exist while the document
was being lost. It reads the recovered original and asserts:

1. **Every phrase of John's copy still reaches the rendered page.** This is the
   one that matters. Every "Claude fucked up the EOR" has been copy silently not
   coming back from a rebuild, with nothing watching the words.
2. Nothing is set below **10pt** — `brand_tokens` makes Arial Nova mandatory
   under 10pt and Arial Nova is not in this repo, so the floor keeps the
   document compliant with a font we actually have.
3. Every text colour is a **brand_token**.
4. Every typeface is an **ERA face**.

It deliberately does not test the layout. The look is meant to change.

## Measured, original against this render

| | recovered original | this engine |
|---|---|---|
| typefaces | Poppins (cover) + Liberation Sans — neither is ERA | Paralucent + Trebuchet MS |
| smallest type | 7.4pt; 112 spans below 9.5pt | 10.0pt; none below |
| colours not in `brand_tokens` | 15 of 26, incl. `#002B54` which rule 34 forbids by name | 0 |
| printed page total | "OF 16" on a 10-page document | computed |

## What this does NOT do

It does not draw the cover and it does not lay out the cover letter. Both exist,
both are locked, and re-implementing them is the exact mistake settled #172
records **twice** — *"THE REPO TEMPLATE IS THE COVER. Do not draw one."* — and
that settled #174 guards with nine assertions in
`tests/test_cover_letter_locked.py`. Pass them in:

    --cover  out of cover/cover_page_engine.py
    --letter out of cover/cover_engine.py
    --back   the back cover

## Open, and needing John

* **Three sheets spill a few lines onto a thin page** (currently pages 3, 8 and
  13). That is real content, not a layout bug — five substantial cards do not
  fit one page. Either accept the thin pages or shorten the copy; it is a
  content decision and not one to make on John's behalf.
* **Arial Nova is not in the repo.** The 10pt floor sidesteps it. If small
  letterspaced caps are ever wanted below 10pt, the font has to be licensed and
  added first.
* **`brand_tokens` rule 33 (nothing below 9.5pt) contradicts settled #172**
  ("nothing below 8.4 and that only for letterspaced eyebrow caps"). The tokens
  are newer — locked 2026-09-06 — so they win here, but the conflict is real.
* **Chat's review recommends five colours the tokens forbid**, `#D88700` and
  `#002B54` by name. Its *rules* are adopted; those two hexes are not. The
  substitutes are Sunrise at a 75% tint, and Midnight Blue `#111127`.
