"""Hero visuals for the CFO rebuild. One per analytical sheet, no exceptions.

The spec's non-negotiables, which are also the rules here:
  ONE hero visual per analytical page. Never a table and a chart saying the same
    thing — that is what pages 8-11 of V2 did.
  DIRECT LABELS. No legend, no key, no footnote that has to be decoded.
  Navy carries authority. Orange marks ONE thing on a page. A border is not a
    design decision, so nothing here is a bordered box.
  Bespoke line marks tied to the actual category work — a truck, a parcel, an
    invoice — never a generic dashboard icon.
  Nothing below 10pt (brand_tokens row 12; Arial Nova is not in this repo).

Geometry is in points and every width is MEASURED against the real font, never
counted in characters.
"""
import math

from charts import NAVY, SUNRISE, MIST, DEEP, INK, SLATE, HAIR, FLOOR, _svg, _t, _w, _wrap

PALE = "#C9D8E8"          # the middle band: visible, not modelled
WHITE_EDGE = "#FFFFFF"
RULE = "#E3E9F0"


def _spread(ys, gap, lo, hi):
    """Push labels apart until none is closer than `gap`, preserving order.

    Ribbon and dot positions are the truth; LABEL positions are not, so the
    labels move and a leader line keeps each one attached to its mark. The
    alternative — a minimum ribbon thickness — would make the widths lie."""
    out = list(ys)
    for i in range(1, len(out)):
        if out[i] - out[i - 1] < gap:
            out[i] = out[i - 1] + gap
    over = out[-1] - hi
    if over > 0:
        for i in range(len(out)):
            out[i] -= over
    for i in range(len(out) - 2, -1, -1):
        if out[i + 1] - out[i] < gap:
            out[i] = out[i + 1] - gap
    if out[0] < lo:
        shift = lo - out[0]
        for i in range(len(out)):
            out[i] += shift
    return out


def _ticks(lo_l, hi_l, px, candidates, size=10):
    """Only the gridlines whose labels do not touch. A tick you cannot read is
    not a tick, and V2's log axis printed "$2.5M$5M$10$15M"."""
    import math as _m
    keep, last = [], -1e9
    for v in candidates:
        if not (lo_l <= _m.log10(v) <= hi_l):
            continue
        lab = f"${v:g}M" if v >= 1 else f"${int(v*1000)}K"
        x = px(v)
        half = _w(lab, size) / 2
        if x - half < last + 8:
            continue
        keep.append((v, lab, x))
        last = x + half
    return keep


def _fit(text, size, width, bold=False, floor=FLOOR):
    """Shrink to fit, never below the floor. Returns the size that fits, and the
    caller decides what to do if it still doesn't."""
    while size > floor and _w(text, size, bold) > width:
        size -= 0.25
    return size


# ── SHEET 5 ─────────────────────────────────────────────────────────────────
def visibility_horizon(w=520):
    """Left: what we can model. Middle: what is visible but too broad. Right: an
    OPEN field — the categories a Form 990 never separates. The open field is the
    argument, so it is drawn as absence rather than as a third bar."""
    modelled, clarify, excluded = 45.274, 36.132, 0.701
    filing = modelled + clarify + excluded
    band = w * 0.60                       # the filing. The open field needs room
    gap_to_open = 34                      # to read as a different KIND of space
    x1 = band * modelled / filing
    x2 = band * (modelled + clarify) / filing
    open_x = band + gap_to_open
    top, bh = 84, 46

    b = _t(0, 20, "$82.1M ON THE FY2024 FILING", 10, SLATE, "bold", ls="0.06em")
    b += _t(w, 20, "BEYOND THE FILING", 10, SLATE, "bold", "end", ls="0.06em")

    mk = x1 * 0.5
    b += _t(mk, top - 34, "$9.67M", 18, NAVY, "bold", "middle")
    b += _t(mk, top - 20, "completed-work median across six categories",
            10, SLATE, anchor="middle")
    b += (f'<path d="M{mk:.1f} {top-15} V{top-4}" stroke="{SUNRISE}" stroke-width="1.8"/>'
          f'<circle cx="{mk:.1f}" cy="{top-3}" r="2.8" fill="{SUNRISE}"/>')

    b += f'<rect x="0" y="{top}" width="{x1:.1f}" height="{bh}" fill="{NAVY}"/>'
    b += f'<rect x="{x1+1.5:.1f}" y="{top}" width="{x2-x1-1.5:.1f}" height="{bh}" fill="{PALE}"/>'
    b += f'<rect x="{x2+1.5:.1f}" y="{top}" width="{band-x2-1.5:.1f}" height="{bh}" fill="{RULE}"/>'
    b += (f'<path d="M{open_x:.1f} {top} H{w} M{open_x:.1f} {top+bh} H{w}" '
          f'stroke="{HAIR}" stroke-width="1"/>')
    b += (f'<path d="M{open_x:.1f} {top} V{top+bh}" stroke="{SLATE}" '
          f'stroke-width="1.2" stroke-dasharray="3 3"/>')

    y = top + bh + 20
    for x, wid, fig, lab in ((0, x1, "$45.3M", "Model now"),
                             (x1 + 1.5, x2 - x1, "$36.1M", "Clarify with your data"),
                             (open_x, w - open_x, "55 categories", "Examine across the operation")):
        b += _t(x, y, fig, 13, NAVY if x == 0 else INK, "bold")
        for j, line in enumerate(_wrap(lab, 10, max(wid, 110))):
            b += _t(x, y + 16 + j * 13, line, 10, SLATE)
    # the excluded sliver is real but tiny; it gets a leader, not a crowded label
    # The excluded sliver is 0.7 of 82.1 — under 3pt of bar. A label pointing at
    # it would be a label pointing at nothing, so it is a footnote to the bar.
    b += f'<path d="M0 {y+30} H{band:.1f}" stroke="{HAIR}" stroke-width="1"/>'
    b += _t(0, y + 44, "Includes $0.7M of legal and lobbying, excluded from the "
                       "indirect-spend portfolio as non-vendor spend.", 10, SLATE)
    return _svg(w, y + 56, b)


