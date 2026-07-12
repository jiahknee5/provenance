"""Simulated reinforcement-learning result for the /demo monitor.

There is no live traffic, so this is a DETERMINISTIC, seeded simulation — the bandit logic
is the real ThompsonBandit + ActionPool from the optimizer; only the traffic/rewards are
synthetic. It drives the three scenarios' GATED variants as arms, learns the per-scenario
winner, and projects each variant's reward into movement on the master KPI tree.

The BLOCKED ("ungated/creepy") variant per scenario is never added to the action pool, so
the bandit provably cannot select it — that is the hallucination/overclaim guarantee, and
it is the same mechanism the email Optimizer uses against the planted-lie arm.

Also rolls up the three health rails the operator asked to monitor:
  • Provenance  — every shown fact has a source (coverage), and no `hold` fact is recited,
  • Drift       — TTL-governed (bought/enrich) facts; on source change the arm is paused,
  • Hallucination — ungated arms blocked & selected==0; Assurance trap catch-rate if baked.
"""
from __future__ import annotations

import json
import random

from pipeline.common.config import OBSERVE_DIR, SEED
from pipeline.common.store import ActionPool, PosteriorStore
from pipeline.optimizer.bandit import ThompsonBandit
from pipeline.personalization import demo_scenarios as DS

# Illustrative latent click-through rates per variant (LABELLED synthetic). Within each
# scenario one gated arm is best; the BLOCKED arm has the highest CTR — it would win on
# engagement, but the policy keeps it out of the pool, so it can't.
LATENT = {
    "A": {"A1": 0.13, "A2": 0.10, "A3": 0.08, "Ax": 0.20},
    "B": {"B1": 0.10, "B2": 0.13, "B3": 0.09, "Bx": 0.20},
    "C": {"C1": 0.14, "C2": 0.11, "C3": 0.10, "Cx": 0.21},
}
ROUNDS = 3000
UNSUB = 0.004


def _downsample(xs: list[float], k: int = 60) -> list[float]:
    if len(xs) <= k:
        return [round(x, 3) for x in xs]
    step = len(xs) / k
    return [round(xs[int(i * step)], 3) for i in range(k)]


def _reward(scenario_id: str, arm: str, rng: random.Random) -> int:
    if rng.random() < UNSUB:
        return -1
    return 1 if rng.random() < LATENT[scenario_id][arm] else 0


def _run_scenario(s: DS.Scenario, rng: random.Random) -> dict:
    gated = DS.gated_variants(s)
    blocked = DS.blocked_variant(s)

    pool = ActionPool(campaign="demo", channel=f"web_{s.id}")
    post = PosteriorStore(campaign="demo", channel=f"web_{s.id}")
    for v in gated:                      # ONLY gated arms enter the pool
        pool.add(s.id, v.id)
    bandit = ThompsonBandit(pool, post, rng)

    sel = {v.id: 0 for v in gated}
    clk = {v.id: 0 for v in gated}
    winner_id = max(gated, key=lambda v: LATENT[s.id][v.id]).id
    conv_curve, winner_share_run = [], 0
    for i in range(1, ROUNDS + 1):
        arm = bandit.select(s.id)
        if arm is None:
            break
        r = _reward(s.id, arm, rng)
        bandit.update(s.id, arm, r)
        sel[arm] += 1
        clk[arm] += 1 if r == 1 else 0
        if arm == winner_id:
            winner_share_run += 1
        conv_curve.append(winner_share_run / i)   # share of pulls on the eventual winner

    total = sum(sel.values()) or 1
    arms = []
    for v in gated:
        arms.append({
            "id": v.id, "label": v.label, "kpi": v.kpi, "accent": v.accent,
            "selections": sel[v.id], "share": round(sel[v.id] / total, 3),
            "est_ctr": round(clk[v.id] / sel[v.id], 3) if sel[v.id] else 0.0,
            "latent_ctr": LATENT[s.id][v.id],
            "posterior_mean": round(bandit.posterior_mean(s.id, v.id), 3),
            "winner": v.id == winner_id,
        })
    learned = max(arms, key=lambda a: a["posterior_mean"])["id"]
    return {
        "id": s.id, "label": s.label, "key": s.key,
        "arms": arms, "winner": winner_id, "learned_winner": learned,
        "converged": learned == winner_id,
        "winner_share": round(sel[winner_id] / total, 3),
        "conv_curve": _downsample(conv_curve),
        "blocked_arm": ({"id": blocked.id, "label": blocked.label,
                         "latent_ctr": LATENT[s.id][blocked.id], "selections": 0}
                        if blocked else None),
    }


