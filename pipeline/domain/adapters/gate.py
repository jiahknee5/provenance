"""Gate verdict → canonical claim/policy events.

AMBER is sendable with disclaimer — emits policy_evaluated, not claim_contradicted.
Compliance-veto RED emits policy_evaluated + dispatch_suppressed.
Unsupported RED emits claim_contradicted.
"""
from __future__ import annotations

from typing import Any, Optional

from pipeline.common.schemas import ClaimVerdict, Verdict
from pipeline.domain.emit import DomainContext, GATE_ACTOR, emit_domain, set_causation
from pipeline.domain.envelope import PolicyRef, StreamType, SubjectRef


def _claim_subject(claim_id: str) -> SubjectRef:
    return SubjectRef(type="claim", id=claim_id)


def emit_claim_verdict(
    cv: ClaimVerdict,
    *,
    rules_version: str,
    ctx: Optional[DomainContext] = None,
    advisory_review: bool = False,
    policy_veto: bool = False,
) -> None:
    """Map a ClaimVerdict to the appropriate catalog event(s).

    policy_veto: the RED was forced by a compliance rule (emit policy_evaluated +
    dispatch_suppressed); otherwise an unsupported RED emits claim_contradicted. The
    caller (the Gate) knows which path produced the verdict — don't re-derive it here
    from rule_flags, which are also set for non-veto AMBER disclaimers.
    """
    subj = _claim_subject(cv.claim_id)
    stream_id = f"lead_{cv.claim_id}"
    base_payload: dict[str, Any] = {
        "claim_id": cv.claim_id,
        "text": cv.text,
        "confidence": cv.confidence,
        "verdict": cv.verdict.value,
        "reasons": cv.reasons,
        "source_id": cv.source_id,
        "source_version": cv.source_version,
    }
    policy = PolicyRef(version=rules_version, rule_refs=list(cv.rule_flags))

    if cv.verdict == Verdict.GREEN:
        eid = emit_domain(
            "claim_verified",
            stream_id=stream_id,
            stream_type=StreamType.LEAD,
            subject_ref=subj,
            payload={**base_payload, "status": "verified"},
            actor=GATE_ACTOR,
            policy_ref=policy,
            ctx=ctx,
        )
        set_causation(eid, ctx)
        return

    if cv.verdict == Verdict.AMBER:
        eid = emit_domain(
            "policy_evaluated",
            stream_id=stream_id,
            stream_type=StreamType.LEAD,
            subject_ref=subj,
            payload={
                **base_payload,
                "outcome": "sendable_with_disclaimer",
                "verification_tier": "amber",
            },
            actor=GATE_ACTOR,
            policy_ref=policy,
            ctx=ctx,
        )
        set_causation(eid, ctx)
        if advisory_review:
            emit_domain(
                "review_requested",
                stream_id=f"review_{cv.claim_id}",
                stream_type=StreamType.REVIEW,
                subject_ref=SubjectRef(type="claim", id=cv.claim_id),
                payload={
                    "object_type": "claim",
                    "object_id": cv.claim_id,
                    "review_type": "factual_verification",
                    "advisory": True,
                    "note": "AMBER — sendable with disclaimer; review is advisory",
                },
                ctx=ctx,
            )
        return

    # RED
    if policy_veto:
        eid = emit_domain(
            "policy_evaluated",
            stream_id=stream_id,
            stream_type=StreamType.LEAD,
            subject_ref=subj,
            payload={**base_payload, "outcome": "blocked", "verification_tier": "red_policy"},
            actor=GATE_ACTOR,
            policy_ref=policy,
            ctx=ctx,
        )
        set_causation(eid, ctx)
        emit_domain(
            "dispatch_suppressed",
            stream_id=f"asset_{cv.claim_id}",
            stream_type=StreamType.ASSET,
            subject_ref=SubjectRef(type="claim", id=cv.claim_id),
            payload={"reason": "policy_veto", "claim_id": cv.claim_id, "flags": cv.rule_flags},
            actor=GATE_ACTOR,
            policy_ref=policy,
            ctx=ctx,
        )
    else:
        eid = emit_domain(
            "claim_contradicted",
            stream_id=stream_id,
            stream_type=StreamType.LEAD,
            subject_ref=subj,
            payload={**base_payload, "status": "contradicted"},
            actor=GATE_ACTOR,
            policy_ref=policy,
            ctx=ctx,
        )
        set_causation(eid, ctx)
        emit_domain(
            "dispatch_suppressed",
            stream_id=f"asset_{cv.claim_id}",
            stream_type=StreamType.ASSET,
            subject_ref=SubjectRef(type="claim", id=cv.claim_id),
            payload={"reason": "unsupported_claim", "claim_id": cv.claim_id},
            actor=GATE_ACTOR,
            ctx=ctx,
        )


def emit_rules_policy(
    claim_id: str,
    rules_version: str,
    rule_tags: list[str],
    verdict: Optional[str],
    flags: list[str],
    reasons: list[str],
    *,
    ctx: Optional[DomainContext] = None,
) -> None:
    emit_domain(
        "policy_evaluated",
        stream_id=f"lead_{claim_id}",
        stream_type=StreamType.LEAD,
        subject_ref=_claim_subject(claim_id),
        payload={
            "claim_id": claim_id,
            "rules_version": rules_version,
            "rule_tags": rule_tags,
            "rule_verdict": verdict,
            "flags": flags,
            "reasons": reasons,
        },
        actor=GATE_ACTOR,
        policy_ref=PolicyRef(version=rules_version, rule_refs=flags),
        ctx=ctx,
    )
