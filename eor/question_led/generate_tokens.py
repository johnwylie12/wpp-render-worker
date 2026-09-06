#!/usr/bin/env python3
"""Emit eor/question_led/tokens_generated.py from the brand_tokens table.

The palette is a two-sided fact: it lives in Postgres AND it has to reach a
stylesheet. WPP has already paid for that shape once — five production defects
on 2026-08-21 from facts typed by hand on both sides. So this file is the only
place the two sides meet, and tokens_generated.py is never edited by hand.

    python eor/question_led/generate_tokens.py           # writes the module
    python eor/question_led/generate_tokens.py --check    # non-zero if drifted
"""
import json, os, subprocess, sys, textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tokens_generated.py")

QUERY = """
select name, hex, tier, token_type, usage_rule, forbidden
from brand_tokens
where hex is not null and token_type = 'colour'
order by id
"""

def slug(name):
    return name.upper().replace(" ", "_").replace("-", "_")

def fetch():
    """Rows come from the database. A caller may pipe them in as JSON instead,
    which is how CI runs this without a live connection."""
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            return json.loads(raw)
    raise SystemExit(
        "No rows on stdin. Run the query in QUERY against the WPP database and "
        "pipe the JSON result in:\n  ... | python eor/question_led/generate_tokens.py"
    )

def render(rows):
    lines = [
        '"""GENERATED FROM brand_tokens. DO NOT EDIT.',
        "",
        "Regenerate with eor/question_led/generate_tokens.py. Editing this file by",
        "hand recreates the exact failure mode that cost five production defects:",
        "a fact stored in Postgres and also typed into the app, with nothing",
        "forcing them to agree.",
        '"""',
        "",
        "# name -> hex, every colour token, in table order",
        "TOKENS = {",
    ]
    for r in rows:
        lines.append(f"    {r['name']!r}: {r['hex']!r},")
    lines.append("}")
    lines.append("")
    for r in rows:
        lines.append(f"{slug(r['name'])} = {r['hex']!r}")
    lines.append("")
    lines.append("# Hexes named as forbidden in a usage rule. A near-miss brand colour is the")
    lines.append("# failure these tokens exist to prevent, so the list is machine-checkable.")
    forbidden = set()
    for r in rows:
        for word in (r.get("forbidden") or "").replace(",", " ").split():
            w = word.strip(".:;()").upper()
            if w.startswith("#") and len(w) == 7:
                forbidden.add(w)
    lines.append("FORBIDDEN_HEXES = {")
    for h in sorted(forbidden):
        lines.append(f"    {h!r},")
    lines.append("}")
    lines.append("")
    lines.append("def css_variables(prefix='--'):")
    lines.append('    """The same palette as CSS custom properties, for the stylesheet."""')
    lines.append("    out = []")
    lines.append("    for name, hex_ in TOKENS.items():")
    lines.append("        var = name.lower().replace(' ', '-')")
    lines.append("        out.append(f'{prefix}{var}: {hex_};')")
    lines.append("    return '\\n'.join(out)")
    return "\n".join(lines) + "\n"

if __name__ == "__main__":
    rows = fetch()
    new = render(rows)
    if "--check" in sys.argv:
        old = open(OUT).read() if os.path.exists(OUT) else ""
        if old != new:
            print("DRIFT: tokens_generated.py does not match brand_tokens.", file=sys.stderr)
            sys.exit(1)
        print("tokens_generated.py matches brand_tokens.")
    else:
        open(OUT, "w").write(new)
        print(f"wrote {OUT} — {len(rows)} colour tokens")
