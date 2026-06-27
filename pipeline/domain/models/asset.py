"""Canonical Asset aggregate — replaces Variant at runtime boundary."""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pipeline.common.schemas import Recipient, Variant


class AssetStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    APPROVED = "approved"
    LIVE = "live"
    RETIRED = "retired"


class Asset(BaseModel):
    asset_id: str
    variant_id: str = ""  # deprecated compat field; equals asset_id when unset
    asset_type: str = "email"
    segment: str = ""
    channel: str = "email"
    arm_label: str = "A"
    template: str = ""
    claim_bindings: list[str] = Field(default_factory=list)
    segment_bindings: list[str] = Field(default_factory=list)
    status: AssetStatus = AssetStatus.DRAFT
    policy_version: str = ""
    emotional_vector: str = "neutral"
    planted_lie: bool = False
    headline: str = ""
    approved_by: str = ""
    approved_at: str = ""
    published_at: str = ""

    def model_post_init(self, __ctx) -> None:
        if not self.variant_id:
            object.__setattr__(self, "variant_id", self.asset_id)
        if not self.claim_bindings and hasattr(self, "_claim_ids"):
            pass

    @property
    def claim_ids(self) -> list[str]:
        return self.claim_bindings

    def render(self, recipient: "Recipient", claim_text: dict[str, str]) -> str:
        body = self.template.format(
            name=recipient.name.split()[0],
            company=recipient.company,
            role=recipient.role,
        )
        for cid in self.claim_bindings:
            body = body.replace(f"[[{cid}]]", claim_text.get(cid, ""))
        return body

    @classmethod
    def from_variant(cls, variant: "Variant", status: AssetStatus = AssetStatus.VALIDATED) -> Asset:
        return cls(
            asset_id=variant.variant_id,
            variant_id=variant.variant_id,
            segment=variant.segment,
            channel=variant.channel,
            arm_label=variant.arm_label,
            template=variant.template,
            claim_bindings=list(variant.claim_ids),
            segment_bindings=[variant.segment] if variant.segment else [],
            status=status,
            emotional_vector=getattr(variant, "emotional_vector", "neutral"),
            planted_lie=variant.planted_lie,
            headline=variant.headline,
            asset_type=variant.channel,
        )

    def to_variant(self) -> "Variant":
        from pipeline.common.schemas import Variant
        return Variant(
            variant_id=self.asset_id,
            segment=self.segment,
            channel=self.channel,
            arm_label=self.arm_label,
            template=self.template,
            claim_ids=list(self.claim_bindings),
            planted_lie=self.planted_lie,
            headline=self.headline,
            emotional_vector=self.emotional_vector,
        )
