#!/usr/bin/env python3
"""
Guard against two defect classes that have each recurred often enough to earn a
gate. Dependency-free — run it directly or under pytest:

    python3 tests/test_prospect_facing_guard.py
    pytest tests/

  1. `prospect_portals.code` printed where `access_code` belongs. `code` is the
     internal record id; `access_code` is what a prospect types. All 169 portals
     carry two different values, so a printed `code` locks the reader out every
     single time. It shipped on brief 745 (two codes in one envelope) and again
     on the package's card pages.

  2. A signoff title typed as a literal instead of read from brand_canon. Canon
     moved to "Consulting Partner" on 2026-08-14 while the cover letter, the
     closing page and the benchmark strip were all still printing the
     previous one.
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from wpp_canon import STALE_TITLES, repair_signoff, signoff  # noqa: E402

# Directories that hold no rendering logic (fonts, bundled assets, this guard).
SKIP_DIRS = {".git", "fonts", "assets", "build", "__pycache__", "tests",
             "node_modules", "enrich_990_xml"}
SCAN_EXTS = (".py", ".html", ".json")


def source_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(SCAN_EXTS):
                yield os.path.join(dirpath, fn)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def rel(path):
    return os.path.relpath(path, ROOT)


class ProspectFacingCode(unittest.TestCase):
    """`code` must never reach a printed surface."""

    # portal["code"] / portal.get("code") / portal['code'] — reading the internal
    # id out of a params portal block is the exact move that printed LJ6HXUE.
    PORTAL_CODE = re.compile(r"""portal(?:_block)?\s*(?:\[\s*["']code["']\s*\]|\.get\(\s*["']code["'])""")

    def test_no_engine_reads_portal_code(self):
        offenders = []
        for path in source_files():
            if rel(path) == "wpp_canon.py":
                continue
            for i, line in enumerate(read(path).splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#") or stripped.startswith("<!--"):
                    continue
                if self.PORTAL_CODE.search(line):
                    offenders.append("%s:%d: %s" % (rel(path), i, line.strip()))
        self.assertEqual(offenders, [], "\n".join(
            ["a render path is reading prospect_portals.code — print access_code:"] + offenders))

    def test_sticker_takes_access_code_and_has_no_code_parameter(self):
        src = read(os.path.join(ROOT, "portal_sticker", "portal_sticker.py"))
        sig = re.search(r"def render_sticker\(([^)]*)\)", src)
        self.assertIsNotNone(sig, "render_sticker signature not found")
        params = sig.group(1)
        self.assertIn("access_code", params)
        # No bare `code` parameter that a caller could feed the record id into.
        self.assertIsNone(re.search(r"(?<![\w_])code\s*:", params),
                          "render_sticker still accepts a bare `code` parameter: " + params)

    def test_cover_letter_prints_access_code_only(self):
        src = read(os.path.join(ROOT, "cover", "cover_engine.py"))
        # The letter's portal block resolves from access_code and nothing else.
        self.assertIn('_g(portal, "access_code")', src)
        self.assertNotIn('_g(portal, "code")', src)
        tpl = read(os.path.join(ROOT, "cover",
                                "WPP_EOP_CoverLetter_TEMPLATE_LOCKED_2026-08-11.html"))
        self.assertIn("{{portal_access_code}}", tpl)


class PackageAssembly(unittest.TestCase):
    """The two 6x4 card pages are out of the bound package (2026-08-19)."""

    def test_package_does_not_assemble_a_portal_card(self):
        src = read(os.path.join(ROOT, "worker.py"))
        live = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("render_sticker", live)
        self.assertNotIn("portal_sticker", live)

    def test_page_total_is_computed_from_the_assembled_document(self):
        # Task 1(3): PAGE N OF X must never read a constant — page count varies
        # by account, so a hardcoded total is wrong the moment a CIR runs long.
        src = read(os.path.join(ROOT, "worker.py"))
        self.assertIn("total = len(reader.pages) if total_mode ==", src)
        self.assertIsNone(re.search(r'"PAGE %d OF \d+"', src),
                          "package footer total is hardcoded")


class SignoffCanon(unittest.TestCase):
    """Every printed signoff reads brand_canon."""

    def test_canon_is_reachable_and_current(self):
        self.assertEqual(signoff()["title"], "Consulting Partner")

    def test_no_stale_title_literal_in_any_render_path(self):
        offenders = []
        for path in source_files():
            if rel(path) == "wpp_canon.py":   # owns the stale list
                continue
            for i, line in enumerate(read(path).splitlines(), 1):
                stripped = line.lstrip()
                if stripped.startswith("#") or stripped.startswith("<!--"):
                    continue
                for stale in STALE_TITLES:
                    if stale in line:
                        offenders.append("%s:%d: %s" % (rel(path), i, line.strip()[:160]))
        self.assertEqual(offenders, [], "\n".join(
            ["hardcoded signoff title — read it from wpp_canon.signoff():"] + offenders))


class ParamsSignoffRepair(unittest.TestCase):
    """A brief carrying a dead title in its params must still print canon.

    250 briefs sit at verification_hold with title="Senior Consultant" baked into
    params.content.signoff. Engines read params before the default, so a code-only
    fix would still have printed the stale title on every one of them.
    """

    def test_stale_title_in_params_is_replaced_by_canon(self):
        for stale in STALE_TITLES:
            fixed = repair_signoff({"name": "John Wylie", "title": stale, "org": "ERA Group"})
            self.assertEqual(fixed["title"], signoff()["title"], "not repaired: %s" % stale)

    def test_a_live_override_passes_through_untouched(self):
        block = {"name": "Dana Reed", "title": "Managing Partner", "org": "ERA Group"}
        self.assertEqual(repair_signoff(block), block)

    def test_missing_or_empty_title_falls_back_to_canon(self):
        self.assertEqual(repair_signoff({})["title"], signoff()["title"])
        self.assertEqual(repair_signoff({"title": "  "})["title"], signoff()["title"])

    def test_non_dict_is_returned_unchanged(self):
        self.assertIsNone(repair_signoff(None))

    def test_every_engine_that_reads_a_params_signoff_repairs_it(self):
        for path in ("cir/src/cir_engine.py", "snapshot/snapshot_engine.py",
                     "exec_brief/exec_brief_engine.py"):
            src = read(os.path.join(ROOT, path))
            self.assertIn("repair_signoff(", src, "%s reads a params signoff without repairing it" % path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
