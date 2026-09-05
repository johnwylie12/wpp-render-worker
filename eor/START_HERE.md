# EOR REBUILD — START HERE

**Three of sixteen pages are done. This is a page-by-page rebuild, not a redesign.**
Do not restart. Do not re-derive anything below.

## Read first — thirty minutes, in this order

Run `select * from wpp_start();` then read these settled decisions:

| # | What it governs |
|---|---|
| **172** | The frozen spec. Sheet order, the bridge page, the letter, the voice. **The cover comes from the repo template, never drawn.** |
| **173** | Selection logic. **Priorities are earned on evidence, never spend size.** Its ten-item acceptance test is run before showing John anything. |
| **174** | The letter is locked. `tests/test_cover_letter_locked.py` is the lock. |
| **175** | LAW 23 — brand marks are **assets, never type**. The sanctioned palette. |
| **178** | LAW 25 — every figure carries meaning, position, **proof**, purpose. |
| **179** | LAW 26 — every filed indirect line appears in the Report. Enforced in `release_gate`. |
| **180** | LAW 27 — recovery quoted from **completed work**, never a published band. |
| **200** | **What was got wrong.** The economics and the ICP contradict #106. Read it. |

## Built, and where

| Page | File | State |
|---|---|---|
| Cover letter | `cover/cover_engine.py` | done, locked, 9 tests |
| 5 — Executive Overview | `eor/overview_page.py` | done |
| Snapshot | `eor/snapshot_page.py` | done |
| 16-page shell | `eor/eor_engine.py` | **fails #173. Not canon.** |

`eor/spec/` holds the frozen spec, the Brand Playbook, `STYLE_TOKENS.json`, and a
`REFERENCE_*.pdf` of every approved page. **Diff against those.**

Worked example: **Goodwill Industries of South Florida, account 23895.**

## The data model — use it, do not rebuild it

```
v_recovery_model            the single evidence model. Every surface reads this.
fn_recovery_evidence(id)    weak / likely / strong per category, completed projects
fn_recovery_summary(id)     the roll-up
fn_scope_accounting(id)     every filed indirect dollar bucketed WITH THE REASON
v_named_not_modelled        what we do not model, and why, in plain language
category_outcome_evidence   quartiles of completed ERA projects, 15-project floor
category_outcome_crosswalk  990 vocabulary -> era_projects vocabulary
v_law26_gap                 per-account: what the page is not showing
```

## Three rules that cause the most rework

**1. One type scale, five steps — 22 / 16 / 11 / 10 / 8.**
Nothing below 10pt except letterspaced caps. A page needing 9pt has a *content*
problem; cut words. The overview was running twelve sizes and that alone made it
look cheap.

**2. Nothing is `position:absolute` or `position:fixed`.**
Both appeared on the letter and both produced the same symptom — a block that moves
into whatever is near it whenever anything changes size. Running furniture goes in
the `@page` margin box.

**3. Assert against the rendered PDF, never the HTML — and always assert page count.**
An empty second page is what overflow looks like here, and it shipped twice while
page one was being inspected alone.

## Thirteen pages remaining, in spec order

```
 1  cover          cover_page_engine + hero_vertical_map. Exists, needs wiring.
 6  the bridge     "Five things stood out. None of them is a conclusion."
                   FIVE CARDS, NO FIGURES ANYWHERE. Fifth set apart in gold for
                   the one question that could CHANGE the answer.
 7  what your own numbers say     the full category table
 8  the position, as we read it
 9  where we looked               the second filing
10  priority 1     six parts: what we see / why it matters / what may be driving
                   it / what we do not know / what we would test first /
                   potential impact if validated
11  priority 2     ONLY IF IT EARNS A PAGE ON EVIDENCE (#173)
12  what this rests on            nine layers, empty ones shown empty
13  what happens next
15  inside back    16  back cover
```

## Open and blocking

- **#200** — partner economics and ICP are wrong. **No earnings figure is quoted
  anywhere** until John rules. #177 is suspended.
- **#199** — four surfaces still read the old bands. `fn_portal_payload` above all:
  the portal and the EOR currently disagree about the same account.
- **#197** — `addressable_lines` and `fn_portal_payload` disagree on category count.
- **#198** — $69.1B of filed indirect never reaches a page across the book.

## The one thing that matters most

John has corrected the same page six times in one session because work was redone
rather than read. **Every page has a reference render in `eor/spec/`.**

Diff against it. Change the one thing asked for. Render. **Look at the PDF.** Show him.
Nothing else.
