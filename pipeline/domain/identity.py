"""IdentityCandidate resolution — emits catalog identity events."""
from __future__ import annotations

import hashlib
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import StreamType, SubjectRef


class ResolutionStatus(str, Enum):
    PENDING = "pending"
    LINKED = "linked"
    CONFLICTED = "conflicted"
    REJECTED = "rejected"


class IdentityCandidate(BaseModel):
    identity_candidate_id: str = ""
    source_refs: list[str] = Field(default_factory=list)
    person_name: str = ""
    email: str = ""
    linkedin_url: str = ""
    company_name: str = ""
    match_confidence: float = 0.0
    resolution_status: ResolutionStatus = ResolutionStatus.PENDING

    @staticmethod
    def make_id(*parts: str) -> str:
        raw = "|".join(parts)
        return "ic_" + hashlib.sha256(raw.encode()).hexdigest()[:12]


class ResolutionResult(BaseModel):
    status: ResolutionStatus
    profile_id: str = ""
    candidates: list[IdentityCandidate] = Field(default_factory=list)
    conflict_reason: str = ""


class IdentityResolver:
    """Deterministic identity linking for the demo funnel."""

    def resolve(
        self,
        candidates: list[IdentityCandidate],
        *,
        profile_id: str,
        ctx: Optional[DomainContext] = None,
    ) -> ResolutionResult:
        emit_domain(
            "identity_resolution_requested",
            stream_id=f"lead_{profile_id}",
            stream_type=StreamType.LEAD,
            subject_ref=SubjectRef(type="profile", id=profile_id),
            payload={"candidate_count": len(candidates)},
            ctx=ctx,
        )

        emails = {c.email.lower() for c in candidates if c.email}
        if len(emails) > 1:
            emit_domain(
                "identity_conflicted",
                stream_id=f"lead_{profile_id}",
                stream_type=StreamType.LEAD,
                subject_ref=SubjectRef(type="profile", id=profile_id),
                payload={"reason": "email_mismatch", "emails": sorted(emails)},
                ctx=ctx,
            )
            return ResolutionResult(
                status=ResolutionStatus.CONFLICTED,
                profile_id=profile_id,
                candidates=candidates,
                conflict_reason="email_mismatch",
            )

        if not candidates:
            return ResolutionResult(status=ResolutionStatus.REJECTED, profile_id=profile_id)

        best = max(candidates, key=lambda c: c.match_confidence)
        best.resolution_status = ResolutionStatus.LINKED
        emit_domain(
            "identity_resolved",
            stream_id=f"lead_{profile_id}",
            stream_type=StreamType.LEAD,
            subject_ref=SubjectRef(type="profile", id=profile_id),
            payload={
                "identity_candidate_id": best.identity_candidate_id,
                "email": best.email,
                "match_confidence": best.match_confidence,
            },
            ctx=ctx,
        )
        return ResolutionResult(
            status=ResolutionStatus.LINKED,
            profile_id=profile_id,
            candidates=candidates,
        )


def candidate_from_customer(customer_id: str, visitor_id: str = "", email: str = "",
                            name: str = "", source: str = "funnel") -> IdentityCandidate:
    refs = [source]
    if visitor_id:
        refs.append(f"visitor:{visitor_id}")
    return IdentityCandidate(
        identity_candidate_id=IdentityCandidate.make_id(customer_id, source),
        source_refs=refs,
        person_name=name,
        email=email,
        match_confidence=0.9 if email else 0.5,
    )
