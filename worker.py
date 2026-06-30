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
  label "Cost Intelligence Report").
* The CIR template is FROZEN. We never edit it. The cover letter is a separate
  template merged with pypdf.
* Uses the service-role key -> bypasses RLS for claim/update + Storage writes.

Run modes
---------
    python worker.py                # poll loop (default)
    python worker.py --once         # claim+render one brief, then exit
    python worker.py --selftest     # render CIR + snapshot + cover, merge, no DB

Env
---
    SUPABASE_URL                 (required)
    SUPABASE_SERVICE_ROLE_KEY    (required)
    STORAGE_BUCKET               (default: collateral)
    SUPPORTED_DOC_TYPES          (default: vertical_deepdive)  comma-separated
    POLL_SECONDS                 (default: 60)
"""
import os, sys, json, time, re, tempfile, subprocess, datetime, traceback
import httpx
from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
CIR_ENGINE      = os.path.join(HERE, "cir", "src", "cir_engine.py")
SNAPSHOT_ENGINE = os.path.join(HERE, "snapshot", "snapshot_engine.py")
FONTS_CONF      = os.path.join(HERE, "cir", "build", "fonts.conf")
sys.path.insert(0, os.path.join(HERE, "cover"))
import cover_engine  # noqa: E402

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY  = (os.environ.get("WPP_SB_SECRET")
                or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")).strip()
BUCKET       = os.environ.get("STORAGE_BUCKET", "collateral")
SUPPORTED    = [s.strip() for s in os.environ.get("SUPPORTED_DOC_TYPES",
                                                   "vertical_deepdive").split(",") if s.strip()]
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
                headers=_headers(), json={"p_doc_types": SUPPORTED})
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


def render_snapshot(content, out_pdf):
    """Render the one-page Executive Opportunity Snapshot via its standalone
    engine (CLI, exactly like the CIR engine). Reads the SAME content JSON the
    CIR uses -- dollars from `opportunity`, framing from `org.vertical`/`org.type`
    -- so no extra inputs are required. Letter page; merges cleanly with the CIR."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(content, f)
        src = f.name
    env = dict(os.environ)
    if os.path.exists(FONTS_CONF):
        env["FONTCONFIG_FILE"] = FONTS_CONF
    try:
        proc = subprocess.run([sys.executable, SNAPSHOT_ENGINE, src, out_pdf],
                              capture_output=True, text=True, env=env, timeout=180)
    finally:
        os.unlink(src)
    if proc.returncode != 0:
        raise RenderError(f"snapshot engine failed: {proc.stderr.strip()[:400]}")
    return out_pdf


def merge_pdfs(parts, out_pdf):
    """Concatenate `parts` (list of PDF paths, in order) into one PDF."""
    w = PdfWriter()
    for part in parts:
        for p in PdfReader(part).pages:
            w.add_page(p)
    with open(out_pdf, "wb") as fh:
        w.write(fh)
    return out_pdf


def merge_front(cover_pdf, body_pdf, out_pdf):
    return merge_pdfs([cover_pdf, body_pdf], out_pdf)


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


def snapshot_config(params):
    """Resolve snapshot delivery mode: 'none' | 'bundled' | 'separate'.

      - bundled : the one-page snapshot is merged in FRONT of the CIR (after the
                  cover letter, if any) -> part of the single Opportunity Brief PDF.
      - separate: rendered as its OWN standalone Letter PDF (a leave-behind),
                  uploaded alongside the CIR and surfaced via snapshot_url.
    Gated entirely by params.snapshot.mode; no snapshot content is needed -- the
    engine derives everything from the same CIR content JSON."""
    sc = params.get("snapshot") or {}
    return sc.get("mode") or "none"


