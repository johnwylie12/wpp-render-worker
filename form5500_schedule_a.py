#!/usr/bin/env python3
"""
RUNG 4 — REGISTRY. Form 5500 Schedule A.

WHY THIS RUNG IS WORTH MORE THAN THE ONE WE ALREADY HAVE
Form 990 Part VII Section B names five contractors and gives no terms.
Schedule A names the insurance CARRIER, names the BROKER who placed the cover,
and states the COMMISSION AND FEES that broker was paid. That is a named vendor
WITH A PRICE, filed by the organisation itself, free, with no model anywhere in
the path — so it cannot be fabricated and it cannot be argued with.

WHY IT LIVES HERE AND NOT IN AN EDGE FUNCTION
Seven versions were attempted as a Supabase edge function on 2026-09-03:

    v1  zipjs from deno.land                 BOOT_ERROR
    v3  whole CSV to a string, then split    WORKER_RESOURCE_LIMIT  (memory)
    v4  streamed inflate, still arrayBuffer  WORKER_RESOURCE_LIMIT  (memory)
    v5  header stripped in flight            read the header, then died (CPU)
    v6  parent/child join                    WORKER_RESOURCE_LIMIT  (CPU)
    v7  fast-path CSV splitter               WORKER_RESOURCE_LIMIT  (CPU)

v5 proved the MEMORY problem was solvable — nothing held but one chunk, one
line, and the ACK_ID index. What remained was a hard compute budget: two files
of roughly a million rows each is more CPU than an edge function is allowed, and
no amount of parser tuning changes that. Railway has no such cap.

The lesson, recorded because it cost half an hour of retries: when the second
attempt fails on RESOURCE rather than on LOGIC, move the work. Optimising into
a ceiling is not engineering.

SOURCE
  https://askebsa.dol.gov/FOIA Files/{year}/Latest/F_SCH_A_{year}_Latest.zip
  https://askebsa.dol.gov/FOIA Files/{year}/Latest/F_SCH_A_PART1_{year}_Latest.zip

  PARENT  one row per Schedule A. SCH_A_EIN, ACK_ID, carrier, persons covered,
          and the SCHEDULE-LEVEL commission and fee totals.
  CHILD   one row per BROKER on that schedule. Broker name and their share.
          NO EIN — it joins on ACK_ID only.

  The parent already carries the money; the child says WHO. A schedule with no
  child row still yields a priced carrier relationship, which is why the parent
  drives the output and the child enriches it.

  NOTE: www.dol.gov is behind an Akamai bot block and returns 403. askebsa.dol.gov
  is not. Do not "fix" the URL to the documentation host.

WHAT THIS REFUSES TO DO
  Invent, infer or fill. A row is written only where the EIN matches an account
  we already hold, and every field is the filer's own value or NULL.

USAGE
  python form5500_schedule_a.py --year 2024 --dry-run
  python form5500_schedule_a.py --year 2024

  Needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in the environment — the same
  two the render worker already uses.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import sys
import zipfile
from typing import Dict, Iterator, List, Optional, Tuple

import httpx

BASE = "https://askebsa.dol.gov/FOIA%20Files"
PAGE = 500


def _sb(method: str, path: str, **kw) -> httpx.Response:
    url = os.environ["SUPABASE_URL"].rstrip("/") + path
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    headers.update(kw.pop("headers", {}))
    r = httpx.request(method, url, headers=headers, timeout=120, **kw)
    r.raise_for_status()
    return r


def load_eins() -> Dict[str, int]:
    """Every EIN we hold, digits only. The archive is every Schedule A in the
    country; we keep only the rows that are ours."""
    out: Dict[str, int] = {}
    start = 0
    while True:
        r = _sb(
            "GET",
            f"/rest/v1/accounts?select=id,ein&ein=not.is.null",
            headers={"Range": f"{start}-{start + 999}", "Prefer": "count=none"},
        )
        rows = r.json()
        if not rows:
            break
        for row in rows:
            k = "".join(ch for ch in str(row.get("ein") or "") if ch.isdigit())
            if len(k) == 9:
                out[k] = row["id"]
        if len(rows) < 1000:
            break
        start += 1000
    return out


def stream_csv(year: int, part: bool) -> Iterator[List[str]]:
    """Download the archive to a temp file and read the single CSV member out of
    it. Streaming to disk rather than into memory keeps a 100MB+ archive off the
    heap, and zipfile then reads the member incrementally."""
    name = f"F_SCH_A_PART1_{year}_Latest.zip" if part else f"F_SCH_A_{year}_Latest.zip"
    url = f"{BASE}/{year}/Latest/{name}"
    tmp = f"/tmp/{name}"
    if not os.path.exists(tmp) or os.path.getsize(tmp) < 1024:
        with httpx.stream("GET", url, timeout=600, follow_redirects=True) as r:
            r.raise_for_status()
            with open(tmp, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
    with zipfile.ZipFile(tmp) as z:
        member = max(
            (n for n in z.namelist() if n.lower().endswith(".csv")),
            key=lambda n: z.getinfo(n).file_size,
        )
        with z.open(member) as fh:
            # latin-1: the DOL files are not UTF-8 and a UTF-8 decode raises on
            # carrier names with accented characters.
            reader = csv.reader(io.TextIOWrapper(fh, encoding="latin-1", newline=""))
            for row in reader:
                yield row


def idx(header: List[str], *names: str) -> int:
    up = [h.strip().upper() for h in header]
    for n in names:
        if n in up:
            return up.index(n)
    return -1


def num(v: Optional[str]):
    if not v:
        return None
    s = "".join(ch for ch in v if ch.isdigit() or ch in ".-")
    try:
        return float(s) if s not in ("", "-", ".") else None
    except ValueError:
        return None


def txt(v: Optional[str]):
    s = (v or "").strip()
    return s or None


def run(year: int, dry_run: bool) -> dict:
    eins = load_eins()

    # PASS 1 — parent. Only schedules whose EIN is ours are kept.
    by_ack: Dict[str, dict] = {}
    parent_rows = 0
    header: Optional[List[str]] = None
    cols: Tuple[int, ...] = ()
    for row in stream_csv(year, part=False):
        if header is None:
            header = row
            cols = (
                idx(header, "ACK_ID"),
                idx(header, "SCH_A_EIN", "SPONS_DFE_EIN"),
                idx(header, "INS_CARRIER_NAME"),
                idx(header, "INS_CARRIER_EIN"),
                idx(header, "INS_PRSN_COVERED_EOY_CNT"),
                idx(header, "INS_TOT_POLICY_YR_PREM_AMT"),
                idx(header, "SCH_A_PLAN_NUM", "SPONS_DFE_PN"),
                idx(header, "INS_BROKER_COMM_TOT_AMT"),
                idx(header, "INS_BROKER_FEES_TOT_AMT"),
            )
            if cols[0] < 0 or cols[1] < 0:
                raise SystemExit(f"parent columns not found: {header[:30]}")
            continue
        parent_rows += 1
        try:
            ein = "".join(ch for ch in row[cols[1]] if ch.isdigit())
        except IndexError:
            continue
        acct = eins.get(ein)
        if acct is None:
            continue
        ack = txt(row[cols[0]])
        if not ack:
            continue
        g = lambda i: row[i] if 0 <= i < len(row) else None  # noqa: E731
        by_ack[ack] = {
            "account_id": acct,
            "ein": ein,
            "plan_year": year,
            "plan_num": txt(g(cols[6])),
            "carrier_name": txt(g(cols[2])),
            "carrier_ein": txt(g(cols[3])),
            "persons_covered": num(g(cols[4])),
            "premium_amt": num(g(cols[5])),
            "_comm": num(g(cols[7])),
            "_fees": num(g(cols[8])),
        }

    # PASS 2 — child. WHO the broker is. Joined on ACK_ID, so a commission can
    # never attach to an organisation we did not match.
    named: Dict[str, List[dict]] = {}
    child_rows = 0
    header = None
    kc: Tuple[int, ...] = ()
    for row in stream_csv(year, part=True):
        if header is None:
            header = row
            kc = (
                idx(header, "ACK_ID"),
                idx(header, "INS_BROKER_NAME"),
                idx(header, "INS_BROKER_US_ADDRESS1"),
                idx(header, "INS_BROKER_COMM_PD_AMT"),
                idx(header, "INS_BROKER_FEES_PD_AMT"),
                idx(header, "INS_BROKER_FEES_PD_TEXT"),
            )
            continue
        child_rows += 1
        try:
            ack = row[kc[0]].strip()
        except IndexError:
            continue
        if ack not in by_ack:
            continue
        g = lambda i: row[i] if 0 <= i < len(row) else None  # noqa: E731
        named.setdefault(ack, []).append({
            "broker_name": txt(g(kc[1])),
            "broker_us_address": txt(g(kc[2])),
            "commission_amt": num(g(kc[3])),
            "fees_amt": num(g(kc[4])),
            "fees_purpose": txt(g(kc[5])),
        })

    # EMIT. One row per broker where a broker is named; one per schedule where
    # none is, so a priced carrier relationship is not lost to a blank line.
    rows: List[dict] = []
    for ack, p in by_ack.items():
        comm, fees = p.pop("_comm"), p.pop("_fees")
        base = dict(p, source_year=year, source_file=f"F_SCH_A + PART1 {year}", ack_id=ack)
        brokers = named.get(ack)
        if brokers:
            for br in brokers:
                rows.append({**base, **br})
        elif comm is not None or fees is not None or base.get("carrier_name"):
            rows.append({**base, "commission_amt": comm, "fees_amt": fees})

    inserted = 0
    if not dry_run and rows:
        _sb("DELETE", f"/rest/v1/account_benefit_broker?source_year=eq.{year}")
        for i in range(0, len(rows), PAGE):
            chunk = rows[i:i + PAGE]
            _sb("POST", "/rest/v1/account_benefit_broker", json=chunk)
            inserted += len(chunk)

    return {
        "year": year,
        "dry_run": dry_run,
        "eins_held": len(eins),
        "parent_rows": parent_rows,
        "our_schedules": len(by_ack),
        "child_rows": child_rows,
        "schedules_with_named_broker": len(named),
        "rows": len(rows),
        "inserted": inserted,
        "sample": rows[:5],
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    import json
    json.dump(run(a.year, a.dry_run), sys.stdout, indent=2, default=str)
    print()