# ── SHEET 6 ─────────────────────────────────────────────────────────────────
def findings_spine(findings, w=520):
    """Five findings down one sweeping orange line, each with ERA's response
    opposite. The spine is the page's only orange, and it is what makes five
    separate observations read as one argument instead of five essays."""
    RESPONSES = ("Separate", "Validate", "Prioritize", "Clarify", "Test")
    resp_w = max(_w(r.upper(), 10, True) + 10 * 0.10 * len(r) for r in RESPONSES) + 6
    lab_w = w - 54 - resp_w - 30
    rows, y = [], 42
    for (n, head, body), resp in zip(findings, RESPONSES):
        h = _wrap(head, 11.5, lab_w, bold=True)
        t = _wrap(body, 10, lab_w)
        rows.append((n, h, t, y, resp))
        y += 15 * len(h) + 13.5 * len(t) + 24
    last_y = rows[-1][3] - 4
    h_total = y - 6

    sx = 30
    b = (f'<path d="M{sx} 30 C{sx-9} {last_y*0.36:.0f} {sx+9} {last_y*0.7:.0f} '
         f'{sx} {last_y}" fill="none" stroke="{SUNRISE}" stroke-width="2.2"/>')
    b += _t(0, 14, "WHAT THE EVIDENCE SAYS", 10, SLATE, "bold", ls="0.08em")
    b += _t(w, 14, "ERA RESPONSE", 10, SLATE, "bold", "end", ls="0.08em")

    for n, head, body, y0, resp in rows:
        cy = y0 - 4
        b += f'<circle cx="{sx}" cy="{cy}" r="10.5" fill="#fff" stroke="{SUNRISE}" stroke-width="2.2"/>'
        b += _t(sx, cy + 4, str(n), 11, NAVY, "bold", "middle")
        yy = y0
        for line in head:
            b += _t(sx + 24, yy, line, 11.5, NAVY, "bold"); yy += 15
        for line in body:
            b += _t(sx + 24, yy, line, 10, INK); yy += 13.5
        # the rule STOPS before the word. It used to run through it.
        label_left = w - _w(resp.upper(), 10, True) - 10 * 0.10 * len(resp) - 10
        b += f'<path d="M{label_left-26:.1f} {cy} H{label_left-8:.1f}" stroke="{HAIR}" stroke-width="1"/>'
        b += _t(w, cy + 4, resp.upper(), 10, SLATE, "bold", "end", ls="0.10em")
    return _svg(w, h_total, b)


