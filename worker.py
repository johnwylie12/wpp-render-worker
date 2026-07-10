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
sys.path.insert(0, os.path.join(HERE, "case_study"))
sys.path.insert(0, os.path.join(HERE, "closing"))
sys.path.insert(0, os.path.join(HERE, "note_card"))
import cover_engine       # noqa: E402
import snapshot_engine    # noqa: E402
import cover_page_engine  # noqa: E402
import benchmark_engine   # noqa: E402
import case_study_engine  # noqa: E402
import closing_engine     # noqa: E402
import note_card_engine   # noqa: E402

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
CASE_STUDY_DOC_TYPES = [s.strip() for s in os.environ.get("CASE_STUDY_DOC_TYPES",
                                                   "case_study").split(",") if s.strip()]
CLOSING_DOC_TYPES = [s.strip() for s in os.environ.get("CLOSING_DOC_TYPES",
                                                   "closing_page").split(",") if s.strip()]
PACKAGE_DOC_TYPES = [s.strip() for s in os.environ.get("PACKAGE_DOC_TYPES",
                                                   "package").split(",") if s.strip()]
NOTE_CARD_DOC_TYPES = [s.strip() for s in os.environ.get("NOTE_CARD_DOC_TYPES", "note_card").split(",") if s.strip()]
WAVE_DOC_TYPES = [s.strip() for s in os.environ.get("WAVE_DOC_TYPES", "wave").split(",") if s.strip()]
# Claim CIR + snapshot + cover_page + benchmark + case_study + closing + package by default - no Railway env edit required.
CLAIM_DOC_TYPES = SUPPORTED + [s for s in (SNAPSHOT_DOC_TYPES + COVER_PAGE_DOC_TYPES + BENCHMARK_DOC_TYPES + CASE_STUDY_DOC_TYPES + CLOSING_DOC_TYPES + PACKAGE_DOC_TYPES) if s not in SUPPORTED] + [s for s in (NOTE_CARD_DOC_TYPES + WAVE_DOC_TYPES) if s not in SUPPORTED]
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


def render_cir(content, out_pdf, hero=True):
    # hero=False suppresses the page-1 photo band -> clean navy header. This is
    # the "packaged" copy that ships behind a cover; the standalone copy keeps
    # the per-vertical hero. One content payload, rendered two ways.
    if not hero:
        content = {**content, "suppress_hero": True}
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


def render_wave_index(rows, mail_date, out_pdf):
    """Collation sheet for a wave: the print order. Piece #N is the same account
    across the cards, cover letters, packages, and labels."""
    from weasyprint import HTML as _HTML
    trs = "".join(
        '<tr><td class="n">{}</td><td>{}</td><td>{}</td></tr>'.format(
            r.get("seq"), (r.get("name") or ""), (r.get("recipient") or ""))
        for r in rows)
    md = '<div class="md">Mail date: {}</div>'.format(mail_date) if mail_date else ""
    html = (
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        '@page{size:8.5in 11in;margin:0.8in 0.9in;}'
        'body{font-family:Arial,Helvetica,sans-serif;color:#1a1a1a;}'
        'h1{color:#003A70;font-size:20pt;margin:0 0 2pt;}'
        '.rule{height:3px;width:56px;background:#FF9C00;margin:8pt 0 14pt;}'
        '.md,.count{color:#555;font-size:10.5pt;margin-bottom:2pt;}'
        '.count{margin-bottom:14pt;}'
        'table{width:100%;border-collapse:collapse;font-size:10.5pt;}'
        'th{text-align:left;color:#003A70;border-bottom:2px solid #003A70;padding:6pt 8pt;}'
        'td{padding:6pt 8pt;border-bottom:0.5px solid #ccc;}'
        'td.n{width:36pt;font-weight:bold;color:#003A70;}'
        '.note{margin-top:16pt;color:#555;font-size:9.5pt;line-height:1.4;}'
        '</style></head><body>'
        '<h1>Mail wave - collation sheet</h1><div class="rule"></div>'
        + md + '<div class="count">{} accounts, in print order.</div>'.format(len(rows))
        + '<table><tr><th>#</th><th>Account</th><th>Ship to</th></tr>' + trs + '</table>'
        + '<div class="note">Print each stack in this order. Piece #N is the same '
          'account across the cards, cover letters, packages, and labels - match by '
          'number when you assemble each envelope.</div>'
        '</body></html>')
    _HTML(string=html).write_pdf(out_pdf)
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


def _study_by_slug(slug):
    for s in case_study_engine.STUDIES:
        if s.get("slug") == slug:
            return s
    return None


# The six bound pieces of the Executive Opening Package, in print order. The two
# loose pieces (5x7 note, cover letter) are NOT here - the note is produced
# outside the worker, the cover letter is a separate print handled below.
BOUND_PIECES = ["cover", "snapshot", "cir", "benchmark", "case_study", "closing"]


