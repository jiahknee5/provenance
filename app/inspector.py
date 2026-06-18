"""The demo inspector — the watchable surface that ties the five modules together.

Reads only persisted artifacts from data/demo/runs/ (so it works after a crash / from a
recorded run) and renders: claim-ledger lights, the regret contrast (constrained vs the
unconstrained twin), the blocked-lie panel, the drift event log, and the Assurance Lab.
"""
from __future__ import annotations

import json

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.charts import calibration, grouped_bars, line_chart
from app.server import app, templates
from pipeline.common.config import RUNS_DIR


def _load(name: str, default=None):
    p = RUNS_DIR / name
    return json.loads(p.read_text()) if p.exists() else default


@app.get("/inspector", response_class=HTMLResponse)
def inspector(request: Request):
    summary = _load("summary.json")
    if not summary:
        return templates.TemplateResponse(request, "inspector_empty.html", {})

    c1 = _load("campaign_c1_email.json")
    twin = _load("campaign_twin_email.json")
    drift = _load("drift_campaign_transition.json")
    assurance = _load("assurance.json")
    pool = _load("pool_report.json") or []
    ledgers = _load("ledgers.json") or {}

    regret_svg = line_chart([
        {"label": "constrained (verified only)", "color": "#0e7c86", "points": c1["regret_curve"]},
        {"label": "unconstrained (lie allowed)", "color": "#d23b3b", "points": twin["regret_curve"]},
    ], ylabel="cumulative regret")

    types = list(assurance["gate"]["by_type"].keys())
    bars_svg = grouped_bars(
        [t.replace("_", " ") for t in types],
        [assurance["gate"]["by_type"][t] for t in types],
        [assurance["baseline"]["by_type"].get(t, 0.0) for t in types])
    cal_svg = calibration(assurance["reliability_bins"])

    seg_contrast = []
    for seg in sorted(c1["per_segment"]):
        honest = c1["per_segment"][seg]["winner"]
        honest_arm = honest.split("__")[-1]
        ctr = c1["per_segment"][seg]["arms"][honest]["posterior_mean"]
        seg_contrast.append({"segment": seg, "honest_arm": honest_arm, "honest_ctr": ctr,
                             "twin_winner": "LIE" if twin["per_segment"][seg]["winner_is_lie"] else "honest"})

    blocked = [r for r in pool if r["planted_lie"]]

    return templates.TemplateResponse(request, "inspector.html", {
        "s": summary, "regret_svg": regret_svg, "bars_svg": bars_svg, "cal_svg": cal_svg,
        "seg_contrast": seg_contrast, "drift": drift, "assurance": assurance,
        "ledgers": ledgers, "spotlight": ledgers.get("_spotlight"),
        "blocked_count": len(blocked),
    })
