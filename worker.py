#!/usr/bin/env python3
"""WPP Collateral render worker.

The back half of the "Create collateral" pipeline. The app enqueues a
`content_briefs` row (status='queued') via the enqueue_brief RPC; this worker
claims it, renders the PDF with the LOCKED CIR engine (+ an optional ERA cover
letter merged in front), uploads the result to Supabase Storage, and writes
rendered_url + status back to the row.

Design notes
------------
* Claiming is atomic via the claim_next_brief(p_doc_types) RPC
  (FOR UPDATE SKIP LOCKED) so two workers never grab the same brief.
* Only doc_types this worker has a renderer for are claimed; everything else is
  left untouched in the queue. Today that's the CIR ('vertical_deepdive',
  "Cost Intelligence Report") and the standalone Executive Opportunity Snapshot
  ('opportunity_snapshot').
* The CIR template is FROZEN. We never edit it. The cover letter is a separate
  template merged with pypdf.
* Uses the service-role key -> bypasses RLS for claim/update + Storage writes.

Run modes
---------
    python worker.py                # poll loop (default)
    python worker.py --once         # claim+render one brief, then exit
    python worker.py --selftest     # render carmel.json + a sample cover, no DB

Env
---
    SUPABASE_URL                 (required)
    SUPABASE_SERVICE_ROLE_KEY    (required)
    STORAGE_BUCKET               (default: collateral)
    SUPPORTED_DOC_TYPES          (default: vertical_deepdive)  comma-separated
    SNAPSHOT_DOC_TYPES           (default: opportunity_snapshot)  comma-separated
    POLL_SECONDS                 (default: 60)
"""
import os, sys, json, time, re, tempfile, subprocess, datetime, traceback
import httpx
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
CIR_ENGINE   = os.path.join(HERE, "cir", "src", "cir_engine.py")
FONTS_CONF   = os.path.join(HERE, "cir", "build", "fonts.conf")
sys.path.insert(0, os.path.join(HERE, "cover"))
sys.path.insert(0, os.path.join(HERE, "snapshot"))
sys.path.insert(0, os.path.join(HERE, "benchmark"))
import cover_engine       # noqa: E402
import snapshot_engine    # noqa: E402
import cover_page_engine  # noqa: E402
import benchmark_engine   # noqa: E402

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY  = (os.environ.get("WPP_SB_SECRET")
                or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")).strip()
BUCKET       = os.environ.get("STORAGE_BUCKET", "collateral")
SUPPORTED    = [s.strip() for s in os.environ.get("SUPPORTED_DOC_TYPES",
                                                   "vertical_deepdive").split(",") if s.strip()]
SNAPSHOT_DOC_TYPES = [s.strip() for s in os.environ.get("SNAPSHOT_DOC_TYPES",
                                                   "opportunity_snapshot").split(",") if s.strip()]
COVER_PAGE_DOC_TYPES = [s.strip() for s in os.environ.get("COVER_PAGE_DOC_TYPES",
                                                   "cover_page").split(",") if s.strip()]
BENCHMARK_DOC_TYPES = [s.strip() for s in os.environ.get("BENCHMARK_DOC_TYPES",
                                                   "sector_benchmark").split(",") if s.strip()]
# Claim CIR + snapshot + cover_page doc_types by default — no Railway env edit required.
CLAIM_DOC_TYPES = SUPPORTED + [s for s in (SNAPSHOT_DOC_TYPES + COVER_PAGE_DOC_TYPES + BENCHMARK_DOC_TYPES) if s not in SUPPORTED]
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "60"))


class RenderError(Exception):
    """A brief-level failure: record on the row, keep the worker alive."""


# ---------------------------------------------------------------- Supabase REST
def _headers(extra=None):
    # The key always goes on the apikey header. Legacy service_role keys are
    # JWTs (eyJ...) and ALSO go on Authorization: Bearer. The new sb_secret_/
    # sb_publishable_ keys are NOT JWTs -- if sent as a Bearer token the gateway
    # tries to parse them as a JWT and rejects the request with 401. So send
    # them on apikey only and let the gateway resolve the role.
    h = {"apikey": SERVICE_KEY, "Content-Type": "application/json"}
    if SERVICE_KEY.startswith("eyJ"):
        h["Authorization"] = f"Bearer {SERVICE_KEY}"
    if extra:
        h.update(extra)
    return h


