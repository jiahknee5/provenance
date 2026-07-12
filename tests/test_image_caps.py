"""T-06 image lane — S3.3 prebuild caps + realtime daily ceiling (R35/R35a).

Covers the four PANEL-locked behaviors:
  1. Prebuild cap enforcement — K=8 states/target, 24 baked/tenant, 80 global;
     scripts/warm_hero_cache.py --check FAILS (exit 1) on any violation.
  2. Per-tenant realtime daily spend ceiling ($5 default, APT_REALTIME_CEILING_USD)
     checked via api_costs BEFORE a realtime generate; past the ceiling the target
     serves its neutral prebuilt/gradient fallback — logged, never silent.
  3. Cost-logged realtime path — success and 429 both write exactly one ledger row
     (only the HTTP transport is faked, like test_wf_design_matrix; the ledger,
     ceiling, and cache logic are real).
  4. Offline ($0) deterministic fallback, and registry-driven surfaces: targets
     beyond hero/og (sections.list_image_targets) resolve with their own keys.

No real API calls anywhere — httpx.post is monkeypatched or must never fire.
"""
from __future__ import annotations

import base64
import contextlib
import io
import json

import pytest
import yaml

from pipeline.observability import api_costs as AC
from pipeline.personalization import image_gen as IG
from pipeline.personalization import prebuild as PB
from pipeline.personalization import sections as SEC
import scripts.warm_hero_cache as W

PNG_B64 = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 32).decode()


