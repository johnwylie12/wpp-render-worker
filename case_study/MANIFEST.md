# ERA Case Study One-Pagers — Kit v1 (locked 2026-07-08)

Reusable, self-contained kit that renders ERA customer case studies as portrait
one-pagers in the WPP package house style. Built to slot into the printed/mailed
package alongside the cover page, cover letter, CIR, and sector benchmark.

## Files
- `case_study_template.html` — Jinja template (portrait, 8.5x11in).
- `case_study_engine.py` — 6 studies as data + `render_one(data, out_pdf)`;
  run `python3 case_study_engine.py <out_dir>` to render all six.
- `assets/fonts/` — Lora + Poppins (Regular/SemiBold/Bold), base64-embedded at render.
- `assets/era_logo.png` — navy ERA Group wordmark, transparent background.
- `prospect_case_study_map.csv` — which study(ies) go with each of the 18-wave prospects.
- `out/` — the six rendered PDFs.

## Brand lock (this kit uses CORRECT Playbook color)
- Navy = Daybreak Blue **#003A70**; Gold = Sunrise Yellow **#FF9C00**; Cool Grey #97999B.
- Fonts: Lora (display) + Poppins (body) — the package substitute for Paralucent/Trebuchet.
- NOTE: the earlier package pieces (cover_page, cir_template.html, sector benchmarks)
  are still on the OLD sampled palette #01426F / #E9B417 and must be corrected to
  #003A70 / #FF9C00 to match. Tracked separately.

## Layout rules (verified)
- Portrait; header pill + ERA logo; Lora headline; left column = client/challenge/
  solution/result; right rail = realized total + category table (or bullet list) + quote.
- Footer is absolutely positioned with a reserved bottom zone; content clears it by
  >=50px on the densest page (box-verified, not eyeballed).
- Body 11pt. Category rows sorted by dollar descending (telecom never leads).
- Case studies use realized **"savings"** language (proof), NOT "Opportunity"
  (Opportunity is reserved for prospect ESTIMATES: CIR / benchmark).

## The six studies (realized savings) + tags
| slug | client | realized | supports (vertical) |
|---|---|---|---|
| one_community_health | One Community Health (FQHC) | $645,583 | community_health |
| north_texas_food_bank | North Texas Food Bank | $200,500 | food_bank, human_services |
| methodist_retirement_communities | Methodist Retirement Communities | $285,250 | senior_living |
| delaware_hospice | Delaware Hospice | $3,500,000 | hospice_living, health_system |
| catholic_charities_denver | Catholic Charities of Denver | $1,116,000 | human_services |
| bethesda_health_group | Bethesda Health Group | $128,860 | senior_living, hospice_living |

Aggregate proof: **~$5.88M realized across 6 nonprofit/health clients** (for a
future case-study section cover page that summarizes the count).

## How selection works
`studies_for(vertical)` returns the matching study slug(s). `vertical` is the same
key used for the cover hero (`coverVertical`), resolved from `accounts.sub_industry`
via `DB_SUBINDUSTRY_TO_VERTICAL`. One vertical resolution drives hero + case study.

## DATA GAP (blocks DB-driven auto-inclusion) — proposed, NOT executed
As of 2026-07-08 the 18-wave accounts are not ready for auto-selection:
1. `sub_industry` is NULL for 18 of 19 (only McLeod = "Medical & Surgical Hospitals").
   Until it's set, `studies_for()` can't resolve from the DB — selection is manual
   via `prospect_case_study_map.csv`.
2. Duplicate account rows persist (Carolina Health Centers x3, Penick x3, Rural
   Health / Family / Moravian / Still Hopes / Thompson / Tri County / New Horizon x2).
   Canonical id per prospect must be chosen (merge_accounts keeper/loser) before tagging.

Proposed fix (present for review before running; log prior state to a backup table):
```sql
-- 1) pick canonical id per prospect, merge dupes:  merge_accounts(keeper_id, loser_id)
-- 2) set sub_industry on the canonical rows so coverVertical + studies_for resolve, e.g.:
-- UPDATE accounts SET sub_industry='FQHC / Community Health Center'
--   WHERE id IN (<canonical FQHC ids>);
-- UPDATE accounts SET sub_industry='Elderly Care Services'
--   WHERE id IN (<canonical senior-living ids>);
-- (verticals then flow to hero + case study automatically)
```

## Lock-down / persistence
`/mnt/outputs` is ephemeral. To persist, commit this kit into a repo (recommended:
`wpp-render-worker/case_study/`) so it survives and is ready to wire as a
`case_study` doc_type (same pattern as the cover: register a content_contract,
add to CLAIM_DOC_TYPES, branch in worker.py build_pdf).
