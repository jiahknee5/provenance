"""Per-variant ad "thinking" explainers (W6-A) — six config-grounded beats for EVERY
X ad variant (gauntlet 12 · planet 12 · skyfi 6), plus the UI affordances:
single-ad pages render the full panel, grids render the compact "The thinking" details.

Everything asserted here is read back from the live catalogs / rules/<tenant>_image.yaml —
the explainer may never invent claims (Art I). Deterministic, offline, $0.
"""
from __future__ import annotations

import html

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import ad_explainers as AE
from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_intents as II
from pipeline.personalization import planet_site as PLS
from pipeline.personalization import skyfi_site as SS

c = TestClient(app)

TENANTS = [("gauntlet", GS, "h1_gold"), ("planet", PLS, "h1_blue"), ("skyfi", SS, "h1_blue")]
BEAT_KEYS = ("thought", "targeting", "development", "mechanic", "promise", "imagery")


def _text(resp) -> str:
    return html.unescape(resp.text)


# --------------------------------------------------------------------------- #
# 1 · The view-model: six beats for every variant of every tenant
# --------------------------------------------------------------------------- #
def test_every_variant_of_every_tenant_gets_all_six_beats_nonempty():
    for tenant, site, _ in TENANTS:
        for v in site.AD_VARIANTS:
            e = AE.explainer_for(tenant, v)
            for key in BEAT_KEYS:
                beat = e[key]
                assert beat["body"].strip(), f"{tenant}/{v['id']}: empty beat {key}"
                assert len(beat["body"]) > 60, f"{tenant}/{v['id']}: thin beat {key}"
                assert beat["title"].strip(), f"{tenant}/{v['id']}: no title on {key}"
            assert [b["key"] for b in e["beats"]] == list(BEAT_KEYS)
            assert e["landing_url"] and e["dev_url"] and e["condensed"]


def test_catalog_counts_are_the_briefed_12_12_6():
    assert len(GS.AD_VARIANTS) == 12
    assert len(PLS.AD_VARIANTS) == 12
    assert len(SS.AD_VARIANTS) == 6


def test_promise_beat_quotes_the_real_page_overrides():
    for tenant, site, h1_key in TENANTS:
        for v in site.AD_VARIANTS:
            e = AE.explainer_for(tenant, v)
            h1 = v["page"]["h1_pre"] + v["page"][h1_key]
            body = e["promise"]["body"]
            assert h1 in body, f"{tenant}/{v['id']}: h1 not quoted"
            assert v["page"]["sub"] in body, f"{tenant}/{v['id']}: sub not quoted"
            assert v["page"]["cta_primary"] in body
            assert v["page"]["cta_secondary"] in body


def test_mechanic_beat_carries_real_utms_and_landing_url():
    for tenant, site, _ in TENANTS:
        for v in site.AD_VARIANTS:
            e = AE.explainer_for(tenant, v)
            body = e["mechanic"]["body"]
            assert f"utm_campaign={v['utm_campaign']}" in body
            assert f"utm_content={v['variant_id']}" in body
            assert "classify_entry" in body and "resolve_ad_variant" in body
            assert e["landing_url"] == site.variant_landing_url(v)
            assert any(e["landing_url"] in p for p in e["mechanic"]["points"])


def test_imagery_beat_states_the_real_intent_and_yaml_metaphor():
    for tenant, site, _ in TENANTS:
        config = II.load_image_config(tenant)
        for v in site.AD_VARIANTS:
            e = AE.explainer_for(tenant, v)
            body = e["imagery"]["body"]
            metaphor = config["ad_metaphors"][v["id"]]
            assert metaphor in body, f"{tenant}/{v['id']}: YAML ad metaphor not quoted"
            # the stated intent must exist in the tenant YAML and match the engine
            stated = next(i for i in config["intent_by_id"] if f"“{i}”" in body)
            ctx = {"channel": "ad", "ad_variant_id": v["id"],
                   "audience_route": AE._image_route(tenant, v),
                   "tier": 0, "top_objections": [], "industry": "general",
                   "region": None, "archetype_id": None}
            sel = II.select_image_intent(ctx, config)
            assert stated == sel["primary"]["intent_id"], f"{tenant}/{v['id']}"
            assert config["intent_by_id"][stated]["mood"] in body


