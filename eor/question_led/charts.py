"""Inline SVG charts for the Brief. Print only: no hover layer, no legends.

RULES THIS FILE OBEYS, and why each one is here rather than a preference:

  Nothing is set below 10pt. brand_tokens row 12 makes Arial Nova MANDATORY
    below 10pt — "Below 10pt, no other face is permitted" — and Arial Nova is
    not in fonts/. So the floor is not a taste call, it is the only compliant
    option available, and _t() raises rather than letting a 7.2pt chip label
    through the way the first cut of this file did.
  Widths are MEASURED, never counted. Wrapping used to test len(text) * 4.3,
    which is a guess about a proportional face; at 10pt the guess put two
    labels 520pt wide into a 520pt chart. _w() asks the actual font.
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
import os

import pymupdf

NAVY   = "#003A70"
SUNRISE= "#FF9C00"
MIST   = "#F2F5F8"
DEEP   = "#E4EBF3"
INK    = "#1B2A41"
SLATE  = "#5A6577"
HAIR   = "#D7DFE9"
FONT   = "Trebuchet MS, Arial, sans-serif"

FLOOR  = 10.0          # brand_tokens row 12. Not negotiable while Arial Nova is absent.

_FONTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "fonts")
_REG  = pymupdf.Font(fontfile=os.path.join(_FONTS, "Trebuchet MS.ttf"))
_BOLD = pymupdf.Font(fontfile=os.path.join(_FONTS, "Trebuchet MS Bold.ttf"))


def _w(text, size, bold=False, ls=0.0):
    """Rendered width in points, from the face that will actually set it."""
    face = _BOLD if bold else _REG
    return face.text_length(text, size) + ls * size * max(0, len(text) - 1)


def _svg(w, h, body, cls="fig"):
    return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" width="100%" '
            f'style="height:auto;display:block;overflow:visible" '
            f'xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">{body}</svg>')


def _t(x, y, s, size=FLOOR, fill=INK, weight="normal", anchor="start", ls=None):
    if size < FLOOR:
        raise ValueError(
            f"{size}pt is below the {FLOOR}pt floor: brand_tokens permits no face "
            f"but Arial Nova under 10pt, and Arial Nova is not in this repo. "
            f"Give the chart more room instead of shrinking the type. ({s[:40]!r})")
    extra = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{extra}>{s}</text>')


def _wrap(text, size, width, bold=False):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if _w(trial, size, bold) > width and line:
            lines.append(line); line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def visibility_bar(w=520):
    """Sheet 5. One bar, the whole filed indirect landscape, split into what the
    public record lets us model and what it names without exposing."""
    total, modelled = 82.12, 45.28
    y, bh = 30, 26
    fx = modelled / total * w
    gap = 2                                    # surface gap between fills
    b  = f'<rect x="0" y="{y}" width="{fx-gap:.1f}" height="{bh}" fill="{NAVY}" rx="2"/>'
    b += f'<rect x="{fx:.1f}" y="{y}" width="{w-fx:.1f}" height="{bh}" fill="{DEEP}" rx="2"/>'
    b += _t(0, y - 8, "$45.28M MODELLED NOW", 10, NAVY, "bold", ls="0.06em")
    b += _t(w, y - 8, "$36.84M NAMED, NOT MODELLED", 10, SLATE, "bold", "end", ls="0.06em")
    # These two read as a pair, and at 10pt the pair is exactly the width of the
    # chart. They stack rather than collide; the copy is not the thing that gives.
    b += _t(0, y + bh + 16, "Six categories, 533 completed engagements behind them", 10, SLATE)
    b += _t(0, y + bh + 31, "$0.93M below our evidence floor · $35.9M the filing blends", 10, SLATE)
    rule = y + bh + 41
    b += f'<line x1="0" y1="{rule}" x2="{w}" y2="{rule}" stroke="{HAIR}"/>'
    b += _t(0, rule + 15, "$82.12M of indirect spend on the filing. "
                          "Totals are rounded to the nearest $10K.", 10, SLATE)
    return _svg(w, rule + 22, b)


def category_bars(rows, w=520):
    """Sheet 7. Filed spend, descending, with evidence depth beside the label.
    Length is spend. Evidence is a number, never a length — the two must not be
    read as the same axis."""
    barx = 182
    right = max(_w(f"{eng} engagements", 10, False) for _, _, eng in rows) + 10
    rowh, top = 24, 18
    mx = max(v for _, v, _ in rows)
    h = top + rowh * len(rows) + 32
    b = _t(0, 11, "FILED SPEND, NOT PROMISED RECOVERY", 10, SLATE, "bold", ls="0.08em")
    for i, (name, val, eng) in enumerate(rows):
        y = top + i * rowh
        bw = max(2.0, val / mx * (w - barx - right - 62))
        b += _t(0, y + 13, name, 10, INK, "bold")
        b += f'<rect x="{barx}" y="{y+4}" width="{bw:.1f}" height="11" fill="{NAVY}" rx="2"/>'
        b += _t(barx + bw + 7, y + 13, f"${val:,.2f}M", 10, INK)
        b += _t(w, y + 13, f"{eng} engagements", 10, SLATE, anchor="end")
    b += f'<line x1="0" y1="{h-20}" x2="{w}" y2="{h-20}" stroke="{HAIR}"/>'
    b += _t(0, h - 6, "Bar length is the filed figure. Engagement count is evidence "
                      "depth, and is not to scale.", 10, SLATE)
    return _svg(w, h, b)


def range_plot(rows, w=520):
    """Sheet 8. The middle half of completed work per category, against the
    filed figure. Endpoints are the quartiles; the orange dot is the median.
    This is the size of the question — never a forecast."""
    x0 = 170
    right = max(_w(f"median {r[3]}", 10) for r in rows) + 12
    x1 = w - right
    rowh, top = 26, 20
    mx = max(r[-1] for r in rows)
    h = top + rowh * len(rows) + 46

    def px(v):
        return x0 + (v / mx) * (x1 - x0)

    b = _t(0, 11, "THE MIDDLE HALF OF COMPLETED WORK", 10, SLATE, "bold", ls="0.08em")
    for i, (name, lo, med, med_label, hi) in enumerate(rows):
        y = top + i * rowh + 10
        b += _t(0, y + 4, name, 10, INK, "bold")
        b += f'<line x1="{px(lo):.1f}" y1="{y}" x2="{px(hi):.1f}" y2="{y}" stroke="{NAVY}" stroke-width="2"/>'
        for v in (lo, hi):
            b += (f'<circle cx="{px(v):.1f}" cy="{y}" r="3.4" fill="#fff" '
                  f'stroke="{NAVY}" stroke-width="1.6"/>')
        b += (f'<circle cx="{px(med):.1f}" cy="{y}" r="4.2" fill="{SUNRISE}" '
              f'stroke="#fff" stroke-width="1.4"/>')
        b += _t(w, y + 4, f"median {med_label}", 10, INK, anchor="end")
    b += f'<line x1="0" y1="{h-34}" x2="{w}" y2="{h-34}" stroke="{HAIR}"/>'
    for j, line in enumerate(_wrap(
            "Quartiles of 533 completed ERA engagements applied to your filed figures. "
            "Not an estimate of what would be recovered here.", 10, w)):
        b += _t(0, h - 20 + j * 14, line, 10, SLATE)
    return _svg(w, h, b)


def process_path(stages, w=520, note=None, mark_last=False, title=None):
    """Sheets 10, 11, 13, 15. A sequence of stages. One orange marker at most,
    on the stage that carries the commercial point."""
    n = len(stages)
    gap = 7
    bw = (w - gap * (n - 1)) / n
    top = 18 if title else 4
    wrapped = [_wrap(s, 10, bw - 12, bold=True) for s in stages]
    bh = 16 + 13 * max(len(x) for x in wrapped)
    h = top + bh + (26 if note else 8)
    b = _t(0, 11, title, 10, SLATE, "bold", ls="0.08em") if title else ""
    for i, lines in enumerate(wrapped):
        x = i * (bw + gap)
        last = mark_last and i == n - 1
        b += (f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{bh}" fill="{MIST}" '
              f'stroke="{SUNRISE if last else HAIR}" stroke-width="{1.6 if last else 1}" rx="2"/>')
        b += f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="2.4" fill="{SUNRISE if last else NAVY}"/>'
        for j, line in enumerate(lines):
            b += _t(x + 6, top + 18 + j * 13, line, 10, INK, "bold")
        if i < n - 1:
            cx = x + bw + gap / 2
            b += (f'<path d="M{cx-2.4:.1f} {top+bh/2-3.2} l3.2 3.2 l-3.2 3.2" fill="none" '
                  f'stroke="{SLATE}" stroke-width="1.3"/>')
    if note:
        b += _t(0, h - 6, note, 10, SLATE)
    return _svg(w, h, b)


def evidence_bridge(layers, w=520):
    """Sheet 12. Nine layers. The four we hold before we meet are filled; the
    five built with the client are outlined. The point of the page is that the
    empty ones are shown empty.

    It used to be nine chips in a row, each carrying the layer name truncated to
    nine characters at 7.2pt. Nine names cannot go across 520pt at the 10pt floor
    — so the chart turns, the names come back whole, and nothing is abbreviated
    to make a typographic rule fit.
    """
    rowh, top = 22, 16
    barx = 196
    barw = w - barx
    split = sum(1 for _, p in layers if p)
    h = top + rowh * len(layers) + 46
    b = _t(0, 10, "BEFORE WE MEET", 10, NAVY, "bold", ls="0.08em")
    for i, (name, present) in enumerate(layers):
        y = top + i * rowh
        if i == split:
            b += f'<line x1="0" y1="{y-6}" x2="{w}" y2="{y-6}" stroke="{SLATE}" stroke-width="1.2" stroke-dasharray="3 3"/>'
            b += _t(0, y + 5, "BUILT WITH YOU", 10, SLATE, "bold", ls="0.08em")
            continue
        b += _t(0, y + 13, name, 10, INK if present else SLATE, "bold")
        b += (f'<rect x="{barx}" y="{y+3}" width="{barw:.1f}" height="13" '
              f'fill="{NAVY if present else MIST}" stroke="{NAVY}" '
              f'stroke-width="{0 if present else 1}" rx="2"/>')
        b += _t(barx + 8, y + 13, "HELD" if present else "EMPTY UNTIL WE MEET", 10,
                "#fff" if present else NAVY, "bold", ls="0.06em")
    b += f'<line x1="0" y1="{h-26}" x2="{w}" y2="{h-26}" stroke="{HAIR}"/>'
    b += _t(0, h - 10, "Four layers carry something for this organization. "
                       "Five are empty, and are shown empty.", 10, SLATE)
    return _svg(w, h, b)


def outcome_branch(stages, outcomes, footer, w=520):
    """Sheet 13. The path branches only at the end, into two equal outcomes —
    because validating the current arrangement is a real result, not a failure."""
    n = len(stages)
    gap = 7
    bw = (w - gap * (n - 1)) / n
    top = 4
    swrap = [_wrap(s, 10, bw - 10, bold=True) for s in stages]
    bh = 14 + 13 * max(len(x) for x in swrap)
    ow = (w - 14) / 2
    owrap = [_wrap(sub, 10, ow - 26) for _, sub in outcomes]
    oh = 24 + 14 * max(len(x) for x in owrap)
    by = top + bh + 30
    h = by + oh + 28
    b = ""
    for i, lines in enumerate(swrap):
        x = i * (bw + gap)
        b += f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{bh}" fill="{MIST}" stroke="{HAIR}" rx="2"/>'
        b += f'<rect x="{x:.1f}" y="{top}" width="{bw:.1f}" height="2.4" fill="{NAVY}"/>'
        y0 = top + bh / 2 - (len(lines) - 1) * 6.5 + 4
        for j, line in enumerate(lines):
            b += _t(x + bw / 2, y0 + j * 13, line, 10, INK, "bold", "middle")
        if i < n - 1:
            cx = x + bw + gap / 2
            b += (f'<path d="M{cx-2.4:.1f} {top+bh/2-3.2} l3.2 3.2 l-3.2 3.2" fill="none" '
                  f'stroke="{SLATE}" stroke-width="1.3"/>')
    b += (f'<path d="M{w/2:.1f} {top+bh} v10 M{ow/2:.1f} {top+bh+10} H{w-ow/2:.1f} '
          f'M{ow/2:.1f} {top+bh+10} v10 M{w-ow/2:.1f} {top+bh+10} v10" '
          f'stroke="{SLATE}" fill="none" stroke-width="1.2"/>')
    for i, (head, _sub) in enumerate(outcomes):
        x = i * (ow + 14)
        b += (f'<rect x="{x:.1f}" y="{by}" width="{ow:.1f}" height="{oh}" fill="#FEF4E2" '
              f'stroke="#F0D8A6" rx="2"/>')
        b += f'<rect x="{x:.1f}" y="{by}" width="3" height="{oh}" fill="{SUNRISE}"/>'
        b += _t(x + 13, by + 18, head, 11, NAVY, "bold")
        for j, line in enumerate(owrap[i]):
            b += _t(x + 13, by + 34 + j * 14, line, 10, SLATE)
    b += _t(w / 2, h - 7, footer, 10, NAVY, "bold", "middle")
    return _svg(w, h, b)


def proof_strip(items, w=520):
    """Sheets 5, 12, 15. Never more than once on a sheet."""
    n = len(items)
    seg = w / n
    wrapped = [_wrap(lab.upper(), 10, seg - 16, bold=True) for _, lab in items]
    rows = max(len(x) for x in wrapped)
    h = 22 + 14 * rows
    b = f'<line x1="0" y1="0" x2="{w}" y2="0" stroke="{HAIR}"/>'
    for i, (fig, _lab) in enumerate(items):
        x = seg * i + seg / 2
        b += _t(x, 16, fig, 12, NAVY, "bold", "middle")
        for j, line in enumerate(wrapped[i]):
            b += _t(x, 30 + j * 14, line, 10, SLATE, "bold", "middle", ls="0.06em")
        if i:
            b += f'<line x1="{seg*i:.1f}" y1="5" x2="{seg*i:.1f}" y2="{h-4}" stroke="{HAIR}"/>'
    return _svg(w, h, b)
