"""The Playbook — how images & copy are made (marketer-facing, real config).

  GET /apt/playbook — apt-shell help surface; ?site= tenant-aware like /costs.
                      Chapters: #images, #copy, #motion (future release), #aeo
                      (roadmap / point of view). View model built by
                      pipeline/personalization/playbook.py from the same YAML the
                      engine reads — the page cannot drift from the product.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.personalization import playbook as PBK


@app.get("/apt/playbook", response_class=HTMLResponse)
def apt_playbook(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "apt_playbook.html",
                                      PBK.build_playbook_view(request))
