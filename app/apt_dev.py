"""/apt/dev — "Preview as visitor" (W8-A): identity + entry simulation.

  GET /apt/dev — pick an identity and an entry channel, open the live page as
                 that visitor. Console links live in the apt sidebar, not here.

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
