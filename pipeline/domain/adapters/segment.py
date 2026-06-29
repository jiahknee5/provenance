"""Segment assignment → canonical catalog events.

Segments are still implicit `role__tier` strings (no SegmentDefinition aggregate yet),
so these record the evaluation and the resulting membership at assignment time:
  segment_evaluated         — the ruleset ran for this subject
  segment_assignment_updated — the subject's segment membership was set/changed
"""
from __future__ import annotations

from typing import Iterable, Optional

from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import StreamType, SubjectRef

RULESET_VERSION = "role_x_size_v1"


def emit_segment_assignment(recipient_id: str, segment: str, *, role: str, size: str,
                            previous_segment: Optional[str] = None,
                            ctx: Optional[DomainContext] = None) -> None:
    subj = SubjectRef(type="recipient", id=recipient_id)
    stream_id = f"lead_{recipient_id}"
    payload = {
        "recipient_id": recipient_id,
        "segment": segment,
        "role": role,
        "size": size,
        "ruleset_version": RULESET_VERSION,
    }
    emit_domain("segment_evaluated", stream_id=stream_id, stream_type=StreamType.LEAD,
                subject_ref=subj, payload=payload, ctx=ctx)
    if segment != previous_segment:
        emit_domain("segment_assignment_updated", stream_id=stream_id, stream_type=StreamType.LEAD,
                    subject_ref=subj, payload={**payload, "previous_segment": previous_segment},
                    ctx=ctx)


def emit_segment_assignments(recipients: Iterable, *, ctx: Optional[DomainContext] = None) -> None:
    """Bulk segment assignment for the seeded recipient cohort."""
    for r in recipients:
        emit_segment_assignment(r.recipient_id, r.segment, role=r.role, size=r.company_size, ctx=ctx)