def test_imagery_intents_hit_the_curated_yaml_rules():
    # The primary rules in the tenant YAMLs must be visible in the explainers.
    def intent_of(tenant, site, vid):
        v = site.AD_BY_VARIANT_ID[vid]
        e = AE.explainer_for(tenant, v)
        cfg = II.load_image_config(tenant)
        return next(i for i in cfg["intent_by_id"] if f"“{i}”" in e["imagery"]["body"])

    assert intent_of("gauntlet", GS, "v08") == "retarget_warm"      # x-engager
    assert intent_of("gauntlet", GS, "v11") == "aspiration"         # x-interest + individual
    assert intent_of("gauntlet", GS, "v09") == "message_match"      # keyword fallback
    assert intent_of("planet", PLS, "v02") == "mission_authority"   # x-defense
    assert intent_of("planet", PLS, "v08") == "retarget_warm"       # x-disaster engager
    assert intent_of("planet", PLS, "v11") == "aspiration_research" # x-age research
    assert intent_of("skyfi", SS, "sv06") == "aor_authority"        # x-defense
    assert intent_of("skyfi", SS, "sv04") == "before_after_archive" # x-insurance
    assert intent_of("skyfi", SS, "sv01") == "order_flow_match"     # vertical fallback


def test_targeting_beat_quotes_real_targeting_config():
    for tenant, site, _ in TENANTS:
        for v in site.AD_VARIANTS:
            e = AE.explainer_for(tenant, v)
            body = e["targeting"]["body"]
            if tenant == "skyfi":
                assert v["segment"] in body
                assert v["audience"] in body
            else:
                assert v["x_targeting_type"] in body
                assert v["x_targeting_example"] in body


def test_development_beat_quotes_the_actual_creative_fields():
    for tenant, site, _ in TENANTS:
        for v in site.AD_VARIANTS:
            e = AE.explainer_for(tenant, v)
            body = e["development"]["body"]
            assert v["ad"]["trigger"] in body, f"{tenant}/{v['id']}: hook not quoted"
            assert v["ad"]["cta_label"] in body
            if v["ad"].get("proof"):
                assert v["ad"]["proof"] in body


def test_hold_notes_surface_in_the_explainer():
    # Age/gender targeting holds the demo fact; defense holds the register (real config).
    for tenant, site, _ in TENANTS:
        for v in site.AD_VARIANTS:
            if not v.get("hold_note"):
                continue
            e = AE.explainer_for(tenant, v)
            all_points = [p for b in e["beats"] for p in b["points"]]
            assert any(v["hold_note"] in p for p in all_points), f"{tenant}/{v['id']}"


def test_dev_url_points_at_the_decision_console_with_the_same_utms():
    for tenant, site, _ in TENANTS:
        dev_root = {"gauntlet": "/dev", "planet": "/planet/dev", "skyfi": "/skyfi/dev"}[tenant]
        for v in site.AD_VARIANTS:
            e = AE.explainer_for(tenant, v)
            assert e["dev_url"].startswith(dev_root + "?")
            assert f"utm_content={v['variant_id']}" in e["dev_url"]
    # mount-aware override
    e = AE.explainer_for("planet", PLS.AD_VARIANTS[0],
                         page_path="/planetapt", dev_path="/planetapt/dev")
    assert e["landing_url"].startswith("/planetapt?")
    assert e["dev_url"].startswith("/planetapt/dev?")


def test_condensed_is_compact_and_never_quotes_ad_copy():
    for tenant, site, _ in TENANTS:
        for v in site.AD_VARIANTS:
            e = AE.explainer_for(tenant, v)
            assert len(e["condensed"]) < 300
            assert v["ad"]["trigger"] not in e["condensed"]
            assert "Hero shift" not in e["condensed"]


def test_explainer_is_deterministic():
    v = PLS.AD_VARIANTS[3]
    assert AE.explainer_for("planet", v) == AE.explainer_for("planet", v)


