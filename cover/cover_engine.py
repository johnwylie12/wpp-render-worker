#!/usr/bin/env python3
"""ERA executive cover letter renderer.

LOCKED 2026-08-11. John: "That is the new cover letter that should be locked in
and used 100% of the time."

Renders cover/WPP_EOP_CoverLetter_TEMPLATE_LOCKED_2026-08-11.html. The five body
paragraphs live IN that template and are NOT built here — this module only
resolves the per-account merge fields, the assets, and the portal QR, then hands
the HTML to WeasyPrint.

RETIRES the nine-paragraph copy previously hardcoded in this file ("prepared
before we ever asked for a meeting" / "Warm regards," / "more than three
decades" / "savings"). Do not reintroduce it.

Public API is UNCHANGED — worker.py needs no edits:
    build_cover(params_cover, recipient, company, *, date_str=None) -> dict
    render_cover(cover, out_pdf, page_size="Letter") -> out_pdf

Access-code contract
--------------------
`prospect_portals.code` is the INTERNAL record id (e.g. NQKF82W) and must never
be printed. `prospect_portals.access_code` is what the prospect types (e.g.
HAC3E9T). This module reads access_code ONLY; if a portal block carries `code`
but no `access_code`, it prints NOTHING (no QR, no code) and logs a warning,
rather than printing the internal id. That mismatch shipped two different codes
in one envelope on brief 745.
"""
import base64
import datetime
import logging
import os
import sys

import segno
from jinja2 import Template
from weasyprint import HTML

log = logging.getLogger(__name__)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # repo root -> wpp_signatures
from wpp_signatures import (  # noqa: E402
    signature_data_uri, signature_for_partner, signature_width_px,
    SIGNATURE_WIDTH_DEFAULT, UnknownSignature,
)

# Brand canon: the cover letter signs with Sig 3 (contained mark), 115px in the
# template. params.cover_letter.signature overrides. The 5x7 note card uses Sig 2
# — they must never be swapped.
SIGNATURE_DEFAULT = "3"

PORTAL_HOST = "portal.wpp-us.com"
BRAND_NAVY = "#003A70"

# --- asset paths (verified against the repo, 2026-08-12) ---------------------
TEMPLATE_PATH = os.path.join(HERE, "WPP_EOP_CoverLetter_TEMPLATE_v2_PARTNER_SIGNOFF.html")
# The ERA header logo — a JPEG stored pre-encoded as base64 (the same asset the
# prior letter shipped with; John approved the header).
LOGO_B64_PATH = os.path.join(HERE, "logo_b64.txt")
# The footer "Value Through Insight(TM)" mark — the NAVY wordmark on transparent
# (vti_white_lockup.png is the WHITE version, for dark backgrounds — not this).
VTI_MARK_PATH = os.path.join(HERE, "..", "meeting_label", "assets", "vti_logo.png")

# Bundled fonts.conf maps Trebuchet -> Liberation Sans (CIR parity). Set it
# defensively so the letter renders in the same typeface even if the worker
# forgot to export it.
_FONTS = os.path.join(HERE, "..", "cir", "build", "fonts.conf")
if os.path.exists(_FONTS):
    os.environ.setdefault("FONTCONFIG_FILE", os.path.abspath(_FONTS))

with open(TEMPLATE_PATH, encoding="utf-8") as _fh:
    _TPL_STR = _fh.read()


# ------------------------------------------------------------------ assets
def _logo_uri():
    """ERA header logo as a data: URI (JPEG). Missing -> None + warning."""
    try:
        with open(LOGO_B64_PATH, encoding="utf-8") as fh:
            b64 = fh.read().strip()
        return "data:image/jpeg;base64," + b64
    except Exception as e:  # pragma: no cover
        log.warning("cover: ERA logo missing (%s); rendering without it", e)
        return None