def _ctx(**overrides):
    base = {
        "channel": "direct",
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


def _isolate_image_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(IG, "CACHE_DIR", tmp_path / "image_cache")
    monkeypatch.setattr(IG, "IMAGE_DIR", tmp_path / "image_cache" / "images")
    monkeypatch.setattr(IG, "MANIFEST", tmp_path / "image_cache" / "manifest.json")


def _isolate_ledger(monkeypatch, tmp_path):
    ledger = tmp_path / "api_cost_ledger.jsonl"
    monkeypatch.setattr(AC, "LEDGER_PATH", ledger)
    return ledger


def _openai_key_env(monkeypatch):
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")   # non-"AQ." → OpenAI-compatible path
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_GEN_API_URL", raising=False)
    monkeypatch.delenv("IMAGE_GEN_MODEL", raising=False)
    monkeypatch.setenv("BRAIN_SIM_BEST_OF_N", "1")        # one candidate per generate — deterministic
    monkeypatch.delenv(IG.REALTIME_CEILING_ENV, raising=False)


class _Resp:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = {}
        self.content = b""

    def json(self):
        return self._payload


def _ledger_rows(ledger):
    if not ledger.exists():
        return []
    return [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]


def _write_manifest_yaml(path, tenant, surfaces):
    """surfaces = {surface_id: n_flagged_states} — minimal valid manifest."""
    data = {
        "tenant": tenant,
        "surfaces": {
            sid: [{"id": f"{sid}-s{i}", "entry": "direct", "identity": "anon",
                   "prebuild": True} for i in range(n)]
            for sid, n in surfaces.items()
        },
    }
    path.write_text(yaml.safe_dump(data))
    return path


# --------------------------------------------------------------------------- #
# 1 · Prebuild caps (S3.3) — the shipped manifest and the --check deploy gate
# --------------------------------------------------------------------------- #
def test_repo_manifests_within_caps_and_check_mode_passes():
    """The version-controlled manifests obey K=8/target, 24/tenant, 80 global —
    and the deploy-gate check mode agrees (exit 0)."""
    assert PB.check_prebuild_caps() == []
    for p in PB.manifest_paths():
        _, counts = PB._flagged_counts(p)
        assert sum(counts.values()) <= PB.CAP_IMAGES_PER_TENANT, p.name
        for sid, n in counts.items():
            assert n <= PB.CAP_STATES_PER_TARGET, f"{p.name}:{sid}"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = W.main(["--check"])
    assert rc == 0
    assert "prebuild cap check OK" in buf.getvalue()


def test_gauntlet_og_short_list_not_hero_mirror():
    """S3.3: og carries its own explicit short list — no YAML-anchor mirroring
    of hero's flag set."""
    manifest = PB.load_prebuild_manifest()
    hero_flagged = [s["id"] for s in manifest["surfaces"]["hero"] if s.get("prebuild", True)]
    og_flagged = [s["id"] for s in manifest["surfaces"]["og"] if s.get("prebuild", True)]
    assert 0 < len(hero_flagged) <= PB.CAP_STATES_PER_TARGET
    assert 0 < len(og_flagged) <= PB.CAP_STATES_PER_TARGET
    assert set(og_flagged) != set(hero_flagged), "og must not mirror hero's flag list"


def test_per_target_cap_violation_rejected(tmp_path):
    p = _write_manifest_yaml(tmp_path / "t1_prebuild.yaml", "t1",
                             {"hero": PB.CAP_STATES_PER_TARGET + 1})
    violations = PB.check_prebuild_caps([p])
    assert len(violations) == 1
    assert "cap 8/target" in violations[0] and "hero" in violations[0]


def test_per_tenant_cap_violation_rejected(tmp_path):
    # 4 surfaces × 7 flagged = 28 > 24, while every surface is within K=8
    p = _write_manifest_yaml(tmp_path / "t1_prebuild.yaml", "t1",
                             {"hero": 7, "og": 7, "banner": 7, "card": 7})
    violations = PB.check_prebuild_caps([p])
    assert len(violations) == 1
    assert "/tenant" in violations[0] and "28" in violations[0]


def test_global_cap_violation_rejected(tmp_path):
    # 4 tenants × 24 flagged = 96 > 80, while every tenant/target is within caps
    paths = [
        _write_manifest_yaml(tmp_path / f"t{i}_prebuild.yaml", f"t{i}",
                             {"hero": 8, "og": 8, "banner": 8})
        for i in range(4)
    ]
    violations = PB.check_prebuild_caps(paths)
    assert len(violations) == 1
    assert "global" in violations[0] and "96" in violations[0]


def test_warm_check_mode_fails_gate_on_violation(monkeypatch, tmp_path, capsys):
    """scripts/warm_hero_cache.py --check exits 1 when a manifest exceeds a cap —
    the deploy/railway.sh gate line."""
    rules = tmp_path / "rules"
    rules.mkdir()
    _write_manifest_yaml(rules / "t1_prebuild.yaml", "t1",
                         {"hero": PB.CAP_STATES_PER_TARGET + 2})
    monkeypatch.setattr(PB, "RULES_DIR", rules)
    rc = W.main(["--check"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "CAP VIOLATION" in captured.err
    assert "prebuild cap check FAILED" in captured.err


def test_registry_prebuilt_states_cap_tightens_target_cap(monkeypatch, tmp_path):
    """A registry prebuilt_states_cap below K tightens the per-target cap."""
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "t9_sections.yaml").write_text(yaml.safe_dump({
        "version": 1,
        "tenant": "t9",
        "sections": [{
            "id": "hero",
            "image_targets": [{
                "surface_id": "hero", "label": "Hero", "workflow": "prebuilt",
                "prebuilt_states_cap": 4,
            }],
        }],
    }))
    monkeypatch.setattr(SEC, "RULES_DIR", rules)
    p = _write_manifest_yaml(rules / "t9_prebuild.yaml", "t9", {"hero": 5})
    violations = PB.check_prebuild_caps([p])
    assert len(violations) == 1
    assert "cap 4/target" in violations[0]


# --------------------------------------------------------------------------- #
# 2 · Realtime daily ceiling (S3.3) — blocked past $5/day, logged, not silent
# --------------------------------------------------------------------------- #
def test_ceiling_blocks_realtime_generate_and_logs(monkeypatch, tmp_path):
    ledger = _isolate_ledger(monkeypatch, tmp_path)
    _isolate_image_cache(monkeypatch, tmp_path)
    _openai_key_env(monkeypatch)
    # today's gauntlet spend already past the $5 default ceiling
    AC.record_call(tenant="gauntlet", service="gemini_image",
                   model="gemini-2.5-flash-image", operation="generate_image",
                   status="success", estimated_cost_usd=5.25)

    def _no_network(*a, **kw):
        raise AssertionError("httpx.post must not be called past the ceiling")

    monkeypatch.setattr(IG.httpx, "post", _no_network)
    receipt = IG.get_surface_image(_ctx(), generate=True)
    assert receipt["source"] in ("gallery", "gradient")
    assert "realtime_ceiling" in receipt["fallback_chain"]

    rows = _ledger_rows(ledger)
    block = [r for r in rows if r["operation"] == "realtime_ceiling_block"]
    assert len(block) == 1, "ceiling refusal must be logged, not silent"
    assert block[0]["status"] == "blocked"
    assert block[0]["estimated_cost_usd"] == 0.0
    assert block[0]["ceiling_usd"] == IG.DEFAULT_REALTIME_CEILING_USD
    assert block[0]["spend_today_usd"] >= 5.25
    assert block[0]["tenant"] == "gauntlet"


def test_ceiling_serves_neutral_prebuilt_base_when_baked(monkeypatch, tmp_path):
    """Past the ceiling, a base+delta visitor gets the baked segment base —
    the neutral prebuilt — instead of a fresh generation."""
    ledger = _isolate_ledger(monkeypatch, tmp_path)
    _isolate_image_cache(monkeypatch, tmp_path)
    _openai_key_env(monkeypatch)
    AC.record_call(tenant="gauntlet", service="gemini_image",
                   model="gemini-2.5-flash-image", operation="generate_image",
                   status="success", estimated_cost_usd=9.99)
    monkeypatch.setattr(IG.httpx, "post",
                        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("no network")))

    ctx = _ctx(industry="technology", region="Texas", tier=2)
    resolved = IG._resolve_prompts(ctx)
    assert resolved["tier"] == "base+delta"
    base_key = resolved["base_disk_key"]
    IG.IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    (IG.IMAGE_DIR / f"{base_key}.png").write_bytes(b"\x89PNG\r\n")
    IG.MANIFEST.write_text(json.dumps({base_key: {
        "source": "generated", "prompt": resolved["base_prompt"], "model": IG._model(),
        "vendor": IG.VENDOR, "cache_key": base_key, "ext": "png",
        "generated_at": "2026-07-09T00:00:00+00:00", "license": "test",
    }}))

    receipt = IG.get_surface_image(ctx, generate=True)
    assert receipt["source"] == "generated"
    assert receipt["cache_key"] == base_key
    assert receipt["fallback_chain"] == ["cache_miss", "realtime_ceiling", "prebuilt_base"]
    assert any(r["operation"] == "realtime_ceiling_block" for r in _ledger_rows(ledger))


def test_ceiling_env_override(monkeypatch, tmp_path):
    ledger = _isolate_ledger(monkeypatch, tmp_path)
    _isolate_image_cache(monkeypatch, tmp_path)
    _openai_key_env(monkeypatch)

    # zero budget → blocked immediately, even with an empty ledger
    monkeypatch.setenv(IG.REALTIME_CEILING_ENV, "0")
    monkeypatch.setattr(IG.httpx, "post",
                        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("no network")))
    receipt = IG.get_surface_image(_ctx(), generate=True)
    assert "realtime_ceiling" in receipt["fallback_chain"]

    # raised ceiling → the same visitor generates (spend $5.25 < $100)
    AC.record_call(tenant="gauntlet", service="gemini_image",
                   model="gemini-2.5-flash-image", operation="generate_image",
                   status="success", estimated_cost_usd=5.25)
    monkeypatch.setenv(IG.REALTIME_CEILING_ENV, "100")
    monkeypatch.setattr(IG.httpx, "post",
                        lambda url, **kw: _Resp(200, {"data": [{"b64_json": PNG_B64}]}))
    receipt = IG.get_surface_image(_ctx(), generate=True)
    assert receipt["source"] == "generated"

    # garbage env is a hard error — never a silent default (Art X)
    monkeypatch.setenv(IG.REALTIME_CEILING_ENV, "five dollars")
    with pytest.raises(ValueError):
        IG.realtime_ceiling_usd()


