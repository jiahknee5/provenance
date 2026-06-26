"""Showcase — the live-demo gallery and each use case's two sister pages.

  GET /showcase                       — index: Live demo + the four Use cases
  GET /showcase/{slug}[/production]    — the full-page landing an end visitor sees
                                         (?v=gated|generic|ungated), driven by a persona, an IP,
                                         or industry/region overrides
  GET /showcase/{slug}/observability   — every input, decision, source, and the trace; with the
                                         same live IP input as /demo/live
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


def _resolve(request: Request, slug: str, industry: str, region: str, ip: str, persona_key: str):
    """Resolve the active signals for a firmographic page, three ways:
      • a persona preset (rich: industry/region/size/role/intent — declared),
      • a real IP (reverse-IP capture), or
      • industry/region overrides (or the visitor's own IP, the default)."""
    real = SC.detect(request)
    p = SH.persona(slug, persona_key) if persona_key else None
    if p:
        il = SC.BY_KEY.get(p["industry"], SC.BY_KEY[SC.DEFAULT_INDUSTRY])["label"]
        cap = [{"label": "Industry", "value": il, "policy": "declared", "drives": "hero · proof · features", "conf": "high"},
               {"label": "Region", "value": p["region"], "policy": "declared", "drives": "hero · local framing", "conf": "high"},
               {"label": "Company size", "value": SH._SIZE_LABEL.get(p["size"], "—"), "policy": "declared", "drives": "offer scale"},
               {"label": "Role / seniority", "value": SH._ROLE_LABEL.get(p["role"], "—"), "policy": "declared", "drives": "feature framing"}]
        if p["intent"]:
            cap.append({"label": "Buying intent", "value": SH._INTENT_LABEL.get(p["intent"], "—"), "policy": "declared", "drives": "offer urgency"})
        det = {"captured": cap, "request_signals": real.get("request_signals", []),
               "network_type": "persona preset", "tier": 2, "tier_label": "firmographic + role",
               "confidence": {"location": "declared", "company": "declared", "industry": "declared"},
               "reason": "persona preset — the rich signals enrichment + declared data provide (an IP alone gives industry + region only)"}
        octx = {"region": p["region"], "industry": p["industry"], "company": None, "city": None, "detected": True,
                "size": p["size"], "role": p["role"], "intent": p["intent"], "persona": persona_key, "ip": ""}
        return det, octx
    company, city = real.get("company"), real.get("city")
    reg = region or real.get("region")
    ind = industry or real.get("industry") or SH.DEMOS[slug].default_industry or "general"
    detected = bool(real.get("region")) and not (region or industry)
    det = real
    if ip:
        rv = SC.resolve_ip(ip)
        reg, ind = rv.get("region") or reg, rv.get("industry") or ind
        company, city = rv.get("company") or company, rv.get("city") or city
        rv["request_signals"] = real.get("request_signals", [])
        det, detected = rv, True
    octx = {"region": reg, "industry": ind, "company": company, "city": city, "detected": detected,
            "size": "", "role": "", "intent": "", "persona": "", "ip": ip}
    return det, octx


def _model(request: Request, slug: str, industry: str, region: str, ip: str, persona: str):
    d = SH.DEMOS[slug]
    if d.kind == "firmographic":
        det, octx = _resolve(request, slug, industry, region, ip, persona)
        return SH.build_view(slug, det=det, octx=octx), "use_case_rich.html"
    # known / optimizer are persona-driven (identity / segment), with an optional reverse-IP
    # firmographic overlay so the same live IP input as /demo/live still resolves real context.
    overlay = SC.resolve_ip(ip) if ip else {}
    if d.kind == "known":
        c = ctx()
        return SH.build_view(slug, gate=c.gate, library=c.library, persona=persona,
                             overlay=overlay, ip=ip, industry=industry, region=region), "use_case_rich.html"
    return SH.build_view(slug, persona=persona, overlay=overlay, ip=ip,
                         industry=industry, region=region), "use_case_rich.html"


@app.get("/showcase", response_class=HTMLResponse)
def showcase(request: Request):
    return templates.TemplateResponse(request, "showcase.html", {"demos": [SH.DEMOS[s] for s in SH.ORDER]})


@app.get("/showcase/{slug}", response_class=HTMLResponse)
@app.get("/showcase/{slug}/production", response_class=HTMLResponse)
def showcase_production(request: Request, slug: str, v: str = "gated", industry: str = "",
                       region: str = "", ip: str = "", persona: str = ""):
    if slug not in SH.DEMOS:
        return _404()
    vm, tpl = _model(request, slug, industry, region, ip, persona)
    version = v if v in ("gated", "ungated", "generic") else "gated"
    return templates.TemplateResponse(request, tpl, {
        **vm, "view": "production", "version": version, "slug": slug,
        "industries": SC.INDUSTRIES, "states": SC.STATES})


@app.get("/showcase/{slug}/observability", response_class=HTMLResponse)
def showcase_observability(request: Request, slug: str, industry: str = "",
                          region: str = "", ip: str = "", persona: str = ""):
    if slug not in SH.DEMOS:
        return _404()
    vm, tpl = _model(request, slug, industry, region, ip, persona)
    return templates.TemplateResponse(request, tpl, {
        **vm, "view": "observability", "slug": slug,
        "industries": SC.INDUSTRIES, "states": SC.STATES})
