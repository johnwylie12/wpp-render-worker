#!/usr/bin/env python3
"""ERA Cost Intelligence Report — render engine.
Frozen shell = cir_template.html. Variable evidence = content/<prospect>.json.
Preview: WeasyPrint. Production: headless Chromium (same HTML)."""
import json, sys, os, re, base64
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- icon library (stroke glyphs; recolored per surface) ----------------
_GLYPH = {
  "freight":   '<path d="M2 6h11v8H2z"/><path d="M13 9h4l3 3v2h-7z"/><circle cx="6" cy="16" r="1.6"/><circle cx="16" cy="16" r="1.6"/>',
  "contracts": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 12h6M9 15h6M9 9h2"/>',
  "operating": '<path d="M6 8h12l-1 12H7z"/><path d="M9 8a3 3 0 0 1 6 0"/>',
  "disclosure":'<path d="M4 20V10M10 20V5M16 20v-8M22 20H2"/>',
  "costbase":  '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M14.5 9.2c0-1.2-1.1-1.9-2.5-1.9s-2.5.8-2.5 2 1.1 1.7 2.5 1.9 2.6.8 2.6 2.1-1.2 2-2.6 2-2.6-.8-2.6-2"/>',
  "professional":'<rect x="3" y="8" width="18" height="11" rx="1.5"/><path d="M9 8V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
  "office":    '<path d="M5 19l1-4L16 5l3 3L9 18z"/><path d="M14 7l3 3"/>',
  "maintenance":'<path d="M14 6a4 4 0 0 0-5 5l-6 6 2 2 6-6a4 4 0 0 0 5-5l-2 2-2-2 2-2z"/>',
  "utilities": '<path d="M13 2 4 14h6l-1 8 9-12h-6z"/>',
  "insurance": '<path d="M12 3l8 3v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6z"/><path d="M9 12l2 2 4-4"/>',
  "packaging": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5 12 12l8-4.5M12 12v9"/>',
  "waste":     '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/><path d="M10 11v6M14 11v6"/>',
  "clinical":  '<rect x="4" y="6" width="16" height="14" rx="2"/><path d="M12 9v8M8 13h8M9 6V4h6v2"/>',
}
def icon_svg(slug, color):
    g = _GLYPH.get(slug, _GLYPH["contracts"])
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="{color}" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{g}</svg>')

# ---- helpers ------------------------------------------------------------
def balance(text):
    """Split a caption into two visually balanced lines at the nearest
    word boundary to the midpoint (no orphan tail)."""
    words = text.split()
    if len(words) < 4:
        return text, ""
    total = sum(len(w) for w in words) + len(words) - 1
    best_i, best_diff = 1, 10**9
    run = 0
    for i in range(1, len(words)):
        run += len(words[i-1]) + 1
        diff = abs(run - total/2)
        if diff < best_diff:
            best_diff, best_i = diff, i
    return " ".join(words[:best_i]), " ".join(words[best_i:])

def usd_k(n):
    if n >= 1_000_000:
        v = n/1_000_000
        return f"${v:.2f}M".replace(".00M","M").rstrip("0").rstrip(".")+("" if "M" in f"${v:.2f}M" else "")
    return f"${int(round(n/1000))}K"

def est_display(c):
    if c.get("est_display"):
        return c["est_display"]
    return f"{usd_k(c['est_low'])}–{usd_k(c['est_high'])}"

DEFAULT_STEPS = [
    {"n":1,"title":"20-minute call","body":"We walk your largest categories and confirm what's worth a closer look."},
    {"n":2,"title":"30-day baseline","body":"No cost. We replace these estimates with your actual contract data."},
    {"n":3,"title":"Options report","body":"Category-by-category findings. You decide what, if anything, to pursue."},
]
DEFAULT_AGG = {"clients":916,"spend":"$2.25B","projects":"6,420","with_savings":"2,656","wtd_avg":"27.5%"}


