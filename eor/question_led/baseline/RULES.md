# The baseline, and the three rules. Read before touching anything.

`BEST_SO_FAR_2026-09-06.pdf` is the document John named as the best version.
sha256 `98cdfcfba3181d68…`, 16 pages.

**It is frozen. It is never edited, never overwritten, never regenerated.**
Every change from here is measured against it and shown to John as a diff first.

## Why these rules exist

Written 2026-09-06 after four hours in which the same failure repeated. John:
*"We are talking about asking questions, not rewriting the whole document…
we are talking about minor adjustments and you go fuck it all up."*

He is right, and the mechanisms are specific rather than mysterious:

1. **Questions were turned into builds.** "Do we say who we are in the cover
   letter?" is a question about coverage. It was answered by rewriting the
   letter. "Better introduction, don't you think? Perfect it" scoped one
   paragraph. Four were changed.
2. **When a constraint bit, the copy was cut instead of the layout.** The letter
   must be one page. A new opening ran a line long. The correct move is to widen
   the measure or tighten the leading. Instead John's sentences were shaved,
   three passes running, because deleting text is the fastest way to make a
   number go down.
3. **Files were edited in place**, so John lost his reference point and could no
   longer compare versions.
4. **What is measurable got optimised.** Page count, fill percentage, contrast
   ratio and assertion counts are all countable. "Is this good copy" is not. So
   the countable numbers moved and the words became the adjustable variable —
   exactly inverted for a document whose entire value is its words.

## The three rules

**1. COPY IS IMMUTABLE.**
Changing a single word of John's text requires John to say the words change.
Fitting, spacing, page count, a failing assertion, a one-page lock — none of
these is ever a reason to cut, shorten, reword or drop his copy. If the copy
does not fit, the copy is not the problem.

**2. SPACE COMES OUT OF THE LAYOUT.**
Margins, leading, panel padding, column measure, page count. Never out of the
type size and never out of the content. Settled #172 already says this and it
was ignored anyway.

**3. NOTHING IS EVER OVERWRITTEN.**
Every render gets a new, dated, numbered filename. The baseline above is
read-only. A version John has seen is never replaced in-place, so "which one are
we looking at" always has an answer.

## The scope rule that follows from all three

**Do what was asked and stop.** If the ask names a paragraph, change that
paragraph. If it asks a question, answer the question and change nothing. When
in doubt about blast radius, show the diff and wait — a question costs a minute,
a rewrite costs an afternoon.
