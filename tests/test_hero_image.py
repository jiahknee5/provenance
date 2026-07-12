"""Hero image generation — intents, guardrails, cache determinism, non-blocking page."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

from app.main import app
from pipeline.common.config import RULES_DIR
from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II

c = TestClient(app)

TEMPLATE_PATH = RULES_DIR / "_image_template.yaml"


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
        "cta_primary": "Hire Proven Talent",
        "_hold": {},
    }
    base.update(overrides)
    return base


def _make_page(params):
    return GS.build_page(_Req(params))


def _prompt_text(ctx):
    return IG.prompt_text(IG.build_image_prompt(ctx))


# --- Intent selection ---

def test_keyword_ad_hire_objection_selects_message_match_and_peer_proof():
    page = _make_page({
        "utm_medium": "paid",
        "utm_campaign": "x-keyword-ai-hiring",
        "utm_content": "v09",
    })
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx)
    ids = [p["intent_id"] for p in sel["intents"]]
    assert "message_match" in ids
    assert "peer_proof" in ids
    assert sel["primary"]["intent_id"] == "message_match"
    assert "keyword" in sel["primary"]["why"].lower() or "ad" in sel["primary"]["why"].lower()


def test_hr_event_ld_budget_selects_roi_clarity():
    page = _make_page({
        "utm_medium": "paid",
        "utm_campaign": "x-event-hrtech",
        "utm_content": "v07",
    })
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx)
    assert sel["primary"]["intent_id"] == "roi_clarity"


def test_engineer_interest_challenger_route_selects_aspiration():
    page = _make_page({
        "utm_medium": "paid",
        "utm_campaign": "x-interest-ai-ml",
        "utm_content": "v11",
    })
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx)
    assert sel["primary"]["intent_id"] == "aspiration"


def test_post_engager_selects_retarget_warm():
    page = _make_page({
        "utm_medium": "paid",
        "utm_campaign": "x-engager-retarget",
        "utm_content": "v08",
    })
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx)
    assert sel["primary"]["intent_id"] == "retarget_warm"


def test_intent_selection_deterministic():
    page = _make_page({"utm_medium": "paid", "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09"})
    ctx = IG.build_image_ctx(page)
    assert IG.select_image_intent(ctx) == IG.select_image_intent(ctx)


# --- Structured prompt + guardrails ---

def test_structured_prompt_has_provenance_fields():
    page = _make_page({"utm_medium": "paid", "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09"})
    structured = IG.build_image_prompt(IG.build_image_ctx(page))
    assert structured["intent_id"] == "message_match"
    assert structured["conversion_goal"]
    assert structured["sales_technique"]
    assert structured["personalization_layers"]
    assert structured["full_prompt"]
    assert structured["drives_action"] == "hire_cta"
    assert structured["pairs_with_objection"] == "open_market_hire"
    for item in structured["must_avoid"]:
        assert "NO" in item


def test_prompt_builder_excludes_pii_and_hold():
    page = GS.build_page(_Req({"utm_medium": "email", "e": GS.sample_magic_token()}),
                         email="maya.chen@gauntletai.com")
    prompt = _prompt_text(IG.build_image_ctx(page))
    low = prompt.lower()
    assert "maya" not in low
    assert "chen" not in low
    assert "@" not in prompt
    assert "cedar health" not in low
    assert "income" not in low
    assert "gauntletai.com" not in low


def test_hold_facts_logged_in_receipt_not_in_prompt(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    page = GS.build_page(_Req({"utm_medium": "email", "e": GS.sample_magic_token()}),
                         email="maya.chen@gauntletai.com")
    receipt = IG.get_hero_image(IG.build_image_ctx(page), generate=False)
    prompt = receipt["prompt"].lower()
    assert "maya" not in prompt
    blocked = receipt.get("guardrails_blocked") or []
    assert any("hold_source" in b or "visitor_name" in b for b in blocked)


def test_tier_strips_industry_layer(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    ctx = _ctx(industry="technology", tier=0, ad_variant_id="x-keyword",
               top_objections=["open_market_hire"], audience_route="b2b_hire")
    structured = IG.build_image_prompt(ctx)
    layers = [l["layer"] for l in structured["personalization_layers"]]
    assert "industry" not in layers
    assert any("industry" in b for b in (structured.get("guardrails_blocked") or []))


def test_must_avoid_enforced_in_every_prompt():
    page = _make_page({"utm_medium": "paid", "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09"})
    structured = IG.build_image_prompt(IG.build_image_ctx(page))
    avoid_blob = " ".join(structured["must_avoid"]).lower()
    assert "no text" in avoid_blob
    assert "no faces" in avoid_blob
    assert "company logos" in avoid_blob
    assert "employer names" in avoid_blob


# --- Offline / cache / API ---

def test_offline_no_api_key_returns_gallery_or_gradient(monkeypatch, tmp_path):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    # isolate from the shipped warm cache — this asserts the no-key cache-miss path
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    receipt = IG.get_hero_image(_ctx(), generate=False)
    assert receipt["source"] in ("gallery", "gradient")
    assert receipt["source"] != "pending"
    assert receipt.get("intent_id")


def test_pending_when_api_key_set_but_not_cached(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    receipt = IG.get_hero_image(_ctx(), generate=False)
    assert receipt["source"] == "pending"
    assert receipt.get("intent_id") == "peer_proof"
    hero = IG.resolve_hero_image({"entry": {"channel": "direct"}, "det": {},
                                    "audience": "neutral", "audience_route": "neutral",
                                    "objections": {"prioritized": []},
                                    "sections": {"hero": {"cta_primary": "Hire"}}},
                                   generate=False)
    assert hero["status"] == "pending"
    assert hero["fallback"] == "gradient"


def test_cache_hit_same_url(monkeypatch, tmp_path):
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    ctx = _ctx(audience_route="b2b_hire", industry="technology", tier=2)
    resolved = IG._resolve_prompts(ctx)
    prompt = resolved["gen_prompt"]
    key = resolved["gen_disk_key"]
    (tmp_path / "images").mkdir(parents=True)
    (tmp_path / "images" / f"{key}.png").write_bytes(b"\x89PNG\r\n")
    manifest = {key: {"source": "generated", "prompt": prompt, "model": IG._model(),
                      "vendor": IG.VENDOR, "cache_key": key, "ext": "png",
                      "generated_at": "2026-07-09T00:00:00+00:00", "license": "test",
                      "intent_id": "authority", "tier": "base+delta"}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    r1 = IG.get_hero_image(ctx)
    r2 = IG.get_hero_image(ctx)
    assert r1["url"] == r2["url"]
    assert r1["url"] == f"/static/generated/{key}.png"


def test_api_mocked_generation_receipt(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    fake_png = b"\x89PNG\r\n\x01"
    monkeypatch.setattr(IG, "_call_image_api", lambda p, **kw: {"b64": __import__("base64").b64encode(fake_png).decode(), "ext": "png"})
    ctx = _ctx(industry="technology", region="Texas", tier=2)
    receipt = IG.get_hero_image(ctx, generate=True)
    assert receipt["source"] == "generated"
    assert receipt["prompt"]
    assert receipt["model"]
    assert receipt["vendor"]
    assert receipt["cache_key"]
    assert receipt["generated_at"]
    assert receipt["intent_id"]
    assert receipt["drives_action"]
    assert receipt["url"].startswith("/static/generated/")


def test_make_page_html_returns_200_without_blocking(monkeypatch):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    with patch.object(IG, "_call_image_api", side_effect=AssertionError("API must not run on page load")):
        r = c.get("/gauntlet?utm_source=x&utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09")
    assert r.status_code == 200
    assert "gauntlet-hero" in r.text


def test_hero_image_api_offline(monkeypatch, tmp_path):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    # isolate from the shipped warm cache — this test asserts the cache-miss path
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    r = c.get("/api/gauntlet/hero-image?utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert data["source"] in ("gallery", "gradient")
    assert data["receipt"].get("intent_id")


def test_portal_hero_image_api_prefixes_static_urls(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    qs = "?utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09"
    r = c.get(f"/gauntletapt/api/hero-image{qs}")
    assert r.status_code == 200
    data = r.json()
    if data.get("url"):
        assert data["url"].startswith("/gauntletapt/static/generated/")
    assert data["receipt"].get("intent_id")


def test_dev_trace_includes_hero_image_stage():
    page = GS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09"}))
    stages = [t["stage"] for t in page["trace"]]
    assert "Hero image resolve" in stages
    assert page.get("hero_image")
    receipt = page["hero_image"]["receipt"]
    assert receipt.get("intent_id") == "message_match"
    hero_trace = next(t for t in page["trace"] if t["stage"] == "Hero image resolve")
    assert any("intent=" in s for s in hero_trace["signals"])
    assert page["hero_image"].get("dev")


def test_dev_panel_shows_intent_provenance():
    r = c.get("/dev?utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09")
    assert r.status_code == 200
    assert "message_match" in r.text
    assert "Hero background" in r.text and "decisioning" in r.text
    assert "Intent selection" in r.text
    assert "rule fired:" in r.text
    assert "Drives action" in r.text or "drives hire_cta" in r.text
    assert "Personalization layers" in r.text
    assert "Two-tier cache" in r.text
    assert "Prompt assembly" in r.text
    assert "Guardrails applied" in r.text
    assert "Fallback chain" in r.text
    assert "Without generation" in r.text


def test_dev_shows_intent_selection_fields():
    page = GS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09"}))
    dev = page["hero_image"]["dev"]
    assert dev["intent_selection"]["rule_fired"]
    assert dev["intent_selection"]["primary_id"] == "message_match"
    assert len(dev["intent_selection"]["intents"]) >= 2
    assert dev["conversion"]["drives_action"] == "hire_cta"
    assert dev["prompt"]["visual_metaphor"]
    assert dev["prompt"]["full_prompt"]


def test_dev_shows_guardrails_blocked_when_tier_strips_industry(monkeypatch, tmp_path):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    # isolate from the shipped warm cache — a cache hit would return the cached
    # receipt (no industry to strip at warm time) instead of this ctx's guardrails
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    ctx = _ctx(industry="technology", tier=0, ad_variant_id="x-keyword",
               top_objections=["open_market_hire"], audience_route="b2b_hire")
    receipt = IG.get_hero_image(ctx, generate=False)
    dev = IG.hero_image_dev_panel({"receipt": receipt, "status": "ready", "fallback": "gradient", "url": None})
    blocked_codes = [g["code"] for g in dev["guardrails"]["blocked"]]
    assert any("industry" in b for b in blocked_codes)
    page = _make_page({"utm_medium": "paid", "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09"})
    r = c.get("/dev?utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09")
    assert r.status_code == 200
    assert "Guardrails applied" in r.text


def test_gemini_api_mocked_generation_vendor(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "AQ.test-google-key")
    monkeypatch.setenv(
        "IMAGE_GEN_API_URL",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent",
    )
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    import base64

    fake_png = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x01])

    def _fake_gemini(prompt, *, url, key):
        assert "Intent:" in prompt or "Primary intent:" in prompt
        assert "Must avoid:" in prompt
        return ({
            "b64": base64.b64encode(fake_png).decode(),
            "ext": "png",
            "vendor": IG.GEMINI_VENDOR,
        }, "success", 42)

    monkeypatch.setattr(IG, "_call_gemini_image_api", _fake_gemini)
    receipt = IG.get_hero_image(_ctx(ad_variant_id="x-keyword", audience_route="b2b_hire",
                                     top_objections=["open_market_hire"]), generate=True)
    assert receipt["source"] == "generated"
    assert receipt["vendor"] == "google-gemini"


def test_call_image_api_routes_to_gemini(monkeypatch):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "AQ.test")
    monkeypatch.setenv("IMAGE_GEN_API_URL", IG.DEFAULT_GEMINI_API_URL)
    called = {}

    def _fake(prompt, *, url, key):
        called["url"] = url
        called["key_set"] = bool(key)
        return ({"b64": "aW1n", "ext": "png", "vendor": IG.GEMINI_VENDOR}, "success", 10)

    monkeypatch.setattr(IG, "_call_gemini_image_api", _fake)
    out = IG._call_image_api("safe abstract hero")
    assert out and out["vendor"] == IG.GEMINI_VENDOR
    assert called["url"] == IG.DEFAULT_GEMINI_API_URL


def test_intent_taxonomy_complete():
    expected = {"peer_proof", "loss_avoidance", "authority", "aspiration",
                "roi_clarity", "retarget_warm", "message_match"}
    cfg = IG.load_image_config("gauntlet")
    assert set(cfg["intent_by_id"]) == expected


def test_gauntlet_yaml_loads_via_framework():
    cfg = IG.load_image_config("gauntlet")
    assert cfg["tenant"] == "gauntlet"
    assert len(cfg["intents"]) == 7
    assert cfg["selection"]["primary_rules"]
    assert cfg["action_map"]["objection_pairs"]["open_market_hire"] == "hire_cta"


def test_template_yaml_loads():
    cfg = II.load_image_config("_template", path=TEMPLATE_PATH)
    assert cfg["tenant"] == "your_company_slug"
    assert len(cfg["intents"]) >= 2
    assert "peer_proof" in cfg["intent_by_id"]
    assert cfg["guardrails"]["tier_gates"]["industry"] == 2


def test_guardrails_global_must_avoid_independent_of_tenant():
    """Global guardrails apply even with minimal tenant must_avoid."""
    cfg = II.load_image_config("_template", path=TEMPLATE_PATH)
    ctx = _ctx(tier=0, industry="technology")
    ctx["_hold"] = {"visitor_name": "Jane Doe", "company": "Acme Corp"}
    sel = II.select_image_intent(ctx, cfg)
    structured = II.build_structured_prompt(ctx, sel, cfg)
    guarded = II.apply_guardrails(structured, ctx, cfg)
    avoid_blob = " ".join(guarded["must_avoid"]).lower()
    assert "no text" in avoid_blob
    assert "no faces" in avoid_blob
    assert "no pii" in avoid_blob or "employer names" in avoid_blob
    assert any("hold_source" in b for b in (guarded.get("guardrails_blocked") or []))


def test_template_selects_default_intent():
    cfg = II.load_image_config("_template", path=TEMPLATE_PATH)
    sel = II.select_image_intent(_ctx(), cfg)
    assert sel["primary"]["intent_id"] == "peer_proof"


def test_three_persona_example_prompts():
    """Keyword CTO, HR event, Engineer interest — distinct intents and actions."""
    cases = [
        ({"utm_medium": "paid", "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09"},
         "message_match", "hire_cta"),
        ({"utm_medium": "paid", "utm_campaign": "x-event-hrtech", "utm_content": "v07"},
         "roi_clarity", "catalyst_cta"),
        ({"utm_medium": "paid", "utm_campaign": "x-interest-ai-ml", "utm_content": "v11"},
         "aspiration", "challenger_cta"),
    ]
    for params, intent, action in cases:
        structured = IG.build_image_prompt(IG.build_image_ctx(_make_page(params)))
        assert structured["intent_id"] == intent, params
        assert structured["drives_action"] == action, params
        assert structured["full_prompt"]


# --- Two-tier base + delta ---

def test_segment_only_visitor_uses_base_key_no_delta():
    ctx = _ctx(ad_variant_id="x-keyword", audience_route="b2b_hire", tier=0)
    assert IG.delta_cache_key(ctx) is None
    base_prompt, base_structured, _ = IG.build_base_prompt(ctx)
    assert IG.build_personalization_delta(ctx, base_structured) is None
    receipt = IG.get_hero_image(ctx, generate=False)
    assert receipt["tier"] == "base_only"
    assert receipt["base_cache_key"] == "gauntlet:base:x-keyword"
    assert receipt.get("delta_cache_key") is None


def test_objection_and_industry_appends_delta():
    ctx = _ctx(ad_variant_id="x-keyword", audience_route="b2b_hire",
               top_objections=["open_market_hire"], industry="technology", tier=2)
    base_prompt, base_structured, _ = IG.build_base_prompt(ctx)
    delta = IG.build_personalization_delta(ctx, base_structured)
    assert delta is not None
    delta_prompt, layers = delta
    layer_names = {l["layer"] for l in layers}
    assert "objection_theme" in layer_names
    assert "industry" in layer_names
    receipt = IG.get_hero_image(ctx, generate=False)
    assert receipt["tier"] == "base+delta"
    assert receipt["delta_cache_key"]
    assert "objection:open_market_hire" in receipt["delta_signals"]


def test_same_segment_same_base_cache_key():
    ctx_a = _ctx(ad_variant_id="x-keyword", audience_route="b2b_hire", tier=0)
    ctx_b = _ctx(ad_variant_id="x-keyword", audience_route="b2b_hire", tier=0,
                 top_objections=["placement_fees"])
    _, struct_a, _ = IG.build_base_prompt(ctx_a)
    _, struct_b, _ = IG.build_base_prompt(ctx_b)
    key_a = IG.segment_cache_key(ctx_a, struct_a["intent_id"])
    key_b = IG.segment_cache_key(ctx_b, struct_b["intent_id"])
    assert key_a == key_b == "gauntlet:base:x-keyword"


def test_receipt_tier_field_populated(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    ctx = _ctx(ad_variant_id="x-keyword", top_objections=["open_market_hire"], tier=0)
    receipt = IG.get_hero_image(ctx, generate=False)
    assert receipt["tier"] in ("base_only", "base+delta")
    assert receipt["base_cache_key"]
    hero = IG.resolve_hero_image({"entry": {"channel": "ad"}, "det": {},
                                  "ad_variant": {"id": "x-keyword"},
                                  "audience": "neutral", "audience_route": "neutral",
                                  "objections": {"prioritized": [{"objection_id": "open_market_hire", "rank": 1}]},
                                  "sections": {"hero": {"cta_primary": "Hire"}}},
                                 generate=False)
    assert hero["dev"]["tier"]["mode"] == "base+delta"


def test_pregen_dry_run_lists_segment_keys():
    from scripts.pregen_segment_images import _segment_specs
    specs = _segment_specs()
    assert len(specs) >= 12
    keys = {s["key"] for s in specs}
    assert "gauntlet:base:x-keyword" in keys
    assert any(k.startswith("gauntlet:base:peer_proof:") for k in keys)


def test_keyword_plus_industry_cache_keys():
    ctx = _ctx(ad_variant_id="x-keyword", top_objections=["open_market_hire"],
               industry="technology", tier=2)
    _, struct, _ = IG.build_base_prompt(ctx)
    base_key = IG.segment_cache_key(ctx, struct["intent_id"])
    delta_key = IG.delta_cache_key(ctx)
    assert base_key == "gauntlet:base:x-keyword"
    assert delta_key and delta_key.startswith("gauntlet:delta:")
    assert "objection:open_market_hire" in II._tier2_signals_present(ctx, IG.load_image_config())
    assert "industry:technology" in II._tier2_signals_present(ctx, IG.load_image_config())
