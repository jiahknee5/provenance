"""Canonical domain event bridge — parallel to pipeline/common/observe.py.

Emits catalog event names with full envelopes when a DomainRecorder is active;
no-op otherwise (tests and plain runs unchanged).
"""
from pipeline.domain.emit import (
    DomainContext,
    active,
    emit_domain,
    end_domain_run,
    new_correlation_id,
    start_domain_run,
)
from pipeline.domain.envelope import EventEnvelope, StreamType, SubjectRef

__all__ = [
    "DomainContext",
    "EventEnvelope",
    "StreamType",
    "SubjectRef",
    "active",
    "emit_domain",
    "end_domain_run",
    "new_correlation_id",
    "start_domain_run",
]
