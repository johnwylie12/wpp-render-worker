"""The release gate's own tests. Each case is something that already shipped.

These build tiny PDFs with reportlab (already a dependency) rather than mocking
the extractor, so a change to how text comes out of a PDF fails here rather
than silently passing everything.
"""
import os
import tempfile
import unittest

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

import release_gate as rg

IDENTITY = {
    "account_id": 20603,
    "short_name": "Hilltop Health",
    "legal_name": "Hilltop Health Services Corporation",
    "portal_subdomain": "htop-benchmark",
}


def pdf_with(lines, path):
    c = canvas.Canvas(path, pagesize=LETTER)
    y = 720
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
        if y < 72:
            c.showPage()
            y = 720
    c.save()
    return path


class GateTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def render(self, lines):
        return pdf_with(lines, os.path.join(self.dir, "t.pdf"))

    def clean_lines(self):
        return [
            "Hilltop Health Services Corporation",
            "Prepared by ERA Group",
            "portal.wpp-us.com/htop-benchmark",
            "Indirect spend $4.79M across 9 categories",
            "Change +12.4%",
        ]

    def test_a_clean_package_passes(self):
        self.assertEqual(rg.check(self.render(self.clean_lines()), IDENTITY), [])

    def test_unresolved_token_fails(self):
        f = rg.check(self.render(self.clean_lines() + ["Dear {A[buyer.name]},"]), IDENTITY)
        self.assertTrue(any("unresolved template token" in x for x in f), f)

    def test_uk_spelling_in_rendered_text_fails(self):
        # v_us_english_violations reported zero while this was in the Brief,
        # because it scans database tables and no rendered document.
        f = rg.check(self.render(self.clean_lines() + ["Comparable organisations file the same way."]), IDENTITY)
        self.assertTrue(any("UK spelling" in x and "organisation" in x for x in f), f)

    def test_banned_vocabulary_fails(self):
        f = rg.check(self.render(self.clean_lines() + ["This is not a pitch."]), IDENTITY)
        self.assertTrue(any("banned vocabulary" in x for x in f), f)
        f2 = rg.check(self.render(self.clean_lines() + ["Annual savings of $2M."]), IDENTITY)
        self.assertTrue(any("savings" in x for x in f2), f2)

    def test_truncated_currency_fails(self):
        # The category table printed "$4,789," where "$4.79M" belonged.
        f = rg.check(self.render(["Hilltop Health", "portal.wpp-us.com/htop-benchmark",
                                  "Professional Services $4,789,"]), IDENTITY)
        self.assertTrue(any("currency stopped mid-render" in x for x in f), f)

    def test_sign_with_no_number_fails(self):
        f = rg.check(self.render(["Hilltop Health", "portal.wpp-us.com/htop-benchmark",
                                  "Change + against last year"]), IDENTITY)
        self.assertTrue(any("sign with no number" in x for x in f), f)

    # THE CONTAMINATION. A Brief shipped carrying another organization's cover,
    # letter, closing and portal URL.
    def test_another_organizations_portal_path_fails(self):
        f = rg.check(self.render(["Hilltop Health", "portal.wpp-us.com/htop-benchmark",
                                  "Visit portal.wpp-us.com/pender-benchmark"]), IDENTITY)
        self.assertTrue(any("another organization's portal path" in x for x in f), f)

    def test_package_that_never_names_the_organization_fails(self):
        f = rg.check(self.render(["Prepared by ERA Group", "portal.wpp-us.com/htop-benchmark"]), IDENTITY)
        self.assertTrue(any("appears nowhere in the render" in x for x in f), f)

    def test_qr_carrying_an_access_code_fails(self):
        f = rg.check(self.render(self.clean_lines()), IDENTITY,
                     qr_payloads=["https://portal.wpp-us.com/htop-benchmark?c=K7M2Q9R"])
        self.assertTrue(any("access code" in x for x in f), f)

    def test_qr_pointing_at_the_wrong_account_fails(self):
        f = rg.check(self.render(self.clean_lines()), IDENTITY,
                     qr_payloads=["https://portal.wpp-us.com/pender-benchmark"])
        self.assertTrue(any("does not point at this account" in x for x in f), f)

    def test_page_count_must_match_the_frozen_plan(self):
        f = rg.check(self.render(self.clean_lines()), IDENTITY, frozen_plan={"page_count": 16})
        self.assertTrue(any("page count" in x for x in f), f)

    def test_priority_count_must_reconcile(self):
        f = rg.check(self.render(self.clean_lines() + ["We surface three priorities."]),
                     IDENTITY, priority_count=2)
        self.assertTrue(any("executive summary claims 3" in x for x in f), f)

    def test_enforce_raises_rather_than_reports(self):
        with self.assertRaises(rg.ReleaseFailure):
            rg.enforce(self.render(["nothing here"]), IDENTITY)


if __name__ == "__main__":
    unittest.main()
