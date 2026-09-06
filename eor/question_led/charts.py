"""Inline SVG charts for the Brief. Print only: no hover layer, no legends.

RULES THIS FILE OBEYS, and why each one is here rather than a preference:

  Direct labels, never a legend. Every chart is one series or a small labelled
    set, so identity never depends on colour alone — which also survives a
    greyscale office printer, the medium this document is actually read in.
  Text wears text tokens. Values and labels are Ink or Slate. A coloured mark
    beside them carries the identity; the number never wears the series colour.
  Two fills are separated by LIGHTNESS, not hue — Daybreak #003A70 against
    Panel Deep #E4EBF3. That is unambiguous under every colour-vision deficiency
    and in black and white, so no validator run can fail it.
  No red or green anywhere, no gauges, no 3D, no gradients, no pie charts.
    Settled #172 and brand_tokens rule 21 both forbid a status palette here.
  Bar length encodes FILED SPEND only. Nothing in these charts is ever allowed
    to imply a promised recovery — LAW 27.

All geometry is in points so it lines up with the type scale in styles.css.
"""

NAVY   = "#003A70"
SUNRISE= "#FF9C00"
MIST   = "#F2F5F8"
DEEP   = "#E4EBF3"
INK    = "#1B2A41"
SLATE  = "#5A6577"
HAIR   = "#D7DFE9"
FONT   = "Trebuchet MS, Arial, sans-serif"


def _svg(w, h, body, cls="fig"):
    return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" width="100%" '
            f'style="height:auto;display:block;overflow:visible" '
            f'xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">{body}</svg>')


def _t(x, y, s, size=9, fill=INK, weight="normal", anchor="start", ls=None):
    extra = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{extra}>{s}</text>')


def visibility_bar(w=520):
    """Sheet 5. One bar, the whole filed indirect landscape, split into what the
    public record lets us model and what it names without exposing."""
    total, modelled = 82.12, 45.28
    h, y, bh = 96, 26, 26
    fx = modelled / total * w
    gap = 2                                    # surface gap between fills
    b  = f'<rect x="0" y="{y}" width="{fx-gap:.1f}" height="{bh}" fill="{NAVY}" rx="2"/>'
    b += f'<rect x="{fx:.1f}" y="{y}" width="{w-fx:.1f}" height="{bh}" fill="{DEEP}" rx="2"/>'
    b += _t(0, y - 7, "$45.28M MODELLED NOW", 8.5, NAVY, "bold", ls="0.06em")
    b += _t(w, y - 7, "$36.84M NAMED, NOT MODELLED", 8.5, SLATE, "bold", "end", ls="0.06em")
    b += _t(0, y + bh + 14, "Six categories, 533 completed engagements behind them", 8.5, SLATE)
    b += _t(w, y + bh + 14, "$0.93M below our evidence floor · $35.9M the filing blends", 8.5, SLATE, anchor="end")
    b += f'<line x1="0" y1="{y+bh+22}" x2="{w}" y2="{y+bh+22}" stroke="{HAIR}"/>'
    b += _t(0, y + bh + 36, "$82.12M of indirect spend on the filing. Totals are rounded to the nearest $10K.", 8, SLATE)
    return _svg(w, h, b)


def category_bars(rows, w=520):
    """Sheet 7. Filed spend, descending, with evidence depth beside the label.
    Length is spend. Evidence is a number, never a length — the two must not be
    read as the same axis."""
    lab, barx = 168, 176
    rowh, top = 21, 16
    mx = max(v for _, v, _ in rows)
    h = top + rowh * len(rows) + 26
    b = _t(0, 10, "FILED SPEND, NOT PROMISED RECOVERY", 8.5, SLATE, "bold", ls="0.08em")
    for i, (name, val, eng) in enumerate(rows):
        y = top + i * rowh
        bw = max(2.0, val / mx * (w - barx - 96))
        b += _t(0, y + 11, name, 9, INK, "bold")
        b += f'<rect x="{barx}" y="{y+3}" width="{bw:.1f}" height="10" fill="{NAVY}" rx="2"/>'
        b += _t(barx + bw + 6, y + 11, f"${val:,.2f}M" if val < 1 else f"${val:,.2f}M", 8.5, INK)
        b += _t(w, y + 11, f"{eng} engagements", 8.5, SLATE, anchor="end")
    b += f'<line x1="0" y1="{h-18}" x2="{w}" y2="{h-18}" stroke="{HAIR}"/>'
    b += _t(0, h - 6, "Bar length is the filed figure. Engagement count is evidence depth, and is not to scale.", 8, SLATE)
    return _svg(w, h, b)