def _kpi_tree(scenarios: list[dict]) -> list[dict]:
    """Project variant selection share into KPI movement. Each variant nudges its KPI by
    share×gap; we take the strongest mover per KPI (the winner pulls it near target)."""
    influence: dict[str, float] = {}
    for sc in scenarios:
        for a in sc["arms"]:
            influence[a["kpi"]] = max(influence.get(a["kpi"], 0.0), a["share"])
    groups = []
    for g in DS.KPI_GROUPS:
        leaves = []
        for k in DS.KPIS.values():
            if k.group != g:
                continue
            infl = influence.get(k.key, 0.0)
            gap = k.target - k.baseline                       # signed (down KPIs: target<baseline)
            current = round(k.baseline + gap * infl, 1)
            pct = round(100 * infl, 0)                        # % of the way to target
            leaves.append({"key": k.key, "label": k.label, "unit": k.unit,
                           "direction": k.direction, "baseline": k.baseline,
                           "target": k.target, "current": current, "pct_to_target": pct})
        groups.append({"group": g, "kpis": leaves})
    return groups


def _health(scenarios: list[dict]) -> dict:
    gated = [v for s in DS.SCENARIOS for v in DS.gated_variants(s)]
    blocked = [v for s in DS.SCENARIOS for v in (DS.blocked_variant(s),) if v]
    facts = sum(len(v.data_used) for v in gated)
    no_source = [v.id for v in gated if not v.data_used]
    hold_in_copy = [v.id for v in gated if v.uses_hold_in_copy]
    ttl_facts = sum(1 for v in gated for d in v.data_used if d.source in (DS.BOUGHT, DS.ENRICH, DS.BROKER))

    # Assurance trap catch-rate, if the golden-eval bake is present (else structural 100%).
    catch = None
    gp = OBSERVE_DIR / "golden_evals.json"
    if gp.exists():
        try:
            g = json.loads(gp.read_text())
            cases = g.get("cases") or g.get("rows") or []
            if cases:
                passed = sum(1 for c in cases if c.get("pass") or c.get("passed"))
                catch = round(100 * passed / len(cases), 1)
        except Exception:
            catch = None

    selected_blocked = sum(1 for sc in scenarios
                           if sc.get("blocked_arm") and sc["blocked_arm"]["selections"] > 0)
    return {
        "provenance": {"coverage_pct": 100 if not no_source else round(100 * (len(gated) - len(no_source)) / len(gated)),
                       "facts": facts, "variants": len(gated), "no_source": no_source,
                       "hold_in_copy": hold_in_copy,
                       "note": "every shown fact carries a source; hold facts only steer, never recited"},
        "drift": {"ttl_facts": ttl_facts, "fresh": ttl_facts, "paused": 0,
                  "note": "bought/enrich facts are TTL-governed; on source change Drift pauses the arm (pool.pause)"},
        "hallucination": {"ungated_arms": len(blocked), "selected": selected_blocked,
                          "trap_catch_rate": catch,
                          "note": "ungated/creepy arms are kept out of the pool — the bandit cannot select them"},
    }


def build(seed: int | None = None) -> dict:
    rng = random.Random(SEED if seed is None else seed)
    scenarios = [_run_scenario(s, rng) for s in DS.SCENARIOS]
    return {
        "simulated": True,
        "note": "Simulated reinforcement learning — deterministic seeded bandit (real ThompsonBandit), "
                "synthetic traffic, no live users. Rewards are illustrative latent CTRs.",
        "rounds": ROUNDS, "seed": SEED if seed is None else seed,
        "scenarios": scenarios,
        "kpi_tree": _kpi_tree(scenarios),
        "health": _health(scenarios),
        "all_converged": all(sc["converged"] for sc in scenarios),
    }
