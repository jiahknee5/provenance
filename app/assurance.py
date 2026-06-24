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

from app.server import app, templates
from pipeline.common.config import DATA_DIR, OBSERVE_DIR, RUNS_DIR
from pipeline.personalization import demo_scenarios as DS
from pipeline.personalization import demo_sim

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
    """Minimalist trust surface that monitors Drift (R26): one trust score + the live
    drift watch + the hallucination/overclaim guard — quiet cards in the new shell."""
    m = demo_sim.build()
    h = m["health"]
    golden = _load("golden_evals.json", {})
    catch = h["hallucination"]["trap_catch_rate"]
    if catch is None and golden.get("summary"):
        s = golden["summary"]
        catch = round(100 * s.get("passed", 0) / max(s.get("total", 1), 1), 1)

    # composite trust score: provenance coverage, no-hold-in-copy, ungated-never-selected, traps
    parts = [h["provenance"]["coverage_pct"],
             100 if not h["provenance"]["hold_in_copy"] else 0,
             100 if h["hallucination"]["selected"] == 0 else 0,
             catch if catch is not None else 100]
    trust = round(sum(parts) / len(parts))

    # drift watch — every TTL-governed (bought/enrich/broker) fact, its source + status
    drift_rows = []
    for s in DS.SCENARIOS:
        for v in DS.gated_variants(s):
            for d in v.data_used:
                if d.source in (DS.BOUGHT, DS.ENRICH, DS.BROKER):
                    drift_rows.append({"signal": d.signal, "source": d.source_label,
                                       "variant": v.label, "status": "fresh"})

    return templates.TemplateResponse(request, "assurance.html", {
        "trust": trust, "h": h, "catch": catch, "drift_rows": drift_rows,
    })


@app.get("/api/observe/golden")
def api_golden():
    return JSONResponse(_load("golden_evals.json") or {"empty": True})


@app.get("/api/observe/history")
def api_history():
    return JSONResponse({"history": _history()})