def _render_piece(piece, content, params, workdir):
    """Render ONE bound piece to a PDF path (rendered in-process; the worker is
    single-threaded, so the package build renders its pieces inline rather than
    enqueuing child briefs and deadlocking on itself)."""
    org = content.get("org") or {}
    if piece == "cover":
        if not org.get("name"):
            raise RenderError("package: cover requires content.org.name")
        cp = params.get("cover_page") or {}
        out = os.path.join(workdir, "01_cover.pdf")
        cover_page_engine.render(org, out, title=cp.get("title"), subtitle=cp.get("subtitle"),
                                 statement=cp.get("statement"), date_str=cp.get("date"),
                                 doc_type=cp.get("for_doc_type", "package"))
        return out
    if piece == "snapshot":
        opp = content.get("opportunity") or {}
        if opp.get("low_usd") is None or opp.get("high_usd") is None:
            raise RenderError("package: snapshot requires content.opportunity low_usd/high_usd")
        out = os.path.join(workdir, "02_snapshot.pdf")
        snapshot_engine.render(content, out)
        return out
    if piece == "cir":
        out = os.path.join(workdir, "03_cir.pdf")
        render_cir(content, out, hero=False)  # packaged copy: no photo band
        return out
    if piece == "benchmark":
        sector = (params.get("benchmark") or {}).get("sector")
        if not sector:
            raise RenderError("package: benchmark requires params.benchmark.sector")
        out = os.path.join(workdir, "04_benchmark.pdf")
        try:
            benchmark_engine.render(sector, out)
        except ValueError as e:
            raise RenderError(f"package benchmark: {e}")
        return out
    if piece == "case_study":
        cs = params.get("case_study") or {}
        slug = cs.get("slug")
        if not slug:
            vertical = cs.get("vertical") or org.get("vertical")
            if not vertical:
                raise RenderError("package: case_study requires a slug or vertical "
                                  "(params.case_study.slug/vertical or content.org.vertical)")
            matches = case_study_engine.studies_for(vertical)
            if not matches:
                raise RenderError(f"package: no case study supports vertical '{vertical}'")
            slug = matches[0]
        study = _study_by_slug(slug)
        if not study:
            raise RenderError(f"package: unknown case study slug '{slug}'")
        out = os.path.join(workdir, "05_case_study.pdf")
        case_study_engine.render_one(study, out)
        return out
    if piece == "closing":
        out = os.path.join(workdir, "06_closing.pdf")
        closing_engine.render(params.get("closing") or {}, out)
        return out
    raise RenderError(f"package: unknown piece '{piece}'")


def stitch_pdfs(paths, out_pdf):
    """Bind PDFs in order into one file."""
    w = PdfWriter()
    for p in paths:
        for page in PdfReader(p).pages:
            w.add_page(page)
    with open(out_pdf, "wb") as fh:
        w.write(fh)
    return out_pdf


