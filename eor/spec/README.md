# The EOR specification — read this before touching eor_engine.py

Two settled decisions govern this document. Read both before writing a line.

**#172 — the frozen structure and voice.** Sheet order, the bridge page, the
five-paragraph letter, the banned and required phrases, provenance, the cover
rule. Recovered 2026-09-04 after the original generator was lost with a chat
container.

**#173 — the selection logic.** John's written assessment of the first rebuild.
This is the one that matters most, because the first rebuild was structurally
correct and analytically wrong.

## The error to never repeat

The rebuild asked *which filed categories are biggest*. The canonical EOR asks
*where does the account differ from peers, which categories have enough evidence
to support a real question, and where does the organization appear well
positioned.*

Ranking priorities by spend size is the regression. **Priorities are earned on
evidence strength first, then materiality, then executive usefulness.**

Generic published recovery ranges are **category ranges, not peer benchmarks**.
Substituting one for the other is what removed the analytical spine.

## Before showing any version

Run the ten-item acceptance test in #173. The first question is the test:
*can a reader tell in thirty seconds how many categories were examined, how many
sit above peer median, and how many are evidence-supported priorities?*

`eor_engine.py` currently fails that test. It is committed so it cannot be lost,
not because it is right.
