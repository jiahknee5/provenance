"""Planet hero motion — cache keys, manifest metadata, template wiring, gauntlet off."""
from __future__ import annotations

import io
import json
from unittest.mock import patch

from PIL import Image
from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import image_gen as IG
from pipeline.personalization import motion_gen as MG
from pipeline.personalization import planet_site as PS

c = TestClient(app)
TENANT = "planet"


class _Req:
    client = None

    def __init__(self, params=None, headers=None):
        self.query_params = params or {}
        self.headers = headers or {}


def _solid_frame(color: tuple[int, int, int], size=(64, 36)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def _write_motion_fixture(monkeypatch, tmp_path, disk_key: str, n_frames: int = 3):
    cache = tmp_path / "image_cache"
    images = cache / "images"
    motion = images / "motion"
    frames = images / "motion_frames" / disk_key
    motion.mkdir(parents=True)
    frames.mkdir(parents=True)
    frame_rows = []
    raw_frames = []
    for i in range(n_frames):
        data = _solid_frame((40 + i * 50, 80, 120))
        ext = "png"
        rel = f"motion_frames/{disk_key}/frame_{i}.{ext}"
        (images / rel).write_bytes(data)
        raw_frames.append((data, ext))
        frame_rows.append({
            "index": i,
            "label": f"t{i}",
            "ext": ext,
            "image_path": rel,
            "image_url": f"/static/generated/{rel}",
        })
    webp = MG.assemble_animated_webp(raw_frames, duration_ms=900, loop=True)
    (motion / f"{disk_key}.webp").write_bytes(webp)
    manifest = {
        MG._manifest_key(disk_key): {
            "source": "generated",
            "motion_metaphor": "pan_left",
            "assembly": "animated_webp",
            "duration_ms": 900,
            "loop": True,
            "cache_key": disk_key,
            "ext": "webp",
            "motion_type": "animated_webp",
            "frames": frame_rows,
            "intent_id": "regional_truth",
            "tier": "base_only",
            "base_cache_key": f"{TENANT}:motion:base:x-agriculture",
        }
    }
    (cache / "manifest.json").write_text(json.dumps(manifest))
    monkeypatch.setattr(IG, "CACHE_DIR", cache)
    monkeypatch.setattr(IG, "IMAGE_DIR", images)
    monkeypatch.setattr(IG, "MANIFEST", cache / "manifest.json")
    monkeypatch.setattr(MG, "MOTION_SUBDIR", "motion")


def test_motion_cache_key_deterministic():
    ctx = {
        "ad_variant_id": "x-agriculture",
        "audience_route": "enterprise",
    }
    k1 = MG.motion_segment_cache_key(ctx, "message_match", tenant=TENANT)
    k2 = MG.motion_segment_cache_key(ctx, "message_match", tenant=TENANT)
    assert k1 == k2 == f"{TENANT}:motion:base:x-agriculture"
    disk = MG.motion_disk_key(k1, "gemini-2.5-flash-image")
    assert len(disk) == 32
    assert MG.motion_disk_key(k1, "gemini-2.5-flash-image") == disk


def test_motion_metaphor_from_intent_yaml():
    config = IG.load_image_config(TENANT)
    ctx = {"ad_variant_id": None, "audience_route": "neutral"}
    assert MG.motion_metaphor(ctx, "change_proof", config) == "change_wipe"
    ctx_ad = {"ad_variant_id": "x-insurance", "audience_route": "enterprise"}
    assert MG.motion_metaphor(ctx_ad, "archive_advantage", config) == "storm_footprint"


def test_motion_manifest_metadata(monkeypatch, tmp_path):
    ctx = {"ad_variant_id": "x-agriculture", "audience_route": "enterprise"}
    sem = MG.motion_segment_cache_key(ctx, "message_match", tenant=TENANT)
    disk = MG.motion_disk_key(sem)
    _write_motion_fixture(monkeypatch, tmp_path, disk)
    loaded = MG._load_motion_cached(disk)
    assert loaded is not None
    assert loaded["motion_metaphor"] == "pan_left"
    assert len(loaded["frames"]) == 3
    assert loaded["url"].endswith(f"{disk}.webp")


def test_resolve_hero_image_includes_motion_url(monkeypatch, tmp_path):
    ctx_page = PS.build_page(_Req({
        "utm_medium": "paid",
        "utm_campaign": "x-location-crop-belts",
        "utm_content": "v01",
    }))
    img_ctx = IG.build_image_ctx(ctx_page)
    keys = MG._resolve_motion_keys(img_ctx, tenant=TENANT)
    disk = keys["disk_key"]
    _write_motion_fixture(monkeypatch, tmp_path, disk)

    hero = IG.resolve_hero_image({
        "entry": ctx_page["entry"],
        "det": ctx_page["det"],
        "identity": ctx_page["identity"],
        "ad_variant": ctx_page["ad_variant"],
        "audience": ctx_page["audience"],
        "audience_route": ctx_page["audience_route"],
        "tier": ctx_page["tier"],
        "objections": ctx_page["objections"],
        "sections": ctx_page["sections"],
    }, tenant=TENANT)
    assert hero.get("motion_url")
    assert hero.get("motion_type") == "animated_webp"
    assert hero.get("motion_status") == "ready"
    assert hero["dev"]["motion"]["preview"]["has_motion"]


def test_planet_template_renders_motion_img(monkeypatch, tmp_path):
    ctx_page = PS.build_page(_Req({
        "utm_medium": "paid",
        "utm_campaign": "x-location-crop-belts",
        "utm_content": "v01",
    }))
    img_ctx = IG.build_image_ctx(ctx_page)
    keys = MG._resolve_motion_keys(img_ctx, tenant=TENANT)
    disk = keys["disk_key"]
    _write_motion_fixture(monkeypatch, tmp_path, disk)

    with patch.object(IG, "_api_key", return_value="test-key"):
        r = c.get("/planet?utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01")
    assert r.status_code == 200
    assert 'class="hero has-motion"' in r.text or "has-motion" in r.text
    assert ".webp" in r.text


def test_planet_template_falls_back_without_motion(monkeypatch, tmp_path):
    cache = tmp_path / "image_cache"
    images = cache / "images"
    images.mkdir(parents=True)
    monkeypatch.setattr(IG, "CACHE_DIR", cache)
    monkeypatch.setattr(IG, "IMAGE_DIR", images)
    monkeypatch.setattr(IG, "MANIFEST", cache / "manifest.json")
    (cache / "manifest.json").write_text("{}")
    r = c.get("/planet")
    assert r.status_code == 200
    assert 'class="hero has-motion"' not in r.text
    assert 'data-motion-url=""' in r.text or "data-motion-url=\"\"" in r.text


def test_gauntlet_motion_disabled():
    config = IG.load_image_config("gauntlet")
    assert not MG.motion_enabled(config)
    page = {
        "entry": {"channel": "direct"},
        "det": {},
        "identity": None,
        "ad_variant": None,
        "audience": "neutral",
        "audience_route": "neutral",
        "tier": 0,
        "objections": {"prioritized": []},
        "sections": {"hero": {}, "compare": {"emphasis": "monitor"}},
    }
    hero = IG.resolve_hero_image(page, tenant="gauntlet")
    assert hero.get("motion_url") is None
    assert hero.get("motion_status") in (None, "disabled")


def test_frame_prompts_include_framing():
    prompts = MG.build_frame_prompts(
        "Base satellite hero.",
        metaphor="change_wipe",
        n_frames=4,
        framing="Simulated timelapse only.",
    )
    assert len(prompts) == 4
    assert all("Simulated timelapse only." in p for p in prompts)
    assert "t0" in prompts[0].lower() or "Frame t0" in prompts[0]