# ── SHEET 7 ─────────────────────────────────────────────────────────────────
def portfolio_bubbles(rows, w=520):
    """Filed spend against completed-engagement depth. Size encodes nothing —
    a second encoding on the same mark is how a bubble chart starts lying. Two
    orange rings say which two advance; every category stays on the page."""
    pad_l, pad_b, pad_t, pad_r = 56, 50, 34, 96
    h = 300
    x0, x1 = pad_l, w - pad_r
    y0, y1 = h - pad_b, pad_t

    xs = [r[1] for r in rows]; ys = [r[2] for r in rows]
    # spend is log — one category is 80x the next, and a linear axis stacks five
    # of six on the left edge, which is exactly what V2's range plot did.
    lo, hi = math.log10(min(xs) * 0.65), math.log10(max(xs) * 1.7)
    px = lambda v: x0 + (math.log10(v) - lo) / (hi - lo) * (x1 - x0)
    ymax = max(ys) * 1.20
    py = lambda v: y0 - v / ymax * (y0 - y1)

    b = ""
    for gv, lab, gx in _ticks(lo, hi, px, (0.25, 0.5, 1, 2, 5, 10, 20, 40)):
        b += f'<path d="M{gx:.1f} {y1} V{y0}" stroke="{RULE}" stroke-width="1"/>'
        b += _t(gx, y0 + 16, lab, 10, SLATE, anchor="middle")
    for gv in (0, 50, 100, 150):
        if gv <= ymax:
            gy = py(gv)
            b += f'<path d="M{x0} {gy:.1f} H{x1}" stroke="{RULE}" stroke-width="1"/>'
            b += _t(x0 - 9, gy + 3.5, str(gv), 10, SLATE, anchor="end")

    b += _t(x0, h - 8, "FILED SPEND  ·  LOG SCALE", 10, SLATE, "bold", ls="0.08em")
    b += _t(0, y1 - 14, "COMPLETED ERA ENGAGEMENTS", 10, SLATE, "bold", ls="0.08em")

    marks = [(px(sp), py(en), nm, sp, en, ring) for nm, sp, en, ring in rows]

    # Label placement by CANDIDATE POSITION, not by pushing down. Try each of
    # eight slots around the dot and take the first that clears every mark, every
    # label already placed, and the plot box. Pushing labels downward until they
    # stopped overlapping just herded them all into the bottom of the chart and
    # walked "Fleet Management" off the axis.
    placed = [(cx - 12, cx + 12, cy - 12, cy + 12) for cx, cy, *_ in marks]
    out = {}
    for i in sorted(range(len(marks)), key=lambda k: -marks[k][1]):
        cx, cy, nm, sp, en, ring = marks[i]
        sub = f"${sp:,.2f}M · {en} engagements"
        tw = max(_w(nm, 10, True), _w(sub, 10))
        best, best_cost = None, None
        for dx, dy, side in ((15, 0, 1), (-15, 0, -1), (15, -22, 1), (-15, -22, -1),
                             (15, 24, 1), (-15, 24, -1), (15, -42, 1), (-15, -42, -1),
                             (15, 44, 1), (-15, 44, -1), (15, -62, 1), (15, 64, 1)):
            x_lo = cx + dx if side > 0 else cx + dx - tw
            ly = cy + dy
            box = (x_lo - 2, x_lo + tw + 2, ly - 12, ly + 17)
            if box[0] < 0 or box[1] > w or box[2] < y1 - 16 or box[3] > y0 + 4:
                continue
            # cost is total overlap area, so a crowded chart degrades to the LEAST
            # bad slot instead of falling back onto the dot it was avoiding
            cost = sum(max(0, min(box[1], q[1]) - max(box[0], q[0])) *
                       max(0, min(box[3], q[3]) - max(box[2], q[2])) for q in placed)
            cost += abs(dy) * 0.4                      # prefer staying near the dot
            if best_cost is None or cost < best_cost:
                best, best_cost = (x_lo, ly, side, box), cost
            if cost <= abs(dy) * 0.4:                  # clean slot, stop looking
                break
        if best is None:
            x_lo, ly, side = cx + 15, cy, 1
            best = (x_lo, ly, side, (x_lo, x_lo + tw, ly - 12, ly + 17))
        x_lo, ly, side, box = best
        placed.append(box)
        out[i] = (side, ly, nm, sub, cx, cy, x_lo, tw)
    for i in range(len(marks)):
        side, ly, nm, sub, cx, cy, x_lo, tw = out[i]
        tx = x_lo if side > 0 else x_lo + tw
        anchor = "start" if side > 0 else "end"
        if abs(ly - cy) > 3:
            b += (f'<path d="M{cx + 8*side:.1f} {cy:.1f} L{tx - 4*side:.1f} {ly-3:.1f}" '
                  f'stroke="{HAIR}" stroke-width="1"/>')
        b += _t(tx, ly - 1, nm, 10, INK, "bold", anchor)
        b += _t(tx, ly + 12, sub, 10, SLATE, anchor=anchor)
    for cx, cy, nm, sp, en, ring in marks:
        if ring:
            b += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="12" fill="none" stroke="{SUNRISE}" stroke-width="2"/>'
        b += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" fill="{NAVY if ring else SLATE}"/>'
    return _svg(w, h, b)


