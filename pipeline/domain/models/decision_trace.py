"""Canonical DecisionTrace model."""
from __future__ import annotations

from pydantic import BaseModel, Field


class DecisionTrace(BaseModel):
    decision_trace_id: str
    decision_type: str
    outcome: str
    claim_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    rule_refs: list[str] = Field(default_factory=list)
    asset_ref: str = ""
    actor_type: str = "system"
    actor_id: str = "provenance"
    explanation: str = ""
    confidence: float = 0.0
    created_at: str = ""
