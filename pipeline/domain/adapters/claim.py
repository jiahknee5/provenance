"""Claim lifecycle → canonical catalog events.

Claims enter the runtime from the versioned library (evidence-bound extraction).
Supersession is emitted when lineage is known (optional supersedes_claim_id) or when
drift re-verification changes a claim's binding under a new source version.
"""
from __future__ import annotations

from typing import Optional

from pipeline.common.schemas import ClaimNode
from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import StreamType, SubjectRef


def _claim_stream(claim_id: str) -> str:
    return f"lead_{claim_id}"


def _claim_subject(claim_id: str) -> SubjectRef:
    return SubjectRef(type="claim", id=claim_id)


def emit_claim_extracted(claim: ClaimNode, *, ctx: Optional[DomainContext] = None) -> None:
    emit_domain(
        "claim_extracted",
        stream_id=_claim_stream(claim.claim_id),
        stream_type=StreamType.LEAD,
        subject_ref=_claim_subject(claim.claim_id),
        payload={
            "claim_id": claim.claim_id,
            "text": claim.text,
            "source_id": claim.source_id,
            "source_version": claim.source_version,
            "status": claim.status.value,
            "span": list(claim.span),
        },
        source={"system": "claims_library"},
        ctx=ctx,
    )


def emit_claim_superseded(
    claim_id: str,
    *,
    supersedes_claim_id: Optional[str] = None,
    prior_source_version: str = "",
    new_source_version: str = "",
    reason: str = "",
    ctx: Optional[DomainContext] = None,
) -> None:
    emit_domain(
        "claim_superseded",
        stream_id=_claim_stream(claim_id),
        stream_type=StreamType.LEAD,
        subject_ref=_claim_subject(claim_id),
        payload={
            "claim_id": claim_id,
            "supersedes_claim_id": supersedes_claim_id or claim_id,
            "prior_source_version": prior_source_version,
            "new_source_version": new_source_version,
            "reason": reason,
        },
        source={"system": "claims_library"},
        ctx=ctx,
    )


def emit_library_ingested(library, *, ctx: Optional[DomainContext] = None) -> None:
    """Emit extraction (+ optional supersession) for every claim in a library snapshot."""
    for claim in library.claims.values():
        emit_claim_extracted(claim, ctx=ctx)
        if claim.supersedes_claim_id:
            emit_claim_superseded(
                claim.claim_id,
                supersedes_claim_id=claim.supersedes_claim_id,
                reason="library_ingestion",
                ctx=ctx,
            )