def _client():
    return httpx.Client(timeout=60.0)


def claim_brief(cx):
    r = cx.post(f"{SUPABASE_URL}/rest/v1/rpc/claim_next_brief",
                headers=_headers(), json={"p_doc_types": CLAIM_DOC_TYPES})
    if r.status_code >= 400:
        print(f"[diag] claim HTTP {r.status_code} body={r.text[:300]!r} "
              f"key_fp={SERVICE_KEY[:6]!r} key_len={len(SERVICE_KEY)} "
              f"sent_bearer={SERVICE_KEY.startswith('eyJ')}",
              file=sys.stderr, flush=True)
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


def update_brief(cx, brief_id, fields):
    r = cx.patch(f"{SUPABASE_URL}/rest/v1/content_briefs?id=eq.{brief_id}",
                 headers=_headers({"Prefer": "return=minimal"}), json=fields)
    r.raise_for_status()


def fetch_contact(cx, contact_id):
    if not contact_id:
        return None
    r = cx.get(f"{SUPABASE_URL}/rest/v1/contacts?id=eq.{contact_id}"
               f"&select=first_name,last_name,title", headers=_headers())
    r.raise_for_status()
    rows = r.json()
    if not rows:
        return None
    c = rows[0]
    name = f"{c.get('first_name') or ''} {c.get('last_name') or ''}".strip()
    return {"name": name or None, "title": c.get("title")}


def fetch_account_name(cx, account_id):
    if not account_id:
        return None
    r = cx.get(f"{SUPABASE_URL}/rest/v1/accounts?id=eq.{account_id}&select=name",
               headers=_headers())
    r.raise_for_status()
    rows = r.json()
    return rows[0]["name"] if rows else None


def upload_pdf(cx, path, pdf_bytes):
    """Upload to Storage (upsert) and return the public URL."""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{path}"
    r = cx.post(url, headers=_headers({"Content-Type": "application/pdf",
                                       "x-upsert": "true"}),
                content=pdf_bytes)
    if r.status_code not in (200, 201):
        raise RenderError(f"storage upload failed {r.status_code}: {r.text[:200]}")
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{path}"


# ---------------------------------------------------------------- rendering
def _slug(s, fallback="collateral"):
    base = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:48].strip("-")
    return base or fallback


def extract_cir_content(params):
    """Return the carmel-shaped content object the locked engine expects, or
    raise a clear RenderError. Accepts either params.content or a params root
    that is itself carmel-shaped."""
    if isinstance(params, dict):
        if isinstance(params.get("content"), dict) and "org" in params["content"]:
            return params["content"]
        if "org" in params and "categories" in params:
            return params
    raise RenderError(
        "no CIR content in params: expected params.content (carmel-shaped, with "
        "'org' + 'categories'). The enqueue for this doc_type isn't producing "
        "CIR content yet.")


def render_cir(content, out_pdf):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(content, f)
        src = f.name
    env = dict(os.environ)
    if os.path.exists(FONTS_CONF):
        env["FONTCONFIG_FILE"] = FONTS_CONF
    try:
        proc = subprocess.run([sys.executable, CIR_ENGINE, src, out_pdf],
                              capture_output=True, text=True, env=env, timeout=180)
    finally:
        os.unlink(src)
    if proc.returncode != 0:
        raise RenderError(f"CIR engine failed: {proc.stderr.strip()[:400]}")
    return out_pdf


def merge_front(cover_pdf, body_pdf, out_pdf):
    w = PdfWriter()
    for p in PdfReader(cover_pdf).pages:
        w.add_page(p)
    for p in PdfReader(body_pdf).pages:
        w.add_page(p)
    with open(out_pdf, "wb") as fh:
        w.write(fh)
    return out_pdf


