"""DecisionTrace store tests."""
from __future__ import annotations

import pytest

from pipeline.common.schemas import ClaimVerdict, MessageLedger, Verdict
from pipeline.domain.decision_trace import explain_decision, from_message_ledger, get_trace, record_trace
from pipeline.domain.emit import end_domain_run, start_domain_run
from pipeline.domain import streams as stream_mod
from pipeline.domain.envelope import StreamType


@pytest.fixture
def domain_recorder(tmp_path, monkeypatch):
    monkeypatch.setattr(stream_mod, "STREAMS_DIR", tmp_path / "streams")
    start_domain_run("trace-test")
    yield
    end_domain_run()


def test_trace_completeness(domain_recorder):
    ledger = MessageLedger(
        recipient_id="r1", variant_id="v1", channel="email",
        claims=[
            ClaimVerdict(claim_id="c1", text="t", span=(0, 0), verdict=Verdict.GREEN,
                         source_id="s", confidence=0.9, rules_version="r1"),
        ],
    )
    trace = from_message_ledger(ledger)
    assert trace.claim_refs == ["c1"]
    assert trace.asset_ref == "v1"
    assert get_trace(trace.decision_trace_id) is not None


def test_decision_trace_stream(domain_recorder):
    trace = record_trace("asset_selection", "selected", claim_refs=["c1"], asset_ref="v1")
    events = stream_mod.active_recorder().read_stream(
        StreamType.DECISION_TRACE, f"decision_trace_{trace.decision_trace_id}"
    )
    assert events[0].event_name == "decision_trace_recorded"
    assert events[0].trace_ref.decision_trace_id == trace.decision_trace_id


def test_explain_decision_intent(domain_recorder):
    trace = record_trace("test", "ok", subject_id="sub1")
    out = explain_decision(trace.decision_trace_id)
    assert out["found"] is True
