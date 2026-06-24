"""Optimizer Assurance Lab — the growth / A/B surface of the platform.

  GET /optimizer — business-facing dashboard: every proposed A/B test across both
                   tenants, adversarially fact-checked, ranked by *realistic* KPI lift,
                   and wired to the truth-bounded bandit. The same assurance discipline
                   that proves the Gate, applied to the optimizer's own copy proposals.

Static research output (swarm run wf_232c4b39-b48); see docs/AB-TEST-OPPORTUNITIES.md.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates


@app.get("/optimizer", response_class=HTMLResponse)
def optimizer(request: Request):
    return templates.TemplateResponse(request, "optimizer.html", {})
