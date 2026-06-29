"""Emotional safety circuit breaker tests."""
from __future__ import annotations

import pytest

from pipeline.common.schemas import Variant
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
