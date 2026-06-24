"""Dependency-free inline-SVG chart helpers — keeps every surface fully offline (no CDN,
no JS chart library). Colours reference quiet.css design tokens via inline
``style="fill:var(--g)"`` so the charts stay on-brand ("colour only in product data") and
adapt with the design system instead of hard-coding hexes.

``wilson_ci`` lives here too so confidence intervals are COMPUTED from real counts and never
hand-typed into a template (CONSTITUTION Article I — a number the code can't substantiate is
a bug). Every chart takes already-real values; nothing here invents data.
"""
from __future__ import annotations

import math

_FNUM = "font-variant-numeric:tabular-nums"
_MONO = "font-family:ui-monospace,'SF Mono',Menlo,monospace;font-variant-numeric:tabular-nums"


# --------------------------------------------------------------------------- #
# numeric helper — so CIs are computed, never hand-typed
# --------------------------------------------------------------------------- #
def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial rate k/n, so a saturated rate is never naked.
    (37,37)->(.906,1.0) · (9,37)->(.134,.401) · (0,10)->(0.0,.278)."""
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3))


# --------------------------------------------------------------------------- #
# existing helpers (token-corrected; still used by inspector.py)
# --------------------------------------------------------------------------- #
def line_chart(series: list[dict], w: int = 640, h: int = 240, pad: int = 34,
               ylabel: str = "") -> str:
    """series: [{label, color, points:[y,...]}]. x is the index."""
    maxy = max((max(s["points"]) for s in series if s["points"]), default=1.0) or 1.0

    def xy(i, y, npts):
        x = pad + (i / max(npts - 1, 1)) * (w - 2 * pad)
        yy = (h - pad) - (y / maxy) * (h - 2 * pad)
        return f"{x:.1f},{yy:.1f}"

    polylines, legend = [], []
    for k, s in enumerate(series):
        pts = " ".join(xy(i, y, len(s["points"])) for i, y in enumerate(s["points"]))
        polylines.append(f'<polyline fill="none" stroke="{s["color"]}" stroke-width="2.5" points="{pts}"/>')
        ly = 16 + k * 18
        legend.append(f'<rect x="{w-180}" y="{ly-9}" width="12" height="12" fill="{s["color"]}"/>'
                      f'<text x="{w-164}" y="{ly+1}" font-size="12" style="fill:var(--ink)">{s["label"]}</text>')
    axes = (f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" style="stroke:var(--hairline)"/>'
            f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h-pad}" style="stroke:var(--hairline)"/>'
            f'<text x="{pad}" y="{pad-10}" font-size="11" style="fill:var(--muted)">{ylabel}</text>'
            f'<text x="{pad}" y="{h-12}" font-size="11" style="fill:var(--muted)">0</text>'
            f'<text x="{w-pad-30}" y="{h-12}" font-size="11" style="fill:var(--muted)">send #</text>')
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">'
            f'{axes}{"".join(polylines)}{"".join(legend)}</svg>')


def grouped_bars(cats: list[str], gate: list[float], base: list[float],
                 w: int = 640, h: int = 240, pad: int = 36) -> str:
    n = len(cats)
    bw = (w - 2 * pad) / max(n, 1)
    bars, labels = [], []
    for i, c in enumerate(cats):
        x0 = pad + i * bw
        gh = gate[i] * (h - 2 * pad)
        bh = base[i] * (h - 2 * pad)
        bars.append(f'<rect x="{x0+bw*0.18:.1f}" y="{h-pad-gh:.1f}" width="{bw*0.28:.1f}" height="{gh:.1f}" style="fill:var(--g)"/>')
        bars.append(f'<rect x="{x0+bw*0.52:.1f}" y="{h-pad-bh:.1f}" width="{bw*0.28:.1f}" height="{bh:.1f}" style="fill:var(--a)"/>')
        labels.append(f'<text x="{x0+bw*0.5:.1f}" y="{h-pad+14}" font-size="10" style="fill:var(--muted)" text-anchor="middle">{c}</text>')
    legend = ('<rect x="46" y="10" width="12" height="12" style="fill:var(--g)"/><text x="62" y="20" font-size="12" style="fill:var(--muted)">Gate</text>'
              '<rect x="120" y="10" width="12" height="12" style="fill:var(--a)"/><text x="136" y="20" font-size="12" style="fill:var(--muted)">single judge</text>')
    axis = f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" style="stroke:var(--hairline)"/>'
    return f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">{axis}{"".join(bars)}{"".join(labels)}{legend}</svg>'


def calibration(bins: list[dict], w: int = 240, h: int = 240, pad: int = 30) -> str:
    """Legacy polyline calibration kept for inspector.py. For the decisive verifier use
    reliability() instead (no polyline through empty bins)."""
    def xy(px, py):
        return f"{pad + px*(w-2*pad):.1f},{(h-pad) - py*(h-2*pad):.1f}"
    diag = (f'<line x1="{xy(0,0).split(",")[0]}" y1="{xy(0,0).split(",")[1]}" '
            f'x2="{xy(1,1).split(",")[0]}" y2="{xy(1,1).split(",")[1]}" style="stroke:var(--border)" stroke-dasharray="4"/>')
    pts = [b for b in bins if b.get("accuracy") is not None]
    dots = "".join(f'<circle cx="{xy(b["conf_mid"], b["accuracy"]).split(",")[0]}" '
                   f'cy="{xy(b["conf_mid"], b["accuracy"]).split(",")[1]}" r="4" style="fill:var(--g)"/>' for b in pts)
    line = ('<polyline fill="none" style="stroke:var(--g);stroke-width:2" points="'
            + " ".join(xy(b["conf_mid"], b["accuracy"]) for b in pts) + '"/>') if len(pts) > 1 else ""
    box = f'<rect x="{pad}" y="{pad}" width="{w-2*pad}" height="{h-2*pad}" fill="none" style="stroke:var(--hairline)"/>'
    labels = (f'<text x="{pad}" y="{h-8}" font-size="10" style="fill:var(--muted)">conf →</text>'
              f'<text x="6" y="{pad+6}" font-size="10" style="fill:var(--muted)">acc</text>')
    return f'<svg viewBox="0 0 {w} {h}" width="{w}">{box}{diag}{line}{dots}{labels}</svg>'


# --------------------------------------------------------------------------- #
# Assurance dashboard charts (all values are real; see app/assurance.py)
# --------------------------------------------------------------------------- #
def operating_point(points: list[dict], *, w: int = 430, h: int = 300,
                    xmax: float = 0.35, pad: int = 46) -> str:
    """ROC-style operating-point scatter. points=[{label, fr, catch, catch_lo, catch_hi,
    fr_hi?, color}]. Two real points only — NO interpolated curve (no threshold sweep exists)."""
    x0, y0, x1, y1 = pad, h - pad, w - 16, 20

    def X(fr):
        return x0 + (fr / xmax) * (x1 - x0)

    def Y(c):
        return y0 - c * (y0 - y1)

    s = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">']
    s.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" style="stroke:var(--border)"/>')
    s.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" style="stroke:var(--border)"/>')
    for t in (0, .25, .5, .75, 1):
        yy = Y(t)
        s.append(f'<line x1="{x0-3}" y1="{yy:.1f}" x2="{x0}" y2="{yy:.1f}" style="stroke:var(--border)"/>')
        s.append(f'<text x="{x0-6}" y="{yy+3:.1f}" font-size="9.5" text-anchor="end" style="fill:var(--label);{_FNUM}">{int(t*100)}</text>')
    for t in (0, .1, .2, .3):
        xx = X(t)
        s.append(f'<line x1="{xx:.1f}" y1="{y0}" x2="{xx:.1f}" y2="{y0+3}" style="stroke:var(--border)"/>')
        s.append(f'<text x="{xx:.1f}" y="{y0+15:.1f}" font-size="9.5" text-anchor="middle" style="fill:var(--label);{_FNUM}">{int(t*100)}</text>')
    # ideal-corner marker (the Gate genuinely sits here): a faint star at the corner, with the
    # 'ideal' annotation pulled to the top-right so it never collides with the Gate dot/label.
    s.append(f'<text x="{X(0):.1f}" y="{Y(1)+5:.1f}" font-size="15" text-anchor="middle" style="fill:var(--border)">&#9733;</text>')
    s.append(f'<text x="{x1}" y="13" text-anchor="end" font-size="9.5" style="fill:var(--label)">&#9733; ideal (0% FR &#183; 100% catch)</text>')
    for p in points:
        cx, cy = X(p["fr"]), Y(p["catch"])
        col = p.get("color", "var(--g)")
        # vertical (catch-rate) Wilson whisker
        s.append(f'<line x1="{cx:.1f}" y1="{Y(p["catch_lo"]):.1f}" x2="{cx:.1f}" y2="{Y(p["catch_hi"]):.1f}" style="stroke:{col};stroke-width:2;opacity:.4"/>')
        for yy in (p["catch_lo"], p["catch_hi"]):
            s.append(f'<line x1="{cx-4:.1f}" y1="{Y(yy):.1f}" x2="{cx+4:.1f}" y2="{Y(yy):.1f}" style="stroke:{col};opacity:.4"/>')
        # horizontal (false-reject) Wilson whisker — so 0/10 isn't read as zero-uncertainty
        if p.get("fr_hi") is not None:
            s.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{X(p["fr_hi"]):.1f}" y2="{cy:.1f}" style="stroke:{col};stroke-width:1.5;opacity:.3"/>')
            s.append(f'<line x1="{X(p["fr_hi"]):.1f}" y1="{cy-4:.1f}" x2="{X(p["fr_hi"]):.1f}" y2="{cy+4:.1f}" style="stroke:{col};opacity:.3"/>')
        s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" style="fill:{col}"/>')
        dy = 16 if (p["fr"] < 0.02 and p["catch"] > 0.98) else 4   # nudge a corner-sitting label clear of the star
        s.append(f'<text x="{cx+12:.1f}" y="{cy+dy:.1f}" font-size="11" style="fill:var(--ink)">{p["label"]}</text>')
    s.append(f'<text x="{(x0+x1)/2:.0f}" y="{h-6}" font-size="10.5" text-anchor="middle" style="fill:var(--muted)">false-reject %  ·  n=10 clean</text>')
    s.append(f'<text transform="translate(13,{(y0+y1)/2:.0f}) rotate(-90)" font-size="10.5" text-anchor="middle" style="fill:var(--muted)">catch-rate %  ·  n=37 traps</text>')
    s.append('</svg>')
    return "".join(s)


def confusion_pair(gate: dict, base: dict, *, w: int = 520, h: int = 232) -> str:
    """Two 2x2 confusion grids side by side (Gate | Single judge). dict={tp,fn,fp,tn} raw counts.
    Always the pair — a lone matrix overstates certainty; the baseline FN cell is the information."""
    cell = 72

    def grid(ox, title, m):
        gx, gy = ox + 60, 46
        out = [f'<text x="{gx+cell}" y="22" font-size="13" text-anchor="middle" style="fill:var(--ink);font-weight:600">{title}</text>',
               f'<text x="{gx+cell/2:.0f}" y="40" font-size="10" text-anchor="middle" style="fill:var(--label)">blocked</text>',
               f'<text x="{gx+cell+cell/2:.0f}" y="40" font-size="10" text-anchor="middle" style="fill:var(--label)">passed</text>',
               f'<text x="{ox+54}" y="{gy+cell/2:.0f}" font-size="10" text-anchor="end" style="fill:var(--label)">trap</text>',
               f'<text x="{ox+54}" y="{gy+cell+cell/2:.0f}" font-size="10" text-anchor="end" style="fill:var(--label)">clean</text>']
        cells = [(0, 0, m["tp"], "tp", "caught"), (1, 0, m["fn"], "fn", "missed"),
                 (0, 1, m["fp"], "fp", "false-rej"), (1, 1, m["tn"], "tn", "correct")]
        for col, row, val, kind, lab in cells:
            x, y = gx + col * cell, gy + row * cell
            if kind in ("tp", "tn"):
                bg, fg = "var(--gbg)", "var(--g)"
            elif val > 0:
                bg, fg = "var(--rbg)", "var(--r)"
            else:
                bg, fg = "var(--fill)", "var(--muted)"
            cx = x + (cell - 5) / 2
            out.append(f'<rect x="{x}" y="{y}" width="{cell-5}" height="{cell-5}" rx="7" style="fill:{bg}"/>')
            out.append(f'<text x="{cx:.0f}" y="{y+(cell-5)/2+2:.0f}" font-size="23" text-anchor="middle" style="fill:{fg};font-weight:600;{_FNUM}">{val}</text>')
            out.append(f'<text x="{cx:.0f}" y="{y+cell-16:.0f}" font-size="9" text-anchor="middle" style="fill:{fg}">{lab}</text>')
        out.append(f'<text x="{gx+cell}" y="{gy+2*cell+14:.0f}" font-size="10" text-anchor="middle" style="fill:var(--label);{_FNUM}">n={sum(m.values())}</text>')
        return "".join(out)

    return (f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">'
            f'{grid(0,"Gate",gate)}{grid(w/2,"Single judge",base)}</svg>')


def lift_bars(rows: list[dict], *, w: int = 580, pad: int = 150, right: int = 64) -> str:
    """Horizontal Gate-vs-single-judge bars. rows=[{label, gate, base, gate_frac, base_frac}]
    (gate/base in 0..1, *_frac like '7/7'). Always two series so the flat Gate row reads as
    CONTRAST against the baseline's holes."""
    rh, top = 50, 26
    h = top + len(rows) * rh + 24
    x0, x1 = pad, w - right
    span = x1 - x0
    s = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">']
    for gx in (0.0, 0.5, 1.0):
        x = x0 + gx * span
        s.append(f'<line x1="{x:.1f}" y1="{top-4}" x2="{x:.1f}" y2="{top+len(rows)*rh-10}" style="stroke:var(--hairline)"/>')
        s.append(f'<text x="{x:.1f}" y="{h-8}" font-size="9.5" text-anchor="middle" style="fill:var(--label);{_FNUM}">{int(gx*100)}%</text>')
    for i, r in enumerate(rows):
        y = top + i * rh
        s.append(f'<text x="0" y="{y+9}" font-size="12" style="fill:var(--ink)">{r["label"]}</text>')
        gw, bw = r["gate"] * span, r["base"] * span
        s.append(f'<rect x="{x0}" y="{y+13}" width="{gw:.1f}" height="13" rx="2" style="fill:var(--g)"/>')
        s.append(f'<text x="{x0+gw+6:.1f}" y="{y+23}" font-size="10.5" style="fill:var(--g);{_FNUM}">{r["gate_frac"]}</text>')
        s.append(f'<rect x="{x0}" y="{y+29}" width="{bw:.1f}" height="13" rx="2" style="fill:var(--a)"/>')
        s.append(f'<text x="{x0+bw+6:.1f}" y="{y+39}" font-size="10.5" style="fill:var(--a);{_FNUM}">{r["base_frac"]}</text>')
    s.append(f'<rect x="{pad}" y="4" width="11" height="11" style="fill:var(--g)"/><text x="{pad+16}" y="13" font-size="11" style="fill:var(--muted)">Gate</text>')
    s.append(f'<rect x="{pad+72}" y="4" width="11" height="11" style="fill:var(--a)"/><text x="{pad+88}" y="13" font-size="11" style="fill:var(--muted)">single judge</text>')
    s.append('</svg>')
    return "".join(s)


