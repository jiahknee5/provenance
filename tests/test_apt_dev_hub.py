"""Tests for the unified /apt/dev console hub."""
from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_apt_dev_hub_returns_200():
    r = c.get("/apt/dev")
    assert r.status_code == 200
    t = r.text
    assert "/apt/dev" in t
    assert "GauntletAI" in t
    assert "Planet" in t


def test_apt_dev_hub_defaults_to_gauntlet():
    t = c.get("/apt/dev").text
    assert 'href="/gauntletapt/dev' in t
    assert "Marketer console" in t
    assert "Engineer console" in t
    m_pos = t.find("Marketer console")
    e_pos = t.find("Engineer console")
    assert m_pos < e_pos


def test_apt_dev_hub_site_planet():
    t = c.get("/apt/dev?site=planet").text
    assert 'href="/planetapt/dev' in t
    assert 'href="/planetapt/dev/business' in t
    assert "location signal" in t.lower() or "Location" in t


def test_apt_dev_hub_identity_preview_links():
    t = c.get("/apt/dev?as=anon").text
    assert "as=anon" in t
    t2 = c.get("/apt/dev?as=known").text
    assert "as=known" in t2


def test_apt_dev_hub_site_toggle_preserves_as():
    t = c.get("/apt/dev?site=gauntlet&as=known").text
    assert 'href="/apt/dev?site=planet&amp;as=known"' in t


def test_apt_dev_hub_entry_links_for_active_site():
    g = c.get("/apt/dev?site=gauntlet").text
    assert "/gauntletapt/ad-lp" in g or "utm_source=x" in g
    p = c.get("/apt/dev?site=planet").text
    assert "/planetapt/ads" in p
