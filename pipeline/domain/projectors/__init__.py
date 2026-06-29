"""Event projectors — rebuild read models from domain streams."""
from __future__ import annotations

from typing import Optional

from pipeline.domain.envelope import EventEnvelope, StreamType
from pipeline.domain.models.asset import Asset, AssetStatus
from pipeline.domain.models.profile import Profile, ProfileClass
from pipeline.domain.models.review import Review, ReviewStatus
from pipeline.domain.models.decision_trace import DecisionTrace
from pipeline.domain.stream_reader import StreamReader
from pipeline.domain.stores.asset_store import AssetStore
from pipeline.domain.stores.decision_trace_store import DecisionTraceStore
from pipeline.domain.stores.profile_store import ProfileStore
from pipeline.domain.stores.review_store import ReviewStore

_SEEN: set[str] = set()


def _idempotent(event_id: str) -> bool:
    if event_id in _SEEN:
        return False
    _SEEN.add(event_id)
    return True


def reset_idempotency() -> None:
    _SEEN.clear()


class LeadProjector:
    def __init__(self, store: Optional[ProfileStore] = None):
        self.store = store or ProfileStore()

    def apply(self, event: EventEnvelope) -> None:
        if not _idempotent(event.event_id):
            return
        # The LEAD stream also carries Gate claim/policy events whose subject is a claim_id,
        # not a profile. Only lead-lifecycle events (subject type 'profile') project here;
        # otherwise we'd write junk Profile rows keyed by claim id into profiles_v2.
        if event.subject_ref.type != "profile":
            return
        pid = event.subject_ref.id
        profile = self.store.get(pid) or Profile(
            profile_id=pid,
            profile_class=ProfileClass.LEAD,
        )
        name = event.event_name
        payload = event.payload
        if name == "visitor_identified":
            profile.identity.visitor_id = payload.get("visitor_id", "")
            profile.profile_class = ProfileClass.ANONYMOUS
        elif name == "form_submitted":
            profile.identity.email = payload.get("email", "")
            profile.identity.name = payload.get("name", "")
            profile.identity.consent = payload.get("consent", False)
            profile.profile_class = ProfileClass.LEAD
        elif name == "identity_resolved":
            profile.profile_class = ProfileClass.LEAD
        elif name == "enrichment_received":
            profile.segment = payload.get("segment", profile.segment)
        elif name == "evidence_captured":
            pass
        self.store.upsert(profile)


class AssetProjector:
    def __init__(self, store: Optional[AssetStore] = None):
        self.store = store or AssetStore()

    def apply(self, event: EventEnvelope) -> None:
        if not _idempotent(event.event_id):
            return
        if event.event_name == "asset_selection_recorded":
            vid = payload.get("variant_id", "") if (payload := event.payload) else ""
            if vid:
                asset = self.store.get(vid) or Asset(
                    asset_id=vid,
                    segment=payload.get("segment", ""),
                    channel=payload.get("channel", "email"),
                    status=AssetStatus.LIVE,
                )
                self.store.save(asset)


class ReviewProjector:
    def __init__(self, store: Optional[ReviewStore] = None):
        self.store = store or ReviewStore()

    def apply(self, event: EventEnvelope) -> None:
        if not _idempotent(event.event_id):
            return
        if event.event_name.startswith("review_"):
            payload = event.payload
            if "review_id" not in payload:
                return
            review = Review.model_validate(payload)
            self.store.upsert(review)


class DecisionTraceProjector:
    def __init__(self, store: Optional[DecisionTraceStore] = None):
        self.store = store or DecisionTraceStore()

    def apply(self, event: EventEnvelope) -> None:
        if not _idempotent(event.event_id):
            return
        if event.event_name in ("decision_trace_recorded", "decision_overridden"):
            trace = DecisionTrace.model_validate(event.payload)
            self.store.upsert(trace)


def project_event(event: EventEnvelope) -> None:
    st = event.stream_type
    if st == StreamType.LEAD:
        LeadProjector().apply(event)
    elif st == StreamType.ASSET:
        AssetProjector().apply(event)
    elif st == StreamType.REVIEW:
        ReviewProjector().apply(event)
    elif st == StreamType.DECISION_TRACE:
        DecisionTraceProjector().apply(event)


def replay_all(reader: Optional[StreamReader] = None) -> int:
    reset_idempotency()
    reader = reader or StreamReader()
    count = 0
    for event in reader.global_sequence():
        project_event(event)
        count += 1
    return count
