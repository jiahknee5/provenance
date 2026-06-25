"""Showcase — the live-demo gallery and each use case's two sister pages.

  GET /showcase                       — index: Live demo + the four Use cases
  GET /showcase/{slug}[/production]    — the gated version that ships vs the ungated one blocked
  GET /showcase/{slug}/observability   — like the live demo: inputs, decisions, provenance, trace

Firmographic use cases (gauntletai, skyfi) accept ?industry/?region/?ip to preview any visitor.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.context import ctx
from app.server import app, templates
from pipeline.personalization import scene as SC
from pipeline.personalization import showcase as SH


def _404():
    return HTMLResponse("<h2 style='font:16px sans-serif;padding:24px'>Unknown use case.</h2>", status_code=404)


def _resolve(request: Request, slug: str, industry: str, region: str, ip: str):
    det = SC.detect(request)
    company, city = det.get("company"), det.get("city")
    reg = region or det.get("region")
    ind = industry or det.get("industry") or SH.DEMOS[slug].default_industry or "general"
    detected = bool(det.get("region")) and not (region or industry)
    if ip:
        rv = SC.resolve_ip(ip)
        reg, ind = rv.get("region") or reg, rv.get("industry") or ind
        company, city = rv.get("company") or company, rv.get("city") or city
        rv["request_signals"] = det.get("request_signals", [])
        det, detected = rv, True
    return det, {"region": reg, "industry": ind, "company": company, "city": city, "detected": detected}


def _view_model(request: Request, slug: str, industry: str, region: str, ip: str) -> dict:
    kind = SH.DEMOS[slug].kind
    if kind == "firmographic":
        det, octx = _resolve(request, slug, industry, region, ip)
        return SH.build_view(slug, det=det, octx=octx)
    if kind == "known":
        c = ctx()
        return SH.build_view(slug, gate=c.gate, library=c.library)
    return SH.build_view(slug)


@app.get("/showcase", response_class=HTMLResponse)
def showcase(request: Request):
    return templates.TemplateResponse(request, "showcase.html", {"demos": [SH.DEMOS[s] for s in SH.ORDER]})


@app.get("/showcase/{slug}", response_class=HTMLResponse)
@app.get("/showcase/{slug}/production", response_class=HTMLResponse)
def showcase_production(request: Request, slug: str, v: str = "gated",
                       industry: str = "", region: str = "", ip: str = ""):
    if slug not in SH.DEMOS:
        return _404()
    vm = _view_model(request, slug, industry, region, ip)
    version = "ungated" if v == "ungated" else "gated"   # the full page shown to the end visitor
    return templates.TemplateResponse(request, "use_case.html", {
        **vm, "view": "production", "version": version, "slug": slug,
        "industries": SC.INDUSTRIES, "states": SC.STATES})


@app.get("/showcase/{slug}/observability", response_class=HTMLResponse)
def showcase_observability(request: Request, slug: str, industry: str = "", region: str = "", ip: str = ""):
    if slug not in SH.DEMOS:
        return _404()
    vm = _view_model(request, slug, industry, region, ip)
    return templates.TemplateResponse(request, "use_case.html", {
        **vm, "view": "observability", "slug": slug, "industries": SC.INDUSTRIES, "states": SC.STATES})
