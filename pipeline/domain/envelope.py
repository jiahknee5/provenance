"""Canonical event envelope — matches docs/domain-design/provenance_event_catalog/Event-Envelope.csv."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class StreamType(str, Enum):
    LEAD = "lead"
    ACCOUNT = "account"
    ASSET = "asset"
    REVIEW = "review"
    DECISION_TRACE = "decision_trace"


class SubjectRef(BaseModel):
    type: str
    id: str


class ActorRef(BaseModel):
    type: str
    id: str


class PolicyRef(BaseModel):
    version: str
    rule_refs: list[str] = Field(default_factory=list)


class ReviewRef(BaseModel):
    review_id: str
    status: str


class TraceRef(BaseModel):
    decision_trace_id: str


class EventEnvelope(BaseModel):
    event_id: str
    event_name: str
    event_version: str = "1.0"
    occurred_at: str
    recorded_at: str
    stream_id: str
    stream_type: StreamType
    stream_position: int
    correlation_id: str
    causation_id: Optional[str] = None
    tenant_id: str = "helix"
    subject_ref: SubjectRef
    actor: ActorRef
    source: dict[str, Any]
    payload: dict[str, Any]
    metadata: Optional[dict[str, Any]] = None
    policy_ref: Optional[PolicyRef] = None
    review_ref: Optional[ReviewRef] = None
    trace_ref: Optional[TraceRef] = None
    privacy_tier: Optional[str] = None
