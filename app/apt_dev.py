"""Unified personalization console hub — one entry for Gauntlet + Planet /dev surfaces.

  GET /apt/dev — site picker at top; links into each tenant's existing consoles
                 (/gauntletapt/dev, /planetapt/dev, etc.) without replacing them.

Query params:
  site=gauntlet|planet  — which demo (default gauntlet)
  as=anon|known         — identity preview for console deep-links
  (other params)        — forwarded to live replica + console links
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.personalization import apt_dev_hub as HUB


@app.get("/apt/dev", response_class=HTMLResponse)
def apt_dev_hub(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "apt_dev_hub.html", HUB.build_hub_view(request))
