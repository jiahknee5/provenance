"""Visitor demo tour sitemap — curated entry paths into Gauntlet + Planet replicas.

  GET /apt/demo — tenant picker + four channel tiles per site (Ads, Direct, Email, Search)

Query params: none required. Channel galleries link to existing ad routes or Phase 2
/direct and /email galleries; search links straight to ?ref=google on the replica.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.personalization import demo_nav as NAV


@app.get("/apt/demo", response_class=HTMLResponse)
def apt_demo_sitemap(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "apt_demo_sitemap.html", {**NAV.build_sitemap_view(request), "demo_flow_active": "start"})
