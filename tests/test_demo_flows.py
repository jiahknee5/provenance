"""Demo flows hub — all ten presenter storylines resolve to live routes."""
from __future__ import annotations

import re

from starlette.testclient import TestClient

from app.demo import DEMO_FLOWS
from app.main import app

c = TestClient(app)


def test_demo_flows_page_renders():
    r = c.get("/demo/flows")
    t = r.text
    assert r.status_code == 200
    assert "Demo flows" in t
    assert t.count('class="q-card df-card"') == len(DEMO_FLOWS)
    for flow in DEMO_FLOWS:
        assert flow["title"] in t
        assert flow["main"].split("#")[0] in t


def test_demo_flows_use_cases_links_showcase():
    t = c.get("/demo/flows").text
    assert 'href="/showcase"' in t
    assert re.search(r'href="/showcase"[^>]*>.*?Use cases', t, re.S)


def test_demo_flow_main_routes_resolve():
    bad = []
    for flow in DEMO_FLOWS:
        path = flow["main"].split("#")[0]
        r = c.get(path)
        if r.status_code != 200:
            bad.append((flow["id"], path, r.status_code))
    assert not bad, f"dead demo flow routes: {bad}"


def test_assurance_shows_false_positive_negative_contrast():
    t = c.get("/assurance").text
    assert "False-reject" in t
    assert "Missed bad claims" in t
    assert 'id="drift-watch"' in t


def test_observatory_in_main_nav():
    t = c.get("/workspace").text
    assert 'href="/observatory"' in t
    assert 'href="/demo/flows"' in t


def test_cmdk_observatory_not_archive():
    t = c.get("/workspace").text
    m = re.search(r'href="/observatory"[^>]*>.*?Observatory.*?hint">(\w+)', t, re.S)
    assert m and m.group(1) == "go"
