"""Enrichment touchpoint → canonical ingestion catalog events."""
from __future__ import annotations

from typing import Optional

from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import StreamType, SubjectRef


def _lead_stream(recipient_id: str) -> str:
    return f"lead_{recipient_id}"


def emit_enrichment_requested(recipient_id: str, *, company: str = "", consent: bool = True,
                              mode: str = "", ctx: Optional[DomainContext] = None) -> None:
    emit_domain(
        "enrichment_requested",
        stream_id=_lead_stream(recipient_id),
        stream_type=StreamType.LEAD,
        subject_ref=SubjectRef(type="recipient", id=recipient_id),
        payload={"recipient_id": recipient_id, "company": company, "consent": consent, "mode": mode},
        source={"system": "clay", "channel": "enrichment"},
        ctx=ctx,
    )


def emit_enrichment_received(recipient_id: str, *, fact_count: int, usable: int, blocked: int,
                             signals: dict, ctx: Optional[DomainContext] = None) -> None:
    emit_domain(
        "enrichment_received",
        stream_id=_lead_stream(recipient_id),
        stream_type=StreamType.LEAD,
        subject_ref=SubjectRef(type="recipient", id=recipient_id),
        payload={
            "recipient_id": recipient_id,
            "fact_count": fact_count,
            "usable": usable,
            "blocked": blocked,
            "signals": signals,
        },
        source={"system": "clay", "channel": "enrichment"},
        ctx=ctx,
    )
