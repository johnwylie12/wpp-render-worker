import unittest

import worker


class _Response:
    status_code = 200
    text = ""


class _Client:
    def __init__(self):
        self.calls = []

    def post(self, url, headers=None, content=None):
        self.calls.append({"url": url, "headers": headers, "content": content})
        return _Response()


class PrivateStorageContractTests(unittest.TestCase):
    def test_upload_returns_stable_private_object_path(self):
        client = _Client()
        path = "package/15589/1600-eop.pdf"

        result = worker.upload_pdf(client, path, b"%PDF-test")

        self.assertEqual(result, path)
        self.assertEqual(len(client.calls), 1)
        self.assertIn("/storage/v1/object/collateral/", client.calls[0]["url"])
        self.assertNotIn("/object/public/", client.calls[0]["url"])

    def test_unrelated_990_lane_is_disabled_by_default(self):
        self.assertFalse(worker.ENABLE_990_JOBS)


if __name__ == "__main__":
    unittest.main()
