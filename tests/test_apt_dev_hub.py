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
    # W8-A menu merge: /apt/dev is "Preview as visitor" — the console-launcher
    # cards are gone (they duplicated the apt sidebar item-for-item).
    t = c.get("/apt/dev").text
    assert "Preview as visitor" in t
    assert 'href="/gauntletapt' in t          # live-page CTA targets the replica
    assert "hub-grid" not in t                # no console-card menu-inside-a-menu
    assert "Marketer console" not in t and "Engineer console" not in t


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
