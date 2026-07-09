"""Hero image generation — offline fallbacks, cache determinism, prompt safety, non-blocking page."""
from __future__ import annotations

import json
import os
from unittest.mock import patch

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_gen as IG

c = TestClient(app)


class _Req:
    client = None

    def __init__(self, params=None, headers=None):
        self.query_params = params or {}
        self.headers = headers or {}


def _ctx(**overrides):
    base = {
        "channel": "direct",
        "ad_variant_id": None,
        "audience": "neutral",
        "audience_route": "neutral",
        "industry": "general",
        "region": None,
        "top_objection": None,
    }
    base.update(overrides)
    return base


def test_offline_no_api_key_returns_gallery_or_gradient(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    receipt = IG.get_hero_image(_ctx(), generate=False)
    assert receipt["source"] in ("gallery", "gradient")
    assert receipt["source"] != "pending"


def test_pending_when_api_key_set_but_not_cached(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    receipt = IG.get_hero_image(_ctx(), generate=False)
    assert receipt["source"] == "pending"
    hero = IG.resolve_hero_image({"entry": {"channel": "direct"}, "det": {},
                                    "audience": "neutral", "audience_route": "neutral",
                                    "objections": {"prioritized": []}}, generate=False)
    assert hero["status"] == "pending"
    assert hero["fallback"] == "gradient"


def test_cache_hit_same_url(monkeypatch, tmp_path):
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    prompt = IG.build_image_prompt(_ctx(audience_route="b2b_hire", industry="technology"))
    key = IG.image_cache_key(prompt)
    (tmp_path / "images").mkdir(parents=True)
    (tmp_path / "images" / f"{key}.png").write_bytes(b"\x89PNG\r\n")
    manifest = {key: {"source": "generated", "prompt": prompt, "model": IG._model(),
                      "vendor": IG.VENDOR, "cache_key": key, "ext": "png",
                      "generated_at": "2026-07-09T00:00:00+00:00", "license": "test"}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    r1 = IG.get_hero_image(_ctx(audience_route="b2b_hire", industry="technology"))
    r2 = IG.get_hero_image(_ctx(audience_route="b2b_hire", industry="technology"))
    assert r1["url"] == r2["url"]
    assert r1["url"] == f"/static/generated/{key}.png"


def test_api_mocked_generation_receipt(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    fake_png = b"\x89PNG\r\n\x01"
    monkeypatch.setattr(IG, "_call_image_api", lambda p: {"b64": __import__("base64").b64encode(fake_png).decode(), "ext": "png"})
    ctx = _ctx(industry="technology", region="Texas")
    receipt = IG.get_hero_image(ctx, generate=True)
    assert receipt["source"] == "generated"
    assert receipt["prompt"]
    assert receipt["model"]
    assert receipt["vendor"]
    assert receipt["cache_key"]
    assert receipt["generated_at"]
    assert receipt["url"].startswith("/static/generated/")


def test_page_html_returns_200_without_blocking(monkeypatch):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    with patch.object(IG, "_call_image_api", side_effect=AssertionError("API must not run on page load")):
        r = c.get("/gauntlet?utm_source=x&utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09")
    assert r.status_code == 200
    assert "gauntlet-hero" in r.text


def test_prompt_builder_excludes_pii_and_hold():
    page = GS.build_page(_Req({"utm_medium": "email", "e": GS.sample_magic_token()}),
                         email="maya.chen@gauntletai.com")
    ctx = IG.build_image_ctx(page)
    prompt = IG.build_image_prompt(ctx)
    low = prompt.lower()
    assert "maya" not in low
    assert "chen" not in low
    assert "@" not in prompt
    assert "cedar health" not in low
    assert "income" not in low
    assert "gauntletai.com" not in low


def test_hero_image_api_offline(monkeypatch):
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    r = c.get("/api/gauntlet/hero-image?utm_medium=paid")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert data["source"] in ("gallery", "gradient")


def test_dev_trace_includes_hero_image_stage():
    page = GS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-keyword-ai-hiring"}))
    stages = [t["stage"] for t in page["trace"]]
    assert "Hero image resolve" in stages
    assert page.get("hero_image")



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
        assert "Cinematic wide hero" in prompt
        return {
            "b64": base64.b64encode(fake_png).decode(),
            "ext": "png",
            "vendor": IG.GEMINI_VENDOR,
        }

    monkeypatch.setattr(IG, "_call_gemini_image_api", _fake_gemini)
    receipt = IG.get_hero_image(_ctx(), generate=True)
    assert receipt["source"] == "generated"
    assert receipt["vendor"] == "google-gemini"


def test_call_image_api_routes_to_gemini(monkeypatch):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "AQ.test")
    monkeypatch.setenv("IMAGE_GEN_API_URL", IG.DEFAULT_GEMINI_API_URL)
    called = {}

    def _fake(prompt, *, url, key):
        called["url"] = url
        called["key_set"] = bool(key)
        return {"b64": "aW1n", "ext": "png", "vendor": IG.GEMINI_VENDOR}

    monkeypatch.setattr(IG, "_call_gemini_image_api", _fake)
    out = IG._call_image_api("safe abstract hero")
    assert out and out["vendor"] == IG.GEMINI_VENDOR
    assert called["url"] == IG.DEFAULT_GEMINI_API_URL
