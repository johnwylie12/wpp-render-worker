#!/usr/bin/env python3
"""
Render a wave's portal QR labels, four to a sheet, from a JSON list.

Input JSON (stdin or argv[1]) is a list in PRINT ORDER, exactly as the wave's
collation sheet numbers the packages, so label N matches package N:

  [{"seq": 1, "name": "...", "url": "https://...", "code": "ABC1234",
    "display": "portal.wpp-us.com/acme-benchmark"}, ...]

url and code come from the database (portal_for_account). Nothing here builds a
portal address.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from portal_sticker.portal_label_sheet import render_label_sheets  # noqa: E402


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    raw = sys.stdin.read() if src == "-" else open(src).read()
    rows = json.loads(raw)
    out = sys.argv[2] if len(sys.argv) > 2 else "portal_labels.pdf"
    rows = sorted(rows, key=lambda r: r.get("seq") or 0)
    path, pages = render_label_sheets(rows, out)
    print(json.dumps({"pdf": path, "labels": len(rows), "pages": pages}))


if __name__ == "__main__":
    main()