def build_pdf(cx, brief, workdir):
    """Render the brief; return (final_path, page_count, cover_path|None, cover_size|None, kind).

    kind is 'cir' or 'snapshot' and selects the storage prefix. cover_path is
    non-None only for CIR mode='separate' (a second, standalone file)."""
    params = brief.get("params") or {}

    # ---- case study: standalone one-page customer story. Pick the study by
    # explicit slug, else the best match for the account's vertical. Reads org
    # from params.content directly - no full CIR content required (so this runs
    # BEFORE extract_cir_content, which would otherwise reject it).
    if brief.get("doc_type") in CASE_STUDY_DOC_TYPES:
        cs = params.get("case_study") or {}
        org = (params.get("content") or {}).get("org") or {}
        slug = cs.get("slug")
        if not slug:
            vertical = cs.get("vertical") or org.get("vertical")
            if not vertical:
                raise RenderError("case_study requires params.case_study.slug, or a "
                                  "vertical via params.case_study.vertical or "
                                  "params.content.org.vertical")
            matches = case_study_engine.studies_for(vertical)
            if not matches:
                raise RenderError(f"no case study supports vertical '{vertical}'")
            slug = matches[0]
        study = _study_by_slug(slug)
        if not study:
            raise RenderError(f"unknown case study slug '{slug}'")
        cs_pdf = os.path.join(workdir, "case_study.pdf")
        case_study_engine.render_one(study, cs_pdf)
        return cs_pdf, len(PdfReader(cs_pdf).pages), None, None, "case_study"

    # ---- closing "Before We Meet" page: near-static. params.closing carries
    # optional overrides (footer_left_b vertical label, person, headshot, etc.).
    if brief.get("doc_type") in CLOSING_DOC_TYPES:
        cl = params.get("closing") or {}
        close_pdf = os.path.join(workdir, "closing.pdf")
        closing_engine.render(cl, close_pdf)
        return close_pdf, len(PdfReader(close_pdf).pages), None, None, "closing"

    # ---- note card: standalone 5x7 intro card (loose piece).
    if brief.get("doc_type") in NOTE_CARD_DOC_TYPES:
        nc = params.get("note_card") or {}
        card_pdf = os.path.join(workdir, "note_card.pdf")
        note_card_engine.render(nc, card_pdf)
        return card_pdf, len(PdfReader(card_pdf).pages), None, None, "note_card"

    # ---- wave: batch of accounts -> combined, sequence-ordered PDFs (cards,
    # letters, packages) + a collation index. Reuses the package assembler per
    # account; uploads all four and records URLs in content_briefs.wave_urls.
    if brief.get("doc_type") in WAVE_DOC_TYPES:
        accts = params.get("accounts") or []
        if not accts:
            raise RenderError("wave requires a non-empty params.accounts list")
        pkg_paths, card_paths, index_rows = [], [], []
        for i, a in enumerate(accts, 1):
            seq = a.get("seq") or i
            pp = a.get("package") or {}
            c = pp.get("content") or {}
            awd = os.path.join(workdir, "a{}".format(seq))
            os.makedirs(awd, exist_ok=True)
            piece_paths = [_render_piece(pc, c, pp, awd) for pc in BOUND_PIECES]
            name = a.get("name") or (c.get("org") or {}).get("name") or "Account {}".format(seq)
            recip = ""
            lb = pp.get("cover_letter")
            if lb:
                company = (c.get("org") or {}).get("name") or name
                cover = cover_engine.build_cover(lb, lb.get("recipient"), company)
                lp = os.path.join(awd, "letter.pdf")
                cover_engine.render_cover(cover, lp, page_size="letter")
                piece_paths = [lp] + piece_paths   # bind letter as page 1
                recip = (lb.get("recipient") or {}).get("name") or ""
            bound = os.path.join(awd, "pkg.pdf")
            stitch_pdfs(piece_paths, bound)
            pkg_paths.append(bound)
            nc = a.get("note_card") or {}
            cardp = os.path.join(awd, "card.pdf")
            note_card_engine.render(nc, cardp)
            card_paths.append(cardp)
            index_rows.append({"seq": seq, "name": name,
                               "recipient": recip or nc.get("recipient_first") or ""})
        wave_cards = os.path.join(workdir, "wave_cards.pdf"); stitch_pdfs(card_paths, wave_cards)
        wave_pkgs = os.path.join(workdir, "wave_packages.pdf"); stitch_pdfs(pkg_paths, wave_pkgs)
        wave_index = os.path.join(workdir, "wave_index.pdf")
        render_wave_index(index_rows, params.get("mail_date"), wave_index)
        bid = brief["id"]
        prefix = "wave/{}".format(bid)
        urls = {"count": len(accts)}
        for label, path in [("index", wave_index), ("cards", wave_cards),
                            ("packages", wave_pkgs)]:
            if path and os.path.exists(path):
                with open(path, "rb") as fh:
                    urls[label] = upload_pdf(cx, "{}/wave_{}.pdf".format(prefix, label), fh.read())
        update_brief(cx, bid, {"wave_urls": urls})
        return wave_index, len(PdfReader(wave_index).pages), None, None, "wave"

    content = extract_cir_content(params)

    # ---- package: assemble the Executive Opening Package (EOP). Render the six
    # bound pieces in-process (single-threaded worker - no child briefs) and stitch
    # them in print order into one PDF. The cover letter, if requested, renders as a
    # separate LOOSE print (returned as cover_path, uploaded alongside). The 5x7
    # note stays outside the worker.
    if brief.get("doc_type") in PACKAGE_DOC_TYPES:
        piece_paths = [_render_piece(pc, content, params, workdir) for pc in BOUND_PIECES]
        letter_block = params.get("cover_letter")
        if letter_block:
            recipient = fetch_contact(cx, brief.get("contact_id"))
            company = (content.get("org") or {}).get("name") or \
                      fetch_account_name(cx, brief.get("account_id"))
            if not (recipient and recipient.get("name")) and not letter_block.get("recipient"):
                raise RenderError("package cover_letter requested but no recipient resolved "
                                  "(set contact_id or params.cover_letter.recipient)")
            cover = cover_engine.build_cover(letter_block, recipient, company)
            letter_path = os.path.join(workdir, "cover_letter.pdf")
            cover_engine.render_cover(cover, letter_path, page_size="letter")
            piece_paths = [letter_path] + piece_paths   # bind letter as page 1 (plain-paper package)
        bound = os.path.join(workdir, "eop_bound.pdf")
        stitch_pdfs(piece_paths, bound)
        return bound, len(PdfReader(bound).pages), None, None, "package"

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
    mode, size, letter_block = cover_config(brief, params)
    # Hero rule: a packaged CIR (a cover ships in front, bundled or separate)
    # suppresses the photo band for a clean navy header; a standalone CIR keeps
    # the per-vertical hero. Explicit params.cir.hero (bool) overrides the rule.
    cir_cfg = params.get("cir") or {}
    hero_on = cir_cfg.get("hero")
    if hero_on is None:
        hero_on = (mode == "none")
    render_cir(content, cir_pdf, hero=bool(hero_on))
    final = cir_pdf
    cover_path = None
    cover_size_used = None
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