def reliability(bins: list[dict], ece: float, *, w: int = 280, h: int = 252, pad: int = 38) -> str:
    """Honest reliability diagram for a DECISIVE verifier: plot only populated bins (dot radius
    ∝ count), ghost the empty ones as 'n=0' on the axis. NO polyline through empty bins."""
    x0, y0, x1, y1 = pad, h - pad, w - 14, 18

    def X(p):
        return x0 + p * (x1 - x0)

    def Y(p):
        return y0 - p * (y0 - y1)

    s = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">']
    s.append(f'<rect x="{x0}" y="{y1}" width="{x1-x0}" height="{y0-y1}" fill="none" style="stroke:var(--hairline)"/>')
    s.append(f'<line x1="{X(0)}" y1="{Y(0)}" x2="{X(1)}" y2="{Y(1)}" style="stroke:var(--border)" stroke-dasharray="4 3"/>')
    populated = 0
    maxc = max((b["count"] for b in bins), default=1) or 1
    for b in bins:
        cx = X(b["conf_mid"])
        if b.get("accuracy") is not None and b["count"] > 0:
            populated += 1
            cy = Y(b["accuracy"])
            r = 4 + 9 * (b["count"] / maxc)
            s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" style="fill:var(--g);opacity:.85"/>')
            s.append(f'<text x="{cx:.1f}" y="{cy-r-3:.1f}" font-size="9" text-anchor="middle" style="fill:var(--muted);{_FNUM}">n={b["count"]}</text>')
        else:
            s.append(f'<line x1="{cx:.1f}" y1="{y0}" x2="{cx:.1f}" y2="{y0-5}" style="stroke:var(--border)"/>')
            s.append(f'<text x="{cx:.1f}" y="{y0+13:.1f}" font-size="8.5" text-anchor="middle" style="fill:var(--label)">n=0</text>')
    s.append(f'<text x="{(x0+x1)/2:.0f}" y="{h-4}" font-size="10" text-anchor="middle" style="fill:var(--muted)">confidence &#8594;</text>')
    s.append(f'<text transform="translate(11,{(y0+y1)/2:.0f}) rotate(-90)" font-size="10" text-anchor="middle" style="fill:var(--muted)">accuracy</text>')
    s.append(f'<text x="{x0}" y="13" font-size="10" style="fill:var(--ink);{_FNUM}">ECE {ece:.3f} &#183; {populated} of {len(bins)} bins</text>')
    s.append('</svg>')
    return "".join(s)


