#!/usr/bin/env python3
"""Focused guards for cover-letter signature variant authorization."""

import ast
import pathlib
import unittest

from wpp_signatures import UnknownSignature, signature_for_partner


class CoverSignoffSignatureTests(unittest.TestCase):
    def test_cover_passes_requested_key_to_authorizer(self):
        source = pathlib.Path("cover/cover_engine.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and getattr(node.func, "id", None) == "signature_for_partner"
        ]

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(calls[0].args), 2)
        self.assertEqual(ast.unparse(calls[0].args[1]), "sd.get('signature_key')")

    def test_john_can_select_approved_signature_two(self):
        self.assertEqual(signature_for_partner(3, "2"), "2")

    def test_john_invalid_variant_fails_closed(self):
        with self.assertRaises(UnknownSignature):
            signature_for_partner(3, "bogus")

    def test_non_john_cannot_borrow_john_variant(self):
        with self.assertRaises(UnknownSignature):
            signature_for_partner(1, "2")


if __name__ == "__main__":
    unittest.main()
