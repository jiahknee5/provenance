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
