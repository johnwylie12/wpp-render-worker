import os
import unittest
from unittest.mock import patch

import worker


class _Response:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _Client:
    def __init__(self, *, bucket=None, patch_rows=None):
        self.calls = []
        self.bucket = bucket if bucket is not None else {"name": "collateral", "public": False}
        self.patch_rows = patch_rows if patch_rows is not None else []

    def post(self, url, headers=None, content=None):
        self.calls.append({"method": "POST", "url": url, "headers": headers, "content": content})
        return _Response()

    def get(self, url, headers=None):
        self.calls.append({"method": "GET", "url": url, "headers": headers})
        return _Response(payload=self.bucket)

    def patch(self, url, params=None, headers=None, json=None):
        self.calls.append({
            "method": "PATCH", "url": url, "params": params,
            "headers": headers, "json": json,
        })
        return _Response(payload=self.patch_rows)


class PrivateStorageContractTests(unittest.TestCase):
    def test_upload_returns_stable_private_object_path(self):
        client = _Client()
        path = "package/15589/1600-eop.pdf"

        result = worker.upload_pdf(client, path, b"%PDF-test")

        self.assertEqual(result, path)
        self.assertEqual(len(client.calls), 1)
        self.assertIn("/storage/v1/object/collateral/", client.calls[0]["url"])
        self.assertNotIn("/object/public/", client.calls[0]["url"])

    def test_target_preflight_accepts_only_expected_private_bucket(self):
        client = _Client()
        with patch.object(worker, "SUPABASE_URL", "https://ivbhlgsxmcokyjazxlkb.supabase.co"), \
             patch.object(worker, "BUCKET", "collateral"):
            worker.validate_isolated_target(client)
        self.assertEqual(client.calls[0]["method"], "GET")
        self.assertIn("/storage/v1/bucket/collateral", client.calls[0]["url"])

    def test_target_preflight_rejects_wrong_project(self):
        with patch.object(worker, "SUPABASE_URL", "https://wrong.supabase.co"), \
             patch.object(worker, "BUCKET", "collateral"):
            with self.assertRaisesRegex(worker.RenderError, "non-isolated"):
                worker.validate_isolated_target(_Client())

    def test_target_preflight_rejects_bucket_override(self):
        with patch.object(worker, "SUPABASE_URL", "https://ivbhlgsxmcokyjazxlkb.supabase.co"), \
             patch.object(worker, "BUCKET", "public-collateral"):
            with self.assertRaisesRegex(worker.RenderError, "storage bucket"):
                worker.validate_isolated_target(_Client())

    def test_target_preflight_rejects_public_bucket_metadata(self):
        client = _Client(bucket={"name": "collateral", "public": True})
        with patch.object(worker, "SUPABASE_URL", "https://ivbhlgsxmcokyjazxlkb.supabase.co"), \
             patch.object(worker, "BUCKET", "collateral"):
            with self.assertRaisesRegex(worker.RenderError, "not private"):
                worker.validate_isolated_target(client)

    def test_one_shot_account_is_pinned_to_15589(self):
        worker.validate_one_shot_account(15589)
        with self.assertRaisesRegex(worker.RenderError, "must be 15589"):
            worker.validate_one_shot_account(15588)

    def test_one_shot_claim_is_exact_account_and_brief(self):
        row = {"id": 1600, "account_id": 15589, "doc_type": "package", "status": "rendering"}
        client = _Client(patch_rows=[row])

        result = worker.claim_one_shot_brief(client, 15589, 1600)

        self.assertEqual(result, row)
        call = client.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(call["params"]["id"], "eq.1600")
        self.assertEqual(call["params"]["account_id"], "eq.15589")
        self.assertEqual(call["params"]["status"], "eq.queued")
        self.assertEqual(call["json"]["status"], "rendering")
        self.assertEqual(call["headers"]["Prefer"], "return=representation")

    def test_one_shot_claim_fails_when_exact_row_is_not_claimable(self):
        with self.assertRaisesRegex(worker.RenderError, "not uniquely claimable"):
            worker.claim_one_shot_brief(_Client(patch_rows=[]), 15589, 1600)

    def test_one_shot_ids_are_required_positive_integers(self):
        for value in ("", "0", "-1", "not-an-id"):
            with self.subTest(value=value), patch.dict(os.environ, {"ONE_SHOT_ACCOUNT_ID": value}):
                with self.assertRaisesRegex(worker.RenderError, "positive integer"):
                    worker._required_positive_int("ONE_SHOT_ACCOUNT_ID")

    def test_unrelated_990_lane_is_disabled_by_default(self):
        self.assertFalse(worker.ENABLE_990_JOBS)


if __name__ == "__main__":
    unittest.main()
