"""Campaign bandit → asset_selection_recorded at per-recipient selection time."""
from __future__ import annotations

from typing import Optional

from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import StreamType, SubjectRef


def emit_asset_selection(
    recipient_id: str,
    segment: str,
    variant_id: str,
    channel: str,
    campaign: str,
    *,
    ctx: Optional[DomainContext] = None,
) -> None:
    emit_domain(
        "asset_selection_recorded",
        stream_id=f"asset_{variant_id}",
        stream_type=StreamType.ASSET,
        subject_ref=SubjectRef(type="recipient", id=recipient_id),
        payload={
            "recipient_id": recipient_id,
            "segment": segment,
            "variant_id": variant_id,
            "channel": channel,
            "campaign": campaign,
        },
        source={"channel": channel, "system": "optimizer"},
        ctx=ctx,
    )