def build_pdf(cx, brief, workdir):
    """Render the brief. Returns a dict:
        { final, npages, cover_path, cover_size, snapshot_path }
    `final` is the deliverable CIR PDF with any bundled fronts merged in.
    `cover_path` / `snapshot_path` are non-None only for that artifact's
    'separate' mode -> standalone files uploaded in addition to the CIR.

    Bundled front order (outermost first): cover letter, then snapshot, then CIR."""
    params = brief.get("params") or {}
    content = extract_cir_content(params)

    cir_pdf = os.path.join(workdir, "cir.pdf")
    render_cir(content, cir_pdf)

    fronts = []                 # bundled pieces, in order, merged before the CIR
    cover_path = None
    cover_size_used = None
    snapshot_path = None

    # ---- cover letter (personalized; needs a recipient) --------------------
    cmode, csize, letter_block = cover_config(brief, params)
    if cmode in ("bundled", "separate"):
        recipient = fetch_contact(cx, brief.get("contact_id"))
        company = (content.get("org") or {}).get("name") or \
                  fetch_account_name(cx, brief.get("account_id"))
        if not (recipient and recipient.get("name")) and \
           not ((letter_block or {}).get("recipient")):
            raise RenderError("cover letter requested but no recipient resolved "
                              "(set contact_id or params.cover.letter.recipient)")
        cover = cover_engine.build_cover(letter_block, recipient, company)
        if cmode == "bundled":
            cover_pdf = os.path.join(workdir, "cover.pdf")
            cover_engine.render_cover(cover, cover_pdf, page_size="letter")
            fronts.append(cover_pdf)
            cover_size_used = "letter"
        else:  # separate
            cover_path = os.path.join(workdir, "cover.pdf")
            cover_engine.render_cover(cover, cover_path, page_size=csize)
            cover_size_used = csize

    # ---- snapshot (data-driven; no recipient, derived from CIR content) -----
    smode = snapshot_config(params)
    if smode == "bundled":
        snap_pdf = os.path.join(workdir, "snapshot.pdf")
        render_snapshot(content, snap_pdf)
        fronts.append(snap_pdf)         # after the cover letter, before the CIR
    elif smode == "separate":
        snapshot_path = os.path.join(workdir, "snapshot.pdf")
        render_snapshot(content, snapshot_path)

    # ---- assemble the deliverable ------------------------------------------
    if fronts:
        final = os.path.join(workdir, "final.pdf")
        merge_pdfs([*fronts, cir_pdf], final)
    else:
        final = cir_pdf

    return {
        "final": final,
        "npages": len(PdfReader(final).pages),
        "cover_path": cover_path,
        "cover_size": cover_size_used,
        "snapshot_path": snapshot_path,
    }


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
            res = build_pdf(cx, brief, wd)
            company = ((brief.get("params") or {}).get("content") or
                       brief.get("params") or {}).get("org", {}).get("name")
            name = _slug(company or brief.get("title") or f"brief-{bid}")
            base = f"cir/{brief.get('account_id') or 'misc'}/{bid}-{name}"
            with open(res["final"], "rb") as fh:
                url = upload_pdf(cx, f"{base}.pdf", fh.read())
            cover_url = None
            if res["cover_path"]:  # cover mode='separate' -> standalone file
                with open(res["cover_path"], "rb") as fh:
                    cover_url = upload_pdf(cx, f"{base}-cover.pdf", fh.read())
            snapshot_url = None
            if res["snapshot_path"]:  # snapshot mode='separate' -> standalone file
                with open(res["snapshot_path"], "rb") as fh:
                    snapshot_url = upload_pdf(cx, f"{base}-snapshot.pdf", fh.read())
        patch = {
            "status": "rendered", "rendered_url": url,
            "rendered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "error": None}
        if cover_url:
            patch["cover_url"] = cover_url
            patch["cover_size"] = res["cover_size"]
        if snapshot_url:
            patch["snapshot_url"] = snapshot_url
        update_brief(cx, bid, patch)
        print(f"[done]  brief {bid} -> {url} ({res['npages']}pp)"
              + (f" + cover[{res['cover_size']}] -> {cover_url}" if cover_url else "")
              + (f" + snapshot -> {snapshot_url}" if snapshot_url else ""))
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
    print(f"[worker] supported doc_types={SUPPORTED} bucket={BUCKET} "
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
    """Render CIR + snapshot + cover, merge all three, no DB. Proves the toolchain.

    Snapshot is rendered from snapshot/carmel.json (guaranteed snapshot-shaped);
    the CIR from cir/content/carmel.json. Bundled order: cover, snapshot, CIR."""
    wd = tempfile.mkdtemp()
    cir_content = json.load(open(os.path.join(HERE, "cir", "content", "carmel.json")))
    cir_pdf = render_cir(cir_content, os.path.join(wd, "cir.pdf"))

    snap_src = os.path.join(HERE, "snapshot", "carmel.json")
    snap_content = json.load(open(snap_src)) if os.path.exists(snap_src) else cir_content
    snap_pdf = render_snapshot(snap_content, os.path.join(wd, "snapshot.pdf"))

    cover = cover_engine.build_cover(
        None, {"name": "Nick Jacobi", "title": "General Manager"},
        cir_content["org"]["name"])
    cover_pdf = cover_engine.render_cover(cover, os.path.join(wd, "cover.pdf"))

    final = merge_pdfs([cover_pdf, snap_pdf, cir_pdf], os.path.join(wd, "final.pdf"))
    print(f"[selftest] {final}  ({len(PdfReader(final).pages)}pp: cover + snapshot + CIR)")
    print(final)


if __name__ == "__main__":
    main()
