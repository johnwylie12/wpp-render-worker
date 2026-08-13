#!/usr/bin/env python3
"""wpp_assets.py — the ONLY way a WPP render script gets a brand mark.

Why this exists
---------------
Six render surfaces (carousel, 5 meeting-label scripts, meeting card, EOP cover
letter, portal label) loaded logos from /home/claude, /tmp, or a UUID-prefixed
upload artifact. Those paths vanish between sessions, so every session had to
re-create the file — and each re-creation was a fresh chance to derive something
wrong. era_dark.png is that failure caught in the act: an unapproved recolour
invented because no source was reachable.

The CIR template and note_card_engine are NOT affected — they carry their marks
embedded in the worker repo and are frozen. Do not repoint them.

Contract
--------
    from wpp_assets import logo

    era  = logo('era_group', 'dark')            # -> local path to approved PNG
    vti  = logo('value_through_insight','dark')

* Resolves through the `brand_assets` table (source of truth).
* Downloads from Supabase Storage, caches under ~/.wpp_assets/.
* Verifies md5 against the registry. Mismatch = hard abort.
* Refuses to return anything for an asset whose bytes are unverified.
* NEVER derives, recolours, resizes, or falls back to a local file.

Env
---
    SUPABASE_URL   (default: the WPP project)
    WPP_ASSET_CACHE (default: ~/.wpp_assets)
"""

import hashlib
import os
import sys
import urllib.request

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL", "https://ouzrrkskrfcvtnmhlycd.supabase.co"
).rstrip("/")
CACHE_DIR = os.environ.get(
    "WPP_ASSET_CACHE", os.path.join(os.path.expanduser("~"), ".wpp_assets")
)

# Mirrors public.brand_assets. Regenerate with:
#   select key, family, use_on, storage_bucket, storage_path, md5, byte_size
#   from brand_assets order by key;
# Only PNG marks are listed; the CMYK JPGs are print-only and must never render.
REGISTRY = {
    ("era_group", "light"): {
        "key": "era_group.full_color",
        "path": "brand/era_group/ERA Group - White Background.png",
        "md5": "1253c9e97763a506d2c4cee5e96b0878",
        "size": 289443,
        "note": "PRIMARY. Orange arc + Daybreak Blue wordmark. White/light fields.",
    },
    ("era_group", "dark"): {
        "key": "era_group.white_orange_arc",
        "path": "brand/era_group/ERA Group - White - Orange.png",
        "md5": "65b01ccd933ce03246d9f8a83233375e",
        "size": 233098,
        "note": "DARK-FIELD LOCKUP. White wordmark + Sunrise Yellow arc. THE carousel logo.",
    },
    ("era_group", "mono_white"): {
        "key": "era_group.all_white",
        "path": "brand/era_group/ERA Group - White.png",
        "md5": "1f250d646aaa63146e8ee05871cf016d",
        "size": 216673,
        "note": "All-white knockout, real alpha.",
    },
    ("era_group", "mono_black"): {
        "key": "era_group.all_black",
        "path": "brand/era_group/ERA Group - Black.png",
        "md5": "47b1dba4a52dda24fe020f40992bd0b7",
        "size": 239773,
        "note": "All-black knockout. Mono print.",
    },
    ("value_through_insight", "light"): {
        "key": "value_through_insight.horizontal_blue",
        "path": "brand/value_through_insight/Value Through Insight - Blue.png",
        "md5": "14b904ddd3adf4bd2924a0fab8d2ce7b",
        "size": 76306,
        "note": "Footer mark, horizontal. Cover letter height 22px.",
    },
    ("value_through_insight", "dark"): {
        "key": "value_through_insight.horizontal_white",
        "path": "brand/value_through_insight/Value Through Insight - White.png",
        "md5": "28dd59731f789acf96fd701f6c719624",
        "size": 73195,
        "note": "Horizontal lockup, white. Carousel footer.",
    },
    ("value_through_insight", "mono_black"): {
        "key": "value_through_insight.horizontal_black",
        "path": "brand/value_through_insight/Value Through Insight - Black.png",
        "md5": "f6f7141e0dfb61c2887a741ada4def32",
        "size": 75741,
        "note": "Horizontal lockup, mono black.",
    },
    ("value_through_insight", "stacked_light"): {
        "key": "value_through_insight.stacked_blue",
        "path": "brand/value_through_insight/Value Through Insight - Centre - Blue.png",
        "md5": "b507bdfade388deb4eb3b15630421ae1",
        "size": 77301,
        "note": "Stacked lockup, blue. Width-constrained placements.",
    },
    ("value_through_insight", "stacked_dark"): {
        "key": "value_through_insight.stacked_white",
        "path": "brand/value_through_insight/Value Through Insight - Centre - White.png",
        "md5": "0326615056d9acbeb5773c7e5756722d",
        "size": 73497,
        "note": "Stacked lockup, white. Dark fields.",
    },
    ("value_through_insight", "stacked_mono_black"): {
        "key": "value_through_insight.stacked_black",
        "path": "brand/value_through_insight/Value Through Insight - Centre - Black.png",
        "md5": "24d2e64ba92e74c43805d8796977f3ea",
        "size": 76597,
        "note": "Stacked lockup, mono black.",
    },
}

