"""Showcase — the live-demo gallery and the two actual personalized use-case sites.

Proves: the index lists Live demo + the use cases; each use case renders a real, branded,
personalized landing with a provenance receipt; overrides re-personalize the hero; the
licensed backdrop is real; unknown slugs 404.
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
        assert f'href="/showcase/{slug}"' in t, f"missing card link for {slug}"


def test_use_case_demos_render_branded_and_personalized():
    for slug in SH.ORDER:
        d = SH.DEMOS[slug]
        r = c.get(f"/showcase/{slug}")
        assert r.status_code == 200
        t = r.text
        assert d.brand in t                              # branded as the seller, not "apt"
        assert "personalized live by apt" in t           # ...but disclosed as an apt demo
        assert f"Use case {d.num}" in t
        assert "What this page used" in t                # the provenance receipt rail
        assert "Reset to my IP" in t                     # the override controls


def test_overrides_repersonalize_the_hero():
    t = c.get("/showcase/skyfi", params={"industry": "mining", "region": "Texas"}).text
    assert "mining" in t.lower() and "Texas" in t
    t2 = c.get("/showcase/gauntletai", params={"industry": "healthcare", "region": "Florida"}).text
    assert "healthcare" in t2.lower() and "Florida" in t2


def test_receipt_is_sourced_and_backdrop_is_really_licensed():
    t = c.get("/showcase/skyfi", params={"industry": "mining", "region": "Arizona"}).text
    assert "ip-api.com" in t                             # a real provenance source in the receipt
    assert "backdrop:" in t                              # the licensed-image attribution row
    assert ("staticflickr" in t or "wikimedia" in t)     # the actual CC photo, not a placeholder


def test_unknown_use_case_404():
    assert c.get("/showcase/nope").status_code == 404


def test_all_showcase_routes_resolve():
    for path in ("/showcase", "/showcase/gauntletai", "/showcase/skyfi", "/demo/live"):
        assert c.get(path).status_code == 200, path
