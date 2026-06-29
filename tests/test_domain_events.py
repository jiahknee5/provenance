"""Tests for canonical domain event bridge."""
from __future__ import annotations

import pytest

from pipeline.common.schemas import Verdict
from pipeline.domain.catalog import EVENT_NAMES, assert_known_event
from pipeline.domain.emit import active, emit_domain, end_domain_run, start_domain_run
from pipeline.domain.envelope import StreamType, SubjectRef
from pipeline.domain.adapters import gate as domain_gate
from pipeline.domain import streams as stream_mod
from pipeline.common.schemas import ClaimVerdict


@pytest.fixture
def domain_recorder(tmp_path, monkeypatch):
    monkeypatch.setattr(stream_mod, "STREAMS_DIR", tmp_path / "streams")
    rec = start_domain_run("test-run")
    yield rec
    end_domain_run()


def test_emit_starts_recorder_when_inactive(tmp_path, monkeypatch):
    monkeypatch.setattr(stream_mod, "STREAMS_DIR", tmp_path / "streams")
    end_domain_run()
    assert not active()
    eid = emit_domain(
        "claim_verified",
        stream_id="lead_c1",
        subject_ref=SubjectRef(type="claim", id="c1"),
        payload={"claim_id": "c1"},
    )
    assert eid is not None
    assert active()
    end_domain_run()


def test_envelope_fields(domain_recorder):
    eid = emit_domain(
        "claim_verified",
        stream_id="lead_c_soc2",
        subject_ref=SubjectRef(type="claim", id="c_soc2"),
        payload={"claim_id": "c_soc2", "status": "verified"},
        tenant_id="helix",
    )
    assert eid is not None
    events = domain_recorder.read_stream(StreamType.LEAD, "lead_c_soc2")
    assert len(events) == 1
    ev = events[0]
    assert ev.event_name == "claim_verified"
    assert ev.tenant_id == "helix"
    assert ev.correlation_id
    assert ev.stream_position == 1
    assert ev.subject_ref.id == "c_soc2"


def test_stream_ordering(domain_recorder):
    subj = SubjectRef(type="claim", id="c1")
    emit_domain("claim_verified", stream_id="lead_c1", subject_ref=subj, payload={"n": 1})
    emit_domain("policy_evaluated", stream_id="lead_c1", subject_ref=subj, payload={"n": 2})
    events = domain_recorder.read_stream(StreamType.LEAD, "lead_c1")
    assert [e.stream_position for e in events] == [1, 2]


def test_gate_amber_emits_policy_not_contradicted(domain_recorder):
    cv = ClaimVerdict(
        claim_id="c_tco", text="tco claim", span=(0, 0), verdict=Verdict.AMBER,
        source_id="s1", confidence=0.4, rules_version="r1",
    )
    domain_gate.emit_claim_verdict(cv, rules_version="r1", advisory_review=True)
    lead_events = domain_recorder.read_stream(StreamType.LEAD, "lead_c_tco")
    names = [e.event_name for e in lead_events]
    assert "policy_evaluated" in names
    assert "claim_contradicted" not in names
    review_events = domain_recorder.read_stream(StreamType.REVIEW, "review_c_tco")
    assert any(e.event_name == "review_requested" for e in review_events)


def test_gate_red_policy_veto(domain_recorder):
    cv = ClaimVerdict(
        claim_id="c_x", text="x", span=(0, 0), verdict=Verdict.RED,
        source_id="s1", confidence=0.02, rule_flags=["mlr_hold_tco"],
        reasons=["blocked by compliance rule"], rules_version="r1",
    )
    domain_gate.emit_claim_verdict(cv, rules_version="r1", policy_veto=True)
    lead = domain_recorder.read_stream(StreamType.LEAD, "lead_c_x")
    assert any(e.event_name == "policy_evaluated" for e in lead)
    asset = domain_recorder.read_stream(StreamType.ASSET, "asset_c_x")
    assert any(e.event_name == "dispatch_suppressed" for e in asset)


def test_gate_red_unsupported_contradicts_even_with_rule_flag(domain_recorder):
    # An unsupported RED that merely carries an AMBER-disclaimer flag must NOT be mislabeled
    # a policy veto: without the explicit policy_veto signal it is claim_contradicted.
    cv = ClaimVerdict(
        claim_id="c_lie", text="guaranteed 60% fewer readmissions", span=(0, 0),
        verdict=Verdict.RED, source_id="s1", confidence=0.02, rule_flags=["mlr_disclaimer"],
        reasons=["not entailed by any approved source"], rules_version="r1",
    )
    domain_gate.emit_claim_verdict(cv, rules_version="r1")
    names = [e.event_name for e in domain_recorder.read_stream(StreamType.LEAD, "lead_c_lie")]
    assert "claim_contradicted" in names
    assert "policy_evaluated" not in names


def test_catalog_closed():
    assert "claim_verified" in EVENT_NAMES
    with pytest.raises(ValueError):
        assert_known_event("not_a_real_event")
