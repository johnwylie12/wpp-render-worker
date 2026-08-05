#!/usr/bin/env python3
"""US ENGLISH IS LAW — the render worker's gate.

This worker renders the Executive Opening Package: the pages a prospect
physically holds. A British spelling that reaches a printed PDF cannot be
recalled, so the renderer carries its own always-on check rather than trusting
the app's.

It scans the worker's own source and templates — worker.py, wpp_signatures.py,
and every template under cir/, cover/, snapshot/, benchmark/, case_study/,
closing/, exec_brief/, note_card/, meeting_label/, portal_sticker/, pvca/,
enrich_990_xml/ — for the whole words in us_english_rules.json.

Two things it deliberately does NOT flag, both real:
  • ReportLab's drawCentredString and friends. Matching is whole-word, so
    'Centred' inside 'drawCentredString' has no word boundary before it and is
    never a hit. The API name is not copy.
  • 'analyses', 'optimistic', 'realistic', 'de minimis', 'programmer' — correct
    US English that prefix matching would wrongly condemn.

Usage
    python scripts/us_english_gate.py            # check; exit 1 on any hit
    python scripts/us_english_gate.py --fix      # rewrite in place, then read the diff

Exemption: a line carrying `us-english-ok` is skipped, and so is the line
directly below it. Give a reason. The only honest use is code that must MATCH a
British spelling in order to read or strip it.

The word list is a copy of the app's src/lib/usEnglish.rules.json, which is the
source of record (see the note inside us_english_rules.json). Change it there
first, then copy it here in the same change.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RULES = json.loads((REPO / "us_english_rules.json").read_text())["pairs"]
UK_RE = re.compile(r"\b(" + "|".join(sorted(RULES)) + r")\b", re.IGNORECASE)
EXEMPT = re.compile(r"us-english-ok", re.IGNORECASE)

SUFFIXES = {".py", ".html", ".htm", ".jinja", ".j2", ".css", ".json", ".txt", ".md", ".yml", ".yaml"}
SKIP_DIRS = {".git", "__pycache__", "fonts", "node_modules"}
SKIP_FILES = {
    "us_english_rules.json",          # the list itself — it must name the UK words
    "scripts/us_english_gate.py",     # this file
}


def match_case(found: str, replacement: str) -> str:
    if found.isupper() and not found.islower():
        return replacement.upper()
    if found[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def files() -> list[Path]:
    out: list[Path] = []
    for p in REPO.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SUFFIXES:
            continue
        rel = p.relative_to(REPO)
        if set(rel.parts) & SKIP_DIRS or str(rel) in SKIP_FILES:
            continue
        out.append(p)
    return sorted(out)


def main() -> int:
    fix = "--fix" in sys.argv[1:]
    violations: list[tuple[str, int, str, str, str]] = []
    fixed = 0
    scanned = files()

    for path in scanned:
        try:
            lines = path.read_text(encoding="utf-8").split("\n")
        except UnicodeDecodeError:
            continue
        changed = False
        for i, line in enumerate(lines):
            if EXEMPT.search(line) or (i and EXEMPT.search(lines[i - 1])):
                continue
            hits = list(UK_RE.finditer(line))
            if not hits:
                continue
            if fix:
                lines[i] = UK_RE.sub(lambda m: match_case(m.group(1), RULES[m.group(1).lower()]), line)
                changed = True
                fixed += len(hits)
            else:
                for h in hits:
                    violations.append((
                        str(path.relative_to(REPO)), i + 1,
                        h.group(1), RULES[h.group(1).lower()], line.strip()[:140],
                    ))
        if changed:
            path.write_text("\n".join(lines), encoding="utf-8")

    if fix:
        print(f"US ENGLISH: rewrote {fixed} British spelling(s) across {len(scanned)} file(s).")
        return 0

    if violations:
        print(f"::error::US ENGLISH IS LAW — {len(violations)} British spelling(s) in the renderer.")
        print()
        for f, ln, found, us, text in violations:
            print(f'  {f}:{ln}  "{found}" -> "{us}"')
            print(f"      {text}")
        print()
        print("Fix: python scripts/us_english_gate.py --fix   (then read the diff).")
        print("If a line must MATCH the British spelling to read or strip it, mark it")
        print("`us-english-ok — <reason>`. That is the only exemption.")
        return 1

    print(f"US ENGLISH GATE: PASS — {len(scanned)} file(s) scanned, 0 British spellings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
