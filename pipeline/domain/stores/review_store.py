"""ReviewStore — canonical Review persistence."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Literal, Optional

from pipeline.common.config import DB_PATH, SCHEMA_VERSION
from pipeline.common.db import connect
from pipeline.common.schema_meta import set_schema_version
from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import ReviewRef, StreamType, SubjectRef
from pipeline.domain.models.review import Review, ReviewStatus

_REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id    TEXT PRIMARY KEY,
    payload      TEXT NOT NULL,
    created_at   TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _review_id(object_type: str, object_id: str) -> str:
    return "rev_" + hashlib.sha256(f"{object_type}|{object_id}".encode()).hexdigest()[:12]


def init_reviews_table(conn=None) -> None:
    conn = conn or connect()
    conn.executescript(_REVIEW_SCHEMA)
    set_schema_version(conn, SCHEMA_VERSION)


class ReviewStore:
    def __init__(self, conn=None):
        self._conn = conn or connect()
        init_reviews_table(self._conn)

    def upsert(self, review: Review) -> Review:
        self._conn.execute(
            "INSERT OR REPLACE INTO reviews (review_id, payload, created_at) VALUES (?,?,?)",
            (review.review_id, review.model_dump_json(), review.requested_at),
        )
        self._conn.commit()
        return review

    def request_review(
        self,
        object_type: str,
        object_id: str,
        *,
        review_type: str = "factual_verification",
        advisory: bool = False,
        ctx: Optional[DomainContext] = None,
    ) -> Review:
        rid = _review_id(object_type, object_id)
        # The id is deterministic on (object_type, object_id): re-requesting an existing
        # review must NOT reset a reviewer's decision (APPROVED/REJECTED) back to QUEUED.
        existing = self._conn.execute(
            "SELECT payload FROM reviews WHERE review_id=?", (rid,)
        ).fetchone()
        if existing:
            return Review.model_validate_json(existing["payload"])
        review = Review(
            review_id=rid,
            object_type=object_type,
            object_id=object_id,
            review_type=review_type,
            status=ReviewStatus.QUEUED,
            advisory=advisory,
            requested_at=_now(),
        )
        self._conn.execute(
            "INSERT INTO reviews (review_id, payload, created_at) VALUES (?,?,?)",
            (rid, review.model_dump_json(), review.requested_at),
        )
        self._conn.commit()
        emit_domain(
            "review_requested",
            stream_id=f"review_{rid}",
            stream_type=StreamType.REVIEW,
            subject_ref=SubjectRef(type=object_type, id=object_id),
            payload=review.model_dump(),
            review_ref=ReviewRef(review_id=rid, status=review.status.value),
            ctx=ctx,
        )
        return review

    def list_pending(self) -> list[Review]:
        rows = self._conn.execute("SELECT payload FROM reviews").fetchall()
        out = []
        for row in rows:
            r = Review.model_validate_json(row["payload"])
            if r.status in (ReviewStatus.QUEUED, ReviewStatus.IN_REVIEW, ReviewStatus.ESCALATED):
                out.append(r)
        return sorted(out, key=lambda x: x.requested_at)

    def for_object(self, object_type: str, object_id: str) -> list[Review]:
        rows = self._conn.execute("SELECT payload FROM reviews").fetchall()
        return [
            Review.model_validate_json(row["payload"])
            for row in rows
            if Review.model_validate_json(row["payload"]).object_type == object_type
            and Review.model_validate_json(row["payload"]).object_id == object_id
        ]

    def decide(
        self,
        review_id: str,
        decision: ReviewStatus,
        *,
        notes: str = "",
        assigned_to: str = "",
        ctx: Optional[DomainContext] = None,
        overridden: bool = False,
    ) -> Optional[Review]:
        row = self._conn.execute(
            "SELECT payload FROM reviews WHERE review_id=?", (review_id,)
        ).fetchone()
        if not row:
            return None
        review = Review.model_validate_json(row["payload"])
        review.status = decision
        review.decision = decision.value
        review.decision_notes = notes
        review.assigned_to = assigned_to or review.assigned_to
        review.completed_at = _now()
        self._conn.execute(
            "UPDATE reviews SET payload=? WHERE review_id=?",
            (review.model_dump_json(), review_id),
        )
        self._conn.commit()

        event_map = {
            ReviewStatus.APPROVED: "review_approved",
            ReviewStatus.REJECTED: "review_rejected",
            ReviewStatus.ESCALATED: "review_escalated",
        }
        ename = event_map.get(decision)
        if ename:
            emit_domain(
                ename,
                stream_id=f"review_{review_id}",
                stream_type=StreamType.REVIEW,
                subject_ref=SubjectRef(type=review.object_type, id=review.object_id),
                payload=review.model_dump(),
                review_ref=ReviewRef(review_id=review_id, status=decision.value),
                ctx=ctx,
            )
        if decision == ReviewStatus.REJECTED and not review.advisory:
            emit_domain(
                "dispatch_suppressed",
                stream_id=f"asset_{review.object_id}",
                stream_type=StreamType.ASSET,
                subject_ref=SubjectRef(type=review.object_type, id=review.object_id),
                payload={"reason": "review_rejected", "review_id": review_id},
                ctx=ctx,
            )
        if overridden:
            from pipeline.domain.stores.decision_trace_store import DecisionTraceStore
            DecisionTraceStore(self._conn).record(
                "review_override", "overridden",
                asset_ref=review.object_id,
                explanation=notes or f"review {decision.value}",
                subject_id=review.object_id,
                overridden=True,
                ctx=ctx,
            )
        return review


def blocks_dispatch(review: Review) -> bool:
    if review.advisory:
        return False
    return review.status in (ReviewStatus.REJECTED, ReviewStatus.QUEUED, ReviewStatus.ESCALATED)


DispatchDecision = Literal["allow", "suppress"]


def check_dispatch(asset_id: str, store: Optional[ReviewStore] = None) -> DispatchDecision:
    """Non-advisory pending/rejected/escalated reviews suppress dispatch."""
    store = store or ReviewStore()
    for r in store.for_object("asset", asset_id):
        if blocks_dispatch(r):
            return "suppress"
    for r in store.for_object("claim", asset_id):
        if blocks_dispatch(r):
            return "suppress"
    return "allow"
