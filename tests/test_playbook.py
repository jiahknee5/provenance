"""Tests for /apt/playbook — the in-shell "how it's made" guide (W6-F).

The playbook must render REAL config (tenant intent catalogs, the imported
persuasion strategy catalog, real registry file paths), carry the honesty
labeling everywhere the stimulation model appears, badge the animated-images
chapter as future release grounded in Planet's shipped motion config, and keep
the AEO chapter framed as roadmap / point of view with zero capability claims.
"""
from __future__ import annotations

import re

from markupsafe import escape
from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import image_intents as II
from pipeline.personalization import persuasion as PS

c = TestClient(app)

TENANTS = ("gauntlet", "planet", "skyfi")


def _page(tenant: str) -> str:
    r = c.get(f"/apt/playbook?site={tenant}")
    assert r.status_code == 200
    return r.text


# --------------------------------------------------------------------------- #
# Page serves, tenant-aware
# --------------------------------------------------------------------------- #
def test_playbook_serves_200_for_all_tenants():
    for t in TENANTS:
        assert c.get(f"/apt/playbook?site={t}").status_code == 200


def test_playbook_unknown_site_falls_back_to_first_tenant():
    r = c.get("/apt/playbook?site=nope")
    assert r.status_code == 200
    assert "gauntlet" in r.text.lower()


def test_playbook_has_all_four_chapter_anchors():
    html = _page("gauntlet")
    for anchor in ('id="images"', 'id="copy"', 'id="motion"', 'id="aeo"'):
        assert anchor in html, f"missing chapter anchor {anchor}"


# --------------------------------------------------------------------------- #
# Chapter 1 — real intent catalog, honesty labeling
# --------------------------------------------------------------------------- #
def test_playbook_renders_each_tenants_real_intent_ids():
    for t in TENANTS:
        html = _page(t)
        cfg = II.load_image_config(t)
        ids = [i["id"] for i in cfg["intents"]]
        assert ids, f"{t}: intent catalog unexpectedly empty"
        for iid in ids:
            assert f'id="intent-{iid}"' in html, f"{t}: intent {iid} not rendered"


def test_playbook_intents_are_the_tenants_not_another_tenants():
    # Gauntlet page shows gauntlet intents, not planet's satellite catalog.
    html = _page("gauntlet")
    assert 'id="intent-peer_proof"' in html
    assert 'id="intent-regional_truth"' not in html


def test_playbook_carries_the_honesty_label_in_chapter_one():
    for t in TENANTS:
        html = _page(t).lower()
        assert "predicted" in html
        assert "not measured" in html
        assert "predicted response modeling" in html
        assert "not measured brain data" in html


def test_playbook_renders_real_guardrails_and_tier_gates():
    for t in TENANTS:
        html = _page(t)
        cfg = II.load_image_config(t)
        must_avoid = ((cfg.get("prompt_defaults") or {}).get("must_avoid")) or []
        assert must_avoid, f"{t}: no must_avoid in config"
        assert must_avoid[0] in html
        for gate in ((cfg.get("guardrails") or {}).get("tier_gates")) or {}:
            assert gate in html


def test_playbook_shows_delivery_caps_and_cost():
    from pipeline.personalization import prebuild as PB
    html = _page("gauntlet")
    assert str(PB.CAP_STATES_PER_TARGET) in html
    assert str(PB.CAP_IMAGES_PER_TENANT) in html
    assert str(PB.CAP_IMAGES_GLOBAL) in html
    assert "prebuilt" in html.lower() and "realtime" in html.lower()


# --------------------------------------------------------------------------- #
# Chapter 2 — the imported strategy catalog (no hardcoded copies drifting)
# --------------------------------------------------------------------------- #
def test_playbook_lists_all_five_persuasion_strategies_from_module():
    assert len(PS.STRATEGIES) == 5
    for t in TENANTS:
        html = _page(t)
        for key, spec in PS.STRATEGIES.items():
            assert f'id="strategy-{key}"' in html, f"{t}: strategy {key} missing"
            # compare against the jinja-escaped form (e.g. & -> &amp;)
            assert str(escape(spec["principle"])) in html, (
                f"{t}: principle for {key} missing")


def test_playbook_explains_say_allude_hold_and_gate():
    html = _page("gauntlet").lower()
    for word in ("say", "allude", "hold"):
        assert word in html
    assert "gate" in html
    assert "frame" in html and "facts" in html