def stability_strip(rows: list[dict], *, w: int = 660, row_h: int = 40) -> str:
    """One mini sparkline per metric, y pinned to a FIXED range (not auto-scaled) so identical
    values render as a true flat line on a reference — flatness = reproducibility, not a trend.
    rows=[{label, points, ymin, ymax, ref, current, color}]."""
    h = len(rows) * row_h + 8
    x0, x1 = 150, w - 150
    s = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">']
    for i, r in enumerate(rows):
        y = i * row_h
        mid = y + row_h / 2
        pts = r["points"]
        n = len(pts)
        rng = (r["ymax"] - r["ymin"]) or 1
        flat = (max(pts) - min(pts) == 0) if pts else True

        def Y(v, y=y, mid=mid, rng=rng, flat=flat):
            if flat:                       # a reproducible flat line sits on its label, not the band top
                return mid
            return (y + row_h - 9) - ((v - r["ymin"]) / rng) * (row_h - 18)

        s.append(f'<text x="0" y="{mid+4:.0f}" font-size="11.5" style="fill:var(--ink)">{r["label"]}</text>')
        refy = Y(r["ref"])
        s.append(f'<line x1="{x0}" y1="{refy:.1f}" x2="{x1}" y2="{refy:.1f}" style="stroke:var(--hairline)" stroke-dasharray="3 3"/>')
        poly = " ".join(f'{x0+(j/max(n-1,1))*(x1-x0):.1f},{Y(v):.1f}' for j, v in enumerate(pts))
        col = r.get("color", "var(--g)")
        s.append(f'<polyline fill="none" style="stroke:{col};stroke-width:2" points="{poly}"/>')
        for j, v in enumerate(pts):
            s.append(f'<circle cx="{x0+(j/max(n-1,1))*(x1-x0):.1f}" cy="{Y(v):.1f}" r="2" style="fill:{col}"/>')
        s.append(f'<text x="{x1+12}" y="{mid+4:.0f}" font-size="11.5" style="fill:var(--slate);{_MONO}">{r["current"]}</text>')
        var = (max(pts) - min(pts)) if pts else 0
        s.append(f'<text x="{w-2}" y="{mid+4:.0f}" font-size="9.5" text-anchor="end" style="fill:var(--g)">{"no change" if var == 0 else "stable"}</text>')
    s.append('</svg>')
    return "".join(s)


