#!/usr/bin/env python3
"""nfp990/db.py — Supabase writer/reader for the 990 Part IX ingestion.

Matches worker.py's conventions: service-role key (WPP_SB_SECRET or
SUPABASE_SERVICE_ROLE_KEY), httpx against {SUPABASE_URL}/rest/v1. All writes are
idempotent so the ingest can be re-run without duplicating line items or categories.

Tables/columns are VERIFIED to exist (John's rule):
  account_financials(account_id, fiscal_year, source_doc_type, total_revenue,
                     total_expenses, addressable_spend, currency, line_items, is_primary)
  account_categories(account_id, spend_category_id, spend_amount, spend_basis,
                     source_doc, source_ref, fiscal_year<text>, confidence,
                     is_confirmed, added_by, display_order)
  nfp990_xml_index(ein, object_id, tax_period, return_type, xml_url, fetched_at)  [added by migration]
  RPC nfp990_extract_targets(p_limit)  [added by migration]
"""
from __future__ import annotations
import os
import datetime
from typing import Optional

import httpx

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = (os.environ.get("WPP_SB_SECRET") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")).strip()


def _headers(extra: Optional[dict] = None) -> dict:
    h = {"apikey": SERVICE_KEY, "Content-Type": "application/json"}
    if SERVICE_KEY.startswith("eyJ"):
        h["Authorization"] = f"Bearer {SERVICE_KEY}"
    if extra:
        h.update(extra)
    return h


def client() -> httpx.Client:
    return httpx.Client(timeout=60.0)


def _rest(cx: httpx.Client, method: str, path: str, *, params=None, json=None, prefer=None):
    extra = {"Prefer": prefer} if prefer else None
    r = cx.request(method, f"{SUPABASE_URL}/rest/v1/{path}", headers=_headers(extra), params=params, json=json)
    r.raise_for_status()
    if r.status_code == 204 or not r.content:
        return None
    return r.json()


# --- targets ----------------------------------------------------------------
def get_targets(cx: httpx.Client, limit: Optional[int] = None) -> list[dict]:
    """Buyer-gated target set, top-of-revenue first, via the nfp990_extract_targets RPC.

    Returns [{account_id, ein, name, filed_revenue, status}].
    """
    body = {"p_limit": limit}
    rows = _rest(cx, "POST", "rpc/nfp990_extract_targets", json=body) or []
    return rows


# --- idempotency ------------------------------------------------------------
def has_object(cx: httpx.Client, ein: str, object_id: str) -> bool:
    rows = _rest(cx, "GET", "nfp990_xml_index",
                 params={"ein": f"eq.{ein}", "object_id": f"eq.{object_id}", "select": "ein", "limit": "1"})
    return bool(rows)


def upsert_xml_index(cx: httpx.Client, *, ein: str, object_id: str, tax_period: str,
                     return_type: str, xml_url: str) -> None:
    _rest(cx, "POST", "nfp990_xml_index",
          prefer="resolution=merge-duplicates,return=minimal",
          json={"ein": ein, "object_id": object_id, "tax_period": tax_period,
                "return_type": return_type, "xml_url": xml_url,
                "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat()})


# --- account_financials -----------------------------------------------------
def write_account_financials(cx: httpx.Client, *, account_id: int, fiscal_year: Optional[int],
                             total_revenue: Optional[int], total_expenses: Optional[int],
                             addressable_spend: int, line_items: list[dict]) -> None:
    """Upsert the real 990 row and make it primary (mirrors enrich-990). Idempotent
    on (account_id, fiscal_year, source_doc_type='990')."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row = {
        "account_id": account_id, "fiscal_year": fiscal_year, "source_doc_type": "990",
        "total_revenue": total_revenue, "total_expenses": total_expenses,
        "addressable_spend": addressable_spend, "currency": "USD",
        "line_items": line_items, "is_primary": True, "updated_at": now,
    }
    existing = _rest(cx, "GET", "account_financials",
                     params={"account_id": f"eq.{account_id}",
                             "fiscal_year": f"eq.{fiscal_year}" if fiscal_year is not None else "is.null",
                             "source_doc_type": "eq.990", "select": "id", "limit": "1"})
    # Only one primary per account (partial unique index) — clear the current one first.
    _rest(cx, "PATCH", "account_financials", params={"account_id": f"eq.{account_id}", "is_primary": "eq.true"},
          json={"is_primary": False, "updated_at": now}, prefer="return=minimal")
    if existing:
        _rest(cx, "PATCH", "account_financials", params={"id": f"eq.{existing[0]['id']}"},
              json=row, prefer="return=minimal")
    else:
        _rest(cx, "POST", "account_financials", json=row, prefer="return=minimal")


# --- account_categories -----------------------------------------------------
def write_account_categories(cx: httpx.Client, *, account_id: int, rollups: list[dict],
                             fiscal_year: Optional[int], object_id: str) -> None:
    """Replace this account's 990-sourced category rollups (idempotent re-run)."""
    _rest(cx, "DELETE", "account_categories",
          params={"account_id": f"eq.{account_id}", "source_doc": "eq.990"}, prefer="return=minimal")
    if not rollups:
        return
    fy_txt = str(fiscal_year) if fiscal_year is not None else None
    rows = [{
        "account_id": account_id,
        "spend_category_id": r["spend_category_id"],
        "spend_amount": r["spend_amount"],
        "spend_basis": "990 Part IX functional expenses",
        "source_doc": "990",
        "source_ref": object_id,
        "fiscal_year": fy_txt,
        "confidence": "high",
        "is_confirmed": False,      # extracted suggestion; John confirms
        "added_by": "nfp990_ingest",
        "display_order": i,
    } for i, r in enumerate(rollups)]
    _rest(cx, "POST", "account_categories", json=rows, prefer="return=minimal")