# --------------------------------------------------------------------------- #
# Customize chips — every block states where it's customizable
# --------------------------------------------------------------------------- #
def test_playbook_customize_chips_reference_tenant_registry():
    for t in TENANTS:
        html = _page(t)
        assert f"rules/{t}_sections.yaml" in html
        assert f"rules/{t}_image.yaml" in html
        assert "Customize" in html


def test_playbook_customize_chips_name_designer_controls():
    html = _page("gauntlet")
    for ctl in ("sd-strategy", "sd-policy", "sd-mode", "sd-workflow", "sd-prompt"):
        assert ctl in html, f"designer control {ctl} not referenced"
    assert "nothing saves live" in html


# --------------------------------------------------------------------------- #
# Chapter 3 — animated images: shipped Planet preview + future-release badge
# --------------------------------------------------------------------------- #
def test_playbook_motion_chapter_present_with_future_release_badge():
    for t in TENANTS:
        html = _page(t)
        assert 'id="motion"' in html
        assert "Future release" in html


def test_playbook_motion_chapter_references_planet_motion_config():
    planet_motion = II.load_image_config("planet").get("motion") or {}
    assert planet_motion.get("enabled") is True  # the grounding fact
    for t in TENANTS:
        html = _page(t)
        assert "rules/planet_image.yaml" in html
        assert "motion_gen.py" in html
        assert "pregen_motion_cache.py" in html
        assert str(planet_motion.get("frames", 4)) in html


def test_playbook_motion_keeps_the_simulated_labeling():
    html = _page("planet").lower()
    assert 'id="motion"' in html
    # the config's own framing line ships on the page
    assert "not measured visitor brain stimulation" in html


# --------------------------------------------------------------------------- #
# Chapter 4 — AEO: roadmap / point of view, no capability claims
# --------------------------------------------------------------------------- #
def test_playbook_aeo_chapter_present_and_labeled_point_of_view():
    for t in TENANTS:
        html = _page(t)
        assert 'id="aeo"' in html
        idx = html.find("Agent Engine Optimization")
        assert idx != -1
        window = html[max(0, idx - 400): idx + 400].lower()
        assert "point of view" in window or "roadmap" in window, (
            f"{t}: AEO heading not labeled roadmap/point-of-view nearby")


def test_playbook_aeo_makes_no_unqualified_capability_claims():
    html = _page("gauntlet")
    lo = re.sub(r"\s+", " ", html.lower())  # collapse template line-wraps
    assert "nothing in this chapter is built" in lo
    assert "no sentence here describes a shipped capability" in lo
    # the thesis close ties to the tagline
    assert "it's the ranking function" in lo


# --------------------------------------------------------------------------- #
# Nav + cross-links
# --------------------------------------------------------------------------- #
def test_shell_nav_shows_playbook_with_four_children():
    from pipeline.personalization import demo_nav as NAV
    for t in TENANTS:
        ctx = NAV.console_shell_ctx(t, "consoles", active_sub="playbook")
        groups = {g["key"]: g for g in ctx["nav_tree"]}
        items = {i["id"]: i for i in groups["consoles"]["items"]}
        pb = items["playbook"]
        assert pb["label"] == "Playbook"
        assert pb["href"] == f"/apt/playbook?site={t}"
        kids = [k["id"] for k in pb["children"]]
        assert kids == ["playbook-images", "playbook-copy",
                        "playbook-motion", "playbook-aeo"]
        assert pb["children"][0]["href"].endswith("#images")
        assert pb["children"][3]["href"].endswith("#aeo")


def test_playbook_link_appears_on_other_shell_pages():
    html = c.get("/costs?site=planet").text
    assert "/apt/playbook?site=planet" in html
    assert "Playbook" in html


def test_designer_cards_link_to_playbook_anchors():
    for t, mount in (("gauntlet", "/gauntletapt/dev/business"),
                     ("planet", "/planetapt/dev/business"),
                     ("skyfi", "/skyfiapt/dev/business")):
        html = c.get(mount).text
        assert f"/apt/playbook?site={t}#copy" in html, f"{t}: no copy cross-link"
        assert f"/apt/playbook?site={t}#images" in html, f"{t}: no images cross-link"
        assert "How this works" in html