# --------------------------------------------------------------------------- #
# 2 · Single-ad pages render the full six-beat panel
# --------------------------------------------------------------------------- #
def test_gauntlet_single_ad_renders_thinking_panel():
    t = _text(c.get("/gauntlet/ad?v=v09"))
    assert "The thinking" in t
    assert "message_match" in t                     # real intent id from the YAML
    assert "Open the landing page →" in t
    assert "See it decide →" in t
    v = GS.AD_BY_VARIANT_ID["v09"]
    assert v["page"]["h1_pre"] + v["page"]["h1_gold"] in t


def test_planet_single_ad_renders_thinking_panel():
    t = _text(c.get("/planet/ad?v=v01"))
    assert "The thinking" in t
    cfg = II.load_image_config("planet")
    assert cfg["ad_metaphors"]["x-agriculture"] in t
    assert "Open the landing page →" in t and "See it decide →" in t


def test_skyfi_single_ad_page_exists_with_thinking_panel():
    r = c.get("/skyfi/ad?v=sv01")
    assert r.status_code == 200
    t = _text(r)
    assert "The thinking" in t
    assert "Monitor your site from orbit" in t      # the real sv01 hook
    assert SS.variant_landing_url(SS.AD_BY_VARIANT_ID["sv01"], "/skyfi") in t
    assert "order_flow_match" in t
    # no match → redirect to the new grid
    resp = c.get("/skyfi/ad", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/skyfi/ads"


# --------------------------------------------------------------------------- #
# 3 · Grids gain the compact "The thinking" affordance
# --------------------------------------------------------------------------- #
def test_gauntlet_ad_lp_cards_have_thinking_details():
    t = _text(c.get("/gauntlet/ad-lp"))
    assert t.count("The thinking") >= 12
    assert "<details" in t and "Full six-beat panel →" in t
    assert '/gauntlet/ad?v=v01' in t and '/gauntlet/ad?v=v12' in t


def test_planet_ads_and_ads_lp_cards_have_thinking_details():
    ads = _text(c.get("/planet/ads"))
    assert ads.count("The thinking") >= 12
    assert "Full six-beat panel →" in ads
    lp = _text(c.get("/planet/ads-lp"))
    assert lp.count("The thinking") >= 12
    assert '/planet/ad?v=v07' in lp


def test_skyfi_ads_grid_shows_all_six_mockups_with_thinking():
    r = c.get("/skyfi/ads")
    assert r.status_code == 200
    t = _text(r)
    for v in SS.AD_VARIANTS:
        assert f"utm_campaign={v['utm_campaign']}" in t, f"missing {v['id']}"
        assert v["ad"]["trigger"] in t, f"missing ad copy for {v['id']}"
        assert SS.variant_landing_url(v, "/skyfi") in t
    assert t.count("The thinking") >= 6
    assert "skyfi.com" in t and "Promoted" in t


def test_skyfi_ads_route_with_v_param_renders_single_mockup():
    r = c.get("/skyfi/ads?v=sv03")
    assert r.status_code == 200
    assert "utm_content=sv03" in r.text
    assert "All 6 ads" in r.text


def test_skyfi_portal_mount_ads_links_stay_under_prefix():
    for path in ("/skyfiapt/ads", "/skyfiapt/ad?v=sv01"):
        r = c.get(path)
        assert r.status_code == 200, path
        t = r.text
        assert 'href="/skyfi?' not in t, path
        assert "/skyfiapt" in t, path


def test_grid_pages_keep_their_contracts():
    # gauntlet ad-lp still shows the hero-shift previews and generic headline
    t = _text(c.get("/gauntlet/ad-lp"))
    assert GS.generic_hero_headline() in t
    # planet /ads still has no landing-page hero-shift previews
    ads = _text(c.get("/planet/ads"))
    assert "Hero shift" not in ads
    # planet /ads-lp still never carries full X ad copy
    lp = _text(c.get("/planet/ads-lp"))
    assert "Every field in the corn belt, imaged today." not in lp
