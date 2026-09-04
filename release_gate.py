"""release_gate.py — the checks that run on the RENDERED PDF and fail the build.

A fixed template is checkable by eye. A composed one is not: it assembles
per-account text, numbers and links that nobody reads before they are printed.
Every check here exists because something already went out wrong.

WHY THE PDF AND NOT THE DATABASE. v_us_english_violations scans six database
tables and no rendered document. It reported zero while a Brief was full of UK
spellings, because the spellings were in composed prose that never lands in a
scanned table. The rendered PDF is the last place the truth is still checkable
and the only place all of it is together.

THESE FAIL THE BUILD. They do not report afterwards. A Brief that trips one of
them is not mailed, because the alternative is a prospect holding it.

WHAT THIS CANNOT DO YET, AND SAYS SO. QR codes are checked by their PAYLOAD —
the string the package was built from — not by decoding the printed pixels.
Pixel decoding needs pyzbar and the zbar system library in the image; until
that lands, a QR that renders corrupt would pass. The payload check still
catches the two failures that actually happened: a QR pointing at the wrong
organization, and one carrying ?c=.
"""
import re

# LAW 7 — US English everywhere, prospect-facing and internal alike. Proper
# nouns and fixed brand marks are the only exception, so the patterns below are
# word-bounded and lowercase-matched.
UK_SPELLINGS = [
    "organisation", "organisations", "programme", "programmes", "realise", "realised",
    "labour", "whilst", "amongst", "colour", "colours", "behaviour", "modelled",
    "authorised", "recognise", "recognised", "optimise", "optimised", "analyse",
    "analysed", "categorise", "categorised", "prioritise", "prioritised",
    "minimise", "minimised", "maximise", "maximised", "licence", "catalogue",
    "fulfilment", "enrolment", "defence", "offence", "judgement", "centre",
    "finance director",
]

# LAW 8 — banned vocabulary in customer-facing copy. "savings" is banned as a
# noun; the verbs save/saves/saved are fine, so the pattern is deliberately
# narrow. "not a pitch" and every variant is banned outright.
BANNED = [
    (r"\bpitch(?:es|ing|ed)?\b", "pitch"),
    (r"\bsavings?\b(?!\s+account)", "savings"),
]

# THE ONE EXEMPTION LAW 8 GRANTS, AND THE GATE DID NOT HONOUR IT.
#
# LAW 8, verbatim: '"Opportunity" for prospect estimates. "Savings" only for
# realized results in case studies.'
#
# The bound package carries an ERA case study - North Texas Food Bank, One
# Community Health - which reports DELIVERED results and quotes named people at
# the client. "Total annual savings realized · $200,500" is exactly what the law
# permits, and rewording a quotation attributed to Ann Dunlap would put words in
# her mouth.
#
# Scanning the whole composed PDF as one string made that legal page indistinguishable
# from a prospect estimate, so the gate would have blocked the package for
# obeying the law. Pages whose text carries these markers are checked for
# everything EXCEPT the savings term.
CASE_STUDY_MARKERS = (
    "case study",
    "total annual savings realized",
    "the client", "the challenge", "the solution", "the result",
)


def _is_case_study_page(page_text):
    """A page is a case study only if it announces itself as one. Deliberately
    narrow: the exemption must never leak onto a page carrying a PROSPECT
    estimate, which is the whole point of the ban."""
    low = (page_text or "").lower()
    return sum(1 for m in CASE_STUDY_MARKERS if m in low) >= 2

# A token the composer failed to resolve. A literal {A[...]} in print is an
# automatic no-print.
UNRESOLVED_TOKEN = re.compile(r"\{[A-Za-z]?\[[^\]]*\]\}|\{\{[^}]*\}\}|\{[A-Z_]{3,}\}")

# A number that stopped mid-render. The category table printed "$4,789," where
# "$4.79M" belonged, and the change column printed a sign with no number. Both
# were invisible to every check that existed.
TRUNCATED_MONEY = re.compile(r"\$\s?[\d,]*[.,]\s*(?=$|[^\d])", re.M)
NAKED_SIGN = re.compile(r"(?<![\w$])[+−-]\s*(?=$|[^\d.\s])", re.M)
TRUNCATED_PCT = re.compile(r"\d[.,]\s*%")


class ReleaseFailure(Exception):
    """Raised with every failing check, so one run reports all of them."""

    def __init__(self, failures):
        self.failures = failures
        super().__init__("release gate failed:\n  - " + "\n  - ".join(failures))


def pdf_text(path):
    """All text in the document, and the per-page list. pypdf is already a
    dependency, so this adds nothing to the image."""
    from pypdf import PdfReader
    pages = []
    for page in PdfReader(path).pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n".join(pages), pages


