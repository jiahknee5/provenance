"""Drift monitor → claim freshness catalog events."""
from __future__ import annotations

from typing import Optional

from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import StreamType, SubjectRef


def emit_drift_reverification(
    claim_id: str,
    before: str,
    after: str,
    *,
    ctx: Optional[DomainContext] = None,
) -> None:
    stream_id = f"lead_{claim_id}"
    subj = SubjectRef(type="claim", id=claim_id)
    if before != after:
        emit_domain(
            "claim_marked_stale",
            stream_id=stream_id,
            stream_type=StreamType.LEAD,
            subject_ref=subj,
            payload={"claim_id": claim_id, "before": before, "after": after},
            ctx=ctx,
        )
    emit_domain(
        "claim_reverification_requested",
        stream_id=stream_id,
        stream_type=StreamType.LEAD,
        subject_ref=subj,
        payload={"claim_id": claim_id, "before": before, "after": after},
        ctx=ctx,
    )
