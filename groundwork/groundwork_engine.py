#!/usr/bin/env python3
"""Render the LAW 15 Groundwork appendix carried by vertical_deepdive content."""
import hashlib
import json
import os
import re
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACT_VERSION = "fathum-groundwork-v1"
ABSENT_COPY = "None found specific enough to this organization to be worth stating. Omitted rather than filled."
LAYERS = ("FILED", "OPERATING", "MARKET")
RUNGS = ("filed", "benchmark", "derived", "registry", "retrieved", "engagement", "verified")
TOKEN_RE = re.compile(r"\{\{[^{}]+\}\}|\{[A-Za-z_][A-Za-z0-9_]*\}|\[[A-Z][A-Z0-9_ -]{2,}\]")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class GroundworkError(ValueError):
    pass


def _stable(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _http_url(value):
    parsed = urlparse(str(value or ""))
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def validate(payload):
    if not isinstance(payload, dict) or payload.get("contract_version") != CONTRACT_VERSION:
        raise GroundworkError("groundwork contract version missing or unsupported")
    if not isinstance(payload.get("account_id"), int) or payload["account_id"] <= 0:
        raise GroundworkError("groundwork account_id must be a positive integer")
    layers = payload.get("layers")
    if not isinstance(layers, dict) or set(layers) != set(LAYERS):
        raise GroundworkError("groundwork must declare FILED, OPERATING, and MARKET")
    rungs = payload.get("rungs")
    if not isinstance(rungs, dict) or set(rungs) != set(RUNGS):
        raise GroundworkError("groundwork must declare all seven evidence rungs")

    for layer_name in LAYERS:
        layer = layers[layer_name]
        claims = layer.get("claims") if isinstance(layer, dict) else None
        if layer.get("status") not in ("present", "absent") or not isinstance(claims, list):
            raise GroundworkError("invalid %s layer" % layer_name)
        if layer["status"] == "absent":
            if claims or layer.get("absence_copy") != ABSENT_COPY:
                raise GroundworkError("%s absence must use canonical copy" % layer_name)
        elif not claims or layer.get("absence_copy") is not None:
            raise GroundworkError("%s present layer must contain claims" % layer_name)

        for claim in claims:
            if claim.get("layer") != layer_name or claim.get("rung") not in RUNGS:
                raise GroundworkError("claim layer or rung mismatch")
            if not str(claim.get("headline") or "").strip():
                raise GroundworkError("claim headline required")
            if not _http_url(claim.get("source_url")):
                raise GroundworkError("claim source URL must resolve as HTTP(S)")
            if not DATE_RE.match(str(claim.get("source_date") or "")):
                raise GroundworkError("claim source date required")
            if claim.get("rung") == "retrieved":
                if claim.get("quote_verified") is not True or len(str(claim.get("verbatim_quote") or "").strip()) < 12:
                    raise GroundworkError("retrieved claims require a mechanically verified verbatim quote")
            text = " ".join(str(claim.get(k) or "") for k in ("headline", "detail", "verbatim_quote", "source_label"))
            if TOKEN_RE.search(text):
                raise GroundworkError("unresolved token in Groundwork claim")

    inference = payload.get("inference") or {}
    if inference.get("status") != "absent" or inference.get("text") is not None:
        if inference.get("label") != "INFERENCE" or inference.get("presentation") != "italic" or inference.get("attribution") != "category experience":
            raise GroundworkError("inference must be separately labelled, italic, and attributed")

    claimed_checksum = str(payload.get("checksum") or "")
    unsigned = {k: v for k, v in payload.items() if k != "checksum"}
    expected_checksum = hashlib.sha256(_stable(unsigned).encode("utf-8")).hexdigest()
    if claimed_checksum != expected_checksum:
        raise GroundworkError("groundwork checksum mismatch")
    return payload


def render(payload, org_name, out_pdf):
    # Keep contract validation importable in environments without WeasyPrint's
    # native Pango/GObject libraries. The Railway image installs them; local
    # contract tests should still run without pretending a PDF was rendered.
    from weasyprint import HTML
    data = validate(payload)
    env = Environment(
        loader=FileSystemLoader(HERE),
        undefined=StrictUndefined,
        autoescape=select_autoescape(("html", "xml")),
    )
    html = env.get_template("groundwork_template.html").render(
        org_name=org_name,
        layers=[(name, data["layers"][name]) for name in LAYERS],
        rungs=[(name, data["rungs"][name]) for name in RUNGS],
        inference=data["inference"],
        checksum=data["checksum"],
    )
    HTML(string=html, base_url=HERE).write_pdf(out_pdf)
    return out_pdf
