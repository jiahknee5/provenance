"""Domain event emission — no-op unless a DomainRecorder is active."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

from pipeline.common.config import SCHEMA_VERSION, SEED
from pipeline.domain.catalog import assert_known_event, default_stream_type
from pipeline.domain.envelope import (
    ActorRef,
    EventEnvelope,
    PolicyRef,
    ReviewRef,
    StreamType,
    SubjectRef,
    TraceRef,
)
from pipeline.domain import streams as stream_mod

SYSTEM_ACTOR = ActorRef(type="system", id="provenance")
GATE_ACTOR = ActorRef(type="Gate", id="gate")

_DEFAULT_CTX: Optional[DomainContext] = None


@dataclass
class DomainContext:
    """Workflow context carried across related domain emissions."""
    correlation_id: str
    tenant_id: str = "helix"
    causation_id: Optional[str] = None
    privacy_tier: Optional[str] = None


def new_correlation_id(label: str = "") -> str:
    raw = f"{SEED}|corr|{label}"
    return "corr_" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def start_domain_run(run_id: str, correlation_id: Optional[str] = None) -> stream_mod.DomainRecorder:
    global _DEFAULT_CTX  # noqa: PLW0603
    cid = correlation_id or new_correlation_id(run_id)
    stream_mod._REC = stream_mod.DomainRecorder(run_id)  # noqa: SLF001
    _DEFAULT_CTX = DomainContext(correlation_id=cid)
    return stream_mod._REC


def end_domain_run() -> None:
    global _DEFAULT_CTX  # noqa: PLW0603
    stream_mod._REC = None  # noqa: SLF001
    _DEFAULT_CTX = None


def active() -> bool:
    return stream_mod._REC is not None


def _resolve_ctx(ctx: Optional[DomainContext]) -> DomainContext:
    if ctx is not None:
        return ctx
    if _DEFAULT_CTX is not None:
        return _DEFAULT_CTX
    return DomainContext(correlation_id=new_correlation_id("fallback"))


def emit_domain(
    event_name: str,
    *,
    stream_id: str,
    subject_ref: SubjectRef,
    payload: dict[str, Any],
    stream_type: Optional[StreamType] = None,
    actor: Optional[ActorRef] = None,
    source: Optional[dict[str, Any]] = None,
    policy_ref: Optional[PolicyRef] = None,
    review_ref: Optional[ReviewRef] = None,
    trace_ref: Optional[TraceRef] = None,
    ctx: Optional[DomainContext] = None,
    causation_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    privacy_tier: Optional[str] = None,
) -> Optional[str]:
    """Emit a canonical domain event. Returns event_id or None on failure."""
    rec = stream_mod._REC
    if rec is None:
        start_domain_run("runtime")
        rec = stream_mod._REC
    if rec is None:
        return None

    assert_known_event(event_name)
    dc = _resolve_ctx(ctx)
    st = stream_type or default_stream_type(event_name)
    pos = rec.next_position(stream_id)
    ts = rec.logical_time()
    eid = rec.next_event_id(event_name, stream_id)

    envelope = EventEnvelope(
        event_id=eid,
        event_name=event_name,
        event_version="1.0",
        occurred_at=ts,
        recorded_at=ts,
        stream_id=stream_id,
        stream_type=st,
        stream_position=pos,
        correlation_id=dc.correlation_id,
        causation_id=causation_id or dc.causation_id,
        tenant_id=tenant_id or dc.tenant_id,
        subject_ref=subject_ref,
        actor=actor or SYSTEM_ACTOR,
        source=source or {"channel": "pipeline", "system": "provenance"},
        payload=payload,
        metadata={"schema_version": str(SCHEMA_VERSION)},
        policy_ref=policy_ref,
        review_ref=review_ref,
        trace_ref=trace_ref,
        privacy_tier=privacy_tier or dc.privacy_tier,
    )
    rec.append(envelope)
    from pipeline.domain.projectors import project_event
    project_event(envelope)
    return eid


def set_causation(event_id: Optional[str], ctx: Optional[DomainContext] = None) -> None:
    global _DEFAULT_CTX  # noqa: PLW0603
    if ctx is None and _DEFAULT_CTX is not None:
        _DEFAULT_CTX.causation_id = event_id
    elif ctx is not None:
        ctx.causation_id = event_id
