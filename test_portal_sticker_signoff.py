#!/usr/bin/env python3
"""Regression guard for the defect that failed EVERY EOP package render.

Decision #78 made the sticker's side A (the book-a-meeting QR) partner-variable,
but worker.py's call site kept passing only (url, code, path). partner_signoff
defaulted to None, wpp_partner.normalize(None) raised

    PartnerError: no partner signoff resolved; refusing to print an unattributed piece

and the package died at the LAST piece, after the letter and all six sections had
already rendered. Brief 1722 failed twice this way; no package had rendered since
2026-08-20.

Nothing caught it because the failure lives in an ARGUMENT THAT WAS NOT PASSED --
there is no wrong value to assert against, only a missing one. So this file
checks the call site itself (test 0) as well as the behaviour.

Run: python3 test_portal_sticker_signoff.py   (needs only reportlab)
"""
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from portal_sticker.portal_sticker import render_sticker          # noqa: E402
from wpp_partner import PartnerError                              # noqa: E402

OUT = "/tmp/_sticker_guard"
URL, CODE = "https://wpp-us.com/p/7T9Q2VB", "7T9Q2VB"

JOHN = {"partner_id": 3, "signoff_name": "John Wylie",
        "signoff_title": "Senior Consultant", "signoff_firm": "ERA Group",
        "signoff_email": "jwylie@eragroup.com", "signoff_phone": "703.244.9868",
        "is_renderable": True, "missing": [],
        "booking_url": "https://outlook.office.com/bookwithme/user/x/meetingtype/y"}
NO_BOOKING = dict(JOHN, partner_id=1, signoff_name="Arvo Kaseorg",
                  signoff_email="akaseorg@eragroup.com", booking_url=None)

failures = []


def check(ok, label):
    print(("  ok   " if ok else "  FAIL ") + label)
    if not ok:
        failures.append(label)


def pages(path):
    return len(re.findall(rb"/Type\s*/Page[^s]", open(path, "rb").read()))


# --- 0. THE CALL SITE. Every render_sticker() call must hand over a signoff. ---
print("0. worker.py passes a signoff at every render_sticker call site")
tree = ast.parse(open(os.path.join(HERE, "worker.py"), encoding="utf-8").read())
calls = [n for n in ast.walk(tree)
         if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "render_sticker"]
check(bool(calls), "found a render_sticker call in worker.py")
for c in calls:
    kw = {k.arg for k in c.keywords}
    check("partner_signoff" in kw,
          "line %d passes partner_signoff (the bug: it did not)" % c.lineno)
    check("include_meeting_side" in kw,
          "line %d decides include_meeting_side explicitly" % c.lineno)

# --- behaviour ---
print("1. a sticker with no signoff refuses to print")
try:
    render_sticker(URL, CODE, OUT + "_a.pdf")
    check(False, "expected PartnerError, got a PDF")
except PartnerError as e:
    check("no partner signoff resolved" in str(e), "raises PartnerError: %s" % e)

print("2. a partner with a booking_url gets both sides")
check(pages(render_sticker(URL, CODE, OUT + "_b.pdf",
                           partner_signoff=JOHN, include_meeting_side=True)) == 2,
      "two pages (meeting side + portal side)")

print("3. a partner with no booking_url still gets the portal side")
check(pages(render_sticker(URL, CODE, OUT + "_c.pdf",
                           partner_signoff=NO_BOOKING, include_meeting_side=False)) == 1,
      "one page, portal side only -- the package still ships")

print("4. a partner with no booking_url never borrows another calendar")
try:
    render_sticker(URL, CODE, OUT + "_d.pdf",
                   partner_signoff=NO_BOOKING, include_meeting_side=True)
    check(False, "printed a meeting QR for a partner with no booking_url")
except PartnerError as e:
    check("booking_url" in str(e), "raises rather than falling back: %s" % e)

print("5. side A encodes THIS partner's calendar, not a module constant")
import portal_sticker.portal_sticker as ps                        # noqa: E402
seen = []
_orig = ps._qr
ps._qr = lambda c, url, x, y, size: (seen.append(url), _orig(c, url, x, y, size))[1]
ps.render_sticker(URL, CODE, OUT + "_e.pdf", partner_signoff=JOHN,
                  include_meeting_side=True)
ps._qr = _orig
check(seen[0] == JOHN["booking_url"], "meeting QR = partner_signoff['booking_url']")
check(seen[1] == URL, "portal QR = the account's portal url (partner-neutral)")

print("6. no partner identity is hardcoded in the sticker module")
src = open(os.path.join(HERE, "portal_sticker", "portal_sticker.py"), encoding="utf-8").read()
check(not re.search(r"^\s*(BOOK_URL|C_NAME|C_TITLE|C_PHONE|C_EMAIL)\s*(,|=)", src, re.M),
      "no BOOK_URL / C_NAME / C_TITLE / C_PHONE / C_EMAIL assignment")

print()
if failures:
    print("FAILED (%d): %s" % (len(failures), "; ".join(failures)))
    sys.exit(1)
print("all sticker signoff guards passed")
