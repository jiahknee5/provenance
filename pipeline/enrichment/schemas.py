"""Enrichment schemas — the receipt every personal fact must carry.

Mirrors the claim substrate (pipeline/common/schemas.py): just as a ClaimNode binds to a
source span + source_version, a ProfileFact binds to a source connector + a lawful basis +
a freshness TTL. `age_seconds` (not a wall clock) carries freshness so the pipeline stays
deterministic — a freshly fetched fact is age 0; a drift event or an audit trap sets it
stale. The Enrichment Gate turns a RawFact into a verdicted ProfileFact.
"""
from __future__ import annotations

import hashlib
from enum import Enum

from pydantic import BaseModel, Field


class FactVerdict(str, Enum):
    USABLE = "usable"          # allowed source + consented + fresh -> may be inlined
    DISCLAIMER = "disclaimer"  # usable but inferred (account-level) -> flag as inferred
    BLOCKED = "blocked"        # no basis / stale / non-consent / PHI -> never inlined


class RawFact(BaseModel):
    """What a connector returns, before the Enrichment Gate verdicts it."""
    key: str                   # e.g. company_domain, recent_news, intent_topic
    value: str
    source: str                # source id — must be in the enrichment allow-list
    confidence: float = 0.8
    age_seconds: int = 0       # 0 = freshly fetched; large = stale (drift / trap)
    detail: str = ""           # provenance note (headline, MX host, …) — the receipt body


class ProfileFact(RawFact):
    fact_id: str = ""
    recipient_id: str = ""
    source_kind: str = ""      # free | paid | first_party
    basis: str = ""            # the recorded lawful basis (the receipt)
    ttl_seconds: int = 0
    verdict: FactVerdict = FactVerdict.BLOCKED
    reasons: list[str] = Field(default_factory=list)

    @staticmethod
    def make_id(recipient_id: str, key: str, source: str) -> str:
        return "f_" + hashlib.sha256(f"{recipient_id}|{key}|{source}".encode()).hexdigest()[:10]

    @property
    def inlinable(self) -> bool:
        return self.verdict in (FactVerdict.USABLE, FactVerdict.DISCLAIMER)


class Profile(BaseModel):
    recipient_id: str
    segment: str = ""
    facts: list[ProfileFact] = Field(default_factory=list)
    signals: dict = Field(default_factory=dict)   # intent_topic, in_market, account_tier
    synthesized_seq: int = 0

    @property
    def usable_facts(self) -> list[ProfileFact]:
        return [f for f in self.facts if f.inlinable]

    @property
    def blocked_facts(self) -> list[ProfileFact]:
        return [f for f in self.facts if f.verdict == FactVerdict.BLOCKED]
