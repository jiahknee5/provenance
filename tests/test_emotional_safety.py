"""Emotional safety circuit breaker tests."""
from __future__ import annotations

import pytest

from pipeline.common.schemas import Variant
from pipeline.common.store import ActionPool, PosteriorStore
from pipeline.domain.emotional import (
    DispatchDecision,
    EmotionalSafetyPolicy,
    infer_signal_from_text,
    pick_reroute_variant,
)
from pipeline.domain.models.profile import Profile
from pipeline.domain.emit import end_domain_run, start_domain_run
from pipeline.domain import streams as stream_mod
from pipeline.domain.envelope import StreamType
from pipeline.generation import recipients
from pipeline.optimizer.campaign import run_campaign


@pytest.fixture
def domain_recorder(tmp_path, monkeypatch):
    monkeypatch.setattr(stream_mod, "STREAMS_DIR", tmp_path / "streams")
    start_domain_run("emotional-test")
    yield
    end_domain_run()


def test_mismatch_blocks_fear_variant(domain_recorder):
    policy = EmotionalSafetyPolicy(track_cap=2)
    profile = Profile(profile_id="p1")
    variant = Variant(
        variant_id="seg__email__A", segment="s", template="t",
        emotional_vector="fear_PAS",
    )
    sig = infer_signal_from_text("I am worried and anxious about costs")
    decision, _ = policy.evaluate(profile, variant, session_track_count=3, signals=[sig])
    assert decision == DispatchDecision.BLOCK
    events = stream_mod.active_recorder().read_stream(
        StreamType.ASSET, f"asset_{variant.variant_id}"
    )
    assert any(e.event_name == "emotional_mismatch_blocked" for e in events)


def test_reroute_selects_relief(domain_recorder):
    policy = EmotionalSafetyPolicy(track_cap=5)
    profile = Profile(profile_id="p1")
    fear = Variant(variant_id="v_fear", segment="s", template="t", emotional_vector="fear_PAS")
    relief = Variant(variant_id="v_relief", segment="s", template="t", emotional_vector="relief_BAB")
    sig = infer_signal_from_text("worried about affordability")
    decision, vector = policy.evaluate(profile, fear, session_track_count=1, signals=[sig])
    assert decision == DispatchDecision.REROUTE
    picked = pick_reroute_variant([fear, relief])
    assert picked.variant_id == "v_relief"
    lead_events = stream_mod.active_recorder().read_stream(StreamType.LEAD, "lead_p1")
    names = [e.event_name for e in lead_events]
    assert "text_sentiment_scored" in names
    assert "emotional_signal_detected" in names
    assert "emotional_segment_assignment_updated" in names


def _high_urgency_cfo(recipient_id: str = "r_emo") -> recipients.Recipient:
    return recipients.Recipient(
        recipient_id=recipient_id,
        token="tok",
        name="Riley Shah",
        email="riley@example.org",
        company="Northwind Health",
        role="cfo",
        company_size="community",
        region="Midwest",
        use_case="lower total cost of ownership",
        urgency="high",
        segment="cfo__core",
        created_at="2026-06-29T00:00:00+00:00",
    )


def _cfo_pool(campaign: str = "emo_campaign") -> tuple[ActionPool, PosteriorStore]:
    pool = ActionPool(campaign, "email")
    pool.add("cfo__core", "cfo__core__email__A")
    pool.add("cfo__core", "cfo__core__email__B")
    posteriors = PosteriorStore(campaign, "email")
    posteriors.set("cfo__core", "cfo__core__email__A", 1000, 1)
    posteriors.set("cfo__core", "cfo__core__email__B", 1, 1000)
    return pool, posteriors


def test_campaign_reroutes_fear_asset_to_relief_before_dispatch(domain_recorder):
    pool, posteriors = _cfo_pool("emo_reroute")

    trace = run_campaign(
        "email",
        "emo_reroute",
        [_high_urgency_cfo()],
        pool,
        posteriors,
        constrained=True,
        seed=4,
        log_db=False,
    )

    assert trace["emotional_loop"]["enabled"] is True
    assert trace["emotional_loop"]["signals_evaluated"] == 1
    assert trace["emotional_loop"]["reroutes"] == 1
    assert trace["emotional_loop"]["blocks"] == 0
    assert trace["per_segment"]["cfo__core"]["arms"]["cfo__core__email__B"]["selections"] == 1

    fear_events = stream_mod.active_recorder().read_stream(
        StreamType.ASSET, "asset_cfo__core__email__A"
    )
    assert [e.event_name for e in fear_events] == [
        "asset_selection_recorded",
        "emotional_reroute_applied",
    ]
    relief_events = stream_mod.active_recorder().read_stream(
        StreamType.ASSET, "asset_cfo__core__email__B"
    )
    assert [e.event_name for e in relief_events] == [
        "asset_publish_requested",
        "asset_dispatched",
    ]
    lead_events = stream_mod.active_recorder().read_stream(StreamType.LEAD, "lead_r_emo")
    lead_names = [e.event_name for e in lead_events]
    assert "text_sentiment_scored" in lead_names
    assert "emotional_signal_detected" in lead_names
    assert "emotional_segment_assignment_updated" in lead_names


def test_campaign_blocks_after_emotional_track_cap(domain_recorder):
    pool, posteriors = _cfo_pool("emo_block")
    r = _high_urgency_cfo()

    trace = run_campaign(
        "email",
        "emo_block",
        [r, r],
        pool,
        posteriors,
        constrained=True,
        seed=4,
        log_db=False,
        emotional_track_cap=2,
    )

    assert trace["emotional_loop"]["reroutes"] == 1
    assert trace["emotional_loop"]["blocks"] == 1

    dispatch_events = stream_mod.active_recorder().read_stream(
        StreamType.ASSET, "asset_dispatch_emo_block_cfo__core"
    )
    assert [e.event_name for e in dispatch_events] == ["dispatch_failed"]
    assert dispatch_events[0].payload["reason"] == "emotional_mismatch_blocked"
