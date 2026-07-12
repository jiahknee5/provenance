"""Headline property — the optimizer LEARNS FROM REAL TRAFFIC, and still can't serve a lie.

The offline campaign (test_optimizer.py) proves the bandit is truth-bounded over a
synthetic oracle. These prove the SAME boundary and real online learning hold for the live
loop: real impressions + clicks move the posteriors, serving converges to what converts,
and the planted lie is never servable to a real visitor (it isn't in the Gate-cleared pool).
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from pipeline.common.store import PosteriorStore
from pipeline.generation.variants import build_action_pool
from pipeline.optimizer import oracle
from pipeline.optimizer.live import LiveOptimizer

SEG = "cfo__core"
A = f"{SEG}__website__A"
B = f"{SEG}__website__B"
T0 = datetime(2026, 6, 25, tzinfo=timezone.utc)


def _opt(gate, tmp_path, campaign="live_test"):
    """A live optimizer over the real Gate-cleared website pool, isolated db + posteriors."""
    pool, _ = build_action_pool(gate, "website", campaign)        # constrained: lie excluded
    post = PosteriorStore(campaign, "website")                    # non-canonical name
    opt = LiveOptimizer(pool, channel="website", posteriors=post,
                        db_path=tmp_path / "live.sqlite", rng=random.Random(7))
    return opt, pool


def test_live_never_serves_the_lie(gate, tmp_path):
    opt, pool = _opt(gate, tmp_path)
    assert not any(v.endswith("__LIE") for v in pool.all_variant_ids())   # not even in pool
    rng = random.Random(0)
    for seg in pool.segments:
        for _ in range(50):
            v = opt.select(seg, rng=rng)
            assert v is not None and not v.endswith("__LIE")


def test_real_clicks_move_posteriors_online(gate, tmp_path):
    opt, _ = _opt(gate, tmp_path)
    # A converts (clicks); B does not (no-clicks, settled). Only the REAL event path is used.
    for i in range(40):
        opt.record_impression(f"a{i}", SEG, A, now=T0)
        assert opt.reward_click(f"a{i}") == A
    for i in range(40):
        opt.record_impression(f"b{i}", SEG, B, now=T0)
    assert opt.settle(now=T0 + timedelta(hours=1)) == 40             # 40 no-clicks settled
    assert opt.posterior_mean(SEG, A) > 0.8
    assert opt.posterior_mean(SEG, B) < 0.2
    assert opt.posterior_mean(SEG, A) > opt.posterior_mean(SEG, B)


def test_serving_converges_to_the_winner(gate, tmp_path):
    opt, _ = _opt(gate, tmp_path)
    for i in range(40):
        opt.record_impression(f"a{i}", SEG, A, now=T0)
        opt.reward_click(f"a{i}")                                    # A clicks
        opt.record_impression(f"b{i}", SEG, B, now=T0)              # B impressions (pending)
    opt.settle(now=T0 + timedelta(hours=1))                         # -> B no-clicks
    rng = random.Random(1)
    picks = [opt.select(SEG, rng=rng) for _ in range(200)]
    assert picks.count(A) > picks.count(B) * 5                      # overwhelmingly the winner


def test_clicks_alone_do_not_separate(gate, tmp_path):
    # Negative control: clicks on BOTH arms (no settle) push both toward 1.0 — proving the
    # no-click settle is what creates separation, not the click signal alone.
    opt, _ = _opt(gate, tmp_path)
    for i in range(20):
        opt.record_impression(f"a{i}", SEG, A, now=T0); opt.reward_click(f"a{i}")
        opt.record_impression(f"b{i}", SEG, B, now=T0); opt.reward_click(f"b{i}")
    assert opt.posterior_mean(SEG, A) > 0.8 and opt.posterior_mean(SEG, B) > 0.8


def test_reward_click_without_impression_is_a_noop(gate, tmp_path):
    opt, _ = _opt(gate, tmp_path)
    assert opt.reward_click("ghost") is None


def test_snapshot_reports_real_counts_and_no_lie(gate, tmp_path):
    opt, _ = _opt(gate, tmp_path)
    opt.record_impression("a0", SEG, A, now=T0)
    opt.reward_click("a0")
    snap = opt.snapshot()
    assert snap["live_clicks"] == 1
    seg = snap["segments"][SEG]
    assert seg["arms"]["A"]["clicks"] == 1
    assert "LIE" not in seg["arms"]


def test_tenants_learn_independently(gate, tmp_path):
    """Item 3: two tenants share the impressions table but their bandits are isolated —
    rewarding one never moves the other's posteriors or appears in its snapshot."""
    pool, _ = build_action_pool(gate, "website", "mt_test")
    db = tmp_path / "mt.sqlite"
    helix = LiveOptimizer(pool, channel="website", tenant="helix", db_path=db,
                          posteriors=PosteriorStore("live_helix_test", "website"), rng=random.Random(1))
    academy = LiveOptimizer(pool, channel="website", tenant="academy", db_path=db,
                            posteriors=PosteriorStore("live_academy_test", "website"), rng=random.Random(2))
    for i in range(20):
        helix.record_impression(f"h{i}", SEG, A, now=T0); helix.reward_click(f"h{i}")     # helix learns A
        academy.record_impression(f"k{i}", SEG, B, now=T0); academy.reward_click(f"k{i}")  # academy learns B
    # posteriors are isolated — each learned its own arm; neither moved the other's
    assert helix.posterior_mean(SEG, A) > 0.8 and academy.posterior_mean(SEG, A) == 0.5
    assert academy.posterior_mean(SEG, B) > 0.8 and helix.posterior_mean(SEG, B) == 0.5
    # the shared table is partitioned by tenant — each snapshot sees only its own traffic
    assert helix.snapshot()["live_clicks"] == 20 and academy.snapshot()["live_clicks"] == 20
    # and one tenant cannot resolve another tenant's pending impression
    helix.record_impression("shared", SEG, A, now=T0)
    assert academy.reward_click("shared") is None
    assert helix.reward_click("shared") == A


def test_context_live_is_tenant_keyed():
    from app.context import Ctx
    c = Ctx()
    a, b = c.live_for("helix"), c.live_for("academy")
    assert a is not b and a.tenant == "helix" and b.tenant == "academy"
    assert c.live is a                                  # the default property is the helix tenant


def test_bandit_beats_random_measured_lift(gate, tmp_path):
    """Item 1: the bandit's lift is MEASURED, not asserted — its adaptive (bandit) slice
    converts better than a random control holdout on simulated live traffic."""
    opt, _ = _opt(gate, tmp_path, campaign="lift_test")
    rng = random.Random(123)
    for i in range(2000):
        vid, policy = opt.assign(SEG, rng=rng, holdout_frac=0.2)   # 20% random control
        rid = f"v{i}"
        opt.record_impression(rid, SEG, vid, policy=policy, now=T0)
        if rng.random() < oracle.latent_ctr(SEG, vid):             # click ~ that arm's true CTR
            opt.reward_click(rid)
    opt.settle(now=T0 + timedelta(hours=1))                        # rest -> no-clicks
    rep = opt.lift_report()
    assert rep["bandit_ctr"] is not None and rep["control_ctr"] is not None
    assert rep["bandit_ctr"] > rep["control_ctr"], rep             # adaptivity beats random
    assert rep["lift"] > 0 and rep["relative_lift_pct"] > 0
    # and it converged to the genuinely best honest arm (A is preferred for cfo__core)
    assert opt.snapshot()["segments"][SEG]["winner"] == "A"
