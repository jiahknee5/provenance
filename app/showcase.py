"""Showcase — the live-demo gallery and the two per-use-case sister pages.

  GET /showcase                         — index: Live demo + the Use cases
  GET /showcase/{slug}                  — the use case (defaults to the Production view)
  GET /showcase/{slug}/production       — the gated version that ships vs the ungated version
                                          the Gate blocks, each with a short description
  GET /showcase/{slug}/observability    — like the live demo: every input, the routing + copy
                                          decisions, the provenance receipt, and the full trace

All three accept ?industry=/?region=/?ip= to preview what any visitor would get.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.personalization import creative as CR
from pipeline.personalization import scene as SC
from pipeline.personalization import showcase as SH


def _resolve(request: Request, slug: str, industry: str, region: str, ip: str):
    """Resolve the visitor (own IP, or an entered ?ip=) + apply ?industry/?region overrides."""
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
        rv["request_signals"] = det.get("request_signals", [])
        det, detected = rv, True
    return det, {"region": reg, "industry": ind, "company": company, "city": city, "detected": detected}


def _base_ctx(slug: str, det: dict, ctx: dict) -> dict:
    data = SH.build(slug, **ctx)
    return {**data, "slug": slug, "det": det, "demos": [SH.DEMOS[s] for s in SH.ORDER],
            "industries": SC.INDUSTRIES, "states": SC.STATES,
            "loc_detected": ctx["detected"], "active_industry": ctx["industry"],
            "active_region": ctx["region"] or ""}


@app.get("/showcase", response_class=HTMLResponse)
def showcase(request: Request):
    return templates.TemplateResponse(request, "showcase.html", {
        "demos": [SH.DEMOS[s] for s in SH.ORDER]})


@app.get("/showcase/{slug}", response_class=HTMLResponse)
@app.get("/showcase/{slug}/production", response_class=HTMLResponse)
def showcase_production(request: Request, slug: str, industry: str = "", region: str = "", ip: str = ""):
    if slug not in SH.DEMOS:
        return HTMLResponse("<h2 style='font:16px sans-serif;padding:24px'>Unknown use case.</h2>", status_code=404)
    det, ctx = _resolve(request, slug, industry, region, ip)
    return templates.TemplateResponse(request, "use_case.html", {**_base_ctx(slug, det, ctx), "view": "production"})


@app.get("/showcase/{slug}/observability", response_class=HTMLResponse)
def showcase_observability(request: Request, slug: str, industry: str = "", region: str = "", ip: str = ""):
    if slug not in SH.DEMOS:
        return HTMLResponse("<h2 style='font:16px sans-serif;padding:24px'>Unknown use case.</h2>", status_code=404)
    det, ctx = _resolve(request, slug, industry, region, ip)
    base = _base_ctx(slug, det, ctx)
    # the copy agent proposes → the Gate verifies (deterministic by default, LLM when keyed)
    ai = CR.ai_copy(industry=ctx["industry"], region=ctx["region"], company=ctx["company"],
                    city=ctx["city"], angle="default", policy="allude")
    # the Gate's verdict on THIS page's two versions: gated lines clear; the ungated lines (which
    # recite the company under an allude policy) are blocked — the truth boundary, on real content.
    gated_checks = CR.verify_copy([base["hero"]["headline"], base["hero"]["sub"]], "", ctx["company"], "allude")
    ungated_checks = CR.verify_copy([base["hero_say"]["headline"], base["hero_say"]["sub"]], "",
                                    ctx["company"], "allude", competitors=CR.COMPETITOR_HINTS)
    return templates.TemplateResponse(request, "use_case.html", {
        **base, "view": "observability", "ai": ai,
        "gated_checks": gated_checks, "ungated_checks": ungated_checks})
