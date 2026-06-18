"""Frozen schemas — the contracts every module codes against.

Two records are load-bearing and frozen:
  * ClaimNode / SourceDoc  — the claim-evidence substrate (with source_version edges,
    so the Drift Monitor can walk claim -> source_version).
  * MessageLedger          — the per-message output (the integration contract from
    team/onboarding.md §4), extended with `channel` so email + website share one ledger.

The verdict cache is keyed (claim_id, source_version, rules_version) — see cache.py.
"""
from __future__ import annotations

import hashlib
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Verdicts
# --------------------------------------------------------------------------- #
class Verdict(str, Enum):
    GREEN = "green"   # entailed by source + permissible -> cited
    AMBER = "amber"   # uncertain / needs disclaimer -> repaired
    RED = "red"       # unsupported or impermissible -> blocked


class PufferyClass(str, Enum):
    FACT = "fact"         # checkable factual claim
    PUFFERY = "puffery"   # subjective/marketing language, not a verifiable fact


class ClaimStatus(str, Enum):
    IN_DATE = "in_date"
    RETIRED = "retired"
    QUARANTINED = "quarantined"


# --------------------------------------------------------------------------- #
# Sources & claims (the substrate)
# --------------------------------------------------------------------------- #
def content_version(text: str) -> str:
    """A source's version is the hash of its content — Drift detects change by diff."""
    return "v_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


class SourceDoc(BaseModel):
    source_id: str
    title: str
    text: str
    jurisdiction: str = "US"
    source_version: str = ""

    def model_post_init(self, __ctx) -> None:  # pydantic v2 hook
        if not self.source_version:
            object.__setattr__(self, "source_version", content_version(self.text))


class ClaimNode(BaseModel):
    claim_id: str
    text: str                       # the canonical claim sentence (verbatim-citable)
    source_id: str
    span: tuple[int, int]           # [start, end] char offsets into the source text
    source_version: str             # the source version this claim depends on
    status: ClaimStatus = ClaimStatus.IN_DATE
    puffery_class: PufferyClass = PufferyClass.FACT
    # the asserted numeric value (if the claim makes one) — what number-drift mutates
    numeric: Optional[float] = None
    numeric_unit: str = ""
    # micro-segments this claim is relevant to (empty = all)
    segments: list[str] = Field(default_factory=list)
    # compliance category tags the rules engine keys on (e.g. "roi_outcome", "superlative")
    rule_tags: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Per-claim verdict + message ledger (the integration contract)
# --------------------------------------------------------------------------- #
class ClaimVerdict(BaseModel):
    claim_id: str
    text: str
    span: tuple[int, int]
    verdict: Verdict
    source_id: str
    confidence: float = 0.0         # calibrated P(entailed & permissible)
    rule_flags: list[str] = Field(default_factory=list)
    nli_score: float = 0.0          # raw entailment score (pre-calibration)
    ensemble_score: float = 0.0     # mean judge agreement
    reasons: list[str] = Field(default_factory=list)
    source_version: str = ""
    rules_version: str = ""


class MessageLedger(BaseModel):
    recipient_id: str
    track: str = "provenance"
    channel: str = "email"          # "email" | "website"
    variant_id: str = ""
    segment: str = ""
    html: str = ""                  # rendered copy
    claims: list[ClaimVerdict] = Field(default_factory=list)
    generated_at: str = ""

    @property
    def cleared(self) -> bool:
        """A message is sendable iff it has no red claim."""
        return all(c.verdict != Verdict.RED for c in self.claims)


# --------------------------------------------------------------------------- #
# Generation: variants (the bandit arms)
# --------------------------------------------------------------------------- #
class Variant(BaseModel):
    variant_id: str
    segment: str
    channel: str = "email"
    arm_label: str = "A"            # A / B / ...
    template: str                   # text with {name},{company} slots + claim markers
    claim_ids: list[str] = Field(default_factory=list)  # approved claims it asserts
    planted_lie: bool = False       # demo trap: an unverifiable high-CTR variant
    headline: str = ""

    def render(self, recipient: "Recipient", claim_text: dict[str, str]) -> str:
        """Slot-fill personalization + inline the *approved* claim text verbatim."""
        body = self.template.format(
            name=recipient.name.split()[0],
            company=recipient.company,
            role=recipient.role,
        )
        for cid in self.claim_ids:
            body = body.replace(f"[[{cid}]]", claim_text.get(cid, ""))
        return body


# --------------------------------------------------------------------------- #
# Recipients (the 1000 synthetic form submissions)
# --------------------------------------------------------------------------- #
class Recipient(BaseModel):
    recipient_id: str
    token: str                      # opaque magic-link token (no PII in URL)
    name: str
    email: str
    company: str
    role: str                       # clinops | cfo | it_security | quality
    company_size: str               # community | regional | idn
    region: str                     # US region
    use_case: str
    urgency: str                    # low | medium | high
    consent: bool = True
    heard_via: str = ""
    segment: str = ""               # role__company_size micro-segment key
    created_at: str = ""

    @staticmethod
    def make_segment(role: str, company_size: str) -> str:
        return f"{role}__{company_size}"
