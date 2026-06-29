"""Review lifecycle — AMBER advisory does not block dispatch."""
from __future__ import annotations

import pytest

from pipeline.domain.emit import end_domain_run, start_domain_run
from pipeline.domain.review import ReviewStatus, ReviewStore, blocks_dispatch
from pipeline.domain import streams as stream_mod
from pipeline.domain.envelope import StreamType


@pytest.fixture
def review_store(tmp_path, tmp_db, monkeypatch):
    monkeypatch.setattr(stream_mod, "STREAMS_DIR", tmp_path / "streams")
    start_domain_run("review-test")
    store = ReviewStore(conn=tmp_db)
    yield store
    end_domain_run()


def test_advisory_review_does_not_block(review_store):
    r = review_store.request_review("claim", "c_tco", advisory=True)
    assert blocks_dispatch(r) is False


def test_reject_non_advisory_blocks(review_store):
    r = review_store.request_review("asset", "v1", advisory=False)
    review_store.decide(r.review_id, ReviewStatus.REJECTED, notes="no")
    r2 = review_store.list_pending()
    assert all(x.review_id != r.review_id for x in r2)
    events = stream_mod.active_recorder().read_stream(StreamType.ASSET, "asset_v1")
    assert any(e.event_name == "dispatch_suppressed" for e in events)


def test_approve_emits_event(review_store):
    r = review_store.request_review("claim", "c1", advisory=True)
    review_store.decide(r.review_id, ReviewStatus.APPROVED)
    events = stream_mod.active_recorder().read_stream(StreamType.REVIEW, f"review_{r.review_id}")
    assert any(e.event_name == "review_approved" for e in events)