def _vti_uri():
    """Footer VTI mark as a data: URI (PNG). Missing -> None + warning."""
    try:
        with open(VTI_MARK_PATH, "rb") as fh:
            return "data:image/png;base64," + base64.b64encode(fh.read()).decode()
    except Exception as e:  # pragma: no cover
        log.warning("cover: VTI mark missing (%s); rendering without it", e)
        return None


def _signature_uri(which):
    """Sig 3 (default) as a data: URI, via wpp_signatures. Missing signature logs
    a warning and renders UNSIGNED rather than crashing the whole package."""
    try:
        return signature_data_uri(str(which or SIGNATURE_DEFAULT))
    except Exception as e:  # pragma: no cover
        log.warning("cover: signature %s unavailable (%s); rendering unsigned", which, e)
        return None


class SignoffError(Exception):
    """The sender could not be resolved. Never downgraded to a default.

    worker.py catches this alongside RenderError and fails the brief, so a
    letter with an unresolved sender never reaches a PDF."""


REQUIRED_SIGNOFF_FIELDS = ("signoff_name", "signoff_title", "signoff_firm",
                           "signoff_email", "signoff_phone")


def resolve_signoff(signoff):
    """Validate a wpp_signoff() row and pick the signature. Raises, never guesses.

    WHY IT RAISES. The v1 template hardcoded John's name, title, email and phone,
    so a batch assigned to another partner printed under John's. The failure was
    invisible on screen and only discoverable by reading 24 letters. A signoff
    that cannot be resolved must stop the render, not fall back to the owner --
    a wrong name on a mailed letter cannot be recalled.
    """
    if not signoff:
        raise SignoffError("cover letter: no signoff resolved; refusing to render "
                           "(v1 would have printed John Wylie here)")
    sd = dict(signoff)

    if sd.get("is_renderable") is False:
        raise SignoffError(
            "cover letter: wpp_signoff reports the partner is not renderable; missing "
            f"{sd.get('missing') or 'unknown'}")

    # ACCEPT BOTH COLUMN SHAPES, the same reconciliation wpp_partner.normalize()
    # needed. account_signoff() returns firm / email / phone; this module has
    # always required signoff_firm / signoff_email / signoff_phone. The mismatch
    # is duplicated in THREE places - here, wpp_partner, and the sticker - so
    # passing the database function's own output raised on the COVER LETTER,
    # page 1 of the mailing, after everything else had rendered.
    for short, long in (("firm", "signoff_firm"), ("email", "signoff_email"),
                        ("phone", "signoff_phone"), ("name", "signoff_name"),
                        ("title", "signoff_title")):
        if not str(sd.get(long) or "").strip() and str(sd.get(short) or "").strip():
            sd[long] = sd[short]

    missing = [f for f in REQUIRED_SIGNOFF_FIELDS if not str(sd.get(f) or "").strip()]
    if missing:
        raise SignoffError(f"cover letter: signoff is missing {', '.join(missing)}")

    # The mark. A partner with no registered signature raises rather than
    # borrowing someone else's; the caller may allow an unsigned letter.
    pid = sd.get("partner_id")
    try:
        key = signature_for_partner(pid)
        sd["signature_key"] = key
        sd["signature_width_px"] = signature_width_px(key)
    except UnknownSignature:
        if not sd.get("allow_unsigned"):
            raise
        log.warning("cover: partner %s has no registered signature; rendering UNSIGNED", pid)
        sd["signature_key"] = None
        sd["signature_width_px"] = SIGNATURE_WIDTH_DEFAULT
    return sd


# ------------------------------------------------------------------ helpers
def _g(m, *keys):
    """First non-empty value among keys of a mapping, or None."""
    if not m:
        return None
    for k in keys:
        v = m.get(k)
        if v not in (None, ""):
            return str(v)
    return None


def _first_name(full_name, explicit):
    if explicit:
        return str(explicit).strip()
    if full_name:
        return str(full_name).strip().split()[0]
    return "there"