# ── SHEET 8 ─────────────────────────────────────────────────────────────────
def quartile_log(rows, w=520):
    """The middle half of completed work, per category. Log scale, because
    Operating Supply is 96x Insurance and a linear axis compressed the five
    smaller categories into a smudge of overlapping dots — the page John called
    hideous. Low and high are ONE label under the bar, not two that collide."""
    lab_w = 178
    x0, x1 = lab_w + 14, w - 118
    rowh, top = 36, 40
    h = top + rowh * len(rows) + 30
    vals = [v for _, lo, _, _, hi in rows for v in (lo, hi)]
    lo_l, hi_l = math.log10(min(vals) * 0.6), math.log10(max(vals) * 1.6)
    px = lambda v: x0 + (math.log10(v) - lo_l) / (hi_l - lo_l) * (x1 - x0)

    b = _t(0, 13, "THE MIDDLE HALF OF COMPLETED ERA WORK, APPLIED TO YOUR FILED SPEND",
           10, SLATE, "bold", ls="0.05em")
    b += _t(w, top - 14, "MEDIAN", 10, SLATE, "bold", "end", ls="0.08em")
    for gv, lab, gx in _ticks(lo_l, hi_l, px, (0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 15)):
        b += f'<path d="M{gx:.1f} {top-8} V{h-24}" stroke="{RULE}" stroke-width="1"/>'
        b += _t(gx, h - 8, lab, 10, SLATE, anchor="middle")

    for i, (name, lo, med, med_label, hi) in enumerate(rows):
        y = top + i * rowh + 12
        b += _t(0, y + 4, name, 10, INK, "bold")
        b += f'<line x1="{px(lo):.1f}" y1="{y}" x2="{px(hi):.1f}" y2="{y}" stroke="{NAVY}" stroke-width="2.4"/>'
        for v in (lo, hi):
            b += (f'<circle cx="{px(v):.1f}" cy="{y}" r="3.6" fill="#fff" '
                  f'stroke="{NAVY}" stroke-width="1.7"/>')
        b += (f'<circle cx="{px(med):.1f}" cy="{y}" r="4.6" fill="{SUNRISE}" '
              f'stroke="#fff" stroke-width="1.5"/>')
        b += _t(w, y + 4, med_label, 11, NAVY, "bold", anchor="end")
        rng = f"{_money(lo)} – {_money(hi)}"
        b += _t((px(lo) + px(hi)) / 2, y + 17, rng, 10, SLATE, anchor="middle")
    return _svg(w, h, b)


def _money(v):
    return f"${v:,.2f}M" if v >= 1 else f"${int(round(v*1000)):,}K"


