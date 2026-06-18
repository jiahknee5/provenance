"""Tiny dependency-free SVG chart helpers — keeps the inspector fully offline (no CDN)."""
from __future__ import annotations


def line_chart(series: list[dict], w: int = 640, h: int = 240, pad: int = 34,
               ylabel: str = "") -> str:
    """series: [{label, color, points:[y,...]}]. x is the index."""
    maxy = max((max(s["points"]) for s in series if s["points"]), default=1.0) or 1.0
    n = max((len(s["points"]) for s in series), default=1)

    def xy(i, y, npts):
        x = pad + (i / max(npts - 1, 1)) * (w - 2 * pad)
        yy = (h - pad) - (y / maxy) * (h - 2 * pad)
        return f"{x:.1f},{yy:.1f}"

    polylines, legend = [], []
    for k, s in enumerate(series):
        pts = " ".join(xy(i, y, len(s["points"])) for i, y in enumerate(s["points"]))
        polylines.append(f'<polyline fill="none" stroke="{s["color"]}" stroke-width="2.5" points="{pts}"/>')
        ly = 16 + k * 18
        legend.append(f'<rect x="{w-160}" y="{ly-9}" width="12" height="12" fill="{s["color"]}"/>'
                      f'<text x="{w-144}" y="{ly+1}" font-size="12" fill="#16202c">{s["label"]}</text>')
    axes = (f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#cbd5dd"/>'
            f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h-pad}" stroke="#cbd5dd"/>'
            f'<text x="{pad}" y="{pad-10}" font-size="11" fill="#5b6b7c">{ylabel}</text>'
            f'<text x="{pad}" y="{h-12}" font-size="11" fill="#5b6b7c">0</text>'
            f'<text x="{w-pad-30}" y="{h-12}" font-size="11" fill="#5b6b7c">send #</text>')
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
        bars.append(f'<rect x="{x0+bw*0.18:.1f}" y="{h-pad-gh:.1f}" width="{bw*0.28:.1f}" height="{gh:.1f}" fill="#0e7c86"/>')
        bars.append(f'<rect x="{x0+bw*0.52:.1f}" y="{h-pad-bh:.1f}" width="{bw*0.28:.1f}" height="{bh:.1f}" fill="#d98a16"/>')
        labels.append(f'<text x="{x0+bw*0.5:.1f}" y="{h-pad+14}" font-size="10" fill="#5b6b7c" text-anchor="middle">{c}</text>')
    legend = ('<rect x="46" y="10" width="12" height="12" fill="#0e7c86"/><text x="62" y="20" font-size="12">Gate</text>'
              '<rect x="120" y="10" width="12" height="12" fill="#d98a16"/><text x="136" y="20" font-size="12">single judge</text>')
    axis = f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#cbd5dd"/>'
    return f'<svg viewBox="0 0 {w} {h}" width="100%" style="max-width:{w}px">{axis}{"".join(bars)}{"".join(labels)}{legend}</svg>'


def calibration(bins: list[dict], w: int = 240, h: int = 240, pad: int = 30) -> str:
    def xy(px, py):
        return f"{pad + px*(w-2*pad):.1f},{(h-pad) - py*(h-2*pad):.1f}"
    diag = f'<line x1="{xy(0,0).split(",")[0]}" y1="{xy(0,0).split(",")[1]}" x2="{xy(1,1).split(",")[0]}" y2="{xy(1,1).split(",")[1]}" stroke="#cbd5dd" stroke-dasharray="4"/>'
    pts = [b for b in bins if b.get("accuracy") is not None]
    dots = "".join(f'<circle cx="{xy(b["conf_mid"], b["accuracy"]).split(",")[0]}" '
                   f'cy="{xy(b["conf_mid"], b["accuracy"]).split(",")[1]}" r="4" fill="#0e7c86"/>' for b in pts)
    line = ('<polyline fill="none" stroke="#0e7c86" stroke-width="2" points="'
            + " ".join(xy(b["conf_mid"], b["accuracy"]) for b in pts) + '"/>') if len(pts) > 1 else ""
    box = f'<rect x="{pad}" y="{pad}" width="{w-2*pad}" height="{h-2*pad}" fill="none" stroke="#cbd5dd"/>'
    labels = (f'<text x="{pad}" y="{h-8}" font-size="10" fill="#5b6b7c">conf →</text>'
              f'<text x="6" y="{pad+6}" font-size="10" fill="#5b6b7c">acc</text>')
    return f'<svg viewBox="0 0 {w} {h}" width="{w}">{box}{diag}{line}{dots}{labels}</svg>'