def range_plot(rows, w=520):
    """Sheet 8. The middle half of completed work per category, against the
    filed figure. Endpoints are the quartiles; the orange dot is the median.
    This is the size of the question — never a forecast."""
    lab, x0 = 150, 158
    rowh, top = 23, 18
    x1 = w - 92
    mx = max(r[-1] for r in rows)
    h = top + rowh * len(rows) + 26

    def px(v):
        return x0 + (v / mx) * (x1 - x0)

    b = _t(0, 10, "THE MIDDLE HALF OF COMPLETED WORK", 8.5, SLATE, "bold", ls="0.08em")
    for i, (name, lo, med, med_label, hi) in enumerate(rows):
        y = top + i * rowh + 9
        b += _t(0, y + 3, name, 9, INK, "bold")
        b += f'<line x1="{px(lo):.1f}" y1="{y}" x2="{px(hi):.1f}" y2="{y}" stroke="{NAVY}" stroke-width="2"/>'
        for v in (lo, hi):
            b += (f'<circle cx="{px(v):.1f}" cy="{y}" r="3.4" fill="#fff" '
                  f'stroke="{NAVY}" stroke-width="1.6"/>')
        b += (f'<circle cx="{px(med):.1f}" cy="{y}" r="4.2" fill="{SUNRISE}" '
              f'stroke="#fff" stroke-width="1.4"/>')
        b += _t(w, y + 3, f"median {med_label}", 8.5, INK, anchor="end")
    b += f'<line x1="0" y1="{h-18}" x2="{w}" y2="{h-18}" stroke="{HAIR}"/>'
    b += _t(0, h - 6, "Quartiles of 533 completed ERA engagements applied to your filed figures. "
                      "Not an estimate of what would be recovered here.", 8, SLATE)
    return _svg(w, h, b)


def process_path(stages, w=520, note=None, mark_last=False, title=None):
    """Sheets 10, 11, 13, 15. A sequence of stages. One orange marker at most,
    on the stage that carries the commercial point."""
    n = len(stages)
    gap = 7
    bw = (w - gap * (n - 1)) / n
    top = 16 if title else 4
    bh = 46
    h = top + bh + (24 if note else 8)
    b = _t(0, 10, title, 8.5, SLATE, "bold", ls="0.08em") if title else ""
    for i, s in enumerate(stages):
        x = i * (bw + gap)
        last = mark_last and i == n - 1
        b += (f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{bh}" fill="{MIST}" '
              f'stroke="{SUNRISE if last else HAIR}" stroke-width="{1.6 if last else 1}" rx="2"/>')
        b += f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="2.4" fill="{SUNRISE if last else NAVY}"/>'
        words, line, ly = s.split(), "", top + 17
        for word in words:
            trial = (line + " " + word).strip()
            if len(trial) * 4.3 > bw - 12 and line:
                b += _t(x + 6, ly, line, 8.2, INK, "bold"); line = word; ly += 10
            else:
                line = trial
        b += _t(x + 6, ly, line, 8.2, INK, "bold")
        if i < n - 1:
            cx = x + bw + gap / 2
            b += (f'<path d="M{cx-2.4:.1f} {top+bh/2-3.2} l3.2 3.2 l-3.2 3.2" fill="none" '
                  f'stroke="{SLATE}" stroke-width="1.3"/>')
    if note:
        b += _t(0, h - 5, note, 8, SLATE)
    return _svg(w, h, b)


