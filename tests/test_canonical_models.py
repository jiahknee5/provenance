"""Canonical domain models and stores."""
from __future__ import annotations

from pipeline.common.schemas import Variant
from pipeline.domain.models import Asset, AssetStatus, Profile, ProfileClass, Review, ReviewStatus
from pipeline.domain.stores.asset_store import AssetStore
from pipeline.domain.stores.profile_store import ProfileStore
from pipeline.domain.stores.review_store import ReviewStore, check_dispatch, blocks_dispatch


def test_profile_roundtrip(tmp_path):
    store = ProfileStore(path=tmp_path / "profiles.sqlite")
    p = Profile(profile_id="p1", profile_class=ProfileClass.LEAD)
    p.identity.email = "a@b.com"
    store.upsert(p)
    loaded = store.get("p1")
    assert loaded.identity.email == "a@b.com"


def test_asset_from_variant(tmp_path):
    v = Variant(variant_id="seg__email__A", segment="seg", template="hi {name}",
                claim_ids=["c1"], emotional_vector="neutral")
    asset = Asset.from_variant(v, status=AssetStatus.VALIDATED)
    assert asset.asset_id == v.variant_id
    store = AssetStore(path=tmp_path / "assets.sqlite")
    store.save(asset)
    assert store.get(asset.asset_id).status == AssetStatus.VALIDATED


def test_advisory_review_does_not_block_dispatch():
    review = Review(
        review_id="r1", object_type="asset", object_id="v1",
        review_type="factual", status=ReviewStatus.QUEUED, advisory=True,
        requested_at="2025-01-01T00:00:00Z",
    )
    assert blocks_dispatch(review) is False
    assert check_dispatch("v1", store=_FakeStore([review])) == "allow"


def test_rejected_review_blocks_dispatch():
    review = Review(
        review_id="r2", object_type="asset", object_id="v2",
        review_type="factual", status=ReviewStatus.REJECTED, advisory=False,
        requested_at="2025-01-01T00:00:00Z",
    )
    assert blocks_dispatch(review) is True
    assert check_dispatch("v2", store=_FakeStore([review])) == "suppress"


class _FakeStore:
    def __init__(self, reviews):
        self._reviews = reviews

    def for_object(self, object_type, object_id):
        return [r for r in self._reviews
                if r.object_type == object_type and r.object_id == object_id]