def tile_grid(rows: list[str], cols: list[str], cells: list[list], *,
              w: int = 600, cell: int = 30, pad: int = 120) -> str:
    """source × mutation caught/missed heat-grid. cells[i][j] is True (caught), False (missed),
    or None (no trap for that source×mutation — rendered hatched, never green)."""
    gx, gy = pad, 44
    h = gy + len(rows) * cell + 10
    s = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">']
    s.append('<defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             '<line x1="0" y1="0" x2="0" y2="5" style="stroke:var(--border)" stroke-width="1"/></pattern></defs>')
    for j, c in enumerate(cols):
        x = gx + j * cell + cell / 2
        s.append(f'<text x="{x:.0f}" y="36" font-size="9.5" text-anchor="middle" style="fill:var(--label)">{c}</text>')
    for i, rlab in enumerate(rows):
        y = gy + i * cell
        s.append(f'<text x="{gx-8}" y="{y+cell/2+3:.0f}" font-size="10" text-anchor="end" style="fill:var(--slate);{_MONO}">{rlab}</text>')
        for j in range(len(cols)):
            v = cells[i][j]
            x = gx + j * cell
            if v is True:
                bg, mark, mc = "var(--gbg)", "&#10003;", "var(--g)"
            elif v is False:
                bg, mark, mc = "var(--rbg)", "&#10007;", "var(--r)"
            else:
                bg, mark, mc = "url(#hatch)", "", "var(--muted)"
            s.append(f'<rect x="{x+2}" y="{y+2}" width="{cell-4}" height="{cell-4}" rx="4" style="fill:{bg}"/>')
            if mark:
                s.append(f'<text x="{x+cell/2:.0f}" y="{y+cell/2+4:.0f}" font-size="13" text-anchor="middle" style="fill:{mc}">{mark}</text>')
    s.append('</svg>')
    return "".join(s)


def small_multiples_curves(panels: list[dict], *, w: int = 660, h: int = 196,
                           pad: int = 26, gap: int = 18) -> str:
    """3 side-by-side bandit convergence panels sharing y[0,1]. panels=[{title, curves:[{label,
    points, color, dashed}], note}]. The blocked arm is a dashed flat line at 0 (selections=0)."""
    n = len(panels)
    pw = (w - gap * (n - 1)) / n
    s = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">']
    for k, p in enumerate(panels):
        ox = k * (pw + gap)
        x0, x1, y0, y1 = ox + pad, ox + pw - 6, h - 36, 22
        s.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" style="stroke:var(--hairline)"/>')
        s.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" style="stroke:var(--hairline)"/>')
        s.append(f'<text x="{x0-4}" y="{y1+4}" font-size="8.5" text-anchor="end" style="fill:var(--label)">1</text>')
        s.append(f'<text x="{x0-4}" y="{y0+3}" font-size="8.5" text-anchor="end" style="fill:var(--label)">0</text>')
        s.append(f'<text x="{(x0+x1)/2:.0f}" y="14" font-size="11" text-anchor="middle" style="fill:var(--ink);font-weight:600">{p["title"]}</text>')
        for cv in p["curves"]:
            pts = cv["points"]
            m = len(pts)
            off = 2 if cv.get("dashed") else 0   # lift the flat blocked-arm line off the x-axis for legibility
            poly = " ".join(f'{x0+(j/max(m-1,1))*(x1-x0):.1f},{y0-v*(y0-y1)-off:.1f}' for j, v in enumerate(pts))
            dash = ' stroke-dasharray="4 3"' if cv.get("dashed") else ''
            s.append(f'<polyline fill="none" style="stroke:{cv["color"]};stroke-width:2"{dash} points="{poly}"/>')
        s.append(f'<text x="{(x0+x1)/2:.0f}" y="{h-18}" font-size="9" text-anchor="middle" style="fill:var(--muted)">{p["note"]}</text>')
        s.append(f'<text x="{(x0+x1)/2:.0f}" y="{h-5}" font-size="8.5" text-anchor="middle" style="fill:var(--label)">rounds &#8594;</text>')
    s.append('</svg>')
    return "".join(s)