def evidence_bridge(layers, w=520):
    """Sheet 12. Nine layers. The four we hold before we meet are filled; the
    five built with the client are outlined. The point of the page is that the
    empty ones are shown empty."""
    n = len(layers)
    gap = 4
    bw = (w - gap * (n - 1)) / n
    top, bh = 18, 40
    h = top + bh + 40
    b = ""
    for i, (name, present) in enumerate(layers):
        x = i * (bw + gap)
        b += (f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{bh}" '
              f'fill="{NAVY if present else MIST}" stroke="{NAVY}" '
              f'stroke-width="{0 if present else 1}" rx="2"/>')
        b += _t(x + bw / 2, top + bh / 2 + 3, name.upper()[:9], 7.2,
                "#fff" if present else NAVY, "bold", "middle", ls="0.04em")
    split = sum(1 for _, p in layers if p)
    xm = split * (bw + gap) - gap / 2
    ay = top + bh + 13
    b += f'<line x1="0" y1="{ay}" x2="{xm-4:.1f}" y2="{ay}" stroke="{NAVY}" stroke-width="1.4"/>'
    b += f'<line x1="{xm+4:.1f}" y1="{ay}" x2="{w}" y2="{ay}" stroke="{SLATE}" stroke-width="1.4" stroke-dasharray="3 3"/>'
    b += _t(0, ay + 13, "BEFORE WE MEET", 8.2, NAVY, "bold", ls="0.08em")
    b += _t(w, ay + 13, "BUILT WITH YOU", 8.2, SLATE, "bold", "end", ls="0.08em")
    b += _t(0, ay + 26, "Four layers carry something for this organization. Five are empty, and are shown empty.", 8, SLATE)
    return _svg(w, h, b)


def outcome_branch(stages, outcomes, footer, w=520):
    """Sheet 13. The path branches only at the end, into two equal outcomes —
    because validating the current arrangement is a real result, not a failure."""
    n = len(stages)
    gap = 7
    bw = (w - gap * (n - 1)) / n
    top, bh = 4, 40
    by = top + bh + 30
    oh = 46
    ow = (w - 14) / 2
    h = by + oh + 26
    b = ""
    for i, s in enumerate(stages):
        x = i * (bw + gap)
        b += f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{bh}" fill="{MIST}" stroke="{HAIR}" rx="2"/>'
        b += f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="2.4" fill="{NAVY}"/>'
        b += _t(x + bw / 2, top + bh / 2 + 4, s, 9, INK, "bold", "middle")
        if i < n - 1:
            cx = x + bw + gap / 2
            b += (f'<path d="M{cx-2.4:.1f} {top+bh/2-3.2} l3.2 3.2 l-3.2 3.2" fill="none" '
                  f'stroke="{SLATE}" stroke-width="1.3"/>')
    b += f'<path d="M{w/2:.1f} {top+bh} v10 M{ow/2:.1f} {top+bh+10} H{w-ow/2:.1f} M{ow/2:.1f} {top+bh+10} v10 M{w-ow/2:.1f} {top+bh+10} v10" stroke="{SLATE}" fill="none" stroke-width="1.2"/>'
    for i, (head, sub) in enumerate(outcomes):
        x = i * (ow + 14)
        b += (f'<rect x="{x:.1f}" y="{by}" width="{ow:.1f}" height="{oh}" fill="#FEF4E2" '
              f'stroke="#F0D8A6" rx="2"/>')
        b += f'<rect x="{x:.1f}" y="{by}" width="3" height="{oh}" fill="{SUNRISE}"/>'
        b += _t(x + 12, by + 17, head, 9.5, NAVY, "bold")
        b += _t(x + 12, by + 31, sub, 8.5, SLATE)
    b += _t(w / 2, h - 6, footer, 9, NAVY, "bold", "middle")
    return _svg(w, h, b)


def proof_strip(items, w=520):
    """Sheets 5, 12, 15. Never more than once on a sheet."""
    n = len(items)
    seg = w / n
    h = 30
    b = f'<line x1="0" y1="0" x2="{w}" y2="0" stroke="{HAIR}"/>'
    for i, (fig, lab) in enumerate(items):
        x = seg * i + seg / 2
        b += _t(x, 14, fig, 11.5, NAVY, "bold", "middle")
        b += _t(x, 25, lab.upper(), 7.4, SLATE, "bold", "middle", ls="0.08em")
        if i:
            b += f'<line x1="{seg*i:.1f}" y1="4" x2="{seg*i:.1f}" y2="26" stroke="{HAIR}"/>'
    return _svg(w, h, b)