# ── SHEET 9 ─────────────────────────────────────────────────────────────────
def disposition_flow(lines, w=520):
    """Twelve filed lines into four destinations. Ribbon width is filed dollars,
    so the eye gets the proportions before it reads a word, and the excluded line
    is visibly excluded rather than quietly folded into a subtotal.

    Ribbon positions are the truth and do not move. LABELS move — spread apart
    with a leader line back to their ribbon — because the alternative, a minimum
    ribbon thickness, would make the widths lie."""
    DEST = [("MODEL NOW", NAVY), ("CLARIFY WITH YOUR DATA", PALE),
            ("INVESTIGATE", DEEP), ("EXCLUDED", RULE)]
    lx, rx = 210, w - 158
    top, gap, dgap = 34, 2.0, 30
    total = sum(v for _, v, _ in lines)
    ribbon = 244.0
    scale = ribbon / total
    amt_w = max(_w(_money(v), 10) for _, v, _ in lines)
    h = top + ribbon + gap * (len(lines) - 1) + dgap * 3 + 54

    order = sorted(range(len(lines)), key=lambda i: (lines[i][2], -lines[i][1]))
    ly, left = top, {}
    for i in order:
        th = max(1.6, lines[i][1] * scale)
        left[i] = (ly, th); ly += th + gap

    rtot = {}
    for _, val, d in lines:
        rtot[d] = rtot.get(d, 0) + val
    ry, right, cursor = top, {}, {}
    for d in range(len(DEST)):
        th = max(5.0, rtot.get(d, 0) * scale)
        right[d] = (ry, th); cursor[d] = ry
        ry += th + dgap

    b = ""
    for i in order:
        name, val, d = lines[i]
        y0, th = left[i]
        y1 = cursor[d]; cursor[d] += th
        col = DEST[d][1]
        c = (lx + rx) / 2
        b += (f'<path d="M{lx} {y0:.1f} C{c} {y0:.1f} {c} {y1:.1f} {rx} {y1:.1f} '
              f'L{rx} {y1+th:.1f} C{c} {y1+th:.1f} {c} {y0+th:.1f} {lx} {y0+th:.1f} Z" '
              f'fill="{col}" opacity="{0.94 if d==0 else 0.86}"/>')

    centres = [left[i][0] + left[i][1] / 2 for i in order]
    placed = _spread(centres, 14.5, top + 4, ly)
    for i, ty in zip(order, placed):
        name, val, d = lines[i]
        cy = left[i][0] + left[i][1] / 2
        # amounts right-align in their own column so they cannot run into the
        # ribbon, and the names right-align against that column
        b += _t(lx - 16, ty + 3.4, _money(val), 10, SLATE, anchor="end")
        b += _t(lx - 20 - amt_w, ty + 3.4, name, 10, INK, anchor="end")
        if abs(ty - cy) > 1:
            b += (f'<path d="M{lx-6} {ty:.1f} H{lx-3} L{lx} {cy:.1f}" fill="none" '
                  f'stroke="{HAIR}" stroke-width="1"/>')

    for d, (dname, col) in enumerate(DEST):
        y0, th = right[d]
        b += f'<rect x="{rx}" y="{y0:.1f}" width="7" height="{th:.1f}" fill="{col}"/>'
        b += _t(rx + 15, y0 + 12, _money(rtot.get(d, 0)), 13, NAVY if d == 0 else INK, "bold")
        for j, line in enumerate(_wrap(dname, 10, w - rx - 15, bold=True)):
            b += _t(rx + 15, y0 + 26 + j * 12.5, line, 10, SLATE, "bold", ls="0.05em")
    # COUNT the rows, never assert twelve. The spec says "twelve filed lines";
    # the data has fourteen — eleven Part IX expense lines and three service
    # relationships named in Part VII Section B. A CFO counts the rows.
    named = sum(1 for n, _, _ in lines if "VII-B" in n)
    words = {11: "ELEVEN", 12: "TWELVE", 13: "THIRTEEN", 14: "FOURTEEN"}
    head = (f"{words.get(len(lines)-named, len(lines)-named)} EXPENSE LINES"
            + (f" AND {words.get(named, named)} NAMED RELATIONSHIPS" if named else ""))
    b += _t(0, 16, head, 10, SLATE, "bold", ls="0.06em")
    b += _t(rx + 15, 16, "WHAT HAPPENS TO EACH", 10, SLATE, "bold", ls="0.08em")
    note = (f"Ribbon width is filed dollars. The four destinations sum to {_money(total)} "
            f"— the whole of the filing, with nothing folded into a subtotal.")
    for j, line in enumerate(_wrap(note, 10, w)):
        b += _t(0, h - 22 + j * 13, line, 10, SLATE)
    return _svg(w, h, b)


# ── SHEET 10 ────────────────────────────────────────────────────────────────
def category_diptych(w=520):
    """Two category-specific diagrams side by side: the supply SPLIT that is the
    Operating Supply question, and the contract ANATOMY that is the Uniforms
    question. Drawn in one coordinate space so the halves stay in proportion —
    two separately scaled SVGs drifted apart and the captions collided."""
    h = 150
    mid = w / 2
    b = f'<path d="M{mid} 6 V{h-6}" stroke="{HAIR}" stroke-width="1"/>'

    # left: one inbound stream splitting in two
    b += _t(0, 16, "OPERATING SUPPLY  ·  $37.97M FILED", 10, NAVY, "bold", ls="0.06em")
    b += f'<path d="M0 74 H70" stroke="{NAVY}" stroke-width="14"/>'
    b += (f'<path d="M70 74 C96 74 96 44 122 44 M70 74 C96 74 96 104 122 104" '
          f'fill="none" stroke="{SLATE}" stroke-width="1.4"/>')
    for y, lab, col in ((44, "Resale inventory", PALE), (104, "Supply consumed", SUNRISE)):
        b += f'<rect x="122" y="{y-9}" width="30" height="18" fill="{col}" rx="2"/>'
        b += _t(160, y + 4, lab, 10, INK, "bold")
    b += _t(0, h - 8, "The split is the question.", 10, SLATE)

    # right: the document, and the clause a renewal quietly carries
    ox = mid + 26
    b += _t(ox, 16, "UNIFORMS  ·  $1.52M FILED", 10, NAVY, "bold", ls="0.06em")
    b += (f'<path d="M{ox} 34 H{ox+56} L{ox+72} 50 V{h-38} H{ox} Z" fill="{MIST}" '
          f'stroke="{NAVY}" stroke-width="1.3"/>'
          f'<path d="M{ox+56} 34 V50 H{ox+72}" fill="none" stroke="{NAVY}" stroke-width="1.3"/>')
    for i, lab in enumerate(("Term and renewal", "Rates and adjustments",
                             "Service levels", "Ancillary charges")):
        y = 62 + i * 18
        last = i == 3
        b += f'<rect x="{ox+10}" y="{y-4}" width="{50 if not last else 44}" height="3" fill="{SUNRISE if last else SLATE}"/>'
        b += _t(ox + 86, y, lab, 10, INK if last else SLATE, "bold" if last else "normal")
    b += _t(ox, h - 8, "What a renewal quietly carries.", 10, SLATE)
    return _svg(w, h, b)


