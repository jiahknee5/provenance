"""The super-personalization channel — every signal a site could use, with its provenance.

  GET /personalize?tier=&mode=   — the personalized page (tasteful|creepy) at a data tier
                                    (anonymous → returning → email → google → broker → crm →
                                    everything), plus the full provenance ledger.
  GET /api/personalize           — the same render as JSON.

Pure render off pipeline.personalization (deterministic, one synthetic persona). No DB, no
network, no run artifact needed — it computes on load, which is the whole point: "what could
this site know the instant it loads, and where would each fact come from?"
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.server import app, templates
from pipeline.personalization import render


@app.get("/personalize", response_class=HTMLResponse)
def personalize(request: Request, tier: str = "anonymous", mode: str = "tasteful"):
    data = render.build(tier, mode)
    return templates.TemplateResponse(request, "personalize.html", data)


@app.get("/api/personalize")
def api_personalize(tier: str = "anonymous", mode: str = "tasteful"):
    return JSONResponse(render.build(tier, mode))
