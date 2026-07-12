"""Optimizer Assurance Lab — the growth / A/B surface of the platform.

  GET /optimizer — business-facing dashboard: every proposed A/B test across both
                   tenants, adversarially fact-checked, ranked by *realistic* KPI lift,
                   and wired to the truth-bounded bandit. The same assurance discipline
                   that proves the Gate, applied to the optimizer's own copy proposals.

Static research output (swarm run wf_232c4b39-b48); see docs/AB-TEST-OPPORTUNITIES.md.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.context import ctx
from app.server import app, templates
from pipeline.personalization import demo_sim


@app.get("/optimizer", response_class=HTMLResponse)
def optimizer(request: Request):
    m = demo_sim.build()
    return templates.TemplateResponse(request, "optimizer.html", {
        "scenarios": m["scenarios"], "note": m["note"]})


@app.get("/api/optimizer/live")
def optimizer_live() -> JSONResponse:
    """Live posteriors moving from REAL /site traffic — the online counterpart to the
    simulated campaign above. Settles overdue impressions first so no-clicks count."""
    c = ctx()
    c.live.settle()
    return JSONResponse(c.live.snapshot())


@app.post("/api/optimizer/live/settle")
def optimizer_live_settle() -> JSONResponse:
    """Resolve impressions with no click as reward-0 (the bandit's negative evidence)."""
    return JSONResponse({"settled": ctx().live.settle()})


@app.get("/api/optimizer/lift")
def optimizer_lift() -> JSONResponse:
    """Measured lift: CTR of the adaptive (bandit) slice vs the random (control) holdout.
    This is the bandit proving it beats random serving on REAL traffic, not just asserting it."""
    c = ctx()
    c.live.settle()
    return JSONResponse(c.live.lift_report())
