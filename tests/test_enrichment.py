"""Enrichment / data-provenance properties (the E1 acceptance + parity + determinism).

These guard the operator's Fork 1-B decision: personal facts MAY appear in copy, but only
gated ones — an un-receipted fact can never reach a message. No network (synthetic mode).
"""
from __future__ import annotations

import pytest

from pipeline.common.schemas import Recipient
from pipeline.enrichment.audit import run_fact_audit
from pipeline.enrichment.engine import enrich, personalize
from pipeline.enrichment.gate import EnrichmentGate
from pipeline.enrichment.schemas import FactVerdict, Profile, RawFact


def _recipient(consent: bool = True) -> Recipient:
    return Recipient(
        recipient_id="r_test", token="t" * 16, name="Maria Chen",
        email="maria.chen@northwindhealth.org", company="Northwind Health",
        role="clinops", company_size="idn", region="Midwest",
        use_case="reduce length of stay", urgency="high", consent=consent,
        heard_via="webinar", segment="clinops__ent", created_at="2025-01-01T00:00:00Z")


@pytest.fixture()
def gate():
    return EnrichmentGate()


def test_disallowed_source_always_blocked(gate):
    pf = gate.evaluate(RawFact(key="seniority", value="VP", source="scraped_linkedin"),
                       _recipient())
    assert pf.verdict == FactVerdict.BLOCKED
    assert not pf.inlinable


def test_stale_fact_blocked(gate):
    pf = gate.evaluate(RawFact(key="recent_news", value="old", source="company_news_rss",
                               age_seconds=10_000_000), _recipient())
    assert pf.verdict == FactVerdict.BLOCKED


def test_phi_key_blocked(gate):
    pf = gate.evaluate(RawFact(key="diagnosis", value="x", source="firmographic_sim"),
                       _recipient())
    assert pf.verdict == FactVerdict.BLOCKED


def test_non_consent_blocks_everything(gate):
    pf = gate.evaluate(RawFact(key="recent_news", value="news", source="company_news_rss"),
                       _recipient(consent=False))
    assert pf.verdict == FactVerdict.BLOCKED


def test_clean_fact_usable(gate):
    pf = gate.evaluate(RawFact(key="recent_news", value="opened a facility",
                               source="company_news_rss"), _recipient())
    assert pf.verdict == FactVerdict.USABLE
    assert pf.basis == "public_record"


def test_blocked_fact_never_in_copy(gate):
    """Parity: a blocked fact cannot reach the rendered message (E1 / Fork 1-B guard)."""
    r = _recipient()
    blocked = gate.evaluate(RawFact(key="seniority", value="SECRET_LEAK",
                                    source="scraped_linkedin"), r)
    usable = gate.evaluate(RawFact(key="recent_news", value="public headline",
                                   source="company_news_rss"), r)
    prof = Profile(recipient_id=r.recipient_id, facts=[blocked, usable])
    out = personalize(r, prof, "VERIFIED CLAIM BODY")
    assert "SECRET_LEAK" not in out["body"]
    assert "VERIFIED CLAIM BODY" in out["body"]
    assert all(rec["key"] != "seniority" for rec in out["personalization"])


def test_every_inlined_fact_carries_a_basis(gate):
    r = _recipient()
    prof = enrich(r)
    out = personalize(r, prof, "BODY")
    for rec in out["personalization"]:
        assert rec["basis"], f"inlined fact {rec['key']} has no recorded basis"


def test_fact_audit_catches_all_unshippable(gate):
    res = run_fact_audit(gate, _recipient())
    assert res["catch_rate"] == 1.0      # every disallowed/stale/PHI/non-consent trap blocked
    assert res["false_block"] == 0.0     # the clean fact is not blocked


def test_synthetic_enrichment_is_deterministic():
    a = enrich(_recipient()).model_dump_json()
    b = enrich(_recipient()).model_dump_json()
    assert a == b
