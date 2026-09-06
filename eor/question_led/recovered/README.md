# The question-led EOR, recovered from the only copy that existed

`EOR_Goodwill_QUESTION_LED_2026-09-05.pdf` is the version John identified on
2026-09-06 as "the best output yet". Until this commit it existed **only** as
that one PDF. It was not in this repo, not in WPP-Prospecting-App, and not on
any of the 17 remote branches — searched for its own distinctive copy
("Where we would start", "Uniforms and linens, start to finish", "PAGE 1 OF 16")
with zero hits. That is open_finding #212, and #195 before it, and the
postmortem inside settled #172 before that. Three times.

**That is the whole reason this document keeps getting destroyed.** With no file
to edit, a session asked to improve the EOR cannot edit it — it regenerates it,
and a regeneration is a different document. The content John has been improving
for a week lived one lost container away from gone.

## What is here

| file | what it is |
|---|---|
| `EOR_Goodwill_QUESTION_LED_2026-09-05.pdf` | the artifact itself, byte-for-byte. sha256 `b3c3bf9fceee0399…` |
| `EOR_QUESTION_LED_extracted.json` | every one of its 572 text spans, 224 vector drawings and 16 images, with font, size, colour, and page coordinates |
| `sheetNN_imgN.png` | every embedded image, extracted |

The JSON is the recovery. The PDF is text and vectors, not scans, so the
extraction carries the real content and layout — enough to rebuild a generator
and to prove the rebuild matches.

## What this is NOT

It is not a generator, and nothing here renders. It is the safety net, committed
first and on its own so that the recovery is never again the same commit as a
change. **Do not edit these files.** They are the reference to diff against.

## The sixteen sheets, as they render today

    1  Cover                                     9  Every line
    2  blank (saddle-stitch, per settled #172)  10  How this works, on one of your lines
    3  Cover letter                             11  The big one
    4  blank (per #172)                         12  A second opinion
    5  You may already have this covered        13  What happens next
    6  What stood out                           14  blank (per #172)
    7  Executive Opportunity Snapshot           15  The look
    8  Where we would start                     16  Back cover

Sheets 2, 4 and 14 are **deliberately blank** — the four-sheet saddle-stitch
imposition frozen in settled #172. They are not a defect. Do not remove them.

## Measured state of the file, 2026-09-06

Recorded here so later work is judged against numbers rather than impressions.

- **15 of the 26 distinct colours in use are not in `brand_tokens`**, including
  `#002B54`, which token rule 34 forbids by name, and five separate greys
  (`#3C4658` `#1A1A1A` `#5A5A5A` `#4A4A4A` `#5A6672`).
- **112 text spans sit below the 9.5pt floor**, down to 7.4pt.
- **Two typefaces, neither of them an ERA face**: the cover is Poppins, every
  other sheet is Liberation Sans. `brand_tokens` specifies Paralucent, Trebuchet
  MS, and Arial Nova below 10pt — all three are already in `fonts/`.
- **The cover sets "VALUE THROUGH INSIGHT™" as 19 hand-letterspaced type spans.**
  Every interior sheet uses the real lockup image. Settled #175 / LAW 23 says
  brand marks are assets, never type.

None of that is fixed here. This commit changes nothing about the document.
