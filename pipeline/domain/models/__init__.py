"""Canonical domain models — aligned with docs/domain-design/proposed/."""
from pipeline.domain.models.asset import Asset, AssetStatus
from pipeline.domain.models.decision_trace import DecisionTrace
from pipeline.domain.models.profile import IdentitySlice, Profile, ProfileClass
from pipeline.domain.models.review import Review, ReviewObjectType, ReviewStatus

# Transition aliases (remove after v2.1)
from pipeline.domain.models.asset import Asset as Variant  # noqa: F401

__all__ = [
    "Asset",
    "AssetStatus",
    "DecisionTrace",
    "IdentitySlice",
    "Profile",
    "ProfileClass",
    "Review",
    "ReviewObjectType",
    "ReviewStatus",
    "Variant",
]