def check(rendered_pdf, identity, frozen_plan=None, qr_payloads=(), priority_count=None):
    """Run every release check. Returns the list of failures; raises nothing.

    identity      the ONE identity object off the frozen plan
    frozen_plan   the plan the render was authorized by (for the page count)
    qr_payloads   every string a QR in this package was generated from
    priority_count  how many priority modules the executive summary claims
    """
    failures = []
    text, pages = pdf_text(rendered_pdf)
    low = text.lower()

    # 1 — unresolved template tokens
    for m in set(UNRESOLVED_TOKEN.findall(text)):
        failures.append(f"unresolved template token in print: {m!r}")

    # 2 — UK spellings in the RENDERED text, which is where they hid
    for w in UK_SPELLINGS:
        if re.search(r"\b" + re.escape(w) + r"\b", low):
            failures.append(f"UK spelling in rendered text: {w!r} (LAW 7)")

    # 3 — banned vocabulary, page by page so the case-study exemption can apply
    #     to the page that earns it and nowhere else.
    for pattern, label in BANNED:
        for i, ptxt in enumerate(pages, 1):
            plow = (ptxt or "").lower()
            if not re.search(pattern, plow):
                continue
            if label == "savings" and _is_case_study_page(plow):
                continue          # LAW 8 permits it for realized results
            failures.append(
                f"banned vocabulary in rendered text: {label!r} on page {i} (LAW 8)")
            break

    # 4 — QR payloads. Checked as strings, not pixels; see the module docstring.
    sub = (identity or {}).get("portal_subdomain")
    for p in qr_payloads or ():
        if "?c=" in p:
            failures.append(f"QR carries an access code, which no printed surface may: {p}")
        if sub and sub not in p:
            failures.append(f"QR does not point at this account's portal ({sub}): {p}")
        if not sub:
            failures.append("QR present but the identity has no portal subdomain")

    # 5 — ONE organization identity, on every page and every link. This is the
    # check that would have caught the contamination: a package carrying another
    # organization's cover, letter, closing and portal URL.
    failures.extend(_identity_failures(text, pages, identity))

    # 6 — every currency and percentage renders complete
    for m in set(TRUNCATED_MONEY.findall(text)):
        failures.append(f"currency stopped mid-render: {m.strip()!r}")
    for m in set(TRUNCATED_PCT.findall(text)):
        failures.append(f"percentage stopped mid-render: {m.strip()!r}")
    if NAKED_SIGN.search(text):
        failures.append("a change column printed a sign with no number after it")

    # 7 — the executive summary's priority count reconciles with what rendered
    if priority_count is not None:
        claimed = _claimed_priority_count(text)
        if claimed is not None and claimed != priority_count:
            failures.append(
                f"executive summary claims {claimed} priorities; {priority_count} modules rendered")

    # 8 — the page count matches the plan that authorized the render
    if frozen_plan:
        planned = frozen_plan.get("page_count") or frozen_plan.get("pages")
        if planned and int(planned) != len(pages):
            failures.append(f"page count {len(pages)} does not match the frozen plan ({planned})")

    return failures


def _identity_failures(text, pages, identity):
    """The organization on the page and the account the package was built for
    must agree — on every page, and in every link."""
    out = []
    identity = identity or {}
    name = (identity.get("short_name") or identity.get("legal_name") or "").strip()
    sub = (identity.get("portal_subdomain") or "").strip()
    if not name:
        return ["identity has no organization name to check the render against"]

    # The name has to appear somewhere. A package that never names the
    # organization it is for is not this organization's package.
    if name.lower() not in text.lower():
        out.append(f"the organization this package is for ({name}) appears nowhere in the render")

    # Every portal path printed anywhere must be this account's. A second
    # subdomain in the document means two organizations are in one package.
    printed_subs = set(re.findall(r"portal\.wpp-us\.com/([A-Za-z0-9-]+)", text))
    printed_subs.discard("p")  # /p/<code> is the permanent alias, not a subdomain
    foreign = {s for s in printed_subs if sub and s.lower() != sub.lower()}
    if foreign:
        out.append(
            f"another organization's portal path is printed in this package: {sorted(foreign)} "
            f"(this account is {sub or 'unset'})")
    if sub and printed_subs and sub.lower() not in {s.lower() for s in printed_subs}:
        out.append(f"this account's portal path ({sub}) is printed nowhere, but others are")
    return out


def _claimed_priority_count(text):
    m = re.search(r"\b(\w+)\s+priorit(?:y|ies)\b", text, re.I)
    if not m:
        return None
    word = m.group(1).lower()
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    if word.isdigit():
        return int(word)
    return words.get(word)


def enforce(rendered_pdf, identity, **kw):
    """Run the gate and RAISE on any failure. This is the call site that turns
    the checks into a gate rather than a report."""
    failures = check(rendered_pdf, identity, **kw)
    if failures:
        raise ReleaseFailure(failures)
    return True