def _address_lines(pc_recipient, recipient):
    """The mailing address as [line1, city/state/zip, ...] — from the enqueued
    recipient block (fetch_contact carries no address)."""
    lines = None
    if isinstance(pc_recipient, dict):
        lines = pc_recipient.get("address_lines")
    if not lines and isinstance(recipient, dict):
        lines = recipient.get("address_lines")
    return [str(x) for x in lines if x] if isinstance(lines, list) else []


def _resolve_letter_date(pc, date_str):
    """The date printed at the top of the letter.

    ORDER MATTERS. params.cover_letter.date ('YYYY-MM-DD') is authoritative when
    present: a letter for a future drop must carry the drop's date, never the day
    the worker happened to render it. Only when no date was chosen do we fall back
    to today.
    """
    iso = pc.get("date")
    if isinstance(iso, str) and iso.strip():
        try:
            return datetime.date.fromisoformat(iso.strip()).strftime("%B %-d, %Y")
        except ValueError:
            pass  # malformed -> fall through rather than fail the render
    if date_str:
        return str(date_str)
    legacy = pc.get("date_str")
    if isinstance(legacy, str) and legacy.strip():
        return legacy
    return datetime.date.today().strftime("%B %-d, %Y")


def _portal_fields(portal):
    """Resolve { subdomain, access_code, qr_uri } for the bottom-right invite.

    access_code ONLY. Returns None (whole block omitted) when there is no
    access_code — a letter must never carry a dead QR or the internal `code`.
    The QR encodes the FULL coded URL so a scan opens straight in; the printed
    line is the clean host + slug with the access code beneath.
    """
    if not portal:
        return None
    access = (_g(portal, "access_code") or "").strip()
    if not access:
        log.warning("cover: portal present but access_code missing; omitting the "
                    "portal block (refusing to print prospect_portals.code)")
        return None

    url = (_g(portal, "url") or "").strip()
    sub = (_g(portal, "subdomain", "slug") or "").strip()
    if not sub and url:
        host_path = url.split("://", 1)[-1].split("?", 1)[0].rstrip("/")
        if "/" in host_path:            # shared host: portal.wpp-us.com/{slug}
            sub = host_path.split("/", 1)[1]
        else:                            # legacy: {slug}.wpp-us.com
            sub = host_path.split(".", 1)[0]

    if not url:
        url = f"https://{PORTAL_HOST}/{sub}?c={access}" if sub else None
    if not url:
        log.warning("cover: portal access_code present but no URL/subdomain; "
                    "omitting the portal block")
        return None

    qr_uri = segno.make(url, error="m").svg_data_uri(dark=BRAND_NAVY, border=0)
    return {"subdomain": sub, "access_code": access, "qr_uri": qr_uri}


# ------------------------------------------------------------------ build
def build_cover(params_cover, recipient, company, *, date_str=None):
    """Resolve every per-account merge field the locked template needs.

    params_cover (params.cover_letter) may carry:
        recipient: {name, first_name, title, company, address_lines:[...]}
        sector:    str          (accounts.industry_group, lowercased)
        date:      'YYYY-MM-DD'  (the drop date; falls back to render date)
        portal:    {subdomain|slug, access_code, url}   <-- access_code, never code
        signature: '3' | '2'     (variant override; Sig 3 default)
    `recipient` (worker.fetch_contact) supplies name/title/first_name when the
    block does not. Body copy is NOT here — it lives in the locked template.
    """
    pc = dict(params_cover or {})
    rc = dict(recipient or {})
    r = pc.get("recipient") if isinstance(pc.get("recipient"), dict) else {}

    name = _g(r, "name") or _g(rc, "name") or _g(pc, "addressee_name") or ""
    title = _g(r, "title") or _g(rc, "title") or _g(pc, "addressee_title") or ""
    first = _first_name(name, _g(r, "first_name") or _g(rc, "first_name"))
    org = _g(r, "company") or _g(rc, "company") or company or ""

    lines = _address_lines(r, rc)
    addr_line1 = lines[0] if lines else ""
    addr_csz = " ".join(lines[1:]) if len(lines) > 1 else ""
    if not (addr_line1 and addr_csz):
        log.warning("cover letter for %s has no full address block", org or company)

    sector = (_g(pc, "sector") or "your sector").lower()

    return {
        "date": _resolve_letter_date(pc, date_str),
        "first_name": first,
        "recipient_name": name,
        "recipient_title": title,
        "org_name": org,
        "addr_line1": addr_line1,
        "addr_city_state_zip": addr_csz,
        "sector": sector,
        # Resolved at render time (access_code only). Absent -> no portal block.
        "portal": pc.get("portal") or None,
        # Signature variant ('3' contained default, '2' long-sweep note-card mark).
        "signature": pc.get("signature"),
        # WHOSE NAME GOES ON THIS. A wpp_signoff() row, supplied by the caller
        # (worker.fetch_signoff). Validated in render_cover; absent -> refuses.
        "signoff": pc.get("signoff"),
    }


