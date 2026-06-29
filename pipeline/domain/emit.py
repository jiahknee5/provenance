"""Domain event emission — no-op unless a DomainRecorder is active."""
from __future__ import annotations

import contextvars
import hashlib
import itertools
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

# Request/task-scoped, NOT a module global: under the multi-threaded server two concurrent
# visitors must not share one correlation_id or cross-link each other's causation chains.
_CTX_VAR: "contextvars.ContextVar[Optional[DomainContext]]" = contextvars.ContextVar(
    "domain_ctx", default=None
)


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
    cid = correlation_id or new_correlation_id(run_id)
    stream_mod._REC = stream_mod.DomainRecorder(run_id)  # noqa: SLF001
    _CTX_VAR.set(DomainContext(correlation_id=cid))
    return stream_mod._REC


def end_domain_run() -> None:
    stream_mod._REC = None  # noqa: SLF001
    _CTX_VAR.set(None)


_REQ_SEQ = itertools.count(1)  # process-monotonic; next() is atomic under the GIL


def begin_request_ctx(label: str = "") -> "contextvars.Token":
    """Scope a fresh domain context (own correlation_id) to the current request/task.
    Returns a token to pass to reset_request_ctx() when the request ends. The seq suffix
    keeps concurrent same-path requests from colliding on one correlation_id."""
    cid = new_correlation_id(f"{label}|{next(_REQ_SEQ)}")
    return _CTX_VAR.set(DomainContext(correlation_id=cid))


def reset_request_ctx(token: "contextvars.Token") -> None:
    _CTX_VAR.reset(token)


def active() -> bool:
    return stream_mod._REC is not None


def _resolve_ctx(ctx: Optional[DomainContext]) -> DomainContext:
    if ctx is not None:
        return ctx
    cur = _CTX_VAR.get()
    if cur is None:
        cur = DomainContext(correlation_id=new_correlation_id("runtime"))
        _CTX_VAR.set(cur)
    return cur


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
        # Create the shared recorder without touching the per-request ctx (start_domain_run
        # would overwrite the correlation_id the request middleware scoped).
        stream_mod._REC = stream_mod.DomainRecorder("runtime")  # noqa: SLF001
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
    target = ctx if ctx is not None else _CTX_VAR.get()
    if target is not None:
        target.causation_id = event_id
