"""Asset lifecycle → canonical catalog events.

Completes the per-asset safety timeline the optimizer dashboard reads:
  create -> validate -> (dispatch | dispatch_failed)
The blocked branch (dispatch_suppressed) is emitted by the Gate adapter, not here.
"""
from __future__ import annotations

from typing import Optional

from pipeline.domain.emit import DomainContext, GATE_ACTOR, emit_domain
from pipeline.domain.envelope import PolicyRef, StreamType, SubjectRef
from pipeline.domain.models.asset import Asset


def _subject(asset_id: str) -> SubjectRef:
    return SubjectRef(type="asset", id=asset_id)


def _asset_payload(asset: Asset) -> dict:
    return {
        "asset_id": asset.asset_id,
        "segment": asset.segment,
        "channel": asset.channel,
        "arm_label": asset.arm_label,
        "claim_bindings": list(asset.claim_bindings),
        "planted_lie": asset.planted_lie,
    }


def emit_draft_created(asset: Asset, *, ctx: Optional[DomainContext] = None) -> Optional[str]:
    return emit_domain(
        "asset_draft_created",
        stream_id=f"asset_{asset.asset_id}",
        stream_type=StreamType.ASSET,
        subject_ref=_subject(asset.asset_id),
        payload={**_asset_payload(asset), "status": "draft"},
        ctx=ctx,
    )


def emit_validated(asset: Asset, *, cleared: bool, rules_version: str = "",
                   ctx: Optional[DomainContext] = None) -> Optional[str]:
    return emit_domain(
        "asset_validated",
        stream_id=f"asset_{asset.asset_id}",
        stream_type=StreamType.ASSET,
        subject_ref=_subject(asset.asset_id),
        payload={**_asset_payload(asset), "cleared": cleared, "status": asset.status.value},
        actor=GATE_ACTOR,
        policy_ref=PolicyRef(version=rules_version) if rules_version else None,
        ctx=ctx,
    )


def emit_emotional_vector_tagged(asset: Asset, *, ctx: Optional[DomainContext] = None) -> Optional[str]:
    vector = asset.emotional_vector or "neutral"
    return emit_domain(
        "asset_emotional_vector_tagged",
        stream_id=f"asset_{asset.asset_id}",
        stream_type=StreamType.ASSET,
        subject_ref=_subject(asset.asset_id),
        payload={**_asset_payload(asset), "emotional_vector": vector},
        ctx=ctx,
    )


def emit_approved(asset: Asset, *, approved_by: str = "gate_auto",
                ctx: Optional[DomainContext] = None) -> Optional[str]:
    return emit_domain(
        "asset_approved",
        stream_id=f"asset_{asset.asset_id}",
        stream_type=StreamType.ASSET,
        subject_ref=_subject(asset.asset_id),
        payload={**_asset_payload(asset), "status": "approved", "approved_by": approved_by},
        actor=GATE_ACTOR,
        ctx=ctx,
    )


def emit_publish_requested(asset_id: str, *, recipient_id: str, segment: str, channel: str,
                           campaign: str, ctx: Optional[DomainContext] = None) -> Optional[str]:
    return emit_domain(
        "asset_publish_requested",
        stream_id=f"asset_{asset_id}",
        stream_type=StreamType.ASSET,
        subject_ref=_subject(asset_id),
        payload={
            "asset_id": asset_id,
            "recipient_id": recipient_id,
            "segment": segment,
            "channel": channel,
            "campaign": campaign,
        },
        source={"channel": channel, "system": "optimizer"},
        ctx=ctx,
    )


def emit_dispatched(asset_id: str, *, recipient_id: str, segment: str, channel: str,
                    campaign: str, ctx: Optional[DomainContext] = None) -> Optional[str]:
    return emit_domain(
        "asset_dispatched",
        stream_id=f"asset_{asset_id}",
        stream_type=StreamType.ASSET,
        subject_ref=_subject(asset_id),
        payload={"asset_id": asset_id, "recipient_id": recipient_id,
                 "segment": segment, "channel": channel, "campaign": campaign},
        source={"channel": channel, "system": "optimizer"},
        ctx=ctx,
    )


def emit_dispatch_failed(*, recipient_id: str, segment: str, channel: str, campaign: str,
                         reason: str, ctx: Optional[DomainContext] = None) -> Optional[str]:
    return emit_domain(
        "dispatch_failed",
        stream_id=f"asset_dispatch_{campaign}_{segment}",
        stream_type=StreamType.ASSET,
        subject_ref=SubjectRef(type="recipient", id=recipient_id),
        payload={"recipient_id": recipient_id, "segment": segment,
                 "channel": channel, "campaign": campaign, "reason": reason},
        source={"channel": channel, "system": "optimizer"},
        ctx=ctx,
    )
