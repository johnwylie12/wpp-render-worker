#!/usr/bin/env python3
"""ERA Portfolio Value Creation Assessment (PVCA) — render engine.

ONE data-driven template renders the LCS suite from params and reproduces John's
locked LCS numbers. Extends the CIR engine pattern (do NOT fork what works):
  - Jinja2 + WeasyPrint, same as cir/src/cir_engine.py
  - reuses the CIR hero library (cir/src/assets/heroes/<vertical>.png) via hero_background()
  - render with the fonts.conf parity path:
      FONTCONFIG_FILE=$PWD/cir/build/fonts.conf python3 pvca/src/pvca_engine.py pvca_reference_LCS.json /tmp/pvca_lcs.pdf

The EV Bridge (§3 of the brief) is the one genuinely new computation:
  recoverable (recurring) -> EBITDA uplift (x ebitda_conversion, default 1.0)
                          -> enterprise value (x exit_multiple).
Derived here, never trusted from params.
"""
import json, sys, os, base64
from jinja2 import Template
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
# Reuse the CIR hero photos (senior_living.png etc.) — do not duplicate assets.
CIR_HEROES = os.path.abspath(os.path.join(HERE, "..", "..", "cir", "src", "assets", "heroes"))

NAVY_GRADIENT = "linear-gradient(100deg,#002851 0%,#003A70 55%,#0a4a86 100%)"


def hero_background(portfolio):
    """Per-vertical hero photo -> CSS background-image value (base64-embedded),
    falling back to the navy gradient. Mirrors cir_engine.hero_background."""
    vert = (portfolio or {}).get("vertical")
    if vert:
        path = os.path.join(CIR_HEROES, vert + ".png")
        if os.path.isfile(path):
            uri = "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()
            overlay = ("linear-gradient(100deg, rgba(0,40,81,0.88) 0%, "
                       "rgba(0,52,100,0.45) 46%, rgba(10,74,134,0.10) 82%)")
            return overlay + ", url('" + uri + "')"
    return NAVY_GRADIENT


# ---- formatting helpers (passed into the template) ----------------------
def m(usd):
    """$X,XXX.XM — millions, one decimal (matches John's LCS display rounding)."""
    if usd is None:
        return "—"
    return "$%sM" % ("{:,.1f}".format(usd / 1_000_000.0))


def m0(usd):
    """$X,XXXM — whole millions (dense tables)."""
    if usd is None:
        return "—"
    return "$%sM" % ("{:,.0f}".format(usd / 1_000_000.0))


def pct(x):
    return "%d%%" % round(x * 100)


def pct1(x):
    return "%s%%" % ("{:.1f}".format(x * 100))


def render(content, out_pdf):
    c = content
    p = c["portfolio"]
    f = c["financials"]
    ev = c["ev_bridge"]
    seg = c.get("segmentation", {})

    # --- the EV bridge: derive, don't trust ---
    conv = ev.get("ebitda_conversion", 1.0)
    mult = ev["exit_multiple"]
    ebitda_low = f["recoverable_low_usd"] * conv
    ebitda_high = f["recoverable_high_usd"] * conv
    ev_low = ebitda_low * mult
    ev_high = ebitda_high * mult

    universe = c.get("universe", [])
    verified = [u for u in universe if u.get("basis") == "Verified"]

    ctx = dict(
        m=m, m0=m0, pct=pct, pct1=pct1,
        portfolio=p, financials=f, ev=ev,
        buyer_model=p.get("buyer_model", "centralized"),
        centralized=(p.get("buyer_model", "centralized") == "centralized"),
        conv=conv, mult=mult,
        ebitda_low=ebitda_low, ebitda_high=ebitda_high,
        ev_low=ev_low, ev_high=ev_high,
        addressable_pct=f.get("addressable_pct", 0.10),
        seg=seg,
        by_ownership=seg.get("by_ownership_class", []),
        by_geography=seg.get("by_geography", []),
        categories=c.get("category_ranges", []),
        sources=c.get("sources", []),
        validation=c.get("validation", {}),
        universe=universe, verified=verified,
        hero_bg=hero_background(p),
    )
    tpl = Template(open(os.path.join(HERE, "pvca_template.html")).read())
    HTML(string=tpl.render(**ctx)).write_pdf(out_pdf)

    # --- §8 acceptance self-check (numbers must reproduce to the dollar) ---
    acc = (c.get("_meta") or {}).get("acceptance")
    if acc:
        checks = {
            "enterprise_revenue_usd": f["enterprise_revenue_usd"],
            "addressable_indirect_usd": f["addressable_indirect_usd"],
            "recoverable_low_usd": f["recoverable_low_usd"],
            "recoverable_high_usd": f["recoverable_high_usd"],
            "ev_created_low_usd": round(ev_low),
            "ev_created_high_usd": round(ev_high),
        }
        ok = True
        for k, got in checks.items():
            want = acc.get(k)
            hit = want is not None and abs(got - want) <= 1
            ok = ok and hit
            print(("  OK  " if hit else " FAIL ") + "%-26s got=%s want=%s" % (k, got, want))
        print("ACCEPTANCE: " + ("PASS" if ok else "FAIL"))
        if not ok:
            raise SystemExit("Acceptance numbers do not reproduce — fix before deploy.")
    return out_pdf


if __name__ == "__main__":
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/pvca_lcs.pdf"
    render(json.load(open(src)), out)
    print("rendered", out)