# ------------------------------------------------------------------ render
# Selectable paper sizes (name -> CSS @page size token). The package cover is
# always Letter; `separate` covers may request another size.
COVER_PAGE_SIZES = {
    "letter": "Letter", "legal": "Legal", "a4": "A4", "a5": "A5",
    "half-letter": "5.5in 8.5in", "monarch": "7.25in 10.5in",
    "executive": "7.25in 10.5in", "6x9": "6in 9in", "note-a2": "4.25in 5.5in",
}


def resolve_page_size(page_size):
    if not page_size:
        return "Letter"
    key = str(page_size).strip().lower()
    return COVER_PAGE_SIZES.get(key, str(page_size).strip())


def render_cover(cover, out_pdf, page_size="Letter"):
    """Render the locked template to a single-page PDF."""
    pf = _portal_fields(cover.get("portal"))
    so = resolve_signoff(cover.get("signoff"))

    sig_key = so.get("signature_key")
    ctx = {
        "era_logo_uri": _logo_uri() or "",
        "vti_uri": _vti_uri() or "",
        "signature_uri": (_signature_uri(sig_key) or "") if sig_key else "",
        "signature_width_px": so.get("signature_width_px", SIGNATURE_WIDTH_DEFAULT),
        "signoff_name": so["signoff_name"],
        "signoff_title": so["signoff_title"],
        "signoff_firm": so["signoff_firm"],
        "signoff_email": so["signoff_email"],
        "signoff_phone": so["signoff_phone"],
        "date": cover.get("date", ""),
        "first_name": cover.get("first_name", ""),
        "recipient_name": cover.get("recipient_name", ""),
        "recipient_title": cover.get("recipient_title", ""),
        "org_name": cover.get("org_name", ""),
        "addr_line1": cover.get("addr_line1", ""),
        "addr_city_state_zip": cover.get("addr_city_state_zip", ""),
        "sector": cover.get("sector", "your sector"),
        "portal_subdomain": pf["subdomain"] if pf else "",
        "portal_access_code": pf["access_code"] if pf else "",
        "qr_uri": pf["qr_uri"] if pf else None,   # None -> template omits the block
    }

    html = _TPL_STR
    size_css = resolve_page_size(page_size)
    if size_css.lower() != "letter":
        html = html.replace("size: Letter;", f"size: {size_css};")

    HTML(string=Template(html).render(**ctx), base_url=HERE).write_pdf(out_pdf)
    return out_pdf


if __name__ == "__main__":
    # self-test (no DB): resolves canon + renders to /tmp
    c = build_cover(
        {"sector": "senior living",
         "portal": {"subdomain": "demo-benchmark", "access_code": "HAC3E9T"}},
        {"name": "Nick Jacobi", "title": "General Manager", "first_name": "Nick",
         "address_lines": ["123 Fairway Dr", "Charlotte, NC 28202"]},
        "Stonebridge Golf Club",
    )
    render_cover(c, "/tmp/cover_test.pdf")
    print("rendered /tmp/cover_test.pdf")