def cover_config(brief, params):
    """Resolve cover delivery: (mode, size, letter_block).

    mode: 'none' | 'bundled' | 'separate'
      - bundled : cover merged in front of the CIR -> ONE Letter PDF (size forced
                  to Letter so it matches the CIR sheet).
      - separate: cover rendered as its OWN PDF at the selected paper size, in
                  addition to the CIR (printed separately).
    Backward compatible: legacy briefs that only set the `cover_letter` boolean
    map to bundled (True) / none (False)."""
    cc = params.get("cover") or {}
    mode = cc.get("mode") or ("bundled" if brief.get("cover_letter") else "none")
    size = cc.get("size") or "letter"
    letter_block = cc.get("letter") or params.get("cover_letter")  # content block
    return mode, size, letter_block


def build_pdf(cx, brief, workdir):
    """Render the brief; return (final_path, page_count, cover_path|None, cover_size|None, kind).

    kind is 'cir' or 'snapshot' and selects the storage prefix. cover_path is
    non-None only for CIR mode='separate' (a second, standalone file)."""
    params = brief.get("params") or {}
    content = extract_cir_content(params)

    # ---- snapshot path: standalone one-page Executive Opportunity Snapshot.
    # Reuses the carmel-shaped content (needs org + opportunity). No cover, no CIR.
    if brief.get("doc_type") in SNAPSHOT_DOC_TYPES:
        opp = content.get("opportunity") or {}
        if opp.get("low_usd") is None or opp.get("high_usd") is None:
            raise RenderError("snapshot requires params.content.opportunity "
                              "low_usd and high_usd")
        snap_pdf = os.path.join(workdir, "snapshot.pdf")
        snapshot_engine.render(content, snap_pdf)
        return snap_pdf, len(PdfReader(snap_pdf).pages), None, None, "snapshot"

    # ---- cover page: standalone premium cover for any collateral. Fields come
    # from `org`; the centered `title` varies by collateral (default per
    # for_doc_type); the hero is auto-picked per vertical from the CIR library.
    if brief.get("doc_type") in COVER_PAGE_DOC_TYPES:
        org = content.get("org") or {}
        if not org.get("name"):
            raise RenderError("cover_page requires params.content.org.name")
        cp = params.get("cover_page") or {}
        cover_pdf = os.path.join(workdir, "cover_page.pdf")
        cover_page_engine.render(
            org, cover_pdf,
            title=cp.get("title"),
            subtitle=cp.get("subtitle"),
            statement=cp.get("statement"),
            date_str=cp.get("date"),
            doc_type=cp.get("for_doc_type", "package"),
        )
        return cover_pdf, len(PdfReader(cover_pdf).pages), None, None, "cover"

    # ---- sector benchmark: standalone one-page "Benchmark Behind This Analysis".
    # params.benchmark.sector selects the sector data block (e.g. 'healthcare',
    # 'not_for_profit'). Sector-level content; no org required.
    if brief.get("doc_type") in BENCHMARK_DOC_TYPES:
        bm = params.get("benchmark") or {}
        sector = bm.get("sector")
        if not sector:
            raise RenderError("sector_benchmark requires params.benchmark.sector "
                              "(e.g. 'healthcare' or 'not_for_profit')")
        bm_pdf = os.path.join(workdir, "benchmark.pdf")
        try:
            benchmark_engine.render(sector, bm_pdf)
        except ValueError as e:
            raise RenderError(str(e))
        return bm_pdf, len(PdfReader(bm_pdf).pages), None, None, "benchmark"

    cir_pdf = os.path.join(workdir, "cir.pdf")
    render_cir(content, cir_pdf)
    final = cir_pdf
    cover_path = None
    cover_size_used = None

    mode, size, letter_block = cover_config(brief, params)
    if mode in ("bundled", "separate"):
        recipient = fetch_contact(cx, brief.get("contact_id"))
        company = (content.get("org") or {}).get("name") or \
                  fetch_account_name(cx, brief.get("account_id"))
        if not (recipient and recipient.get("name")) and \
           not ((letter_block or {}).get("recipient")):
            raise RenderError("cover letter requested but no recipient resolved "
                              "(set contact_id or params.cover.letter.recipient)")
        cover = cover_engine.build_cover(letter_block, recipient, company)
        if mode == "bundled":
            cover_pdf = os.path.join(workdir, "cover.pdf")
            cover_engine.render_cover(cover, cover_pdf, page_size="letter")
            final = os.path.join(workdir, "final.pdf")
            merge_front(cover_pdf, cir_pdf, final)
            cover_size_used = "letter"
        else:  # separate
            cover_path = os.path.join(workdir, "cover.pdf")
            cover_engine.render_cover(cover, cover_path, page_size=size)
            cover_size_used = size

    return final, len(PdfReader(final).pages), cover_path, cover_size_used, "cir"