# ── SHEET 11 ────────────────────────────────────────────────────────────────
def concentric_landscape(w=520):
    """Centre: the six modelled. Middle ring: the $36.1M that needs detail. Outer:
    representative categories a 990 never separates, drawn as the marks of the
    work — a truck, a parcel, a bin — so breadth is tangible without claiming
    every category is an opportunity."""
    h = 320
    cx, cy = w * 0.29, h / 2
    b = (f'<circle cx="{cx}" cy="{cy}" r="126" fill="none" stroke="{HAIR}" stroke-dasharray="4 4"/>'
         f'<circle cx="{cx}" cy="{cy}" r="88" fill="{MIST}" stroke="{HAIR}"/>'
         f'<circle cx="{cx}" cy="{cy}" r="46" fill="{NAVY}"/>')
    b += _t(cx, cy - 4, "$45.3M", 14, "#fff", "bold", "middle")
    b += _t(cx, cy + 11, "six modelled", 10, "#CFDCEA", anchor="middle")
    b += _t(cx, cy - 68, "$36.1M NEEDS YOUR DETAIL", 10, SLATE, "bold", "middle", ls="0.06em")
    b += _t(cx, cy + 112, "BEYOND THE FILING", 10, SLATE, "bold", "middle", ls="0.06em")

    marks = (("Waste", _m_bin), ("Telecom", _m_signal), ("Packaging", _m_parcel),
             ("Payment processing", _m_card), ("Utilities", _m_bolt),
             ("Maintenance", _m_wrench), ("Office supply", _m_clip))
    lx = w * 0.62
    for i, (lab, fn) in enumerate(marks):
        y = 34 + i * 36
        b += fn(lx, y)
        b += _t(lx + 30, y + 4, lab, 10, INK)
    b += _t(lx, h - 6, "Only your internal data can say which apply.", 10, SLATE)
    return _svg(w, h, b)


def _m_bin(x, y):
    return (f'<path d="M{x} {y-7} h18 l-2 17 h-14 Z M{x-2} {y-7} h22 M{x+6} {y-11} h6" '
            f'fill="none" stroke="{NAVY}" stroke-width="1.4"/>')

def _m_signal(x, y):
    return "".join(f'<rect x="{x+i*5}" y="{y+4-(i+1)*4}" width="3" height="{(i+1)*4}" fill="{NAVY}"/>'
                   for i in range(4))

def _m_parcel(x, y):
    return (f'<path d="M{x} {y-6} h18 v14 h-18 Z M{x+9} {y-6} v14 M{x} {y-1} h18" '
            f'fill="none" stroke="{NAVY}" stroke-width="1.4"/>')

def _m_card(x, y):
    return (f'<path d="M{x} {y-6} h20 v13 h-20 Z" fill="none" stroke="{NAVY}" stroke-width="1.4"/>'
            f'<rect x="{x}" y="{y-3}" width="20" height="3" fill="{NAVY}"/>')

def _m_bolt(x, y):
    return f'<path d="M{x+10} {y-8} l-8 10 h6 l-3 9 l9 -11 h-6 Z" fill="{NAVY}"/>'

def _m_wrench(x, y):
    return (f'<path d="M{x+3} {y+7} l11 -11 M{x+13} {y-8} a5.5 5.5 0 1 0 4 9" '
            f'fill="none" stroke="{NAVY}" stroke-width="1.6" stroke-linecap="round"/>')

def _m_clip(x, y):
    return (f'<path d="M{x+4} {y+6} v-10 a4 4 0 0 1 8 0 v11 a6 6 0 0 1 -12 0 v-9" '
            f'fill="none" stroke="{NAVY}" stroke-width="1.4"/>')


