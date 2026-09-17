"""EOB v2: renders from content, signs correctly, passes the release gate, and refuses
what it must not print. Fixtures are real fn_eob_v2_content output (2026-09-17)."""
import os
import sys

import pytest
from pypdf import PdfReader

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (ROOT, os.path.join(ROOT, "cover"), os.path.join(ROOT, "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("eob_v2_engine_t", os.path.join(ROOT, "eor", "eob_v2", "engine.py"))
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)
import release_gate  # noqa: E402
import eob_v2_fixtures as F  # noqa: E402


def _text(pdf):
    return "\n".join(p.extract_text() for p in PdfReader(pdf).pages)


@pytest.mark.parametrize("content,signoff,cosign", [
    (F.TEST, F.JOHN6, None),
    (F.HUDSON, F.JOHN6, None),
    (F.HUDSON, F.JODI, F.JOHN3),
])
def test_renders_eight_pages_and_passes_the_gate(tmp_path, content, signoff, cosign):
    out, n = engine.render(content, signoff, cosign, str(tmp_path))
    assert n == 8
    identity = {"short_name": content["org"]["display"], "portal_subdomain": content["portal"]["subdomain"]}
    assert release_gate.check(out, identity, qr_payloads=engine.qr_payloads(content)) == []


def test_co_signed_letter_carries_both_names_partner_first(tmp_path):
    out, _ = engine.render(F.HUDSON, F.JODI, F.JOHN3, str(tmp_path))
    letter = PdfReader(out).pages[1].extract_text()
    assert "John Wylie" in letter and "Jodi Wiktor" in letter
    assert letter.index("John Wylie") < letter.index("Jodi Wiktor")


def test_month_only_and_figures_from_content(tmp_path):
    out, _ = engine.render(F.HUDSON, F.JOHN6, None, str(tmp_path))
    t = _text(out)
    assert "September 2026" in t and "September 17" not in t
    assert "$2.0M" in t and "$4.4M" in t and "$37,585,000" in t


def test_printed_qr_never_carries_the_access_code():
    for u in engine.qr_payloads(F.HUDSON):
        assert "?c=" not in u and F.HUDSON["portal"]["code"] not in u


@pytest.mark.parametrize("patch,why", [
    ({"portal": None}, "portal"),
    ({"recipient": dict(F.HUDSON["recipient"], blocks_package=True, blocks_reason="no address")}, "recipient"),
    ({"lines": []}, "priced lines"),
    ({"error": "no primary filing"}, "content"),
])
def test_refuses_what_it_must_not_print(tmp_path, patch, why):
    with pytest.raises(engine.EobV2Error) as e:
        engine.render(dict(F.HUDSON, **patch), F.JOHN6, None, str(tmp_path))
    assert why in str(e.value)


def test_refuses_without_a_signer(tmp_path):
    with pytest.raises(engine.EobV2Error):
        engine.render(F.HUDSON, None, None, str(tmp_path))
