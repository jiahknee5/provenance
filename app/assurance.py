"""The Assurance dashboard — evaluate the entire Provenance workflow.

  GET /assurance              — metrics-over-time + workflow Assurance Lab + golden evals
                                (per step, table: inputs | graph log | output) + lifecycle eval
  GET /api/observe/golden     — the golden eval suite (per-step cases + graph logs)
  GET /api/observe/history    — the over-time metrics history (one entry per run)

Reads persisted artifacts (decision R5: live = deterministic seeded replay).
"""
from __future__ import annotations

import json

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.charts import calibration, grouped_bars
from app.server import app, templates
from pipeline.common.config import DATA_DIR, OBSERVE_DIR, RUNS_DIR

EVAL_HISTORY = DATA_DIR / "eval_history.jsonl"


def _load(name: str, d=None):
    p = OBSERVE_DIR / name
    if not p.exists():
        p = RUNS_DIR / name
    return json.loads(p.read_text()) if p.exists() else d


def _history() -> list[dict]:
    if not EVAL_HISTORY.exists():
        return []
    return [json.loads(line) for line in EVAL_HISTORY.read_text().splitlines() if line.strip()]


@app.get("/assurance", response_class=HTMLResponse)
def assurance(request: Request):
    golden = _load("golden_evals.json")
    if not golden:
        return templates.TemplateResponse(request, "assurance.html", {"empty": True})

    a = _load("assurance.json", {})
    bars_svg = cal_svg = ""
    if a:
        types = list(a["gate"]["by_type"].keys())
        bars_svg = grouped_bars([t.replace("_", " ") for t in types],
                                [a["gate"]["by_type"][t] for t in types],
                                [a["baseline"]["by_type"].get(t, 0.0) for t in types])
        cal_svg = calibration(a["reliability_bins"])

    return templates.TemplateResponse(request, "assurance.html", {
        "empty": False, "golden": golden, "lifecycle": golden.get("lifecycle"),
        "assurance": a, "bars_svg": bars_svg, "cal_svg": cal_svg,
        "history": _history(), "meta": _load("meta.json", {}),
        "topology": _load("topology.json", {}),
    })


@app.get("/api/observe/golden")
def api_golden():
    return JSONResponse(_load("golden_evals.json") or {"empty": True})


@app.get("/api/observe/history")
def api_history():
    return JSONResponse({"history": _history()})