# ── SHEET 12 ────────────────────────────────────────────────────────────────
def value_chain(w=520):
    """Question to verified result, through the five artifacts the work actually
    touches. Document silhouettes, not five identical boxes — the point is that
    each stage handles a different kind of evidence."""
    h = 132
    stages = (("Filing", _a_doc), ("Contract", _a_contract), ("Invoice", _a_invoice),
              ("Option", _a_option), ("Measured result", _a_result))
    n = len(stages)
    span = w - 40
    step = span / (n - 1)
    y = 62
    b = f'<path d="M20 {y} H{20+span}" stroke="{HAIR}" stroke-width="1.4"/>'
    b += _t(0, 16, "QUESTION", 10, SLATE, "bold", ls="0.08em")
    b += _t(w, 16, "VERIFIED RESULT", 10, SLATE, "bold", "end", ls="0.08em")
    for i, (lab, fn) in enumerate(stages):
        x = 20 + i * step
        last = i == n - 1
        b += fn(x, y, last)
        for j, line in enumerate(_wrap(lab, 10, step - 12, bold=True)):
            b += _t(x, y + 40 + j * 13, line, 10, NAVY if last else INK, "bold", "middle")
    return _svg(w, h, b)


def _a_doc(x, y, last=False):
    return (f'<path d="M{x-11} {y-20} h15 l7 7 v27 h-22 Z M{x+4} {y-20} v7 h7" '
            f'fill="#fff" stroke="{NAVY}" stroke-width="1.4"/>'
            + "".join(f'<rect x="{x-6}" y="{y-8+k*5}" width="12" height="1.8" fill="{HAIR}"/>' for k in range(3)))

def _a_contract(x, y, last=False):
    return (_a_doc(x, y) +
            f'<path d="M{x-5} {y+8} c4 -5 7 3 11 -2" fill="none" stroke="{SLATE}" stroke-width="1.3"/>')

def _a_invoice(x, y, last=False):
    return (_a_doc(x, y) +
            f'<rect x="{x-6}" y="{y+6}" width="7" height="1.8" fill="{SLATE}"/>'
            f'<rect x="{x+3}" y="{y+6}" width="4" height="1.8" fill="{SLATE}"/>')

def _a_option(x, y, last=False):
    return (f'<path d="M{x} {y-20} l13 13 l-13 13 l-13 -13 Z" fill="#fff" '
            f'stroke="{NAVY}" stroke-width="1.4"/>'
            f'<path d="M{x-5} {y-7} h10 M{x} {y-12} v10" stroke="{SLATE}" stroke-width="1.3"/>')

def _a_result(x, y, last=True):
    return (f'<circle cx="{x}" cy="{y-7}" r="14" fill="{SUNRISE}"/>'
            f'<path d="M{x-6} {y-7} l4 5 l8 -10" fill="none" stroke="#fff" '
            f'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')


# ── SHEET 13 ────────────────────────────────────────────────────────────────
def decision_tree(w=520):
    """One entry, two honest outcomes. Validation is drawn as a real terminus,
    the same weight as recovery, because "your arrangements are competitive" is
    a result the CFO is allowed to want.

    h is COMPUTED from the last thing drawn. It was a literal 210 while the
    fee line was drawn at 246, and _svg carries overflow:visible — so the line
    painted straight across the copy on the sheet below it."""
    h = 100 + 3 * 44 + 34
    cx = w / 2
    b = ""
    bw, bh = 190, 40
    b += f'<rect x="{cx-bw/2:.1f}" y="6" width="{bw}" height="{bh}" fill="{NAVY}" rx="3"/>'
    b += _t(cx, 24, "30-MINUTE REVIEW", 11, "#fff", "bold", "middle", ls="0.06em")
    b += _t(cx, 38, "no cost, no commitment", 10, "#CFDCEA", anchor="middle")

    ly, ry = 100, 100
    assert h >= ry + 3 * 44 + 20, "decision_tree: content drawn past its own box"
    lxc, rxc = w * 0.24, w * 0.72
    # the verticals stop ABOVE the branch labels; they used to run through them
    b += (f'<path d="M{cx} {6+bh} V70 M{lxc} 70 H{rxc} M{lxc} 70 V80 M{rxc} 70 V80" '
          f'fill="none" stroke="{SLATE}" stroke-width="1.2"/>')

    # A: validated
    b += f'<rect x="{lxc-84:.1f}" y="{ly}" width="168" height="46" fill="{MIST}" stroke="{HAIR}" rx="3"/>'
    b += _t(lxc, ly + 19, "Arrangements validated", 10.5, NAVY, "bold", "middle")
    b += _t(lxc, ly + 33, "A useful result. No fee.", 10, SLATE, anchor="middle")

    # B: three steps
    steps = ("No-cost baseline", "Approved action", "Verified recovery")
    sw, sh = 150, 34
    for i, s in enumerate(steps):
        y = ry + i * 44
        last = i == len(steps) - 1
        b += (f'<rect x="{rxc-sw/2:.1f}" y="{y}" width="{sw}" height="{sh}" '
              f'fill="{"#FEF4E2" if last else MIST}" stroke="{SUNRISE if last else HAIR}" rx="3"/>')
        b += _t(rxc, y + 21, s, 10.5, NAVY, "bold", "middle")
        if not last:
            b += (f'<path d="M{rxc} {y+sh} v6 M{rxc-3.4} {y+sh+2.6} l3.4 3.4 l3.4 -3.4" '
                  f'fill="none" stroke="{SLATE}" stroke-width="1.3"/>')
    b += _t(rxc, ry + 3 * 44 + 14, "Paid only from recovery, after you receive it.",
            10, SLATE, anchor="middle")
    b += _t(lxc, ly - 10, "IF THE QUESTIONS DO NOT HOLD", 10, SLATE, "bold", "middle", ls="0.06em")
    b += _t(rxc, ry - 10, "IF THEY DO", 10, SLATE, "bold", "middle", ls="0.06em")
    return _svg(w, h, b)


