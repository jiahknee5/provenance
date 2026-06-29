"""Canonical event catalog — mirrors Event-Catalog.csv."""
from __future__ import annotations

from typing import Literal, get_args

from pipeline.domain.envelope import StreamType

EventName = Literal[
    "visitor_identified",
    "form_submitted",
    "enrichment_requested",
    "enrichment_received",
    "identity_resolution_requested",
    "identity_resolved",
    "identity_conflicted",
    "evidence_captured",
    "text_sentiment_scored",
    "claim_extracted",
    "claim_verified",
    "claim_contradicted",
    "claim_marked_stale",
    "claim_reverification_requested",
    "claim_superseded",
    "segment_evaluated",
    "segment_assignment_updated",
    "emotional_signal_detected",
    "emotional_segment_assignment_updated",
    "asset_draft_created",
    "asset_emotional_vector_tagged",
    "asset_validated",
    "asset_approved",
    "asset_publish_requested",
    "review_requested",
    "review_approved",
    "review_rejected",
    "review_escalated",
    "policy_evaluated",
    "emotional_mismatch_blocked",
    "emotional_reroute_applied",
    "dispatch_suppressed",
    "asset_dispatched",
    "dispatch_failed",
    "asset_selection_recorded",
    "decision_overridden",
    "decision_trace_recorded",
]

EVENT_NAMES: tuple[str, ...] = get_args(EventName)

# Primary stream type per catalog entry
EVENT_STREAM: dict[str, StreamType] = {
    "visitor_identified": StreamType.LEAD,
    "form_submitted": StreamType.LEAD,
    "enrichment_requested": StreamType.LEAD,
    "enrichment_received": StreamType.LEAD,
    "identity_resolution_requested": StreamType.LEAD,
    "identity_resolved": StreamType.LEAD,
    "identity_conflicted": StreamType.LEAD,
    "evidence_captured": StreamType.LEAD,
    "text_sentiment_scored": StreamType.LEAD,
    "claim_extracted": StreamType.LEAD,
    "claim_verified": StreamType.LEAD,
    "claim_contradicted": StreamType.LEAD,
    "claim_marked_stale": StreamType.LEAD,
    "claim_reverification_requested": StreamType.LEAD,
    "claim_superseded": StreamType.LEAD,
    "segment_evaluated": StreamType.LEAD,
    "segment_assignment_updated": StreamType.LEAD,
    "emotional_signal_detected": StreamType.LEAD,
    "emotional_segment_assignment_updated": StreamType.LEAD,
    "asset_draft_created": StreamType.ASSET,
    "asset_emotional_vector_tagged": StreamType.ASSET,
    "asset_validated": StreamType.ASSET,
    "asset_approved": StreamType.ASSET,
    "asset_publish_requested": StreamType.ASSET,
    "review_requested": StreamType.REVIEW,
    "review_approved": StreamType.REVIEW,
    "review_rejected": StreamType.REVIEW,
    "review_escalated": StreamType.REVIEW,
    "policy_evaluated": StreamType.LEAD,
    "emotional_mismatch_blocked": StreamType.ASSET,
    "emotional_reroute_applied": StreamType.ASSET,
    "dispatch_suppressed": StreamType.ASSET,
    "asset_dispatched": StreamType.ASSET,
    "dispatch_failed": StreamType.ASSET,
    "asset_selection_recorded": StreamType.ASSET,
    "decision_overridden": StreamType.DECISION_TRACE,
    "decision_trace_recorded": StreamType.DECISION_TRACE,
}


def default_stream_type(event_name: str) -> StreamType:
    return EVENT_STREAM.get(event_name, StreamType.LEAD)


def assert_known_event(event_name: str) -> None:
    if event_name not in EVENT_NAMES:
        raise ValueError(f"unknown domain event {event_name!r}")