# --------------------------------------------------------------------------- #
# 3 · Cost-logged realtime path (S3.1/R35a) — success + 429, transport-only fake
# --------------------------------------------------------------------------- #
def test_realtime_generate_cost_logged_success(monkeypatch, tmp_path):
    ledger = _isolate_ledger(monkeypatch, tmp_path)
    _isolate_image_cache(monkeypatch, tmp_path)
    _openai_key_env(monkeypatch)
    monkeypatch.setattr(IG.httpx, "post",
                        lambda url, **kw: _Resp(200, {"data": [{"b64_json": PNG_B64}]}))

    receipt = IG.get_surface_image(_ctx(), generate=True)
    assert receipt["source"] == "generated"
    rows = _ledger_rows(ledger)
    gen = [r for r in rows if r["operation"] in ("generate_image", "best_of_n_candidate")]
    assert len(gen) >= 1
    assert all(r["status"] == "success" and r["estimated_cost_usd"] > 0 for r in gen)
    assert any(r["cache_key"] == receipt["cache_key"] for r in gen)
    # replay: second resolve is a cache hit — no new ledger rows, identical url
    n_rows = len(_ledger_rows(ledger))
    again = IG.get_surface_image(_ctx(), generate=True)
    assert again["url"] == receipt["url"]
    assert len(_ledger_rows(ledger)) == n_rows


