"""Brain simulator scorer — Tribe v2 integration + proxy_v1 MVP."""
from __future__ import annotations

import struct
import zlib

from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II
from pipeline.personalization.brain_simulator import (
    BrainSimulatorScorer,
    GeneratedCandidate,
    brain_sim_enabled,
    intent_brain_fields,
)


def _minimal_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """Build a valid RGB PNG for deterministic scorer tests."""
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", 13) + b"IHDR" + ihdr
    ihdr_chunk += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    raw_rows = bytearray()
    r, g, b = rgb
    for _ in range(height):
        raw_rows.append(0)
        for _ in range(width):
            raw_rows.extend((r, g, b))
    compressed = zlib.compress(bytes(raw_rows), 9)
    idat_chunk = struct.pack(">I", len(compressed)) + b"IDAT" + compressed
    idat_chunk += struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    return header + ihdr_chunk + idat_chunk + iend


def _gradient_png(width: int, height: int) -> bytes:
    """PNG with vertical luminance gradient (higher scene_depth / approach scores)."""
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", 13) + b"IHDR" + ihdr
    ihdr_chunk += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    raw_rows = bytearray()
    for y in range(height):
        raw_rows.append(0)
        lum = int(40 + (y / max(height - 1, 1)) * 180)
        for _ in range(width):
            raw_rows.extend((lum, lum + 20, min(255, lum + 60)))
    compressed = zlib.compress(bytes(raw_rows), 9)
    idat_chunk = struct.pack(">I", len(compressed)) + b"IDAT" + compressed
    idat_chunk += struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    return header + ihdr_chunk + idat_chunk + iend


def test_planet_intents_load_brain_target_mapping():
    cfg = II.load_image_config("planet")
    assert brain_sim_enabled(cfg)
    for intent in cfg["intents"]:
        target, regions = intent_brain_fields(intent)
        assert target, intent["id"]
        assert regions, intent["id"]
        assert intent["brain_target"] == target


def test_gauntlet_intents_have_brain_fields_but_disabled_by_default():
    cfg = II.load_image_config("gauntlet")
    assert not brain_sim_enabled(cfg)
    for intent in cfg["intents"]:
        assert intent.get("brain_target")
        assert intent.get("brain_regions")


def test_scorer_deterministic_for_fixed_bytes():
    scorer = BrainSimulatorScorer()
    blob = _minimal_png(32, 24, (30, 80, 140))
    ctx = {"prompt": "satellite dusk navy calm", "must_avoid": ["NO surveillance"]}
    a = scorer.score(blob, "attention", ["v1", "v4", "intraparietal"], ctx)
    b = scorer.score(blob, "attention", ["v1", "v4", "intraparietal"], ctx)
    assert a["total"] == b["total"]
    assert a["brain_simulator"] == "proxy_v1"
    assert "v1" in a["region_scores"]


def test_best_of_n_selects_highest_scoring_candidate():
    scorer = BrainSimulatorScorer()
    flat = _minimal_png(40, 30, (50, 50, 50))
    rich = _gradient_png(40, 30)
    candidates = [
        GeneratedCandidate(0, flat),
        GeneratedCandidate(1, rich),
    ]
    winner, best, all_scores = scorer.select_best(
        candidates, "approach", ["ventral_striatum", "ppa_depth"],
        {"prompt": "warm dawn accent approach", "must_avoid": []},
    )
    assert winner.index in (0, 1)
    assert best["total"] == max(s["total"] for s in all_scores)


def test_guardrail_violation_penalized():
    scorer = BrainSimulatorScorer()
    # Cross-like pattern: white cross on black
    w, h = 40, 40
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", 13) + b"IHDR" + ihdr
    ihdr_chunk += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    raw_rows = bytearray()
    for y in range(h):
        raw_rows.append(0)
        for x in range(w):
            if abs(y - h // 2) <= 1 or abs(x - w // 2) <= 1:
                raw_rows.extend((250, 250, 250))
            else:
                raw_rows.extend((5, 5, 5))
    compressed = zlib.compress(bytes(raw_rows), 9)
    idat_chunk = struct.pack(">I", len(compressed)) + b"IDAT" + compressed
    idat_chunk += struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    cross_png = header + ihdr_chunk + idat_chunk + iend
    calm = _minimal_png(40, 40, (40, 60, 90))
    cross_score = scorer.score(
        cross_png, "trust", ["amygdala_threat_proxy", "ppa"],
        {"must_avoid": ["NO surveillance"], "prompt": "calm map-room"},
    )
    calm_score = scorer.score(
        calm, "trust", ["amygdala_threat_proxy", "ppa"],
        {"must_avoid": ["NO surveillance"], "prompt": "calm map-room"},
    )
    assert cross_score["guardrail_penalty"] > calm_score["guardrail_penalty"]


def test_image_gen_receipt_includes_brain_fields_planet(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    png_a = _minimal_png(24, 16, (20, 40, 80))
    png_b = _gradient_png(24, 16)
    calls = iter([
        {"b64": __import__("base64").b64encode(png_a).decode(), "ext": "png"},
        {"b64": __import__("base64").b64encode(png_b).decode(), "ext": "png"},
        {"b64": __import__("base64").b64encode(png_b).decode(), "ext": "png"},
    ] * 4)
    monkeypatch.setattr(IG, "_call_image_api", lambda p: next(calls, None))
    ctx = {
        "channel": "ad",
        "ad_variant_id": "x-agriculture",
        "audience_route": "neutral",
        "industry": "general",
        "region": None,
        "tier": 0,
        "top_objection": None,
        "top_objections": [],
        "_hold": {},
    }
    receipt = IG.get_hero_image(ctx, generate=True, tenant="planet")
    assert receipt["source"] == "generated"
    assert receipt.get("brain_simulator") == "proxy_v1"
    assert receipt.get("brain_target")
    assert receipt.get("brain_score") is not None
    assert receipt.get("candidates_evaluated", 0) >= 2
    assert "brain_region_scores" in receipt


def test_gauntlet_brain_scoring_off_by_default(monkeypatch, tmp_path):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "manifest.json")
    png = _minimal_png(16, 16, (10, 10, 10))
    monkeypatch.setattr(
        IG, "_call_image_api",
        lambda p: {"b64": __import__("base64").b64encode(png).decode(), "ext": "png"},
    )
    ctx = {
        "channel": "direct",
        "ad_variant_id": None,
        "audience_route": "b2b_hire",
        "industry": "technology",
        "tier": 2,
        "top_objections": [],
        "_hold": {},
    }
    receipt = IG.get_hero_image(ctx, generate=True, tenant="gauntlet")
    assert receipt["source"] == "generated"
    assert receipt.get("brain_simulator") is None