BUCKET = "content-assets"


class BrandAssetError(RuntimeError):
    """Raised when an approved mark cannot be produced. Never catch-and-default."""


def _public_url(path: str) -> str:
    from urllib.parse import quote
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{quote(path)}"


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def logo(family: str, field: str = "light") -> str:
    """Return a local filesystem path to the approved mark.

    family : 'era_group' | 'value_through_insight'
    field  : 'light' | 'dark' | 'mono_white' | 'mono_black'
             | 'stacked_light' | 'stacked_dark' | 'stacked_mono_black'

    Raises BrandAssetError rather than returning a wrong or derived mark.
    """
    entry = REGISTRY.get((family, field))
    if entry is None:
        raise BrandAssetError(
            f"No approved mark for family={family!r} field={field!r}. "
            f"Available: {sorted(REGISTRY.keys())}. "
            f"Do NOT derive one — add it to brand_assets first."
        )

    os.makedirs(CACHE_DIR, exist_ok=True)
    cached = os.path.join(CACHE_DIR, entry["key"] + ".png")

    if os.path.exists(cached):
        with open(cached, "rb") as fh:
            data = fh.read()
        if _md5(data) == entry["md5"]:
            return cached
        os.remove(cached)  # corrupt/stale cache

    url = _public_url(entry["path"])
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            if resp.status != 200:
                raise BrandAssetError(f"{url} returned HTTP {resp.status}")
            data = resp.read()
    except BrandAssetError:
        raise
    except Exception as exc:
        raise BrandAssetError(
            f"Could not fetch {entry['key']} from {url}: {exc}\n"
            f"If the bucket is empty the 12 masters have not been uploaded yet — "
            f"check: select * from v_brand_assets_pending_upload;"
        ) from exc

    actual = _md5(data)
    if actual != entry["md5"]:
        raise BrandAssetError(
            f"CHECKSUM MISMATCH for {entry['key']}.\n"
            f"  expected md5 {entry['md5']} ({entry['size']} bytes)\n"
            f"  got      md5 {actual} ({len(data)} bytes)\n"
            f"The stored object is not the approved mark. Do not render."
        )

    with open(cached, "wb") as fh:
        fh.write(data)
    return cached


def preflight() -> int:
    """Fetch and verify every registered mark. Returns count of failures."""
    failures = 0
    for (family, field), entry in sorted(REGISTRY.items()):
        try:
            path = logo(family, field)
            print(f"  OK    {family:24} {field:18} {entry['key']:44} -> {path}")
        except BrandAssetError as exc:
            failures += 1
            print(f"  FAIL  {family:24} {field:18} {entry['key']:44}")
            print(f"        {exc}")
    print(f"\n{len(REGISTRY) - failures}/{len(REGISTRY)} marks verified.")
    return failures


if __name__ == "__main__":
    sys.exit(1 if preflight() else 0)
