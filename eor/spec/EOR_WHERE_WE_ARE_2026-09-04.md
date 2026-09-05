# EOR — WHERE WE ARE
**Session close, 4 September 2026.** Read this cold; it assumes nothing.

---

## The short version

Three of sixteen pages of the Executive Opportunity Report are built and approved.
Everything is committed. Nothing is lost. **Nothing is mailing and nothing is at risk.**

Two things are wrong and are recorded as blockers: the **partner economics**
and the **ICP** were both derived tonight without reading decisions that already
existed, and they contradict them.

---

## What is built

| | Where | State |
|---|---|---|
| Cover letter | `cover/cover_engine.py` | Done. Locked. 9 tests. |
| Page 5 — Executive Overview | `eor/overview_page.py` | Done. |
| Snapshot | `eor/snapshot_page.py` | Done. |
| 16-page shell | `eor/eor_engine.py` | **Fails the acceptance test. Not canon.** |

Rendered set: **`EOR_Goodwill_SouthFlorida.pdf`** — letter, overview, snapshot.
Worked example is **Goodwill Industries of South Florida**, account 23895.

Every approved page has a reference render in `eor/spec/`. **Diff against those
rather than rebuilding.**

---

## The thing I could not explain well tonight — in plain terms

You asked why we only modelled two categories. Here is the whole logic, in order.

**1. Their filing lists 12 lines of indirect spend.** $82.1M. That is everything
they spend that is not payroll, depreciation, interest or grants.

**2. Seven of those 12 map to a category ERA works.** The other five are lines
like *Occupancy* — one number covering rent, utilities, maintenance and
janitorial. We work everything in it except the rent, and a Form 990 does not
separate them. So we name it and do not estimate it.

**3. Of those seven, only two have enough completed ERA projects behind them
to quote a real outcome.** Operating supply (69 projects) and freight (89).

**4. So the $8.7M comes from two categories only.** It is a floor, not a
forecast. Everything else is upside sized in the baseline.

**And here is the part that is our problem, not theirs:**

| Category | Why it was not modelled | My verdict |
|---|---|---|
| **Office Supplies** | Sits on an exclusion list — **despite ERA having 204 completed projects at a 25% median** | **Wrong. Should be fixed.** |
| **Fleet** | 13 usable projects; my floor was 15 | **My floor was arbitrary.** |
| Travel | 8 projects, 3% median | Floor is right — a 3% median would weaken the document |
| Marketing | 5 projects | Floor is right |
| Professional Services | Excluded by rule | Probably right — legal fees are not sourceable |

Fixing Office Supplies alone moves the figure from $8.7M to roughly $9.0M, and
from **two categories to three** — which matters more, because that is the number
a CFO asks about.

**Two open questions for you.** Why is Office Supplies excluded? There will be a
reason. And is the project floor 15, or 10? I picked 15 without evidence. Both
change every account in the book, so neither should move quietly.

---

## Blockers — read before quoting any number

**#200 — the partner economics are wrong.**
I calculated your share as 20.13% of modelled recovery, giving $1.7M on Goodwill.
ERA's own FDD (settled #106) puts the **median project invoice at $14,632** and the
largest ever raised at **$851,955**. A $1.7M partner share implies a $4.2M fee —
five times the biggest project ERA has ever invoiced. **Quote no earnings figure
anywhere until this is settled.**

**#200 also — the ICP includes accounts you may not solicit.**
A $250M–$1B prospect is an **ERA Threshold Account**: must be referred to ERA, may
not be knowingly solicited. I ranked that band as the first priority. **Decision
#177 is suspended.**

**#199 — the portal and the EOR disagree about the same account.**
The EOR now quotes completed-work outcomes; `fn_portal_payload` still quotes
published bands. 166 portals are live carrying the old number.

**#198 — $69.1B of filed indirect never reaches a page** across the book. Mostly
occupancy and catch-all lines.

**#197 — two functions disagree** on how many categories an account has.

---

## Where to start tomorrow

**Say: "read `eor/START_HERE.md`, then page 6."**

That file names the eight decisions to read first, the data model not to rebuild,
and the three rules that cause the most rework. It exists so the next session
reads instead of re-deriving.

Page 6 is **the bridge** — *"Five things stood out. None of them is a
conclusion."* Five cards, **no figures anywhere on the page**, the fifth set apart
in gold for the one question that could change the answer.

---

## What was settled today, and holds

| # | |
|---|---|
| **172** | The EOR frozen spec — recovered after it was lost with a chat container |
| **173** | Priorities are earned on evidence, never spend size |
| **174** | The cover letter is locked, with 9 tests against the rendered PDF |
| **175** | LAW 23 — brand marks are assets, never type. The sanctioned palette |
| **178** | LAW 25 — every figure carries meaning, position, proof, purpose |
| **179** | LAW 26 — every filed indirect line appears in the Report. Enforced in the gate |
| **180** | LAW 27 — recovery is quoted from completed work, not a published band |

Plus the data model: `v_recovery_model`, `fn_recovery_evidence`,
`fn_scope_accounting`, `category_outcome_evidence`, `v_named_not_modelled`.

---

## One honest note

Much of tonight was me learning your system and reporting the gaps as findings.
The occupancy exclusion was a good decision someone had already made. Four settled
decisions sat in the database all evening while I derived an ICP that contradicted
them.

`START_HERE.md` and the reference renders exist so that does not repeat.
