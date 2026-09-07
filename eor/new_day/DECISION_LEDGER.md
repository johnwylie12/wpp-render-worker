# Decision ledger — Executive Opportunity Brief, Goodwill Industries of South Florida
Account 23895 · built 2026-09-07 · `template_registry` id 23, `doc_type = eob_new_day` v1.0

Every figure was re-queried against `ouzrrkskrfcvtnmhlycd` on 2026-09-07. Nothing was
copied from the build brief into the artifact. That check mattered: **two of the brief's
own vendor figures did not survive it.**

## 1. Factual claims and their sources

| Claim in the document | Source | Verified |
|---|---|---|
| Total revenue $196,096,296 | `v_build_queue` | exact |
| 40 affiliates break out the line | cohort query, §8 of the brief | exact |
| Affiliate median 2.44%, mean 3.77% | same | exact |
| Middle half 1.71–3.86% | same | brief said 1.72–3.87 (rounding) |
| Subject 19.36% | same | exact |
| Southwestern Michigan 20.21%, the only affiliate above | same | exact |
| Houston $224.6M / 1.71% · Columbia Willamette $215.5M / 2.18% | same | exact |
| Manasota $147.0M / 0.80% · Southwest Florida 2.66% · Gulfstream $17.8M / 17.21% | same | exact |
| Four Florida affiliates in the cohort | same | exact |
| Five named contractors and amounts | `account_contractors` | exact |
| 18,482 named contracts · 4,542 organisations · $22.19B | `account_contractors` | exact |
| $42,726,083 evidenced across 3 categories, 171 projects | `fn_recovery_evidence(23895)` | exact |
| Likely recovery $9,007,432 | sum of the three `likely` values | exact |
| ADP 19 orgs, median $225,708, $108,830–$678,036 | `account_contractors` | exact |
| SourceAmerica 13 orgs, median $411,983 | see §3 | exact, with a caveat |

## 2. Derived calculations
- Operating supply as a share of revenue: the filed Operating Supply line divided by
  `revenue_usd`, per filer. No normalisation beyond that, and the document says so.
- $39.03M "named, not modelled" = the nine indirect lines the filing separates that carry
  no completed-work evidence. Derived by subtraction from the twelve-line table, which is
  printed in full so a reader can check the arithmetic.
- Groundwork occupies 2 of 15 sheets — **13%**, against the brief's 40% ceiling.

## 3. Excluded claims — and why

**GALLAGHER BASSETT IS NOT IN THE DOCUMENT.** The brief states *8 organisations, median
$610,618, Goodwill below median.* That figure comes from `ilike '%GALLAGHER%'`, which
matches **Arthur J Gallagher** — a different company — and `GALLAGHER EVELIUS & JONES LLP`,
a law firm. Matching the actual firm returns **2 organisations, one of which is the
subject.** One comparator is not a distribution, and "below median" against a median of two
points including yourself is meaningless. Excluded; the document says on the page that
Gallagher Bassett is named by one other organisation and draws nothing from it.

**SOURCEAMERICA NEEDS A NORMALISED MATCH.** The brief's `ilike '%SOURCEAMERICA%'` returns
6 organisations and a median of $922,664 — which would have collapsed the claim. The firm
is filed under three spellings (`SOURCEAMERICA`, `SOURCE AMERICA`, `Source America`).
Normalising on `upper(replace(name,' ',''))` returns exactly **13 organisations, median
$411,983** — the brief's figure to the dollar. The query in §8 does not reproduce it; the
one in `data_goodwill.py` does.

**"97th percentile" was not printed.** 39 of 40 is the 97.5th. The document says *second of
forty* and *thirty-nine spend less*, which is unambiguous and needs no percentile.

## 4. Unresolved conflicts, and how each was handled

**#206 — `fn_scope_accounting` vs `fn_recovery_evidence`.** `fn_recovery_evidence` used
throughout, as instructed. `fn_scope_accounting` was not called.

**#199 — four surfaces still read the old published bands.** Every percentage in this
document is a completed-work quartile from `fn_recovery_evidence`. **The figures here will
disagree with the portal until #199 is reconciled.** Nothing was reconciled by this build.

**Stage defect in `refresh_category_outcomes()` — measured, and it is live.**
Filtering on `savings_pct` without filtering on `stage` lets Analysis, Research, Selection
and Ceased count as completed work. Measured on the two categories that matter here:

| Category | Current basis | With the stage filter applied |
|---|---|---|
| Operating Supply | 89 | 59 — safe either way |
| **Fleet Management** | 17 | **10 — exactly the ten-job floor** |

Fleet Management is the one category whose eligibility to carry a percentage depends on an
unfixed defect. **Basis used: the current one, via `fn_recovery_evidence`.** If the defect
is fixed and Fleet falls to nine, the three-category figure of $9.01M becomes a
two-category figure and every page carrying it must be rebuilt. Pending John.

## 5. Why each visual form was chosen
- **V1 beeswarm** — 40 points on one axis, so the reader counts rather than trusts. A bar
  chart of 40 affiliates would be unreadable; a box plot would hide that only one sits above.
- **V2 scatter, log revenue** — the two counter-arguments are both about position, so both
  are killed on one pair of axes. Log, because the cohort spans $10.5M to $224.6M.
- **V3 dumbbell** — two points per row, and the distance between them *is* the question.
  The uncertainty annotation sits on the chart, per the definition of done, not in a footnote.
- **V4 concentric, not a funnel** — a funnel implies the outer ring converts into the inner.
  The outer ring carries **no number**, and that absence is the honesty of the chart.
- **V5 six-step flow** — the two steps that cost the client anything are in Decision Cream;
  everything else is ERA capacity. That contrast is the whole argument of the page.

## 6. Definition of done
- [x] Generator committed, registered in `template_registry` (id 23)
- [x] Approved ERA cover rendered through `cover_page_engine` — not redrawn
- [x] Cover letter passes all nine settled #174 assertions, run against the rendered PDF
- [x] Nothing on the letter is `position:absolute` or `position:fixed`
- [x] Every colour resolves to a `brand_tokens` row; zero forbidden near-miss golds
- [x] No occurrence of "savings" as a noun
- [x] No percentage that is not a completed-work quartile
- [x] Groundwork 13% of the experience
- [x] No assertion of spend in an unseen category
- [x] V3 carries its uncertainty annotation on the chart
- [x] Every page rendered and inspected at full size
- [x] Decision ledger delivered
- [ ] **Copy shown to John before final commit** — this delivery is that step

**Known exception:** six spans on the cover sit at 8.7pt, below the 9.5pt floor. They are
in the approved ERA cover asset's benefit strip, which GATE 2 forbids redrawing. Declared
rather than silently fixed.
