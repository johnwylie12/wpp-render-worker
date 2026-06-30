# WPP Collateral Render Worker

The back half of the **Create collateral** pipeline. The app enqueues a
`content_briefs` row (`status='queued'`) via the `enqueue_brief` RPC; this
service renders the PDF and writes `rendered_url` + `status` back. Until this
worker runs, briefs sit `queued` forever (which is exactly what was happening).

## What it does
1. **Claims** the oldest `queued` brief of a supported `doc_type` via the
   `claim_next_brief(p_doc_types)` RPC (`FOR UPDATE SKIP LOCKED` — multi-worker
   safe). Flips it to `rendering`, stamps `claimed_at`, bumps `attempts`.
2. **Renders the CIR** ("Cost Intelligence Report", doc_type `vertical_deepdive`)
   with the **locked** engine in `cir/` — design frozen, never edited here.
3. **Cover letter** — when the brief's `cover_letter = true`, renders a 1-page
   ERA letter (separate template in `cover/`) addressed to the brief's
   `contact_id`, and merges it in **front** of the CIR with pypdf.
4. **Uploads** the final PDF to Supabase Storage bucket `collateral` at
   `cir/<account_id>/<brief_id>-<slug>.pdf` and writes the public URL to
   `content_briefs.rendered_url`, `status='rendered'`, `rendered_at=now()`.
   On failure: `status='failed'`, `error=<message>`.

Only doc_types in `SUPPORTED_DOC_TYPES` are claimed; everything else is left
untouched in the queue (so unbuilt types never get stuck in a fail loop).

## Deploy (Railway — recommended, ~$5/mo)
1. Push this folder to a repo (or a subfolder).
2. Railway → **New Project → Deploy from Repo** (it auto-detects the Dockerfile).
3. **Variables**:
   - `SUPABASE_URL` = `https://ouzrrkskrfcvtnmhlycd.supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY` = *(service-role key — bypasses RLS; never ship to the browser)*
4. Deploy. It polls every 60s. Logs print `[claim] / [done] / [fail]` per brief.

Near-$0 alternative: Fly.io scale-to-zero machine + a Supabase DB webhook on
`content_briefs` insert that wakes it. Same image.

Already provisioned in Supabase (done via MCP, not by this service):
- `claim_next_brief(text[])` RPC
- public Storage bucket `collateral`
- `content_briefs.contact_id` + `content_briefs.cover_letter` columns

## Params contract (what the enqueue must put in `content_briefs.params`)
The CIR engine is driven by a **carmel.json-shaped** content object. The worker
accepts either:
- `params.content = { org, thesis, intro_md, reasons, opportunity, observations,
  categories[], methodology, honesty, reassurance, signoff, source, aggregate,
  assets? }`  *(preferred)*, **or**
- a `params` root that is itself carmel-shaped (has `org` + `categories`).

Hero photo auto-loads from `org.vertical` (`private_club`, `wholesale_distribution`,
`business_services`, `construction`, `senior_living`, `healthcare`;
`manufacturing` → navy gradient fallback). See `cir/content/carmel.json` for a
complete reference payload.

Cover letter (optional), set `content_briefs.cover_letter = true` and either a
`contact_id` (recipient resolved from `contacts`) or
`params.cover_letter = { recipient{name,title,company}, salutation?, body[]?, ps? }`.
Missing pieces fall back to the ERA canon signoff and a default body.

> NOTE: the in-app enqueue currently only wires `exec_brief`. Wiring the CIR
> (`vertical_deepdive`) to emit carmel-shaped `params.content` + the cover-letter
> toggle/person-picker is the next step.

## Local testing
```bash
pip install -r requirements.txt
export FONTCONFIG_FILE=$PWD/cir/build/fonts.conf

python worker.py --selftest   # render carmel.json + sample cover, merge -> /tmp (no DB)

export SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=...
python worker.py --once       # claim+render a single real brief, then exit
python worker.py              # poll loop
```

## Layout
```
worker.py              claim → render → merge → upload → update; --once / --selftest
requirements.txt       pinned (weasyprint 69.0 — matches the locked render)
Dockerfile             python:3.12-slim + Pango/Cairo/gdk-pixbuf + Liberation
cover/cover_letter.html  ERA cover-letter shell (NOT the CIR)
cover/cover_engine.py    cover renderer + ERA canon signoff
cover/logo_b64.txt       ERA logo (letterhead)
cir/                   the LOCKED CIR engine — frozen, do not edit
  src/cir_engine.py, src/cir_template.html, src/assets/heroes/*.png
  build/fonts.conf, content/carmel.json (reference payload)
```
