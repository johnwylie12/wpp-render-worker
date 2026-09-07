"""The five visuals for "The Only Comparison That Matters".

Every chart carries a CONCLUSION as its title, truthful scale and denominators,
direct labels, and an annotation saying why the pattern matters. Banned by the
brief and absent here: dashboard cards, generic icons, pie charts, gauges, 3D,
fake precision, unexplained bubbles, rainbow palettes, tiny legends, and boxes
containing paragraphs.

Type floor is 9.5pt (this brief), enforced in _t rather than trusted.
Every colour is a brand_tokens row. Widths are MEASURED against the real font.
"""
import math
import os

import pymupdf

# brand_tokens, core + extended only
NAVY     = "#003A70"   # Daybreak Blue — authority
SUNRISE  = "#FF9C00"   # look here, once per page
MIST     = "#F2F5F8"   # evidence ground
DEEP     = "#E4EBF3"   # nested panel
CREAM    = "#FEF4E2"   # decision / commercial consequence
CREAM_ED = "#F0D8A6"
INK      = "#1B2A41"   # body
SLATE    = "#5A6577"   # secondary the CFO must still read
COOL     = "#97999B"   # metadata
HAIR     = "#D7DFE9"   # rules
FONT     = "Trebuchet MS, Arial, sans-serif"

FLOOR = 9.5

_F = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "fonts")
_REG = pymupdf.Font(fontfile=os.path.join(_F, "Trebuchet MS.ttf"))
_BLD = pymupdf.Font(fontfile=os.path.join(_F, "Trebuchet MS Bold.ttf"))


def _w(t, size, bold=False, ls=0.0):
    f = _BLD if bold else _REG
    return f.text_length(t, size) + ls * size * max(0, len(t) - 1)


def _svg(w, h, body):
    return (f'<svg class="fig" viewBox="0 0 {w} {h}" width="100%" '
            f'style="height:auto;display:block;overflow:visible" '
            f'xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">{body}</svg>')


def _t(x, y, s, size=FLOOR, fill=INK, weight="normal", anchor="start", ls=None):
    if size < FLOOR:
        raise ValueError(f"{size}pt is below the {FLOOR}pt floor: {s[:40]!r}")
    extra = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{extra}>{s}</text>')


def _wrap(text, size, width, bold=False):
    out, line = [], ""
    for word in text.split():
        t = (line + " " + word).strip()
        if _w(t, size, bold) > width and line:
            out.append(line); line = word
        else:
            line = t
    if line:
        out.append(line)
    return out


def _money(v):
    return f"${v/1e6:,.2f}M" if v >= 1e6 else f"${v/1e3:,.0f}K"


def _place(boxes, cand):
    """First candidate rectangle that hits nothing already placed."""
    for box in cand:
        if not any(box[0] < q[1] and q[0] < box[1] and box[2] < q[3] and q[2] < box[3]
                   for q in boxes):
            return box
    return cand[-1]


