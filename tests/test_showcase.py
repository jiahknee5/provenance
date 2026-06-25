"""Showcase — the gallery + each use case's two sister pages (Production, Observability).

Production shows the gated version (ships) vs the ungated version (blocked) with a short
description of each. Observability shows, like the live demo, every input, the routing +
copy/Gate decisions, the provenance receipt, and the full trace.
"""
from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import showcase as SH

c = TestClient(app)


def test_showcase_index_lists_live_demo_and_use_cases():
    t = c.get("/showcase").text
    assert c.get("/showcase").status_code == 200
    assert "Showcase" in t and "Live demo" in t and "Use cases" in t
    assert 'href="/demo/live"' in t
    for slug in SH.ORDER:
        assert f'href="/showcase/{slug}"' in t


def test_production_shows_gated_and_ungated_with_descriptions():
    for slug in SH.ORDER:
        d = SH.DEMOS[slug]
        t = c.get(f"/showcase/{slug}").text          # /showcase/{slug} defaults to Production
        assert c.get(f"/showcase/{slug}").status_code == 200
        assert d.brand in t and f"Use case {d.num}" in t
        assert "Gated · ships" in t and "Ungated · blocked" in t      # both versions...
        assert "What ships" in t and "What the Gate blocks" in t      # ...each with a description
        # the two sister-page tabs are present
        assert f'href="/showcase/{slug}/production"' in t
        assert f'href="/showcase/{slug}/observability"' in t


def test_observability_shows_inputs_decisions_provenance_trace():
    for slug in SH.ORDER:
        t = c.get(f"/showcase/{slug}/observability").text
        assert c.get(f"/showcase/{slug}/observability").status_code == 200
        for panel in ("Inputs", "Routing decision", "Copy agent", "Provenance", "Trace"):
            assert panel in t, f"{slug} observability missing panel: {panel}"
        assert "ip-api.com" in t                       # a real provenance source
        assert "gated · ships" in t                    # the page being observed is the gated one
        # the Gate's verdicts are shown, including a blocked line
        assert "blocked" in t and "ships" in t


def test_overrides_repersonalize_both_views():
    p = c.get("/showcase/skyfi/production", params={"industry": "mining", "region": "Texas"}).text
    assert "Texas" in p and "mining" in p.lower()
    o = c.get("/showcase/skyfi/observability", params={"industry": "mining", "region": "Texas"}).text
    assert "Texas" in o and ("Mining & metals" in o or "mining" in o.lower())


def test_unknown_use_case_404():
    assert c.get("/showcase/nope").status_code == 404
    assert c.get("/showcase/nope/observability").status_code == 404


def test_all_sister_routes_resolve():
    for slug in SH.ORDER:
        for suffix in ("", "/production", "/observability"):
            assert c.get(f"/showcase/{slug}{suffix}").status_code == 200, f"/showcase/{slug}{suffix}"
    assert c.get("/demo/live").status_code == 200
