"""Customer-record schemas — identity, a timeline of touchpoint events, and facts.

A CustomerFact mirrors the enrichment ProfileFact (value bound to a source + a lawful basis
+ when it was observed) and adds the dimension this funnel needs: a **surface policy**.

  surface policy   1:1 rep may…                         mass copy / website
  -------------     ----------------------------------   -------------------------------
  say              reference it directly                 may be inlined (with its receipt)
  allude           NOT state it; raise an adjacent topic never literal; may steer selection
  hold             never surface or allude               never used

`mass_inlineable` and `selection_ok` are derived from the surface policy so the two views
read from one source of truth.
"""
from __future__ import annotations

import hashlib
from enum import Enum

from pydantic import BaseModel, Field


class SurfacePolicy(str, Enum):
    SAY = "say"
    ALLUDE = "allude"
    HOLD = "hold"


class Stage(str, Enum):
    ANONYMOUS = "anonymous"     # ad click / anonymous visit — no identity yet
    LEAD = "lead"               # filled a form — identified
    ENGAGED = "engaged"         # opened/clicked/returned
    REGISTRANT = "registrant"   # signed up for a class — has a login
    ATTENDEE = "attendee"       # attended a class
    RELATIONSHIP = "relationship"  # 1:1 admissions conversation
    ENROLLED = "enrolled"


class CustomerFact(BaseModel):
    fact_id: str = ""
    key: str                    # e.g. interest:career_outcomes, concern:affordability, goal
    value: str
    source: str                 # touchpoint/connector id (web_form, class_question, voice, rep_note, ad…)
    channel_in: str = ""        # where it was observed
    basis: str = ""             # recorded lawful basis
    observed_at: str = ""
    confidence: float = 0.8
    sensitive: bool = False
    surface_policy: SurfacePolicy = SurfacePolicy.HOLD
    reasons: list[str] = Field(default_factory=list)

    @staticmethod
    def make_id(customer_id: str, key: str, source: str) -> str:
        return "cf_" + hashlib.sha256(f"{customer_id}|{key}|{source}".encode()).hexdigest()[:10]

    @property
    def mass_inlineable(self) -> bool:
        """Only facts the customer stated to us directly may be put in mass copy verbatim."""
        return self.surface_policy == SurfacePolicy.SAY

    @property
    def selection_ok(self) -> bool:
        """`allude`/`say` may silently steer which class/claim we feature; `hold` may not."""
        return self.surface_policy != SurfacePolicy.HOLD


class TouchpointEvent(BaseModel):
    event_id: str = ""
    ts: str = ""
    stage: Stage = Stage.ANONYMOUS
    source: str = ""            # ad · web_form · email · web_return · class_signup · class_attend
                                # · class_question · admissions
    detail: str = ""
    payload: dict = Field(default_factory=dict)
    fact_keys: list[str] = Field(default_factory=list)


class Customer(BaseModel):
    customer_id: str
    visitor_id: str = ""        # anonymous cookie id (top of funnel)
    email: str = ""
    name: str = ""
    magic_token: str = ""       # the class login — same opaque token as the website channel
    consent: bool = False
    stage: Stage = Stage.ANONYMOUS
    created_at: str = ""
    events: list[TouchpointEvent] = Field(default_factory=list)
    facts: list[CustomerFact] = Field(default_factory=list)

    def upsert_fact(self, fact: CustomerFact) -> None:
        for i, f in enumerate(self.facts):
            if f.key == fact.key and f.source == fact.source:
                self.facts[i] = fact
                return
        self.facts.append(fact)

    def by_policy(self, policy: SurfacePolicy) -> list[CustomerFact]:
        return [f for f in self.facts if f.surface_policy == policy]
