"""Identity resolution tests."""
from __future__ import annotations

import pytest

from pipeline.customer.funnel import new_visitor, web_signup
from pipeline.domain.emit import end_domain_run, start_domain_run
from pipeline.domain.identity import IdentityResolver, ResolutionStatus, candidate_from_customer
from pipeline.domain import streams as stream_mod
from pipeline.domain.envelope import StreamType


@pytest.fixture
def domain_recorder(tmp_path, monkeypatch):
    monkeypatch.setattr(stream_mod, "STREAMS_DIR", tmp_path / "streams")
    start_domain_run("identity-test")
    yield
    end_domain_run()


def test_identity_happy_path(domain_recorder):
    resolver = IdentityResolver()
    cands = [candidate_from_customer("c1", email="a@test.com", name="Ann")]
    result = resolver.resolve(cands, profile_id="c1")
    assert result.status == ResolutionStatus.LINKED


def test_identity_email_conflict(domain_recorder):
    resolver = IdentityResolver()
    cands = [
        candidate_from_customer("c1", email="a@test.com"),
        candidate_from_customer("c1", email="b@test.com"),
    ]
    result = resolver.resolve(cands, profile_id="c1")
    assert result.status == ResolutionStatus.CONFLICTED


def test_funnel_emits_identity_events(domain_recorder):
    c = new_visitor("vis_abc")
    web_signup(c, "Test User", "user@example.com")
    events = stream_mod.active_recorder().read_stream(StreamType.LEAD, f"lead_{c.customer_id}")
    names = [e.event_name for e in events]
    assert "visitor_identified" in names
    assert "form_submitted" in names
    assert "identity_resolved" in names