NAVY_GRADIENT = "linear-gradient(100deg,#002851 0%,#003A70 55%,#0a4a86 100%)"
def hero_background(content):
    """Resolve the per-vertical hero photo and return a CSS background-image value.
    Prefers content.assets.hero, else assets/heroes/<org.vertical>.png. Falls back
    to the navy gradient (master look) when no photo exists (e.g. manufacturing)."""
    # Explicit suppression (the "packaged" copy that ships behind a cover) ->
    # clean navy header, skipping the per-vertical photo fallback.
    if content.get("suppress_hero"):
        return NAVY_GRADIENT
    rel  = (content.get("assets") or {}).get("hero")
    vert = (content.get("org") or {}).get("vertical")
    candidates = []
    if rel:  candidates.append(os.path.join(HERE, "assets", rel))
    if vert: candidates.append(os.path.join(HERE, "assets", "heroes", vert + ".png"))
    for path in candidates:
        if os.path.isfile(path):
            uri = "data:image/png;base64," + base64.b64encode(open(path,"rb").read()).decode()
            overlay = ("linear-gradient(100deg, rgba(0,40,81,0.85) 0%, "
                       "rgba(0,52,100,0.30) 42%, rgba(10,74,134,0.00) 78%)")
            return overlay + ", url('" + uri + "')"
    return NAVY_GRADIENT

def render(content, out_pdf):
    c = content
    cats = c["categories"]
    n = len(cats)
    row_h = max(88, min(138, round(732/n)))           # clamp(732/N, 88, 138)
    for cat in cats:
        cat["est_display"] = est_display(cat)

    obs = c.get("observations", [])
    half = (len(obs)+1)//2
    cap1, cap2 = balance(c["opportunity"]["basis_note"])

    agg = {**DEFAULT_AGG, **c.get("aggregate", {})}
    so = c.get("signoff", {"name":"John Wylie","title":"Senior Consultant","email":"jwylie@eragroup.com","phone":"703.244.9868"})
    src = c.get("source", {})
    src_line = (f"Source: {src['filing']} {src.get('basis','')}".strip()
                if src.get("filing") and c.get("org",{}).get("has_990")
                else f"{src.get('filing','')} {src.get('basis','')}".strip())

    ctx = dict(
        org=c["org"], thesis=c["thesis"],
        intro_paras=[p for p in c["intro_md"].split("\n\n") if p.strip()],
        reasons=c["reasons"], opportunity=c["opportunity"],
        caption_line1=cap1, caption_line2=cap2,
        obs_intro=c.get("obs_intro","Four things stand out from the public financials:"),
        obs_left=obs[:half], obs_right=obs[half:],
        cat_intro=c.get("cat_intro","The largest indirect opportunities visible in public filings — not the full review. ERA benchmarks 50-plus indirect categories; the baseline covers every one that applies. Ordered by size."),
        categories=cats, row_h=row_h,
        method_intro=c.get("method_intro","A transparent, outside-in estimate built from three inputs — and a candid account of what an external view can and cannot establish."),
        methodology=c["methodology"], aggregate=agg, honesty=c["honesty"],
        next_steps=c.get("next_steps", DEFAULT_STEPS),
        reassurance_tail=c.get("reassurance","No savings, no fee. No upfront cost. Nothing changes without your approval.").replace("No savings, no fee. ","").replace(". 90%",".<br>90%",1),
        signoff=so, source_line=src_line,
        hero_bg=hero_background(c),
        icons={k:icon_svg(k,"#FFFFFF") for k in _GLYPH},
        table_icons={k:icon_svg(k,"#FFFFFF") for k in _GLYPH},
    )
    tpl = Template(open(os.path.join(HERE,"cir_template.html")).read())
    HTML(string=tpl.render(**ctx)).write_pdf(out_pdf)
    return out_pdf

if __name__ == "__main__":
    src = sys.argv[1]; out = sys.argv[2]
    render(json.load(open(src)), out)
    print("rendered", out)
