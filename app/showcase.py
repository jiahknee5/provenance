"""Showcase — the live-demo gallery.

  GET /showcase              — the index: Live demo + the Use cases (real personalized sites).
  GET /showcase/{slug}       — an actual personalized demo website for one use case. Resolves
                               the visitor (reverse-IP) like /demo/live; ?industry=/?region=/?ip=
                               override it to preview what any visitor would get.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.personalization import scene as SC
from pipeline.personalization import showcase as SH


@app.get("/showcase", response_class=HTMLResponse)
def showcase(request: Request):
    return templates.TemplateResponse(request, "showcase.html", {
        "demos": [SH.DEMOS[s] for s in SH.ORDER],
    })


@app.get("/showcase/{slug}", response_class=HTMLResponse)
def showcase_demo(request: Request, slug: str, industry: str = "", region: str = "", ip: str = ""):
    if slug not in SH.DEMOS:
        return HTMLResponse("<h2 style='font:16px sans-serif;padding:24px'>Unknown use case.</h2>",
                            status_code=404)
    det = SC.detect(request)
    company, city = det.get("company"), det.get("city")
    reg = region or det.get("region")
    ind = industry or det.get("industry") or SH.DEMOS[slug].default_industry
    detected = bool(det.get("region")) and not (region or industry)
    if ip:
        rv = SC.resolve_ip(ip)
        reg = rv.get("region") or reg
        ind = rv.get("industry") or ind
        company = rv.get("company") or company
        city = rv.get("city") or city
        detected = True
    data = SH.build(slug, region=reg, industry=ind, company=company, city=city, detected=detected)
    return templates.TemplateResponse(request, "use_case.html", {
        **data, "slug": slug, "demos": [SH.DEMOS[s] for s in SH.ORDER],
        "industries": SC.INDUSTRIES, "states": SC.STATES,
        "loc_detected": detected, "active_industry": ind, "active_region": reg or "",
    })
