"""T-02 — the per-decision cleared pool's five locked contract invariants
(04-spec/contracts/decision-pool.md), against the REAL Gate (no mocks, Art VII):

  1. a planted lie / superlative / competitor / hold-fact candidate is 0-servable —
     pick() can never return it (mirrors test_optimizer P1: structural, not filtered);
  2. on_claims_invalidated pauses exactly the dependent variants (P3);
  3. every pick() result has a receipt (the 9 pinned provenance fields);
  4. posteriors move on real events and lift > 0 vs the random control on seeded traffic;
  5. same visit key -> same variant on replay (Art IV).

Plus the [PANEL — locked] keying: (tenant, channel) posterior-store identity and the
pooled _all cell below 30 resolved impressions.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pytest

from pipeline.common.schemas import Variant
from pipeline.common.store import PosteriorStore
from pipeline.personalization.decision_pool import (ALL_CELL, FALLBACK_MIN_RESOLVED,
                                                    ROUTES, DecisionPool)

TENANT, SECTION, TARGET = "gauntlet", "hero", "hero_sub"     # a real registry target
PID = DecisionPool.pool_id(TENANT, SECTION, TARGET)
T0 = datetime(2026, 7, 12, tzinfo=timezone.utc)
HOUR = timedelta(hours=1)


# --- candidates: honest arms + the four planted bad ones -----------------------------
def _mk(arm: str, headline: str, claim_ids: list[str], lie: bool = False) -> Variant:
    lines = [f"{headline}."]
    lines += [f"Helix Analytics [[{cid}]]." for cid in claim_ids]
    lines.append("See the full ROI breakdown. Start your assessment →")
    return Variant(variant_id=arm, segment="site", channel="website", arm_label=arm,
                   template="\n".join(lines), claim_ids=claim_ids, planted_lie=lie,
                   headline=headline)


HONEST = [
    ("A", "Cut length of stay with verified analytics", ["c_los"]),
    ("B", "Transparent pricing with no implementation fee", ["c_price", "c_nofee"]),
    ("C", "Deployed across twelve health systems", ["c_deployed"]),
]
PLANTED = [
    ("LIE", "Guaranteed 60% fewer readmissions — risk-free", ["c_deployed"], True),
    ("SUP", "The #1 analytics platform for hospitals", ["c_deployed"], False),
    ("COMP", "Better than Epic at claims analytics", ["c_deployed"], False),
    ("HOLD", "A verified cut in total cost of ownership", ["c_tco"], False),
]


def _provider(specs_by_target: dict[str, list[tuple]]):
    def provider(tenant, section_id, target_id):
        return [_mk(*s) for s in specs_by_target[target_id]]
    return provider


def _dp(gate, tmp_path, specs=None, **kw) -> DecisionPool:
    specs = specs or {TARGET: HONEST}
    kw.setdefault("posteriors", {TENANT: PosteriorStore("t_dp", "website")})
    kw.setdefault("rng", random.Random(7))
    tmp_path.mkdir(parents=True, exist_ok=True)
    return DecisionPool(gate, _provider(specs), db_path=tmp_path / "dp.sqlite",
                        persist=False, **kw)


def _cid(arm: str, pid: str = PID) -> str:
    return f"{pid}__{arm}"


# --- invariant 1: planted lie / superlative / competitor / hold-fact -> 0-servable ---
def test_planted_bad_candidates_are_zero_servable(gate, rules, tmp_path):
    rules.set_hold("mlr_hold_tco", True)                  # the hold-fact trap is LIVE
    dp = _dp(gate, tmp_path, specs={TARGET: HONEST + PLANTED})
    cleared = dp.cleared_pool(TENANT, SECTION, TARGET)

    ids = {v.variant_id for v in cleared}
    assert ids == {_cid("A"), _cid("B"), _cid("C")}       # only the honest arms exist
    for bad in ("LIE", "SUP", "COMP", "HOLD"):
        # structurally absent from every cell — never constructed in, not filtered out
        for cell in ROUTES + (ALL_CELL,):
            assert _cid(bad) not in dp.active(TENANT, SECTION, TARGET, cell)
        with pytest.raises(KeyError):                     # never cleared -> no receipt
            dp.receipt(_cid(bad))

    # pick can never return one — both policies, every route, many draws
    bad_ids = {_cid(b) for b in ("LIE", "SUP", "COMP", "HOLD")}
    for i in range(200):
        v = dp.pick(TENANT, SECTION, TARGET, ROUTES[i % 4], visit_key=f"v{i}", now=T0)
        assert v is not None and v.variant_id not in bad_ids

    # and the clearance report shows each trap blocked for its own reason
    rep = {r["variant_id"]: r for r in dp.clearance_report(TENANT, SECTION, TARGET)}
    assert not rep[_cid("LIE")]["claims_cleared"]          # unverifiable claim -> red
    assert not rep[_cid("HOLD")]["claims_cleared"]         # held claim -> red
    assert not rep[_cid("SUP")]["message_ok"]              # superlative -> hygiene veto
    assert not rep[_cid("COMP")]["message_ok"]             # comparative -> hygiene veto


# --- invariant 2: on_claims_invalidated pauses exactly the dependents ---------------
def test_surgical_pause_exactness_across_pools(gate, tmp_path):
    specs = {
        "hero_sub": [
            ("A", "Cut length of stay with verified analytics", ["c_los"]),
            ("B", "A verified cut in total cost of ownership", ["c_tco"]),
            ("C", "Transparent pricing for every bed count", ["c_price"]),
            ("E", "Priced per record and deployed today", ["c_price", "c_deployed"]),
        ],
        "hero_eyebrow": [
            ("X", "A verified total cost story", ["c_tco"]),
            ("Y", "Compliant reporting for care teams", ["c_hipaa"]),
        ],
    }
    dp = _dp(gate, tmp_path, specs=specs)
    dp.cleared_pool(TENANT, SECTION, "hero_sub")
    dp.cleared_pool(TENANT, SECTION, "hero_eyebrow")
    pid2 = DecisionPool.pool_id(TENANT, SECTION, "hero_eyebrow")

    # exactly the c_tco-dependent variants pause — across BOTH pools, nothing else
    paused = dp.on_claims_invalidated(["c_tco"])
    assert paused == sorted([_cid("B"), f"{pid2}__X"])
    for cell in ROUTES + (ALL_CELL,):                     # atomically out of every cell
        assert _cid("B") not in dp.active(TENANT, SECTION, "hero_sub", cell)
        assert f"{pid2}__X" not in dp.active(TENANT, SECTION, "hero_eyebrow", cell)
    assert set(dp.active(TENANT, SECTION, "hero_sub", ALL_CELL)) == \
        {_cid("A"), _cid("C"), _cid("E")}                 # the others keep serving
    assert dp.active(TENANT, SECTION, "hero_eyebrow", ALL_CELL) == [f"{pid2}__Y"]

    # no over-invalidation: a claim nothing asserts pauses nothing
    assert dp.on_claims_invalidated(["c_speed"]) == []
    # no under-invalidation: BOTH c_price variants pause together
    assert dp.on_claims_invalidated(["c_price"]) == sorted([_cid("C"), _cid("E")])

    # picks after the pause can only return still-active arms
    for i in range(60):
        v = dp.pick(TENANT, SECTION, "hero_sub", ROUTES[i % 4], visit_key=f"p{i}", now=T0)
        assert v.variant_id == _cid("A")
    # provenance survives the pause
    assert dp.receipt(_cid("B"))["claim_ids"] == ["c_tco"]


# --- invariant 3: every pick has a receipt (the 9 pinned fields) --------------------
def test_receipt_on_every_pick(gate, library, tmp_path):
    dp = _dp(gate, tmp_path)
    pinned = ("source_id", "lawful_basis", "policy", "gate_verdict", "claim_ids",
              "cache_key", "mode", "workflow", "rules_version")
    for i in range(40):
        v = dp.pick(TENANT, SECTION, TARGET, ROUTES[i % 4], visit_key=f"r{i}", now=T0)
        r = dp.receipt(v.variant_id)
        for k in pinned:
            assert k in r and r[k] is not None, f"receipt missing {k}: {r}"

    # the receipt is truthful: registry target fields + the claim's bound source + Gate state
    ra = dp.receipt(_cid("A"))
    assert ra["claim_ids"] == ["c_los"]
    assert ra["source_id"] == library.claim("c_los").source_id
    assert ra["policy"] == "say" and ra["mode"] == "deterministic" \
        and ra["workflow"] == "realtime"                   # gauntlet hero_sub registry row
    assert ra["gate_verdict"] in ("green", "amber")        # cleared is never red
    assert ra["rules_version"] == gate.rules.rules_version()
    assert ra["pool_id"] == PID


# --- invariant 4: posteriors move on real events; measured lift > control ------------
def test_posteriors_move_and_lift_beats_control_on_seeded_traffic(gate, tmp_path):
    post = PosteriorStore("t_lift", "website")
    dp = _dp(gate, tmp_path, posteriors={TENANT: post}, holdout_frac=0.3)
    latent = {_cid("A"): 0.55, _cid("B"): 0.25, _cid("C"): 0.05}   # A is the true winner
    clicker = random.Random(23)

    for i in range(400):
        route = ROUTES[i % 4]
        v = dp.pick(TENANT, SECTION, TARGET, route, visit_key=f"s{i}", now=T0)
        if clicker.random() < latent[v.variant_id]:        # click ~ that arm's true CTR
            dp.reward_click(PID, v.variant_id, route)
        if i % 25 == 24:
            dp.settle(PID, now=T0 + 2 * HOUR)              # no-clicks become evidence
    dp.settle(PID, now=T0 + 2 * HOUR)

    # posteriors moved off the Beta(1,1) prior, on real events only
    a, b = post.get(ALL_CELL, _cid("A"))
    assert a + b > 2.0
    # and they rank the true best arm on top
    assert dp.posterior_mean(TENANT, ALL_CELL, _cid("A")) > \
        dp.posterior_mean(TENANT, ALL_CELL, _cid("C"))

    rep = dp.lift_report(PID)
    assert rep["bandit_ctr"] is not None and rep["control_ctr"] is not None
    assert rep["lift"] > 0, rep                            # adaptivity beats random — measured


# --- invariant 5: same visit key -> same variant on replay (Art IV) ------------------
def test_same_visit_key_replays_same_variant(gate, tmp_path):
    dp1 = _dp(gate, tmp_path / "a", rng=random.Random(1),
              posteriors={TENANT: PosteriorStore("t_rp1", "website")})
    dp2 = _dp(gate, tmp_path / "b", rng=random.Random(999),
              posteriors={TENANT: PosteriorStore("t_rp2", "website")})
    for i in range(20):
        vk, route = f"replay{i}", ROUTES[i % 4]
        a = dp1.pick(TENANT, SECTION, TARGET, route, visit_key=vk, now=T0)
        b = dp1.pick(TENANT, SECTION, TARGET, route, visit_key=vk, now=T0)
        c = dp2.pick(TENANT, SECTION, TARGET, route, visit_key=vk, now=T0)
        # same key -> same variant: within a session AND across identical fresh instances
        assert a.variant_id == b.variant_id == c.variant_id
    # the control assignment is a stable slice of the key space too
    assert dp1.assign_control("k1") == dp1.assign_control("k1") == dp2.assign_control("k1")


# --- [PANEL — locked] keying: (tenant, channel) store identity + _all fallback -------
def test_posterior_store_identity_and_all_fallback(gate, tmp_path):
    post = PosteriorStore("live_gauntlet_t", "website")
    dp = _dp(gate, tmp_path,
             specs={TARGET: HONEST, "hero_eyebrow": [("X", "A verified total cost story",
                                                      ["c_deployed"])]},
             posteriors={TENANT: post})

    # below 30 resolved the route serves from the pooled _all cell
    assert dp.serving_cell(TENANT, SECTION, TARGET, "individual") == ALL_CELL
    for i in range(FALLBACK_MIN_RESOLVED):
        v = dp.pick(TENANT, SECTION, TARGET, "individual", visit_key=f"f{i}", now=T0)
        dp.reward_click(PID, v.variant_id, "individual")   # resolve each impression
    assert dp.serving_cell(TENANT, SECTION, TARGET, "individual") == "individual"
    assert dp.serving_cell(TENANT, SECTION, TARGET, "neutral") == ALL_CELL   # still pooled

    # every real event updated BOTH the route cell and the pooled cell
    assert any(a > 1.0 for a, _ in post.params["individual"].values())
    assert any(a > 1.0 for a, _ in post.params[ALL_CELL].values())

    # ONE store per (tenant, channel): a second target's arms land in the SAME store,
    # namespaced by pool id — live.py's identity, not a store per pool
    pid2 = DecisionPool.pool_id(TENANT, SECTION, "hero_eyebrow")
    v2 = dp.pick(TENANT, SECTION, "hero_eyebrow", "neutral", visit_key="e0", now=T0)
    dp.reward_click(pid2, v2.variant_id, "neutral")
    assert v2.variant_id.startswith(f"{pid2}__")
    assert v2.variant_id in post.params[ALL_CELL]
    assert post.channel == "website"

    # unknown routes fail loud — the segment vocabulary is pinned
    with pytest.raises(ValueError):
        dp.pick(TENANT, SECTION, TARGET, "_all")
    # rewards without a pending impression are a no-op (posteriors move on real events)
    assert dp.reward_click(PID, _cid("A"), "b2b_hire") is None
