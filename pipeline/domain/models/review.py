"""Canonical Review model."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ReviewStatus(str, Enum):
    QUEUED = "queued"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ReviewObjectType(str, Enum):
    CLAIM = "claim"
    ASSET = "asset"
    SEGMENT = "segment"
    POLICY = "policy"


class Review(BaseModel):
    review_id: str
    object_type: str
    object_id: str
    review_type: str = "factual_verification"
    status: ReviewStatus = ReviewStatus.QUEUED
    requested_by: str = "system"
    assigned_to: str = ""
    decision: str = ""
    decision_notes: str = ""
    advisory: bool = False
    sla_due_at: str = ""
    requested_at: str = ""
    completed_at: str = ""
