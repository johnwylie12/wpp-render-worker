#!/usr/bin/env python3
"""
wpp_canon.py — the ONE brand_canon reader for the render worker.

Every prospect-facing signoff (cover letter, CIR, snapshot, closing page,
benchmark, exec brief, meeting label, portal card) must print the title stored
in `brand_canon` where token_group='signoff'. Hardcoding it is how the fleet
ended up printing "Senior Advisor" on some surfaces and "Senior Consultant" on
others while canon said something else again.

Reads brand_canon over the Supabase REST API using the same service-role key
worker.py uses, caches the result for the life of the process, and falls back to
the canon values baked in below when the DB is unreachable (self-tests, offline
renders). The fallback is a copy of canon, not a second opinion: if canon moves,
update it here too — but the DB always wins at runtime.

Usage in an engine:
    from wpp_canon import signoff, signoff_title
    role = signoff_title()                  # "Consulting Partner"
    so   = signoff()                        # {name,title,company,email,phone,tagline}
"""
import os
import logging

log = logging.getLogger(__name__)

# Canon as of brand_canon.updated_at 2026-08-14. Fallback only — the DB wins.
_FALLBACK = {
    "name": "John Wylie",
    "title": "Consulting Partner",
    "company": "ERA Group",
    "email": "jwylie@eragroup.com",
    "phone": "703.244.9868",
    "tagline": "Value Through Insight™",
}

# Stale titles that must never be printed again. Kept here so the guard test and
# any drift scan read the same list.
STALE_TITLES = ("Senior Consultant", "Senior Advisor", "Chief Value Officer")

_cache = {}


def _rest_signoff():
    """GET brand_canon signoff tokens. Returns {} on any failure — never raises."""
    url = (os.environ.get("SUPABASE_URL", "") or "").rstrip("/")
    key = (os.environ.get("WPP_SB_SECRET")
           or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")).strip()
    if not url or not key:
        return {}
    headers = {"apikey": key, "Content-Type": "application/json"}
    if key.startswith("eyJ"):          # legacy JWT service_role key
        headers["Authorization"] = "Bearer %s" % key
    try:
        import httpx
        r = httpx.get(
            "%s/rest/v1/brand_canon" % url,
            params={"select": "token_key,token_value",
                    "token_group": "eq.signoff", "is_active": "eq.true"},
            headers=headers, timeout=15.0)
        r.raise_for_status()
        rows = r.json() or []
    except Exception as e:                                  # noqa: BLE001
        log.warning("brand_canon lookup failed (%s); using canon fallback", e)
        return {}
    out = {}
    for row in rows:
        k = (row.get("token_key") or "").strip()
        v = row.get("token_value")
        if k and isinstance(v, str) and v.strip():
            out[k] = v.strip()
    return out


def signoff(refresh=False):
    """The canonical signoff block. Cached per process."""
    if refresh:
        _cache.pop("signoff", None)
    if "signoff" not in _cache:
        merged = dict(_FALLBACK)
        merged.update(_rest_signoff())
        _cache["signoff"] = merged
    return dict(_cache["signoff"])


def signoff_title():
    """The canonical role line, e.g. 'Consulting Partner'."""
    return signoff()["title"]


def repair_signoff(block, org_key="org"):
    """Return a signoff block with any STALE title replaced by canon.

    Engines read `params.content.signoff` when the brief carries one, and briefs
    carry whatever the app stamped at enqueue time. 250 briefs sitting at
    verification_hold still carry title="Senior Consultant", which stopped being
    canon on 2026-08-14 — a code fix alone would still print the stale title on
    every one of them, because params wins over the default.

    This repairs the value at render time WITHOUT removing the override seam: a
    title that is not on the stale list (a partner's own signoff, say) is passed
    through untouched. Only known-dead titles are corrected.
    """
    if not isinstance(block, dict):
        return block
    title = (block.get("title") or "").strip()
    if title and title not in STALE_TITLES:
        return block                      # a deliberate, live override — leave it
    so = signoff()
    out = dict(block)
    out["title"] = so["title"]
    if not (out.get("name") or "").strip():
        out["name"] = so["name"]
    if org_key in out and not (out.get(org_key) or "").strip():
        out[org_key] = so["company"]
    return out


def signoff_title_org(sep=", "):
    """'Consulting Partner, ERA Group' — the one-line form the cards print."""
    s = signoff()
    return "%s%s%s" % (s["title"], sep, s["company"])


if __name__ == "__main__":
    print(signoff())
