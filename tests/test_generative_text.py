"""T-05 — the opt-in generative text mode (S2/R31), against the REAL Gate (Art VII):

  * a planted lie / superlative / competitor-recite / hold-fact candidate is 0-servable
    from a generative target's pool — structurally absent, never filtered (Art II);
  * the offline default is $0 and deterministic — no key, no cost rows, byte-identical
    candidate synthesis on every build;
  * workflow prebuilt: scripts/warm_copy_cache.py bakes candidates with stable bytes and
    candidates_for() replays the baked bytes (the pool still re-Gates them);
  * workflow realtime: serve() caches the pick by visit key — same key, same variant,
    one impression;
  * the keyed path records an api_costs row per REAL Anthropic call (transport faked,
    ledger logic real) and replays from LLMCache at $0 thereafter.

Registry fixtures ride a tmp rules dir (tenant = config, Art V) because the T-01 seed
registries are pinned deterministic-only by test_sections_registry until T-08 binds the
generative rows.
"""
from __future__ import annotations

import json
import random
import textwrap

import pytest

from pipeline.common import config
from pipeline.common.cache import LLMCache
from pipeline.common.db import connect
from pipeline.common.store import PosteriorStore
from pipeline.observability import api_costs as AC
from pipeline.personalization import creative as CR
from pipeline.personalization import decision_pool as DP
from pipeline.personalization import generative_text as GT
from pipeline.personalization import sections
from pipeline.personalization.decision_pool import ALL_CELL, ROUTES, DecisionPool
from scripts import warm_copy_cache as WCC

TENANT = "gauntlet"
PREBUILT = ("hero", "hero_sub_gen")          # section, slot — workflow: prebuilt
REALTIME = ("cta", "cta_gen")                # section, slot — workflow: realtime
TRAPS = ("trap_lie", "trap_superlative", "trap_competitor", "trap_hold")

_FIXTURE_REGISTRY = textwrap.dedent("""\
    version: 1
    tenant: gauntlet
    sections:
      - id: hero
        label: "Hero"
        region: hero
        personalize: true
        goal: "T-05 fixture"
        channels: [direct, search, ads, email]
        text_targets:
          - slot_id: hero_sub
            label: "Hero sub (deterministic)"
            mode: deterministic
            workflow: realtime
            strategy: neutral
            policy: say
            source: catalog
            claims: []
            prompt: ""
          - slot_id: hero_sub_gen
            label: "Hero sub (generative pool)"
            mode: generative
            workflow: prebuilt
            strategy: loss-aversion
            policy: allude
            source: catalog
            claims: []
            prompt: "Hero sub for an AI fellowship: outcome-led, honest, no superlatives, no competitor names, no invented numbers."
            gate: helix_tenant
        image_targets: []
        guardrails: {}
        evals: [gate_pass, hold_never_ships]
      - id: cta
        label: "Final CTA"
        region: cta
        personalize: true
        goal: "T-05 fixture"
        channels: [direct]
        text_targets:
          - slot_id: cta_gen
            label: "CTA (generative realtime)"
            mode: generative
            workflow: realtime
            strategy: scarcity-honest
            policy: allude
            source: catalog
            claims: []
            prompt: "Closing CTA for an AI fellowship: honest scarcity only with a provable deadline, no superlatives."
            gate: helix_tenant
        image_targets: []
        guardrails: {}
        evals: [gate_pass]
    """)


