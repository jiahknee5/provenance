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
from pipeline.domain.adapters import asset as domain_asset
from pipeline.domain.adapters import campaign as domain_campaign
from pipeline.domain import decision_trace as dt
from pipeline.domain.emotional import (
    DispatchDecision,
    EmotionalSafetyPolicy,
    infer_signal_from_text,
    pick_reroute_variant,
)
from pipeline.domain.models.profile import IdentitySlice, Profile, ProfileClass
from pipeline.common.config import RUNS_DIR
from pipeline.common.db import connect
from pipeline.common.schemas import Recipient, Variant
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


def _profile_from_recipient(r: Recipient) -> Profile:
    return Profile(
        profile_id=r.recipient_id,
        profile_class=ProfileClass.RECIPIENT,
        identity=IdentitySlice(
            recipient_id=r.recipient_id,
            email=r.email,
            name=r.name,
            magic_token=r.token,
            consent=r.consent,
            stage="lead",
        ),
        segment=r.segment,
        signals={"urgency": r.urgency, "use_case": r.use_case, "source": "campaign_replay"},
        created_at=r.created_at,
    )


def _signal_text(r: Recipient) -> str:
    if r.urgency == "high":
        return f"{r.use_case}; urgent risk and stress surfaced in campaign behavior"
    if r.urgency == "medium":
        return f"{r.use_case}; evaluating options with ordinary urgency"
    return f"{r.use_case}; calm exploratory browsing"


def _candidate_variants(
    pool: ActionPool,
    variant_map: dict[str, Variant],
    segment: str,
    selected_arm: str,
) -> list[Variant]:
    return [
        variant_map[arm]
        for arm in pool.active(segment)
        if arm != selected_arm and arm in variant_map
    ]


def run_campaign(channel: str, campaign: str, recipients: list[Recipient],
                 pool: ActionPool, posteriors: PosteriorStore,
                 constrained: bool = True, seed: int = 0, log_db: bool = True,
                 emotional_loop: bool = True, emotional_track_cap: int = 3) -> dict:
    rng = random.Random(seed)
    bandit = ThompsonBandit(pool, posteriors, rng)
    emotional_enabled = emotional_loop and constrained
    emotional_policy = EmotionalSafetyPolicy(track_cap=emotional_track_cap)
    emotional_track_counts: dict[tuple[str, str], int] = defaultdict(int)

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

    from pipeline.generation.variants import build_variants
    from pipeline.domain.models.asset import Asset
    from pipeline.domain.stores.asset_store import AssetStore
    variant_map = {v.variant_id: v for vs in build_variants(channel).values() for v in vs}
    asset_store = AssetStore()

    counts: dict = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # seg -> arm -> [sel, clk]
    regret_cum, cum, lie_selections = [], 0.0, 0
    emotional_stats = {
        "enabled": emotional_enabled,
        "signals_evaluated": 0,
        "reroutes": 0,
        "blocks": 0,
        "safe_reroute_misses": 0,
    }
    events = []

    for r in recipients:
        seg = r.segment
        selected_arm = bandit.select(seg)
        if selected_arm is None:
            domain_asset.emit_dispatch_failed(
                recipient_id=r.recipient_id, segment=seg, channel=channel,
                campaign=campaign, reason="no_cleared_arm",
            )
            continue
        arm = selected_arm
        domain_campaign.emit_asset_selection(
            r.recipient_id, seg, arm, channel, campaign,
        )
        v = variant_map.get(arm)
        if v and emotional_enabled:
            profile = _profile_from_recipient(r)
            signal = infer_signal_from_text(_signal_text(r), source="text")
            vector = getattr(v, "emotional_vector", "") or "neutral"
            track_key = (r.recipient_id, vector)
            emotional_track_counts[track_key] += 1
            decision, target_vector = emotional_policy.evaluate(
                profile,
                v,
                session_track_count=emotional_track_counts[track_key],
                signals=[signal],
            )
            emotional_stats["signals_evaluated"] += 1
            if decision == DispatchDecision.BLOCK:
                emotional_stats["blocks"] += 1
                domain_asset.emit_dispatch_failed(
                    recipient_id=r.recipient_id, segment=seg, channel=channel,
                    campaign=campaign, reason="emotional_mismatch_blocked",
                )
                observe.emit(
                    _lane, "DECISION", node=_node, claim_id=seg,
                    detail=f"{seg}: blocked {arm.split('__')[-1]} for emotional mismatch",
                    decision={"recipient_id": r.recipient_id, "selected_arm": arm,
                              "emotional_vector": vector, "outcome": "blocked"},
                )
                if selected_arm.endswith("__LIE"):
                    lie_selections += 1
                continue
            if decision == DispatchDecision.REROUTE:
                rerouted = pick_reroute_variant(
                    _candidate_variants(pool, variant_map, seg, selected_arm),
                    target_vector,
                )
                if rerouted is None:
                    emotional_stats["safe_reroute_misses"] += 1
                    domain_asset.emit_dispatch_failed(
                        recipient_id=r.recipient_id, segment=seg, channel=channel,
                        campaign=campaign, reason="no_safe_emotional_reroute",
                    )
                    if selected_arm.endswith("__LIE"):
                        lie_selections += 1
                    continue
                emotional_stats["reroutes"] += 1
                observe.emit(
                    _lane, "DECISION", node=_node, claim_id=seg,
                    detail=f"{seg}: rerouted {arm.split('__')[-1]} -> {rerouted.arm_label}",
                    decision={"recipient_id": r.recipient_id, "selected_arm": arm,
                              "dispatched_arm": rerouted.variant_id,
                              "target_vector": target_vector},
                )
                dt.record_trace(
                    "emotional_reroute",
                    "rerouted",
                    asset_ref=rerouted.variant_id,
                    explanation=f"emotional safety rerouted {arm} to {rerouted.variant_id}",
                    subject_id=r.recipient_id,
                )
                arm = rerouted.variant_id
                v = rerouted

        domain_asset.emit_publish_requested(
            arm, recipient_id=r.recipient_id, segment=seg, channel=channel, campaign=campaign,
        )
        domain_asset.emit_dispatched(
            arm, recipient_id=r.recipient_id, segment=seg, channel=channel, campaign=campaign,
        )
        if v:
            asset_store.save(Asset.from_variant(v))
            dt.record_trace(
                "asset_selection", "selected",
                claim_refs=list(v.claim_ids),
                asset_ref=arm,
                subject_id=r.recipient_id,
            )
        rew = oracle.reward(seg, arm, rng)
        bandit.update(seg, arm, rew)
        counts[seg][arm][0] += 1
        counts[seg][arm][1] += 1 if rew == 1 else 0
        if selected_arm.endswith("__LIE"):
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
        "emotional_loop": emotional_stats,
    }
    observe.emit(_lane, "OUTPUT", node=_node,
                 detail=f"{campaign}/{channel}: lie selected {lie_selections}× · final regret {round(cum, 2)}",
                 output={"selections_of_lie": lie_selections, "final_regret": round(cum, 2),
                         "winner_is_lie_anywhere": trace["winner_is_lie_anywhere"]})
    (RUNS_DIR / f"campaign_{campaign}_{channel}.json").write_text(json.dumps(trace, indent=2))
    return trace
