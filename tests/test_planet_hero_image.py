"""Planet hero image generation — intents, anti-surveillance guardrails, tenant cache
keys (planet:base:… / planet:delta:…), non-blocking page, and the YAML framework."""
from __future__ import annotations

import json
from unittest.mock import patch

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II
from pipeline.personalization import planet_site as PS

c = TestClient(app)

TENANT = "planet"


class _Req:
    client = None

    def __init__(self, params=None, headers=None):
        self.query_params = params or {}
        self.headers = headers or {}


def _ctx(**overrides):
    base = {
        "channel": "ad",
        "ad_variant_id": None,
        "audience": "neutral",
        "audience_route": "neutral",
        "industry": "general",
        "region": None,
        "tier": 0,
        "top_objection": None,
        "top_objections": [],
        "cta_primary": "Talk to Sales",
        "_hold": {},
    }
    base.update(overrides)
    return base


def _make_page(params):
    return PS.build_page(_Req(params))


def _prompt_text(ctx):
    return IG.prompt_text(IG.build_image_prompt(ctx, tenant=TENANT))


# --- Intent selection ---

def test_crop_belt_ad_cloud_objection_selects_message_match_and_regional_truth():
    page = _make_page({
        "utm_medium": "paid",
        "utm_campaign": "x-location-crop-belts",
        "utm_content": "v01",
    })
    ctx = IG.build_image_ctx(page)
    assert ctx["top_objection"] == "cloud_cover"
    sel = IG.select_image_intent(ctx, tenant=TENANT)
    ids = [p["intent_id"] for p in sel["intents"]]
    assert "message_match" in ids
    assert "regional_truth" in ids
    assert sel["primary"]["intent_id"] == "message_match"


def test_defense_ad_selects_mission_authority():
    page = _make_page({
        "utm_medium": "paid",
        "utm_campaign": "x-lookalike-defense",
        "utm_content": "v02",
    })
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx, tenant=TENANT)
    assert sel["primary"]["intent_id"] == "mission_authority"


def test_maritime_ad_selects_mission_authority():
    page = _make_page({
        "utm_medium": "paid",
        "utm_campaign": "x-interest-maritime",
        "utm_content": "v07",
    })
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx, tenant=TENANT)
    assert sel["primary"]["intent_id"] == "mission_authority"


def test_insurance_ad_verification_objection_selects_archive_advantage():
    page = _make_page({
        "utm_medium": "paid",
        "utm_campaign": "x-event-insurance",
        "utm_content": "v03",
    })
    ctx = IG.build_image_ctx(page)
    assert ctx["top_objection"] == "verification_trust"
    sel = IG.select_image_intent(ctx, tenant=TENANT)
    assert sel["primary"]["intent_id"] == "archive_advantage"


def test_crisis_engager_selects_retarget_warm():
    page = _make_page({
        "utm_medium": "paid",
        "utm_campaign": "x-engager-crisis",
        "utm_content": "v08",
    })
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx, tenant=TENANT)
    assert sel["primary"]["intent_id"] == "retarget_warm"


def test_researcher_ads_select_aspiration_research():
    for campaign, content in (("x-movies-earth-docs", "v09"), ("x-age-early-career", "v11")):
        page = _make_page({"utm_medium": "paid", "utm_campaign": campaign, "utm_content": content})
        ctx = IG.build_image_ctx(page)
        sel = IG.select_image_intent(ctx, tenant=TENANT)
        assert sel["primary"]["intent_id"] == "aspiration_research", campaign


def test_neutral_direct_defaults_to_regional_truth():
    page = _make_page({})
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx, tenant=TENANT)
    assert sel["primary"]["intent_id"] == "regional_truth"


def test_intent_selection_deterministic():
    page = _make_page({"utm_medium": "paid", "utm_campaign": "x-location-crop-belts", "utm_content": "v01"})
    ctx = IG.build_image_ctx(page)
    assert IG.select_image_intent(ctx, tenant=TENANT) == IG.select_image_intent(ctx, tenant=TENANT)


# --- Structured prompt + guardrails ---