def test_realtime_generate_429_logged_and_falls_back(monkeypatch, tmp_path):
    ledger = _isolate_ledger(monkeypatch, tmp_path)
    _isolate_image_cache(monkeypatch, tmp_path)
    _openai_key_env(monkeypatch)
    monkeypatch.setattr(IG.httpx, "post", lambda url, **kw: _Resp(429))

    receipt = IG.get_surface_image(_ctx(), generate=True)
    assert receipt["source"] in ("gallery", "gradient")
    assert "api_failed" in receipt["fallback_chain"]
    rows = [r for r in _ledger_rows(ledger) if r["operation"] == "generate_image"]
    assert len(rows) == 1, "a throttled call still writes exactly one ledger row"
    assert rows[0]["status"] == "429"
    assert rows[0]["estimated_cost_usd"] == 0.0
    assert rows[0]["images_generated"] == 0


# --------------------------------------------------------------------------- #
# 4 · Offline default + registry-driven surfaces beyond hero/og
# --------------------------------------------------------------------------- #
def test_offline_fallback_deterministic_and_zero_cost(monkeypatch, tmp_path):
    ledger = _isolate_ledger(monkeypatch, tmp_path)
    _isolate_image_cache(monkeypatch, tmp_path)
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)

    r1 = IG.get_surface_image(_ctx(), generate=True)
    r2 = IG.get_surface_image(_ctx(), generate=True)
    assert r1 == r2, "offline fallback must be deterministic"
    assert r1["source"] in ("gallery", "gradient")
    assert _ledger_rows(ledger) == [], "offline path costs $0 — no ledger rows"


def test_registry_image_targets_drive_surface_ids():
    """The registry (sections.list_image_targets) drives the surface list: every
    registered target resolves, with registry workflow metadata on the spec."""
    for tenant in ("gauntlet", "planet"):
        registered = {t["surface_id"] for t in SEC.list_image_targets(tenant)}
        assert registered <= set(IG.list_surface_ids(tenant=tenant))
    # registry workflow lands on the spec (gauntlet baked, planet realtime)
    assert IG.surface_spec("hero", tenant="gauntlet")["workflow"] == "prebuilt"
    assert IG.surface_spec("hero", tenant="planet")["workflow"] == "realtime"
    assert IG.surface_spec("og", tenant="gauntlet")["section_id"] == "hero"


def test_registry_target_beyond_hero_og_resolves(monkeypatch, tmp_path):
    """A target beyond hero/og registered in <tenant>_sections.yaml resolves
    through the image lane with its own surface-scoped cache key."""
    rules = tmp_path / "rules"
    rules.mkdir()
    (rules / "gauntlet_sections.yaml").write_text(yaml.safe_dump({
        "version": 1,
        "tenant": "gauntlet",
        "sections": [{
            "id": "hero",
            "image_targets": [
                {"surface_id": "hero", "label": "Hero background",
                 "workflow": "prebuilt", "prebuilt_states_cap": 8},
                {"surface_id": "og", "label": "Open Graph / social preview",
                 "workflow": "prebuilt", "prebuilt_states_cap": 8},
            ],
        }, {
            "id": "cta",
            "image_targets": [
                {"surface_id": "cta_banner", "label": "CTA banner backdrop",
                 "workflow": "realtime"},
            ],
        }],
    }))
    monkeypatch.setattr(SEC, "RULES_DIR", rules)
    monkeypatch.delenv("IMAGE_GEN_API_KEY", raising=False)
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    _isolate_image_cache(monkeypatch, tmp_path)

    assert "cta_banner" in IG.list_surface_ids(tenant="gauntlet")
    spec = IG.surface_spec("cta_banner", tenant="gauntlet")
    assert spec["label"] == "CTA banner backdrop"
    assert spec["workflow"] == "realtime"
    assert spec["section_id"] == "cta"

    banner = IG.get_surface_image(_ctx(), surface_id="cta_banner")
    hero = IG.get_surface_image(_ctx(), surface_id="hero")
    assert banner["source"] in ("gallery", "gradient")
    assert banner["cache_key"] != hero["cache_key"], "surface id must scope the cache key"
