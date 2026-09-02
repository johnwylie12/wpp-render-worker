import copy
import hashlib
import json
import unittest

from groundwork.groundwork_engine import ABSENT_COPY, GroundworkError, validate


def signed(payload):
    payload = copy.deepcopy(payload)
    payload["checksum"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    return payload


def fixture():
    empty = lambda: {"status": "absent", "absence_copy": ABSENT_COPY, "claims": []}
    return signed({
        "contract_version": "fathum-groundwork-v1",
        "account_id": 15589,
        "layers": {
            "FILED": empty(),
            "OPERATING": {"status": "present", "absence_copy": None, "claims": [{
                "finding_id": 1, "claim_key": "program", "rung": "retrieved", "layer": "OPERATING",
                "headline": "The organization expanded its community program.", "detail": "Published on its own domain.",
                "source_url": "https://example.org/program", "source_label": "Example Organization",
                "source_date": "2026-08-20", "self_published": True,
                "verbatim_quote": "We expanded the community program this year.", "quote_verified": True,
            }]},
            "MARKET": empty(),
        },
        "rungs": {"filed": 0, "benchmark": 0, "derived": 0, "registry": 0, "retrieved": 1, "engagement": 0, "verified": 0},
        "suppressed": [],
        "inference": {"status": "absent", "label": "INFERENCE", "text": None, "presentation": "italic", "attribution": "category experience"},
    })


class GroundworkContractTest(unittest.TestCase):
    def test_validates_complete_contract(self):
        payload = fixture()
        self.assertEqual(validate(payload)["account_id"], 15589)

    def test_rejects_unverified_retrieved_quote(self):
        payload = fixture()
        payload["layers"]["OPERATING"]["claims"][0]["quote_verified"] = False
        with self.assertRaisesRegex(GroundworkError, "mechanically verified"):
            validate(signed({k: v for k, v in payload.items() if k != "checksum"}))

    def test_rejects_noncanonical_absence(self):
        payload = fixture()
        payload["layers"]["MARKET"]["absence_copy"] = "Nothing here."
        with self.assertRaisesRegex(GroundworkError, "canonical copy"):
            validate(signed({k: v for k, v in payload.items() if k != "checksum"}))

    def test_rejects_unresolved_tokens(self):
        payload = fixture()
        payload["layers"]["OPERATING"]["claims"][0]["headline"] = "Update for {{ company }}"
        with self.assertRaisesRegex(GroundworkError, "unresolved token"):
            validate(signed({k: v for k, v in payload.items() if k != "checksum"}))

    def test_rejects_checksum_drift(self):
        payload = fixture()
        payload["layers"]["OPERATING"]["claims"][0]["headline"] = "Changed after signing"
        with self.assertRaisesRegex(GroundworkError, "checksum mismatch"):
            validate(payload)


if __name__ == "__main__":
    unittest.main()
