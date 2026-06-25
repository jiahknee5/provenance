"""The /demo surface — live-clone a website, render 3 personalized variants per scenario,
and a KPI control tower that shows a simulated reinforcement-learning loop moving toward
target KPIs while monitoring provenance, drift, and hallucination.

  GET /demo?url=&scenario=     — the demo: pick a scenario, see its 3 variants rendered onto
                                 the live-cloned site, each with its DATA USED provenance.
  GET /demo/variant?url=&scenario=&v=  — one variant's cloned+injected page (served into an iframe).
  GET /demo/monitor            — the KPI control tower (simulated RL + health rails).
  GET /api/demo/monitor        — the monitor data as JSON.

The monitor reads the baked data/demo/observe/demo_monitor.json when present, else computes
it live (deterministic). Cloning a NEW url touches the network; gauntletai.com is the default.
"""
from __future__ import annotations

import json

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.server import app, templates
from pipeline.common.config import OBSERVE_DIR
from pipeline.personalization import demo_scenarios as DS
from pipeline.personalization import demo_sim
from pipeline.personalization import creative as CR
from pipeline.personalization import scene as SC
from pipeline.personalization.cloner import DEFAULT_URL, brand_from_url, clone, normalize_url


def _monitor_data() -> dict:
    p = OBSERVE_DIR / "demo_monitor.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return demo_sim.build()


def _spark(curve: list[float]) -> str:
    """conv_curve (0..1) → an SVG polyline points string in a 100×26 box."""
    if not curve:
        return ""
    n = len(curve)
    pts = []
    for i, y in enumerate(curve):
        x = round(i / max(n - 1, 1) * 100, 1)
        pts.append(f"{x},{round(26 - max(0.0, min(1.0, y)) * 24 - 1, 1)}")
    return " ".join(pts)


@app.get("/demo", response_class=HTMLResponse)
def demo(request: Request, url: str = DEFAULT_URL, scenario: str = "A", v: str = ""):
    s = DS.scenario(scenario) or DS.SCENARIOS[0]
    focus = None
    if v:
        found = DS.find_variant(s.id, v)
        if found:
            focus = found[1]
    return templates.TemplateResponse(request, "demo.html", {
        "subtitle": "personalization demo",
        "url": normalize_url(url),
        "scenarios": DS.SCENARIOS,
        "scenario": s,
        "gated": DS.gated_variants(s),
        "blocked": DS.blocked_variant(s),
        "focus": focus,
        "brand": brand_from_url(normalize_url(url)),
    })


@app.get("/demo/variant", response_class=HTMLResponse)
def demo_variant(url: str = DEFAULT_URL, scenario: str = "A", v: str = ""):
    found = DS.find_variant(scenario, v)
    if not found:
        return HTMLResponse("<p style='font:14px sans-serif;padding:20px'>unknown variant</p>",
                            status_code=404)
    s, variant = found
    return HTMLResponse(clone(url, s.id, variant)["html"])


@app.get("/demo/monitor", response_class=HTMLResponse)
def demo_monitor(request: Request):
    m = _monitor_data()
    for sc in m.get("scenarios", []):
        sc["spark"] = _spark(sc.get("conv_curve", []))
    return templates.TemplateResponse(request, "demo_monitor.html", {
        "subtitle": "KPI control tower", "m": m,
    })


@app.get("/api/demo/monitor")
def api_demo_monitor():
    return JSONResponse(_monitor_data())


@app.get("/demo/live", response_class=HTMLResponse)
def demo_live(request: Request):
    """Real firmographic landing: resolves region + company + industry from the visitor's
    actual IP (reverse-IP + PDL), renders localized copy + a curated licensed backdrop, and
    lets you override location/industry to preview what any IP would get."""
    det = SC.detect(request)
    industry = det["industry"] or SC.DEFAULT_INDUSTRY
    sc = SC.build_scene(det["region"], industry, detected=bool(det["region"]),
                        company=det["company"], city=det["city"])
    design = CR.design_select(industry=industry, region=det["region"], company=det["company"],
                              daypart=det.get("daypart"))
    return templates.TemplateResponse(request, "demo_live.html", {
        "det": det, "scene": sc, "industries": SC.INDUSTRIES, "states": SC.STATES,
        "client_map": SC.client_map(), "default_industry": industry,
        "loc_detected": bool(det["region"]), "gallery": SC.GALLERY,
        "angles": CR.ANGLES, "design": design, "examples": SC.EXAMPLE_ACCOUNTS,
    })


@app.get("/api/demo/aicopy")
def api_demo_aicopy(industry: str = "", region: str = "", company: str = "", city: str = "",
                    angle: str = "default", policy: str = "allude", competitive: bool = False):
    """The gated copy agent: LLM proposes (if keyed) → Gate verifies → angle falls back.
    competitive=true engages the Tier-3 path (provable differentiators, Gate-enforced)."""
    return JSONResponse(CR.ai_copy(industry=industry or SC.DEFAULT_INDUSTRY, region=region or None,
                                   company=company or None, city=city or None,
                                   angle=angle, policy=policy, competitive=competitive))


@app.get("/api/demo/resolve")
def api_demo_resolve(ip: str = ""):
    """Resolve an ENTERED IP → company / location / industry (real reverse-IP + PDL).
    Powers the 'try a different IP' override on /demo/live."""
    return JSONResponse(SC.resolve_ip(ip))


@app.get("/api/demo/resolve_email")
def api_demo_resolve_email(email: str = ""):
    """FIRST-PARTY lane: a work email → company (domain) + person (PDL). Works for small
    companies the reverse-IP lane can't see; the facts are `say` (self-declared)."""
    return JSONResponse(SC.resolve_email(email))


@app.get("/api/demo/scene")
def api_demo_scene(region: str = "", industry: str = "", company: str = "",
                   city: str = "", policy: str = "allude"):
    """Server-authoritative scene for a (region × industry × policy) preview."""
    return JSONResponse(SC.build_scene(region or None, industry or SC.DEFAULT_INDUSTRY,
                                       detected=False, company=company or None,
                                       city=city or None, policy=policy))
