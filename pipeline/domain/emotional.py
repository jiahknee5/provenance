"""Emotional safety layer — rule-based signals and mismatch circuit breaker."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from pipeline.common.schemas import Variant
from pipeline.domain.decision_trace import record_trace
from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import StreamType, SubjectRef
from pipeline.domain.models.profile import Profile


class EmotionalValence(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ArousalBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EmotionalSignal(BaseModel):
    signal_type: str
    source: str
    emotional_valence: EmotionalValence = EmotionalValence.NEUTRAL
    arousal_intensity: ArousalBand = ArousalBand.LOW
    detected_at: str = ""


class DispatchDecision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    REROUTE = "reroute"


FEAR_KEYWORDS = ("afraid", "worried", "anxious", "scared", "stress", "urgent", "risk")
RELIEF_VECTORS = ("relief_BAB", "neutral", "relief")
FEAR_VECTORS = ("fear_PAS", "fear")


def infer_signal_from_text(text: str, source: str = "text") -> EmotionalSignal:
    lower = text.lower()
    valence = EmotionalValence.NEUTRAL
    arousal = ArousalBand.LOW
    if any(w in lower for w in FEAR_KEYWORDS):
        valence = EmotionalValence.NEGATIVE
        arousal = ArousalBand.HIGH
    return EmotionalSignal(
        signal_type="text_sentiment",
        source=source,
        emotional_valence=valence,
        arousal_intensity=arousal,
    )


class EmotionalSafetyPolicy:
    """Circuit breaker from 05-safety-policy.md — high anxiety + fear asset + track cap."""

    def __init__(self, track_cap: int = 3):
        self.track_cap = track_cap

    def evaluate(
        self,
        profile: Profile,
        variant: Variant,
        session_track_count: int,
        *,
        signals: list[EmotionalSignal] | None = None,
        ctx: Optional[DomainContext] = None,
    ) -> tuple[DispatchDecision, str]:
        vector = getattr(variant, "emotional_vector", "") or "neutral"
        sigs = signals or []
        high_anxiety = any(
            s.emotional_valence == EmotionalValence.NEGATIVE
            and s.arousal_intensity == ArousalBand.HIGH
            for s in sigs
        )
        fear_asset = any(vector.startswith(f) for f in FEAR_VECTORS)

        for sig in sigs:
            emit_domain(
                "emotional_signal_detected",
                stream_id=f"lead_{profile.profile_id}",
                stream_type=StreamType.LEAD,
                subject_ref=SubjectRef(type="profile", id=profile.profile_id),
                payload=sig.model_dump(),
                ctx=ctx,
            )

        if high_anxiety and fear_asset and session_track_count >= self.track_cap:
            emit_domain(
                "emotional_mismatch_blocked",
                stream_id=f"asset_{variant.variant_id}",
                stream_type=StreamType.ASSET,
                subject_ref=SubjectRef(type="profile", id=profile.profile_id),
                payload={
                    "variant_id": variant.variant_id,
                    "emotional_vector": vector,
                    "session_track_count": session_track_count,
                },
                ctx=ctx,
            )
            record_trace(
                "emotional_dispatch",
                "blocked",
                asset_ref=variant.variant_id,
                explanation="emotional mismatch: high anxiety + fear induction",
                subject_id=profile.profile_id,
                ctx=ctx,
            )
            return DispatchDecision.BLOCK, vector

        if high_anxiety and fear_asset:
            emit_domain(
                "emotional_reroute_applied",
                stream_id=f"asset_{variant.variant_id}",
                stream_type=StreamType.ASSET,
                subject_ref=SubjectRef(type="profile", id=profile.profile_id),
                payload={"from_vector": vector, "to_vector": "relief_BAB"},
                ctx=ctx,
            )
            return DispatchDecision.REROUTE, "relief_BAB"

        return DispatchDecision.ALLOW, vector


def pick_reroute_variant(variants: list[Variant], target_vector: str = "relief_BAB") -> Optional[Variant]:
    for v in variants:
        ev = getattr(v, "emotional_vector", "") or ""
        if ev == target_vector or ev in RELIEF_VECTORS:
            return v
    for v in variants:
        ev = getattr(v, "emotional_vector", "") or "neutral"
        if not any(ev.startswith(f) for f in FEAR_VECTORS):
            return v
    return variants[0] if variants else None