def test_structured_prompt_has_provenance_fields():
    page = _make_page({"utm_medium": "paid", "utm_campaign": "x-location-crop-belts", "utm_content": "v01"})
    structured = IG.build_image_prompt(IG.build_image_ctx(page), tenant=TENANT)
    assert structured["intent_id"] == "message_match"
    assert structured["conversion_goal"]
    assert structured["sales_technique"]
    assert structured["personalization_layers"]
    assert structured["full_prompt"]
    assert structured["drives_action"] == "trial_cta"        # cloud_cover → trial_cta
    assert structured["pairs_with_objection"] == "cloud_cover"
    assert structured["tenant"] == "planet"
    for item in structured["must_avoid"]:
        assert "NO" in item


def test_prompt_builder_excludes_pii_and_hold():
    page = PS.build_page(_Req({"utm_medium": "email", "e": PS.sample_magic_token()}),
                         email="amara.diallo@meridianagronomy.com")
    prompt = _prompt_text(IG.build_image_ctx(page))
    low = prompt.lower()
    assert "amara" not in low
    assert "diallo" not in low
    assert "@" not in prompt
    assert "meridian" not in low
    assert "income" not in low
    assert "pacificrelief" not in low


def test_hold_facts_logged_in_receipt_not_in_prompt(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    page = PS.build_page(_Req({"utm_medium": "email", "e": PS.sample_magic_token()}),
                         email="amara.diallo@meridianagronomy.com")
    receipt = IG.get_hero_image(IG.build_image_ctx(page), generate=False, tenant=TENANT)
    prompt = receipt["prompt"].lower()
    assert "amara" not in prompt
    blocked = receipt.get("guardrails_blocked") or []
    assert any("hold_source" in b or "visitor_name" in b for b in blocked)


def test_tier_strips_industry_layer(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    ctx = _ctx(industry="agriculture", tier=0, ad_variant_id="x-agriculture",
               top_objections=["cloud_cover"], audience_route="enterprise")
    structured = IG.build_image_prompt(ctx, tenant=TENANT)
    layers = [l["layer"] for l in structured["personalization_layers"]]
    assert "industry" not in layers
    assert any("industry" in b for b in (structured.get("guardrails_blocked") or []))


def test_anti_surveillance_guardrails_in_every_prompt():
    """Planet's brand-specific rules: region scale only, never property scale."""
    page = _make_page({"utm_medium": "paid", "utm_campaign": "x-location-crop-belts", "utm_content": "v01"})
    structured = IG.build_image_prompt(IG.build_image_ctx(page), tenant=TENANT)
    avoid_blob = " ".join(structured["must_avoid"]).lower()
    assert "no text" in avoid_blob
    assert "no faces" in avoid_blob
    assert "company logos" in avoid_blob
    assert "street-level or property-scale" in avoid_blob
    assert "private homes" in avoid_blob
    assert "crosshairs" in avoid_blob or "targeting reticles" in avoid_blob


def test_region_layer_ships_at_tier_1_the_location_signal():
    """Region (the Planet differentiator) reaches the image prompt when tier ≥ 1."""
    ctx = _ctx(region="Iowa", tier=1, ad_variant_id="x-agriculture",
               audience_route="enterprise")
    structured = IG.build_image_prompt(ctx, tenant=TENANT)
    layers = {l["layer"]: l for l in structured["personalization_layers"]}
    assert "region_mood" in layers
    assert "Iowa" in layers["region_mood"]["value"]
    assert layers["region_mood"]["disposition"] == "allude"
    # …and is stripped below tier 1
    cold = IG.build_image_prompt(_ctx(region="Iowa", tier=0, ad_variant_id="x-agriculture"),
                                 tenant=TENANT)
    assert "region_mood" not in [l["layer"] for l in cold["personalization_layers"]]


# --- Offline / cache / API ---

def test_offline_no_api_key_returns_gallery_or_gradient(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    receipt = IG.get_hero_image(_ctx(), generate=False, tenant=TENANT)
    assert receipt["source"] in ("gallery", "gradient")
    assert receipt["source"] != "pending"
    assert receipt.get("intent_id")


def test_pending_when_api_key_set_but_not_cached(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    receipt = IG.get_hero_image(_ctx(), generate=False, tenant=TENANT)
    assert receipt["source"] == "pending"
    assert receipt.get("intent_id") == "regional_truth"
    hero = IG.resolve_hero_image({"entry": {"channel": "direct"}, "det": {},
                                  "audience": "neutral", "audience_route": "neutral",
                                  "objections": {"prioritized": []},
                                  "sections": {"hero": {"cta_primary": "Talk to Sales"}}},
                                 generate=False, tenant=TENANT)
    assert hero["status"] == "pending"
    assert hero["fallback"] == "gradient"


def test_cache_hit_same_url(monkeypatch, tmp_path):
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    ctx = _ctx(audience_route="enterprise", industry="agriculture", tier=2)
    resolved = IG._resolve_prompts(ctx, tenant=TENANT)
    prompt = resolved["gen_prompt"]
    key = resolved["gen_disk_key"]
    (tmp_path / "images").mkdir(parents=True)
    (tmp_path / "images" / f"{key}.png").write_bytes(b"\x89PNG\r\n")
    manifest = {key: {"source": "generated", "prompt": prompt, "model": IG._model(),
                      "vendor": IG.VENDOR, "cache_key": key, "ext": "png",
                      "generated_at": "2026-07-09T00:00:00+00:00", "license": "test",
                      "intent_id": "mission_authority", "tier": "base+delta"}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    r1 = IG.get_hero_image(ctx, tenant=TENANT)
    r2 = IG.get_hero_image(ctx, tenant=TENANT)
    assert r1["url"] == r2["url"]
    assert r1["url"] == f"/static/generated/{key}.png"


def test_api_mocked_generation_receipt(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    fake_png = b"\x89PNG\r\n\x01"
    monkeypatch.setattr(IG, "_call_image_api", lambda p: {"b64": __import__("base64").b64encode(fake_png).decode(), "ext": "png"})
    ctx = _ctx(industry="agriculture", region="Iowa", tier=2)
    receipt = IG.get_hero_image(ctx, generate=True, tenant=TENANT)
    assert receipt["source"] == "generated"
    assert receipt["prompt"]
    assert receipt["model"]
    assert receipt["vendor"]
    assert receipt["cache_key"]
    assert receipt["generated_at"]
    assert receipt["intent_id"]
    assert receipt["drives_action"]
    assert receipt["url"].startswith("/static/generated/")


def test_planet_page_html_returns_200_without_blocking(monkeypatch):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    with patch.object(IG, "_call_image_api", side_effect=AssertionError("API must not run on page load")):
        r = c.get("/planet?utm_source=x&utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01")
    assert r.status_code == 200
    assert "planet-hero" in r.text


def test_hero_image_api_offline(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    r = c.get("/api/planet/hero-image?utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert data["source"] in ("gallery", "gradient")
    assert data["receipt"].get("intent_id")


def test_portal_hero_image_api_prefixes_static_urls(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    qs = "?utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01"
    r = c.get(f"/planetapt/api/hero-image{qs}")
    assert r.status_code == 200
    data = r.json()
    if data.get("url"):
        assert data["url"].startswith("/planetapt/static/generated/")
    assert data["receipt"].get("intent_id")


def test_dev_trace_includes_hero_image_stage():
    page = PS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-location-crop-belts", "utm_content": "v01"}))
    stages = [t["stage"] for t in page["trace"]]
    assert "Hero image resolve" in stages
    assert page.get("hero_image")
    receipt = page["hero_image"]["receipt"]
    assert receipt.get("intent_id") == "message_match"
    hero_trace = next(t for t in page["trace"] if t["stage"] == "Hero image resolve")
    assert any("intent=" in s for s in hero_trace["signals"])
    assert page["hero_image"].get("dev")


def test_dev_panel_shows_intent_provenance():
    r = c.get("/planet/dev?utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01")
    assert r.status_code == 200
    assert "message_match" in r.text
    assert "Hero background" in r.text and "decisioning" in r.text
    assert "Intent selection" in r.text
    assert "rule fired:" in r.text
    assert "Personalization layers" in r.text
    assert "Two-tier cache" in r.text
    assert "Prompt assembly" in r.text
    assert "Guardrails applied" in r.text
    assert "Fallback chain" in r.text
    assert "Without generation" in r.text


def test_dev_shows_intent_selection_fields():
    page = PS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-location-crop-belts", "utm_content": "v01"}))
    dev = page["hero_image"]["dev"]
    assert dev["intent_selection"]["rule_fired"]
    assert dev["intent_selection"]["primary_id"] == "message_match"
    assert len(dev["intent_selection"]["intents"]) >= 2
    assert dev["conversion"]["drives_action"] == "trial_cta"
    assert dev["prompt"]["visual_metaphor"]
    assert dev["prompt"]["full_prompt"]


def test_dev_shows_guardrails_blocked_when_tier_strips_industry(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    ctx = _ctx(industry="agriculture", tier=0, ad_variant_id="x-agriculture",
               top_objections=["cloud_cover"], audience_route="enterprise")
    receipt = IG.get_hero_image(ctx, generate=False, tenant=TENANT)
    dev = IG.hero_image_dev_panel({"receipt": receipt, "status": "ready", "fallback": "gradient", "url": None})
    blocked_codes = [g["code"] for g in dev["guardrails"]["blocked"]]
    assert any("industry" in b for b in blocked_codes)
    r = c.get("/planet/dev?utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01")
    assert r.status_code == 200
    assert "Guardrails applied" in r.text


# --- YAML framework ---

def test_intent_taxonomy_complete():
    expected = {"regional_truth", "change_proof", "mission_authority", "archive_advantage",
                "aspiration_research", "retarget_warm", "message_match"}
    cfg = IG.load_image_config(TENANT)
    assert set(cfg["intent_by_id"]) == expected


def test_planet_yaml_loads_via_framework():
    cfg = IG.load_image_config(TENANT)
    assert cfg["tenant"] == "planet"
    assert len(cfg["intents"]) == 7
    assert cfg["selection"]["primary_rules"]
    assert cfg["action_map"]["objection_pairs"]["tasked_competitor"] == "sales_cta"
    assert cfg["action_map"]["route_defaults"]["research"] == "research_cta"
    assert cfg["brand"]["accent_color"] == "#3ba1ff"
    # tenant-specific anti-surveillance guardrails present
    additions = " ".join(cfg["brand"]["must_avoid_additions"]).lower()
    assert "property-scale" in additions


def test_planet_ad_metaphors_cover_all_twelve_variants():
    cfg = IG.load_image_config(TENANT)
    metaphors = cfg.get("ad_metaphors") or {}
    for v in PS.AD_VARIANTS:
        assert v["id"] in metaphors, f"missing ad_metaphor for {v['id']}"


def test_three_persona_example_prompts():
    """Crop-belt agronomy, defense GEOINT, early-career researcher — distinct intents/actions."""
    cases = [
        ({"utm_medium": "paid", "utm_campaign": "x-location-crop-belts", "utm_content": "v01"},
         "message_match", "trial_cta"),
        ({"utm_medium": "paid", "utm_campaign": "x-lookalike-defense", "utm_content": "v02"},
         "mission_authority", "sales_cta"),
        ({"utm_medium": "paid", "utm_campaign": "x-age-early-career", "utm_content": "v11"},
         "aspiration_research", "research_cta"),
    ]
    for params, intent, action in cases:
        structured = IG.build_image_prompt(IG.build_image_ctx(_make_page(params)), tenant=TENANT)
        assert structured["intent_id"] == intent, params
        assert structured["drives_action"] == action, params
        assert structured["full_prompt"]


# --- Two-tier base + delta (tenant planet cache keys) ---

def test_segment_only_visitor_uses_base_key_no_delta():
    ctx = _ctx(ad_variant_id="x-agriculture", audience_route="enterprise", tier=0)
    assert IG.delta_cache_key(ctx, tenant=TENANT) is None
    base_prompt, base_structured, _ = IG.build_base_prompt(ctx, tenant=TENANT)
    assert IG.build_personalization_delta(ctx, base_structured, tenant=TENANT) is None
    receipt = IG.get_hero_image(ctx, generate=False, tenant=TENANT)
    assert receipt["tier"] == "base_only"
    assert receipt["base_cache_key"] == "planet:base:x-agriculture"
    assert receipt.get("delta_cache_key") is None


def test_objection_and_industry_appends_delta():
    ctx = _ctx(ad_variant_id="x-agriculture", audience_route="enterprise",
               top_objections=["cloud_cover"], industry="agriculture", tier=2)
    base_prompt, base_structured, _ = IG.build_base_prompt(ctx, tenant=TENANT)
    delta = IG.build_personalization_delta(ctx, base_structured, tenant=TENANT)
    assert delta is not None
    delta_prompt, layers = delta
    layer_names = {l["layer"] for l in layers}
    assert "objection_theme" in layer_names
    assert "industry" in layer_names
    receipt = IG.get_hero_image(ctx, generate=False, tenant=TENANT)
    assert receipt["tier"] == "base+delta"
    assert receipt["delta_cache_key"]
    assert receipt["delta_cache_key"].startswith("planet:delta:")
    assert "objection:cloud_cover" in receipt["delta_signals"]


def test_region_only_visitor_gets_location_delta():
    """The location signal alone (tier 1 + region) creates a personalization delta."""
    ctx = _ctx(ad_variant_id="x-agriculture", audience_route="enterprise",
               region="Iowa", tier=1)
    signals = II._tier2_signals_present(ctx, IG.load_image_config(TENANT))
    assert "region:Iowa" in signals
    key = IG.delta_cache_key(ctx, tenant=TENANT)
    assert key and key.startswith("planet:delta:")


def test_same_segment_same_base_cache_key():
    ctx_a = _ctx(ad_variant_id="x-agriculture", audience_route="enterprise", tier=0)
    ctx_b = _ctx(ad_variant_id="x-agriculture", audience_route="enterprise", tier=0,
                 top_objections=["price_opacity"])
    _, struct_a, _ = IG.build_base_prompt(ctx_a, tenant=TENANT)
    _, struct_b, _ = IG.build_base_prompt(ctx_b, tenant=TENANT)
    key_a = IG.segment_cache_key(ctx_a, struct_a["intent_id"], tenant=TENANT)
    key_b = IG.segment_cache_key(ctx_b, struct_b["intent_id"], tenant=TENANT)
    assert key_a == key_b == "planet:base:x-agriculture"


def test_receipt_tier_field_populated(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    ctx = _ctx(ad_variant_id="x-agriculture", top_objections=["cloud_cover"], tier=0)
    receipt = IG.get_hero_image(ctx, generate=False, tenant=TENANT)
    assert receipt["tier"] in ("base_only", "base+delta")
    assert receipt["base_cache_key"]
    hero = IG.resolve_hero_image({"entry": {"channel": "ad"}, "det": {},
                                  "ad_variant": {"id": "x-agriculture"},
                                  "audience": "neutral", "audience_route": "neutral",
                                  "objections": {"prioritized": [{"objection_id": "cloud_cover", "rank": 1}]},
                                  "sections": {"hero": {"cta_primary": "Talk to Sales"}}},
                                 generate=False, tenant=TENANT)
    assert hero["dev"]["tier"]["mode"] == "base+delta"


def test_pregen_dry_run_lists_planet_segment_keys():
    from scripts.pregen_segment_images import _segment_specs
    specs = _segment_specs("planet")
    assert len(specs) >= 12
    keys = {s["key"] for s in specs}
    assert "planet:base:x-agriculture" in keys
    assert "planet:base:x-defense" in keys
    assert any(k.startswith("planet:base:regional_truth:") for k in keys)
    # the gauntlet default is untouched
    gauntlet = {s["key"] for s in _segment_specs()}
    assert "gauntlet:base:x-keyword" in gauntlet


def test_agriculture_plus_region_cache_keys():
    ctx = _ctx(ad_variant_id="x-agriculture", top_objections=["cloud_cover"],
               industry="agriculture", region="Iowa", tier=2)
    _, struct, _ = IG.build_base_prompt(ctx, tenant=TENANT)
    base_key = IG.segment_cache_key(ctx, struct["intent_id"], tenant=TENANT)
    delta_key = IG.delta_cache_key(ctx, tenant=TENANT)
    assert base_key == "planet:base:x-agriculture"
    assert delta_key and delta_key.startswith("planet:delta:")
    signals = II._tier2_signals_present(ctx, IG.load_image_config(TENANT))
    assert "objection:cloud_cover" in signals
    assert "industry:agriculture" in signals
    assert "region:Iowa" in signals
