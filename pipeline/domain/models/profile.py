"""Canonical Profile aggregate — namespaced under one profile_id."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from pipeline.customer.schemas import Customer, CustomerFact, Stage, SurfacePolicy, TouchpointEvent
from pipeline.enrichment.schemas import Profile as EnrichProfile
from pipeline.enrichment.schemas import ProfileFact


class ProfileClass(str, Enum):
    ANONYMOUS = "anonymous"
    LEAD = "lead"
    RECIPIENT = "recipient"
    CUSTOMER = "customer"
    ACCOUNT = "account"


class IdentitySlice(BaseModel):
    visitor_id: str = ""
    email: str = ""
    name: str = ""
    magic_token: str = ""
    recipient_id: str = ""
    consent: bool = False
    stage: str = "anonymous"


class Profile(BaseModel):
    profile_id: str
    profile_class: ProfileClass = ProfileClass.ANONYMOUS
    identity: IdentitySlice = Field(default_factory=IdentitySlice)
    funnel_facts: list[CustomerFact] = Field(default_factory=list)
    enrichment_facts: list[ProfileFact] = Field(default_factory=list)
    events: list[TouchpointEvent] = Field(default_factory=list)
    segment: str = ""
    signals: dict = Field(default_factory=dict)
    active_claim_refs: list[str] = Field(default_factory=list)
    segment_refs: list[str] = Field(default_factory=list)
    copy_safe_claim_refs: list[str] = Field(default_factory=list)
    routing_only_claim_refs: list[str] = Field(default_factory=list)
    last_reconciled_at: str = ""
    created_at: str = ""
    synthesized_seq: int = 0

    def reconcile_refs(self) -> None:
        self.copy_safe_claim_refs = [f.fact_id or f.key for f in self.funnel_facts
                                     if f.surface_policy == SurfacePolicy.SAY]
        self.routing_only_claim_refs = [f.fact_id or f.key for f in self.funnel_facts
                                        if f.surface_policy == SurfacePolicy.ALLUDE]
        self.segment_refs = sorted(set(
            [self.identity.stage] + ([self.segment] if self.segment else [])
        ))
        self.active_claim_refs = sorted(set(self.copy_safe_claim_refs + self.active_claim_refs))
        self.last_reconciled_at = datetime.now(timezone.utc).isoformat()

    def upsert_funnel_fact(self, fact: CustomerFact) -> None:
        for i, f in enumerate(self.funnel_facts):
            if f.key == fact.key and f.source == fact.source:
                self.funnel_facts[i] = fact
                return
        self.funnel_facts.append(fact)

    def by_policy(self, policy: SurfacePolicy) -> list[CustomerFact]:
        return [f for f in self.funnel_facts if f.surface_policy == policy]

    @property
    def usable_enrichment_facts(self) -> list[ProfileFact]:
        return [f for f in self.enrichment_facts if f.inlinable]

    @classmethod
    def from_customer(cls, customer: Customer) -> Profile:
        stage_map = {
            Stage.ANONYMOUS: ProfileClass.ANONYMOUS,
            Stage.LEAD: ProfileClass.LEAD,
            Stage.ENGAGED: ProfileClass.LEAD,
            Stage.REGISTRANT: ProfileClass.CUSTOMER,
            Stage.ATTENDEE: ProfileClass.CUSTOMER,
            Stage.RELATIONSHIP: ProfileClass.CUSTOMER,
            Stage.ENROLLED: ProfileClass.CUSTOMER,
        }
        p = cls(
            profile_id=customer.customer_id,
            profile_class=stage_map.get(customer.stage, ProfileClass.CUSTOMER),
            identity=IdentitySlice(
                visitor_id=customer.visitor_id,
                email=customer.email,
                name=customer.name,
                magic_token=customer.magic_token,
                consent=customer.consent,
                stage=customer.stage.value,
            ),
            funnel_facts=list(customer.facts),
            events=list(customer.events),
            created_at=customer.created_at,
        )
        p.reconcile_refs()
        return p

    def to_customer(self) -> Customer:
        """Backward-compatible view for funnel code during migration."""
        return Customer(
            customer_id=self.profile_id,
            visitor_id=self.identity.visitor_id,
            email=self.identity.email,
            name=self.identity.name,
            magic_token=self.identity.magic_token,
            consent=self.identity.consent,
            stage=Stage(self.identity.stage) if self.identity.stage in Stage._value2member_map_ else Stage.ANONYMOUS,
            created_at=self.created_at,
            events=list(self.events),
            facts=list(self.funnel_facts),
        )

    @classmethod
    def from_enrichment(cls, enrich: EnrichProfile, profile_id: str | None = None) -> Profile:
        pid = profile_id or enrich.recipient_id
        p = cls(
            profile_id=pid,
            profile_class=ProfileClass.RECIPIENT,
            identity=IdentitySlice(recipient_id=enrich.recipient_id),
            enrichment_facts=list(enrich.facts),
            segment=enrich.segment,
            signals=dict(enrich.signals),
            synthesized_seq=enrich.synthesized_seq,
        )
        p.reconcile_refs()
        return p

    def merge_enrichment(self, enrich: EnrichProfile) -> None:
        self.enrichment_facts = list(enrich.facts)
        self.segment = enrich.segment or self.segment
        self.signals = dict(enrich.signals)
        self.synthesized_seq = enrich.synthesized_seq
        if enrich.recipient_id:
            self.identity.recipient_id = enrich.recipient_id
        self.reconcile_refs()

    def to_enrichment_profile(self) -> EnrichProfile:
        return EnrichProfile(
            recipient_id=self.identity.recipient_id or self.profile_id,
            segment=self.segment,
            facts=list(self.enrichment_facts),
            signals=dict(self.signals),
            synthesized_seq=self.synthesized_seq,
        )