# ── V1 ──────────────────────────────────────────────────────────────────────
def affiliate_beeswarm(rows, subject_id, median, q1, q3, w=520):
    """40 affiliates on one axis. Theirs is second from the top of its own
    peer set, and the peer median sits where the all-nonprofit median sits."""
    pad_l, pad_r = 4, 4
    x0, x1 = pad_l, w - pad_r
    top, band_h = 58, 92
    h = top + band_h + 52
    hi = 21.0
    px = lambda v: x0 + v / hi * (x1 - x0)

    b = ""
    # Q1-Q3 band first, so every dot sits on top of it
    b += (f'<rect x="{px(q1):.1f}" y="{top}" width="{px(q3)-px(q1):.1f}" '
          f'height="{band_h}" fill="{MIST}"/>')
    b += _t(px(q3) + 6, top + 12, f"middle half, {q1:.2f}–{q3:.2f}%", FLOOR, SLATE)
    b += (f'<path d="M{px(median):.1f} {top-8} V{top+band_h+6}" stroke="{NAVY}" '
          f'stroke-width="1.6"/>')
    b += _t(px(median), top - 13, f"AFFILIATE MEDIAN {median:.2f}%", FLOOR, NAVY,
            "bold", "middle", ls="0.05em")

    # deterministic vertical placement: collision-free, no random jitter
    placed, subject = [], None
    for r in sorted(rows, key=lambda r: r["pct"]):
        cx = px(r["pct"])
        cy, step = top + band_h / 2, 0
        while any(abs(cx - qx) < 9 and abs(cy - qy) < 9 for qx, qy in placed):
            step += 1
            cy = top + band_h / 2 + (9 if step % 2 else -9) * ((step + 1) // 2)
        placed.append((cx, cy))
        if r["account_id"] == subject_id:
            subject = (cx, cy, r)
        else:
            b += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4" fill="{COOL}"/>'
    sx, sy, srow = subject
    b += f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="8" fill="{SUNRISE}"/>'

    for v in (0, 5, 10, 15, 20):
        b += _t(px(v), top + band_h + 20, f"{v}%", FLOOR, COOL, anchor="middle")
    b += (f'<path d="M{x0} {top+band_h+6} H{x1}" stroke="{HAIR}" stroke-width="1"/>')

    b += _t(sx, sy - 14, "GOODWILL SOUTH FLORIDA", FLOOR, NAVY, "bold", "end", ls="0.05em")
    b += _t(sx, sy - 2, f"{srow['pct']:.2f}%", 13, NAVY, "bold", "end")
    top_other = max((r for r in rows if r["account_id"] != subject_id),
                    key=lambda r: r["pct"])
    # anchored to the RIGHT EDGE, not centred on the dot: centred, the text ran
    # 300pt past the end of the chart.
    b += _t(w, top - 30, f"{top_other['short']} is the only affiliate above them",
            FLOOR, SLATE, anchor="end")
    b += _t(w, top - 18, f"{top_other['pct']:.2f}%  ·  ${top_other['rev']/1e6:.1f}M revenue",
            FLOOR, COOL, anchor="end")
    b += _t(0, h - 14, "OPERATING SUPPLY AS A SHARE OF TOTAL REVENUE  ·  40 GOODWILL "
                       "AFFILIATES THAT BREAK OUT THE LINE", FLOOR, SLATE, "bold", ls="0.05em")
    return _svg(w, h, b)


# ── V2 ──────────────────────────────────────────────────────────────────────
def size_and_state(rows, subject_id, label_ids, w=520):
    """Revenue against the same ratio. Neither scale nor state explains it."""
    pad_l, pad_b, pad_t, pad_r = 46, 44, 30, 12
    h = 300
    x0, x1, y0, y1 = pad_l, w - pad_r, h - pad_b, pad_t
    lo = math.log10(min(r["rev"] for r in rows) * 0.8)
    hi = math.log10(max(r["rev"] for r in rows) * 1.25)
    px = lambda v: x0 + (math.log10(v) - lo) / (hi - lo) * (x1 - x0)
    ymax = max(r["pct"] for r in rows) * 1.16
    py = lambda v: y0 - v / ymax * (y0 - y1)

    b = ""
    for gv in (10e6, 25e6, 50e6, 100e6, 200e6):
        if lo <= math.log10(gv) <= hi:
            gx = px(gv)
            b += f'<path d="M{gx:.1f} {y1} V{y0}" stroke="{HAIR}" stroke-width="1"/>'
            b += _t(gx, y0 + 16, f"${gv/1e6:.0f}M", FLOOR, COOL, anchor="middle")
    for gv in (0, 5, 10, 15, 20):
        gy = py(gv)
        b += f'<path d="M{x0} {gy:.1f} H{x1}" stroke="{HAIR}" stroke-width="1"/>'
        b += _t(x0 - 7, gy + 3.4, f"{gv}%", FLOOR, COOL, anchor="end")
    b += _t(x0, h - 8, "TOTAL REVENUE  ·  LOG SCALE", FLOOR, SLATE, "bold", ls="0.06em")
    b += _t(0, y1 - 13, "OPERATING SUPPLY AS A SHARE OF REVENUE", FLOOR, SLATE, "bold", ls="0.06em")

    boxes = [(px(r["rev"]) - 5, px(r["rev"]) + 5, py(r["pct"]) - 5, py(r["pct"]) + 5)
             for r in rows]
    for r in rows:
        cx, cy = px(r["rev"]), py(r["pct"])
        if r["account_id"] == subject_id:
            continue
        col = NAVY if r["state"] == "FL" else COOL
        b += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.4" fill="{col}"/>'
    sr = next(r for r in rows if r["account_id"] == subject_id)
    b += (f'<circle cx="{px(sr["rev"]):.1f}" cy="{py(sr["pct"]):.1f}" r="8" fill="{SUNRISE}"/>')

    for aid in label_ids:
        r = next(x for x in rows if x["account_id"] == aid)
        cx, cy = px(r["rev"]), py(r["pct"])
        nm, sub = r["short"], f"${r['rev']/1e6:.1f}M · {r['pct']:.2f}%"
        tw = max(_w(nm, FLOOR, True), _w(sub, FLOOR))
        # the box is TWO LINES tall. It used to be sixteen points, so three
        # labels in the same corner all "fitted" and printed on top of each other.
        # A WIDE ladder. Three of the five labelled affiliates sit in the same
        # corner of the plot, so eight candidate slots all collided and the code
        # fell through to its last resort — printing them on top of each other.
        cands = []
        offsets = [(13, -4), (-13, -4), (13, 20), (-13, 20), (13, -26), (-13, -26)]
        for d in (34, 48, 62, 76, 90):
            offsets += [(13, -d), (-13, -d), (13, d), (-13, d)]
        for dx, dy in offsets:
            xl = cx + dx if dx > 0 else cx + dx - tw
            if xl < 0 or xl + tw > w:
                continue
            t0 = cy + dy - 12
            if t0 < y1 - 18 or t0 + 26 > y0 + 16:
                continue
            cands.append((xl - 3, xl + tw + 3, t0, t0 + 26))
        if not cands:
            xl = min(max(0, cx + 13), w - tw)
            cands = [(xl - 3, xl + tw + 3, cy - 12, cy + 14)]
        box = _place(boxes, cands)
        boxes.append(box)
        if abs(box[2] + 13 - cy) > 16:      # only lead when the label has moved
            b += (f'<path d="M{cx:.1f} {cy:.1f} L{box[0]+3:.1f} {box[2]+9:.1f}" '
                  f'stroke="{HAIR}" stroke-width="1"/>')
        b += _t(box[0] + 3, box[2] + 9, nm, FLOOR, INK, "bold")
        b += _t(box[0] + 3, box[2] + 21, sub, FLOOR, SLATE)
    b += _t(x1, y1 - 13, "FLORIDA AFFILIATES IN NAVY", FLOOR, NAVY, "bold", "end", ls="0.06em")
    return _svg(w, h, b)


# ── V3 ──────────────────────────────────────────────────────────────────────
def vendor_dumbbell(vendors, w=520):
    """What comparable organisations disclosed paying the same named supplier.
    Not a benchmark — a set of filed figures. The uncertainty is ON the chart
    because the brief requires it there and not in a footnote."""
    lab = 150
    x0, x1 = lab + 14, w - 118
    rowh, top = 60, 46
    h = top + rowh * len(vendors) + 62
    hi = max(max(v["hi"], v["theirs"]) for v in vendors) * 1.08
    px = lambda v: x0 + v / hi * (x1 - x0)

    b = _t(0, 13, "WHAT OTHER ORGANISATIONS DISCLOSED PAYING THE SAME NAMED SUPPLIER",
           FLOOR, SLATE, "bold", ls="0.05em")
    for gv in (0, 500e3, 1e6):   # fewer ticks: six of them touched at 9.5pt
        if gv <= hi:
            gx = px(gv)
            b += f'<path d="M{gx:.1f} {top-10} V{h-46}" stroke="{HAIR}" stroke-width="1"/>'
            b += _t(gx, h - 40, _money(gv) if gv else "$0", FLOOR, COOL, anchor="middle")

    for i, v in enumerate(vendors):
        y = top + i * rowh + 16
        b += _t(0, y - 2, v["name"], 11, INK, "bold")
        b += _t(0, y + 12, f"{v['orgs']} organisations name it", FLOOR, SLATE)
        if v.get("lo") is not None:
            b += (f'<rect x="{px(v["lo"]):.1f}" y="{y-9}" width="{px(v["hi"])-px(v["lo"]):.1f}" '
                  f'height="18" fill="{MIST}"/>')
            b += _t(px(v["lo"]), y + 22, _money(v["lo"]), FLOOR, COOL, anchor="middle")
            b += _t(px(v["hi"]), y + 22, _money(v["hi"]), FLOOR, COOL, anchor="middle")
        b += (f'<path d="M{px(v["median"]):.1f} {y} H{px(v["theirs"]):.1f}" '
              f'stroke="{HAIR}" stroke-width="2"/>')
        b += f'<circle cx="{px(v["median"]):.1f}" cy="{y}" r="5" fill="{COOL}"/>'
        b += f'<circle cx="{px(v["theirs"]):.1f}" cy="{y}" r="6.5" fill="{SUNRISE}"/>'
        b += _t(w, y - 3, _money(v["theirs"]), 11, NAVY, "bold", "end")
        b += _t(w, y + 10, f"median {_money(v['median'])}", FLOOR, SLATE, anchor="end")

    note = ("Disclosed amounts are annual totals, not rates, and organisation size and "
            "scope differ. This is a question to put to the arrangement, not a finding "
            "about it.")
    ny = h - 22
    b += f'<path d="M0 {ny-13} H{w}" stroke="{HAIR}" stroke-width="1"/>'
    for j, line in enumerate(_wrap(note, FLOOR, w)):
        b += _t(0, ny + j * 12, line, FLOOR, SLATE)
    return _svg(w, h + 12 * (len(_wrap(note, FLOOR, w)) - 1), b)


# ── V4 ──────────────────────────────────────────────────────────────────────
def observable_universe(evidenced, evidenced_n, separated, separated_n, worked_n, w=520):
    """Concentric, never a funnel. The outer ring carries NO number, and the
    absence of that number is the honesty of the chart."""
    h = 300
    cx, cy = 148, h / 2
    b = (f'<circle cx="{cx}" cy="{cy}" r="132" fill="none" stroke="{SLATE}" '
         f'stroke-width="1.2" stroke-dasharray="4 4"/>'
         f'<circle cx="{cx}" cy="{cy}" r="92" fill="{DEEP}"/>'
         f'<circle cx="{cx}" cy="{cy}" r="52" fill="{NAVY}"/>')
    b += _t(cx, cy - 3, _money(evidenced), 15, "#fff", "bold", "middle")
    b += _t(cx, cy + 12, f"{evidenced_n} categories", FLOOR, "#CFDCEA", anchor="middle")

    lx = 310
    items = [
        (NAVY, f"{_money(evidenced)} · {evidenced_n} categories",
         "Completed ERA work stands behind every one."),
        (DEEP, f"{_money(separated)} · {separated_n} more indirect lines",
         "The filing separates them but names no supplier, so we size nothing."),
        (None, f"The rest of the {worked_n} categories ERA works",
         "We do not know whether there is material spend here. Neither does your "
         "P&L. That is what we would find out."),
    ]
    y = 52
    for col, head, sub in items:
        if col:
            b += f'<rect x="{lx}" y="{y-9}" width="13" height="13" fill="{col}"/>'
        else:
            b += (f'<rect x="{lx}" y="{y-9}" width="13" height="13" fill="none" '
                  f'stroke="{SLATE}" stroke-width="1.2" stroke-dasharray="3 2"/>')
        b += _t(lx + 21, y + 2, head, 10.5, NAVY, "bold")
        yy = y + 16
        for line in _wrap(sub, FLOOR, w - lx - 21):
            b += _t(lx + 21, yy, line, FLOOR, SLATE); yy += 12
        y = yy + 18
    return _svg(w, h, b)


# ── V5 ──────────────────────────────────────────────────────────────────────
def evidence_to_action(steps, w=520):
    """Six steps. The two that cost them anything are marked, and everything
    after their decision is ERA capacity rather than their time."""
    n = len(steps)
    gap = 6
    bw = (w - gap * (n - 1)) / n
    top, bh = 34, 66
    h = top + bh + 54
    b = _t(0, 13, "YOU APPROVE EVERY STEP", FLOOR, SLATE, "bold", ls="0.06em")
    for i, (label, whose) in enumerate(steps):
        x = i * (bw + gap)
        theirs = whose == "them"
        b += (f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{bh}" '
              f'fill="{CREAM if theirs else MIST}" '
              f'stroke="{CREAM_ED if theirs else HAIR}" rx="2"/>')
        b += (f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="2.6" '
              f'fill="{SUNRISE if theirs else NAVY}"/>')
        yy = top + 20
        for line in _wrap(label, FLOOR, bw - 12, bold=True):
            b += _t(x + 6, yy, line, FLOOR, INK, "bold"); yy += 11.5
        if i < n - 1:
            ax = x + bw + gap / 2
            b += (f'<path d="M{ax-2.2:.1f} {top+bh/2-3} l3 3 l-3 3" fill="none" '
                  f'stroke="{SLATE}" stroke-width="1.3"/>')
    ty = top + bh + 20
    b += f'<rect x="0" y="{ty-9}" width="11" height="11" fill="{CREAM}" stroke="{CREAM_ED}"/>'
    b += _t(18, ty, "The only two steps that cost you anything: one contract, one "
                    "invoice export.", FLOOR, INK)
    b += _t(18, ty + 14, "Everything after your decision is ERA capacity, not your "
                         "team's time.", FLOOR, SLATE)
    return _svg(w, h, b)
