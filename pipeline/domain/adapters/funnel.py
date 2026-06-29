"""Customer funnel → ingestion and evidence catalog events."""
from __future__ import annotations

from typing import Optional

from pipeline.customer.schemas import Customer, TouchpointEvent
from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import StreamType, SubjectRef


def _profile_stream(customer_id: str) -> str:
    return f"lead_{customer_id}"


def emit_visitor_identified(customer: Customer, *, ctx: Optional[DomainContext] = None) -> None:
    emit_domain(
        "visitor_identified",
        stream_id=_profile_stream(customer.customer_id),
        stream_type=StreamType.LEAD,
        subject_ref=SubjectRef(type="profile", id=customer.customer_id),
        payload={"visitor_id": customer.visitor_id, "customer_id": customer.customer_id},
        source={"channel": "web", "system": "funnel"},
        privacy_tier="ANONYMOUS" if not customer.email else "WEAK_CONTEXTUAL",
        ctx=ctx,
    )


def emit_form_submitted(customer: Customer, *, ctx: Optional[DomainContext] = None) -> None:
    emit_domain(
        "form_submitted",
        stream_id=_profile_stream(customer.customer_id),
        stream_type=StreamType.LEAD,
        subject_ref=SubjectRef(type="profile", id=customer.customer_id),
        payload={"email": customer.email, "name": customer.name, "consent": customer.consent},
        source={"channel": "web_form", "system": "funnel"},
        privacy_tier="STRONG_IDENTIFIED",
        ctx=ctx,
    )


def emit_evidence_captured(
    customer: Customer,
    event: TouchpointEvent,
    *,
    ctx: Optional[DomainContext] = None,
) -> None:
    emit_domain(
        "evidence_captured",
        stream_id=_profile_stream(customer.customer_id),
        stream_type=StreamType.LEAD,
        subject_ref=SubjectRef(type="profile", id=customer.customer_id),
        payload={
            "event_id": event.event_id,
            "source": event.source,
            "detail": event.detail,
            "fact_keys": event.fact_keys,
        },
        source={"channel": event.source, "system": "funnel"},
        ctx=ctx,
    )
