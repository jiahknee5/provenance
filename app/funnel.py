"""The funnel dashboard — every way a customer enters, what's captured, and who may use it.

  GET /funnel            — the funnel paths + a walked journey + the two personalization
                           views (1:1 rep vs mass) + the surface-policy invariant
  GET /api/observe/funnel— the funnel report json

Reads the persisted funnel.json (produced by scripts.trace / scripts.funnel_evals).
"""
from __future__ import annotations

import json

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.server import app, templates
from pipeline.common.config import OBSERVE_DIR


def _load():
    p = OBSERVE_DIR / "funnel.json"
    return json.loads(p.read_text()) if p.exists() else None


@app.get("/funnel", response_class=HTMLResponse)
def funnel_dashboard(request: Request):
    rep = _load()
    if not rep:
        return templates.TemplateResponse(request, "funnel.html", {"empty": True})
    return templates.TemplateResponse(request, "funnel.html", {"empty": False, "r": rep})


@app.get("/api/observe/funnel")
def api_funnel():
    return JSONResponse(_load() or {"empty": True})
