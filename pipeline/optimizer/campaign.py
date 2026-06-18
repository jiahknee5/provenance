"""Run a campaign — drive the bandit over recipients, log simulated CTA, track regret.

Regret is measured against the best arm *available in this pool*: for the constrained
campaign that is the best honest arm (regret -> 0 as it converges); for the unconstrained
twin it is the lie. So both converge — the difference is *what* they converge to. The
constrained run never selects the lie (it isn't in the pool); the twin does.
"""
from __future__ import annotations

import json
import random
from collections import defaultdict

from pipeline.common import observe
from pipeline.common.config import RUNS_DIR
from pipeline.common.db import connect
from pipeline.common.schemas import Recipient
from pipeline.common.store import ActionPool, PosteriorStore
from pipeline.optimizer import oracle
from pipeline.optimizer.bandit import ThompsonBandit


def _optimal_ctr(segment: str, pool: ActionPool) -> float:
    return max((oracle.latent_ctr(segment, v) for v in pool.active(segment)), default=0.0)


def _downsample(xs: list[float], k: int = 200) -> list[float]:
    if len(xs) <= k:
        return [round(x, 3) for x in xs]
    step = len(xs) / k
    return [round(xs[int(i * step)], 3) for i in range(k)]


def run_campaign(channel: str, campaign: str, recipients: list[Recipient],
                 pool: ActionPool, posteriors: PosteriorStore,
                 constrained: bool = True, seed: int = 0, log_db: bool = True) -> dict:
    rng = random.Random(seed)
    bandit = ThompsonBandit(pool, posteriors, rng)

    # node identity for the observability lane: the unconstrained twin and the website
    # channel are distinct nodes from the email optimizer, though they share this driver.
    _lane, _node = ("optimizer", "bandit")
    if not constrained:
        _lane, _node = ("optimizer", "twin")
    elif channel == "website":
        _lane, _node = ("website", "website")
    observe.emit(_lane, "INPUT", node=_node,
                 tool="Thompson bandit + synthetic CTA oracle",
                 detail=f"campaign {campaign}/{channel} over {len(recipients)} recipients "
                        f"({'verified arms only' if constrained else 'lie in pool'})",
                 input={"campaign": campaign, "channel": channel, "constrained": constrained,
                        "n": len(recipients), "warm_started": bool(posteriors.params),
                        "active_arms": {seg: pool.active(seg) for seg in sorted(pool.segments)}})

    counts: dict = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # seg -> arm -> [sel, clk]
    regret_cum, cum, lie_selections = [], 0.0, 0
    events = []

    for r in recipients:
        seg = r.segment
        arm = bandit.select(seg)
        if arm is None:
            continue
        rew = oracle.reward(seg, arm, rng)
        bandit.update(seg, arm, rew)
        counts[seg][arm][0] += 1
        counts[seg][arm][1] += 1 if rew == 1 else 0
        if arm.endswith("__LIE"):
            lie_selections += 1
        cum += _optimal_ctr(seg, pool) - oracle.latent_ctr(seg, arm)
        regret_cum.append(cum)
        events.append((r.recipient_id, channel, campaign, arm, rew, r.created_at))

    if log_db:
        conn = connect()
        try:
            conn.executemany(
                "INSERT INTO cta_events (recipient_id,channel,campaign,variant_id,clicked,ts) "
                "VALUES (?,?,?,?,?,?)", events)
            conn.commit()
        finally:
            conn.close()

    per_segment = {}
    for seg, arms in counts.items():
        arm_stats = {}
        for arm, (sel, clk) in arms.items():
            arm_stats[arm] = {"selections": sel, "clicks": clk,
                              "est_ctr": round(clk / sel, 3) if sel else 0.0,
                              "latent_ctr": round(oracle.latent_ctr(seg, arm), 3),
                              "posterior_mean": round(bandit.posterior_mean(seg, arm), 3)}
        best_sel = max(arm_stats, key=lambda a: arm_stats[a]["selections"])
        # the winner the optimizer LEARNED = highest posterior mean (what the website uses)
        best_post = max(arm_stats, key=lambda a: arm_stats[a]["posterior_mean"])
        per_segment[seg] = {"arms": arm_stats, "best_by_selections": best_sel,
                            "winner": best_post, "best_by_posterior": best_post,
                            "winner_is_lie": best_post.endswith("__LIE")}
        observe.emit(_lane, "DECISION", node=_node, claim_id=seg,
                     detail=f"{seg}: learned winner {best_post.split('__')[-1]}"
                            + (" — LIE" if best_post.endswith("__LIE") else ""),
                     decision={"segment": seg, "winner_arm": best_post.split("__")[-1],
                               "posterior_mean": arm_stats[best_post]["posterior_mean"],
                               "est_ctr": arm_stats[best_post]["est_ctr"],
                               "winner_is_lie": best_post.endswith("__LIE")})

    posteriors.save()
    pool.save()
    trace = {
        "campaign": campaign, "channel": channel, "constrained": constrained,
        "n": len(recipients), "selections_of_lie": lie_selections,
        "final_regret": round(cum, 2), "regret_curve": _downsample(regret_cum),
        "per_segment": per_segment,
        "winner_is_lie_anywhere": any(s["winner_is_lie"] for s in per_segment.values()),
    }
    observe.emit(_lane, "OUTPUT", node=_node,
                 detail=f"{campaign}/{channel}: lie selected {lie_selections}× · final regret {round(cum, 2)}",
                 output={"selections_of_lie": lie_selections, "final_regret": round(cum, 2),
                         "winner_is_lie_anywhere": trace["winner_is_lie_anywhere"]})
    (RUNS_DIR / f"campaign_{campaign}_{channel}.json").write_text(json.dumps(trace, indent=2))
    return trace