# ── SHEET 15 ────────────────────────────────────────────────────────────────
def promise_rail(promises, w=520):
    """Five promises down one quiet rule. No statistic on this page — the close
    is trust and control, and a number here would be another proof dump."""
    marks = (_p_scale, _p_hand, _p_doc, _p_check, _p_link)
    rows, y = [], 30
    for (head, sub), fn in zip(promises, marks):
        hh = _wrap(head, 12, w - 92, bold=True)
        ss = _wrap(sub, 10.5, w - 92)
        rows.append((hh, ss, y, fn))
        y += 16 * len(hh) + 14.5 * len(ss) + 30
    h = y
    b = f'<path d="M22 14 V{h-24}" stroke="{HAIR}" stroke-width="1.4"/>'
    for hh, ss, y0, fn in rows:
        b += fn(22, y0 - 5)
        yy = y0
        for line in hh:
            b += _t(52, yy, line, 12, NAVY, "bold"); yy += 16
        for line in ss:
            b += _t(52, yy, line, 10.5, INK); yy += 14.5
    return _svg(w, h, b)


def _p_scale(x, y):
    """A balance: we will tell you when an arrangement is already strong."""
    return (_ring(x, y) +
            f'<path d="M{x} {y-6} V{y+6} M{x-7} {y-3} H{x+7} M{x-7} {y-3} l-2.5 5 h5 Z '
            f'M{x+7} {y-3} l-2.5 5 h5 Z" fill="none" stroke="{NAVY}" stroke-width="1.3" '
            f'stroke-linejoin="round"/>')

def _p_hand(x, y):
    """A dial turned part way: value comes from more than one lever."""
    return (_ring(x, y) +
            f'<path d="M{x-6} {y+4} a6.5 6.5 0 1 1 12 0" fill="none" stroke="{NAVY}" '
            f'stroke-width="1.4"/><path d="M{x} {y+3} L{x+4.5} {y-3.5}" stroke="{SUNRISE}" '
            f'stroke-width="1.8" stroke-linecap="round"/>')

def _p_doc(x, y):
    """A page with a corner turned: every recommendation shows its source."""
    return (_ring(x, y) +
            f'<path d="M{x-5} {y-7} h7 l4 4 v10 h-11 Z M{x+2} {y-7} v4 h4" fill="none" '
            f'stroke="{NAVY}" stroke-width="1.3" stroke-linejoin="round"/>')

def _p_check(x, y):
    return (_ring(x, y) +
            f'<path d="M{x-5} {y} l3.5 4 l7 -8" stroke="{NAVY}" stroke-width="1.8" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')

def _p_link(x, y):
    """Two marks moving together: our economics depend on yours."""
    return (_ring(x, y) +
            f'<path d="M{x-6} {y+4} L{x-1} {y-3} L{x+3} {y+1} L{x+7} {y-5}" fill="none" '
            f'stroke="{NAVY}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>')

def _ring(x, y):
    return f'<circle cx="{x}" cy="{y}" r="11.5" fill="#fff" stroke="{SUNRISE}" stroke-width="1.8"/>'
