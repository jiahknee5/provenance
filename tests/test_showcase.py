"""Showcase — the gallery + four use cases, each with two sister pages.

Production is a FULL-PAGE landing exactly as an end visitor sees it, with a Gated (ships) /
Ungated (blocked) toggle. Observability shows the inputs, the routing + Gate decisions, the
provenance, and the trace. The four use cases run on different engines (scene / persuasion /
bandit) but render the same normalized view.
"""
from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import showcase as SH

c = TestClient(app)
SLUGS = SH.ORDER   # gauntletai, skyfi, known, optimizer


def test_index_lists_live_demo_and_all_four_use_cases():
    t = c.get("/showcase").text
    assert c.get("/showcase").status_code == 200
    assert "Live demo" in t and "Use cases" in t and 'href="/demo/live"' in t
    assert len(SLUGS) == 4
    for slug in SLUGS:
        assert f'href="/showcase/{slug}"' in t, slug
        assert SH.DEMOS[slug].brand in t


def test_production_is_a_full_page_with_gated_ungated_toggle():
    for slug in SLUGS:
        d = SH.DEMOS[slug]
        t = c.get(f"/showcase/{slug}").text                 # defaults to the gated full page
        assert c.get(f"/showcase/{slug}").status_code == 200
        assert 'class="fp-hero"' in t                        # a full-bleed landing, not cards
        assert "End-visitor view" in t and "personalized live by apt" in t
        assert d.brand in t
        # the gated/ungated toggle, both versions reachable
        assert f'href="/showcase/{slug}/production?v=gated' in t
        assert f'href="/showcase/{slug}/production?v=ungated' in t
        # the ungated full page carries the blocked banner
        u = c.get(f"/showcase/{slug}/production", params={"v": "ungated"}).text
        assert "Ungated — the Gate blocks this in production" in u


def test_observability_shows_decisions_gate_and_trace():
    for slug in SLUGS:
        t = c.get(f"/showcase/{slug}/observability").text
        assert c.get(f"/showcase/{slug}/observability").status_code == 200
        assert "Gate — what ships" in t and "Trace — the pipeline path" in t
        assert "gated · ships" in t
        assert "blocked" in t and "ships" in t               # the Gate shows both verdicts


def test_firmographic_overrides_and_provenance():
    # firmographic use cases personalize by industry/region and show a real source
    p = c.get("/showcase/skyfi/production", params={"industry": "mining", "region": "Texas"}).text
    assert "Texas" in p and "mining" in p.lower()
    o = c.get("/showcase/skyfi/observability", params={"industry": "mining", "region": "Texas"}).text
    assert "ip-api.com" in o and "Texas" in o


def test_known_use_case_is_a_gate_bounded_persuasion_play():
    p = c.get("/showcase/known").text                        # production gated
    assert "Known customer" in p
    u = c.get("/showcase/known/production", params={"v": "ungated"}).text
    assert "$190K" in u                                      # the ungated version recites PII
    o = c.get("/showcase/known/observability").text
    assert "persuasion strategy" in o.lower() and "Provenance" in o


def test_optimizer_use_case_is_truth_bounded():
    p = c.get("/showcase/optimizer").text
    assert "Long-running A/B" in p and "wins" in p
    o = c.get("/showcase/optimizer/observability").text
    assert "Arms" in o and "bandit" in o.lower()
    assert "0×" in o                                         # the lie/creepy arm selected 0 times


def test_unknown_use_case_404():
    assert c.get("/showcase/nope").status_code == 404
    assert c.get("/showcase/nope/observability").status_code == 404


def test_all_sister_routes_resolve():
    for slug in SLUGS:
        for suffix in ("", "/production", "/observability"):
            assert c.get(f"/showcase/{slug}{suffix}").status_code == 200, f"/showcase/{slug}{suffix}"
    assert c.get("/demo/live").status_code == 200