# ---------------------------------------------------------------- loop
def process_one(cx):
    brief = claim_brief(cx)
    if not brief:
        return False
    bid = brief["id"]
    print(f"[claim] brief {bid} doc_type={brief['doc_type']} "
          f"cover={brief.get('cover_letter')} account={brief.get('account_id')}")
    try:
        with tempfile.TemporaryDirectory() as wd:
            final, npages, cover_path, cover_size, kind = build_pdf(cx, brief, wd)
            company = ((brief.get("params") or {}).get("content") or
                       brief.get("params") or {}).get("org", {}).get("name")
            name = _slug(company or brief.get("title") or f"brief-{bid}")
            base = f"{kind}/{brief.get('account_id') or 'misc'}/{bid}-{name}"
            with open(final, "rb") as fh:
                url = upload_pdf(cx, f"{base}.pdf", fh.read())
            cover_url = None
            if cover_path:  # mode='separate' -> upload the standalone cover too
                with open(cover_path, "rb") as fh:
                    cover_url = upload_pdf(cx, f"{base}-cover.pdf", fh.read())
        patch = {
            "status": "rendered", "rendered_url": url,
            "rendered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "error": None}
        if cover_url:
            patch["cover_url"] = cover_url
            patch["cover_size"] = cover_size
        if kind == "snapshot":
            patch["snapshot_url"] = url
        update_brief(cx, bid, patch)
        print(f"[done]  brief {bid} -> {url} ({npages}pp)"
              + (f" + cover[{cover_size}] -> {cover_url}" if cover_url else ""))
    except Exception as e:
        msg = str(e) if isinstance(e, RenderError) else f"{type(e).__name__}: {e}"
        print(f"[fail]  brief {bid}: {msg}")
        if not isinstance(e, RenderError):
            traceback.print_exc()
        update_brief(cx, bid, {"status": "failed", "error": msg[:1000]})
    return True


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not SUPABASE_URL or not SERVICE_KEY:
        sys.exit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    once = "--once" in sys.argv
    print(f"[worker] claim doc_types={CLAIM_DOC_TYPES} bucket={BUCKET} "
          f"poll={POLL_SECONDS}s once={once}")
    print(f"[diag] startup url={SUPABASE_URL!r} key_fp={SERVICE_KEY[:6]!r} "
          f"key_len={len(SERVICE_KEY)} sent_bearer={SERVICE_KEY.startswith('eyJ')}",
          file=sys.stderr, flush=True)
    with _client() as cx:
        while True:
            try:
                worked = process_one(cx)
            except Exception:
                traceback.print_exc()
                worked = False
            if once:
                break
            if not worked:
                time.sleep(POLL_SECONDS)


def selftest():
    """Render carmel.json + a sample cover, merge, no DB. Proves the toolchain."""
    wd = tempfile.mkdtemp()
    content = json.load(open(os.path.join(HERE, "cir", "content", "carmel.json")))
    cir_pdf = render_cir(content, os.path.join(wd, "cir.pdf"))
    cover = cover_engine.build_cover(
        None, {"name": "Nick Jacobi", "title": "General Manager"},
        content["org"]["name"])
    cover_pdf = cover_engine.render_cover(cover, os.path.join(wd, "cover.pdf"))
    final = merge_front(cover_pdf, cir_pdf, os.path.join(wd, "final.pdf"))
    snap_pdf = snapshot_engine.render(content, os.path.join(wd, "snapshot.pdf"))
    print(f"[selftest] CIR+cover {final} ({len(PdfReader(final).pages)}pp); "
          f"snapshot {snap_pdf} ({len(PdfReader(snap_pdf).pages)}pp)")
    print(final)


if __name__ == "__main__":
    main()