@pytest.fixture()
def reg(tmp_path, monkeypatch):
    """A tmp registry with generative targets + isolated copy cache + clean GT state."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "gauntlet_sections.yaml").write_text(_FIXTURE_REGISTRY, encoding="utf-8")
    monkeypatch.setattr(sections, "RULES_DIR", rules_dir)
    monkeypatch.setattr(GT, "COPY_CACHE_DIR", tmp_path / "copy_cache")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")     # offline unless a test keys it
    GT.reset_state()
    yield rules_dir
    GT.reset_state()


def _dp(gate, tmp_path, **kw) -> DecisionPool:
    kw.setdefault("posteriors", {TENANT: PosteriorStore("t_gen", "website")})
    kw.setdefault("rng", random.Random(7))
    tmp_path.mkdir(parents=True, exist_ok=True)
    return DecisionPool(gate, GT.candidates_for, db_path=tmp_path / "dp.sqlite",
                        persist=False, **kw)


def _ledger_rows(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


# --------------------------------------------------------------------------- #
# 1 · planted lie / superlative / competitor / hold candidate -> 0-servable
# --------------------------------------------------------------------------- #
def test_planted_traps_zero_servable_from_generative_pool(gate, rules, tmp_path, reg):
    rules.set_hold("mlr_hold_tco", True)                  # the hold-fact trap is LIVE
    dp = _dp(gate, tmp_path)
    sec, slot = PREBUILT
    pid = DecisionPool.pool_id(TENANT, sec, slot)
    cleared = dp.cleared_pool(TENANT, sec, slot)

    assert cleared, "generative target must have a non-empty cleared pool"
    ids = {v.variant_id for v in cleared}
    for trap in TRAPS:
        tid = f"{pid}__{trap}"
        assert tid not in ids
        for cell in ROUTES + (ALL_CELL,):                 # structurally absent everywhere
            assert tid not in dp.active(TENANT, sec, slot, cell)
        with pytest.raises(KeyError):                     # never cleared -> no receipt
            dp.receipt(tid)

    # pick can never return one — every route, many draws
    trap_ids = {f"{pid}__{t}" for t in TRAPS}
    for i in range(120):
        v = dp.pick(TENANT, sec, slot, ROUTES[i % 4], visit_key=f"v{i}")
        assert v is not None and v.variant_id not in trap_ids

    # each trap is blocked for its own reason, on the record
    rep = {r["variant_id"]: r for r in dp.clearance_report(TENANT, sec, slot)}
    assert not rep[f"{pid}__trap_lie"]["claims_cleared"]           # unverifiable -> red
    assert not rep[f"{pid}__trap_hold"]["claims_cleared"]          # held claim -> red
    assert not rep[f"{pid}__trap_superlative"]["copy_ok"]          # copy Gate veto
    assert not rep[f"{pid}__trap_competitor"]["copy_ok"]           # competitor recite veto
    assert any("competitor" in b for b in rep[f"{pid}__trap_competitor"]["copy_blocks"])

    # and every pool member passes the same line check the WF-DESIGN harness applies
    for v in cleared:
        assert CR._line_is_unclean(f"{v.headline} {v.template}") is None
        assert not v.planted_lie


def test_provider_refuses_deterministic_targets(reg):
    with pytest.raises(ValueError, match="mode='deterministic'"):
        GT.candidates_for(TENANT, "hero", "hero_sub")


# --------------------------------------------------------------------------- #
# 2 · offline default: $0, deterministic
# --------------------------------------------------------------------------- #
def test_offline_default_is_zero_dollar_and_deterministic(tmp_path, monkeypatch, reg):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(AC, "LEDGER_PATH", ledger)
    sec, slot = PREBUILT

    a = GT.build_candidates(TENANT, sec, slot, use_cache=False)
    b = GT.build_candidates(TENANT, sec, slot, use_cache=False)
    assert a and a == b                                    # byte-identical synthesis
    assert _ledger_rows(ledger) == []                      # no key -> no API -> $0
    # the deterministic layer + the four probes, nothing else
    assert [v.variant_id for v in a if v.variant_id.startswith("trap_")] == list(TRAPS)
    assert all(v.variant_id.startswith(("gen_", "trap_")) for v in a)


# --------------------------------------------------------------------------- #
# 3 · prebuilt workflow: warm_copy_cache bakes stable bytes; replay serves them
# --------------------------------------------------------------------------- #
def test_warm_copy_cache_bakes_byte_identical_and_pool_regates(gate, tmp_path,
                                                               monkeypatch, reg):
    monkeypatch.setattr(GT, "_build_gate", lambda rule_set: gate)   # real Gate, tmp caches
    sec, slot = PREBUILT

    assert WCC.main(["--tenant", TENANT]) == 0
    path = GT._cache_path(TENANT, sec, slot)
    assert path.exists()
    first = path.read_bytes()

    GT.reset_state()
    assert WCC.main(["--tenant", TENANT, "--force-regen"]) == 0
    assert path.read_bytes() == first                      # byte-identical re-warm

    # candidates_for now REPLAYS the baked bytes — edit the file, the edit serves
    data = json.loads(path.read_text(encoding="utf-8"))
    for c in data["candidates"]:
        if not c["variant_id"].startswith("trap_"):
            c["headline"] = "Baked replay headline"
            c["template"] = "Baked replay headline\nProof attached to every line."
            break
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    replayed = GT.candidates_for(TENANT, sec, slot)
    assert any(v.headline == "Baked replay headline" for v in replayed)

    # the pool still re-Gates baked candidates: traps stay structurally absent
    dp = _dp(gate, tmp_path)
    cleared = dp.cleared_pool(TENANT, sec, slot)
    assert cleared
    assert not {v.variant_id for v in cleared} & \
        {f"{DecisionPool.pool_id(TENANT, sec, slot)}__{t}" for t in ("trap_lie",
                                                                     "trap_superlative",
                                                                     "trap_competitor")}


def test_warm_copy_cache_noop_on_seed_registries(tmp_path, monkeypatch):
    """The T-01 seed registries carry no generative targets yet — the warm script must
    be a clean $0 no-op over them (rc 0, nothing baked)."""
    monkeypatch.setattr(GT, "COPY_CACHE_DIR", tmp_path / "copy_cache")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    GT.reset_state()
    assert WCC.main([]) == 0
    assert not (tmp_path / "copy_cache").exists()


# --------------------------------------------------------------------------- #
# 4 · realtime workflow: serve() caches by visit key
# --------------------------------------------------------------------------- #
def test_realtime_serve_caches_by_visit_key(gate, tmp_path, reg):
    dp = _dp(gate, tmp_path)
    sec, slot = REALTIME

    first = GT.serve(TENANT, sec, slot, route="individual", visit_key="k1", pool=dp)
    again = GT.serve(TENANT, sec, slot, route="individual", visit_key="k1", pool=dp)
    assert first is not None and again is not None
    assert first["variant_id"] == again["variant_id"]      # same key -> same variant
    assert not first["cached"] and again["cached"]
    assert first["receipt"]["mode"] == "generative"
    assert first["receipt"]["workflow"] == "realtime"

    conn = connect(tmp_path / "dp.sqlite")
    try:
        n = conn.execute("SELECT COUNT(*) AS n FROM impressions WHERE recipient_id='k1'",
                         ).fetchone()["n"]
    finally:
        conn.close()
    assert n == 1                                          # the cached hit re-samples nothing

    # a fresh identical pool replays the same variant for the same key (Art IV)
    dp2 = _dp(gate, tmp_path / "b", posteriors={TENANT: PosteriorStore("t_gen2", "website")})
    replay = GT.serve(TENANT, sec, slot, route="individual", visit_key="k1", pool=dp2)
    assert replay["variant_id"] == first["variant_id"]


# --------------------------------------------------------------------------- #
# 5 · keyed path: every real Anthropic call writes a cost row; cache replays $0
# --------------------------------------------------------------------------- #
def test_keyed_path_records_cost_row_and_replays_from_cache(gate, tmp_path, tmp_db,
                                                            monkeypatch, reg):
    anthropic = pytest.importorskip("anthropic")
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(AC, "LEDGER_PATH", ledger)
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setattr(GT, "_get_llm_cache", lambda: LLMCache(tmp_db))

    payload = {"candidates": [
        {"headline": "Proof you can put in front of a buyer",
         "sub": "Every line ships with its source attached."},
        {"headline": "The #1 choice for winning teams",          # the Gate's problem
         "sub": "Better than every alternative out there."},
    ]}

    class _Block:
        type = "text"

        def __init__(self, text):
            self.text = text

    class _Usage:
        input_tokens = 200_000
        output_tokens = 50_000

    class _Resp:
        content = [_Block(json.dumps(payload))]
        usage = _Usage()

    calls = {"n": 0}

    class _FakeAnthropic:                                  # transport fake ONLY
        def __init__(self, **kw):
            self.messages = self

        def create(self, **kw):
            calls["n"] += 1
            return _Resp()

    monkeypatch.setattr(anthropic, "Anthropic", _FakeAnthropic)

    sec, slot = REALTIME
    cands = GT.build_candidates(TENANT, sec, slot, use_cache=False)
    ai = [v for v in cands if v.variant_id.startswith("gen_ai_")]
    assert [v.headline for v in ai] == [c["headline"] for c in payload["candidates"]]

    rows = _ledger_rows(ledger)
    assert calls["n"] == 1 and len(rows) == 1              # one call, one cost row
    row = rows[0]
    assert row["service"] == "anthropic" and row["operation"] == "copy_candidates"
    assert row["tenant"] == TENANT and row["model"] == GT.LLM_MODEL
    assert row["input_tokens"] == 200_000 and row["output_tokens"] == 50_000
    assert row["estimated_cost_usd"] > 0

    # replay: LLMCache hit -> no second call, no second cost row, identical candidates
    again = GT.build_candidates(TENANT, sec, slot, use_cache=False)
    assert calls["n"] == 1 and len(_ledger_rows(ledger)) == 1
    assert again == cands

    # and the Gate disposes of the bad AI draft while clearing the honest one
    dp = _dp(gate, tmp_path)
    cleared_ids = {v.variant_id for v in dp.cleared_pool(TENANT, sec, slot)}
    pid = DecisionPool.pool_id(TENANT, sec, slot)
    assert f"{pid}__gen_ai_1" in cleared_ids
    assert f"{pid}__gen_ai_2" not in cleared_ids


# --------------------------------------------------------------------------- #
# 6 · the module-level seam the WF-DESIGN harness calls for gen rows
# --------------------------------------------------------------------------- #
def test_module_level_cleared_pool_seam(gate, monkeypatch, reg):
    monkeypatch.setattr(GT, "_build_gate", lambda rule_set: gate)
    sec, slot = PREBUILT
    pool = DP.cleared_pool(TENANT, sec, slot)              # exactly the harness call
    assert pool
    pid = DecisionPool.pool_id(TENANT, sec, slot)
    ids = {v.variant_id for v in pool}
    assert not ids & {f"{pid}__trap_lie", f"{pid}__trap_superlative",
                      f"{pid}__trap_competitor"}
    for v in pool:                                         # the harness's own line check
        assert CR._line_is_unclean(f"{v.headline} {v.template}") is None
        assert not v.planted_lie
