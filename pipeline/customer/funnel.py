"""The funnel — every way a customer enters and what happens at each touchpoint.

Each touchpoint function appends a TouchpointEvent to the customer's timeline and derives
facts, each gated by the surface policy. One customer object accumulates the whole journey;
identity is stitched as it goes (anonymous visitor → email → magic-link token). Two views
read the same record: rep_briefing (1:1) and mass_personalization (email/website).

Deterministic: event timestamps are a logical clock (event index), so a journey replays
byte-identical and the tests are seed-free.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from pipeline.common import observe
from pipeline.customer import surface
from pipeline.customer.schemas import (Customer, CustomerFact, Stage, SurfacePolicy,
                                       TouchpointEvent)

_BASE = datetime(2025, 1, 1, tzinfo=timezone.utc)


def _ts(c: Customer) -> str:
    return (_BASE + timedelta(seconds=len(c.events))).isoformat()


def _topic(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["job", "placement", "career", "hire", "salary", "employ"]):
        return "interest:career_outcomes"
    if any(w in t for w in ["cost", "price", "pay", "afford", "scholarship", "financ", "tuition"]):
        return "concern:affordability"
    if any(w in t for w in ["time", "schedule", "night", "weekend", "full-time", "full time"]):
        return "concern:schedule"
    if any(w in t for w in ["prereq", "experience", "beginner", "background", "ready", "qualif"]):
        return "concern:readiness"
    return "interest:general"


def _fact(c: Customer, key, value, source, sensitive=False, basis="", channel="") -> CustomerFact:
    sp, reasons = surface.decide(key, source, c.consent, sensitive)
    return CustomerFact(
        fact_id=CustomerFact.make_id(c.customer_id, key, source), key=key, value=str(value),
        source=source, channel_in=channel, basis=basis or "first_party", observed_at=_ts(c),
        sensitive=sensitive, surface_policy=sp, reasons=reasons)


def _event(c: Customer, source, stage, detail, payload=None, facts=()):
    for f in facts:
        c.upsert_fact(f)
    ev = TouchpointEvent(event_id=f"e{len(c.events) + 1}", ts=_ts(c), stage=stage, source=source,
                         detail=detail, payload=payload or {}, fact_keys=[f.key for f in facts])
    c.events.append(ev)
    if stage:
        c.stage = stage
    observe.emit("funnel", "OUTPUT", node=source, detail=f"{c.customer_id}: {detail}",
                 output={"stage": stage.value, "facts": [f.key for f in facts]})
    return ev


def repolicy(c: Customer) -> None:
    """Re-evaluate every fact's surface policy with the current consent (e.g. after signup
    unlocks prior anonymous behavioral data)."""
    for f in c.facts:
        sp, reasons = surface.decide(f.key, f.source, c.consent, f.sensitive)
        f.surface_policy, f.reasons = sp, reasons


# --------------------------------------------------------------------------- #
# touchpoints
# --------------------------------------------------------------------------- #
def new_visitor(visitor_id: str) -> Customer:
    cid = "c_" + hashlib.sha256(visitor_id.encode()).hexdigest()[:10]
    return Customer(customer_id=cid, visitor_id=visitor_id, stage=Stage.ANONYMOUS,
                    created_at=_BASE.isoformat())


def ad_click(c: Customer, campaign: str, creative: str = "") -> Customer:
    f = _fact(c, _topic(campaign), campaign, "ad", channel="ad")
    _event(c, "ad", Stage.ANONYMOUS, f"clicked ad '{campaign}'",
           {"campaign": campaign, "creative": creative}, [f])
    return c


def web_signup(c: Customer, name: str, email: str, goal: str = "", background: str = "",
               consent: bool = True) -> Customer:
    c.name, c.email, c.consent = name, email, consent
    facts = []
    if goal:
        facts.append(_fact(c, "goal", goal, "web_form", channel="website"))
    if background:
        facts.append(_fact(c, "background", background, "web_form", channel="website"))
    _event(c, "web_form", Stage.LEAD, f"signed up for more info ({email})",
           {"name": name, "email": email, "consent": consent}, facts)
    repolicy(c)   # consent now unlocks prior anonymous facts
    return c


def email_event(c: Customer, kind: str, email_id: str, link: str = "") -> Customer:
    f = _fact(c, f"engagement:email_{kind}", email_id, "email", channel="email")
    _event(c, "email", Stage.ENGAGED, f"email {kind}: {email_id}",
           {"email_id": email_id, "link": link}, [f])
    return c


def web_return(c: Customer, viewed_class: str = "") -> Customer:
    facts = []
    if viewed_class:
        facts.append(_fact(c, "interest:class_viewed", viewed_class, "web_return", channel="website"))
    _event(c, "web_return", Stage.ENGAGED, f"returned to site (viewed {viewed_class or 'site'})",
           {"viewed_class": viewed_class}, facts)
    return c


def class_signup(c: Customer, class_name: str) -> str:
    """Sign up for a (night) class. Issues the magic-link token — the login — and ties it to
    this customer. Returns the token."""
    if not c.magic_token:
        c.magic_token = hashlib.sha256(f"{c.customer_id}|magic".encode()).hexdigest()[:16]
    f = _fact(c, "intent:class", class_name, "class_signup", channel="website")
    _event(c, "class_signup", Stage.REGISTRANT, f"registered for '{class_name}'",
           {"class": class_name, "magic_token": c.magic_token}, [f])
    return c.magic_token


def class_attend(c: Customer, class_name: str, attended: bool = True, minutes: int = 0) -> Customer:
    f = _fact(c, "engagement:attended", f"{class_name}:{minutes}min", "web_return")
    _event(c, "class_attend", Stage.ATTENDEE,
           f"{'attended' if attended else 'no-show'} '{class_name}' ({minutes}min)",
           {"class": class_name, "attended": attended, "minutes": minutes}, [f] if attended else [])
    return c


def class_question(c: Customer, text: str, modality: str = "text") -> Customer:
    """A question asked live in class. Text = the customer stated it (say); voice = more
    sensitive capture (allude). The question content is the signal."""
    source = "class_question_voice" if modality == "voice" else "class_question_text"
    key = _topic(text)
    f = _fact(c, key, text, source, channel=f"class_{modality}")
    _event(c, "class_question", c.stage if c.stage == Stage.ATTENDEE else Stage.ATTENDEE,
           f"asked ({modality}): {text[:60]}", {"modality": modality, "text": text}, [f])
    return c


def admissions_note(c: Customer, note: str, topic: str, officer: str = "Drew Rice",
                    sensitive: bool = False) -> Customer:
    """A 1:1 note from the admissions officer. A rep's own observation → `allude` (don't
    quote your notes back); flag personal/sensitive content as `hold`."""
    f = _fact(c, topic, note, "rep_note", sensitive=sensitive, channel="admissions")
    _event(c, "admissions", Stage.RELATIONSHIP, f"{officer}: {note[:60]}",
           {"officer": officer, "note": note, "topic": topic}, [f])
    return c


# --------------------------------------------------------------------------- #
# the two views over the one record
# --------------------------------------------------------------------------- #
def rep_briefing(c: Customer) -> dict:
    """The 1:1 view (e.g. admissions officer Drew Rice): what to say, what to only allude to
    via an adjacent topic, and what to hold."""
    return {
        "customer": {"id": c.customer_id, "name": c.name, "email": c.email, "stage": c.stage.value},
        "say": [{"key": f.key, "value": f.value, "source": f.source} for f in c.by_policy(SurfacePolicy.SAY)],
        "allude": [{"key": f.key, "value": f.value, "source": f.source, "opener": surface.opener(f)}
                   for f in c.by_policy(SurfacePolicy.ALLUDE)],
        "hold": [{"key": f.key, "source": f.source, "why": (f.reasons[0] if f.reasons else "")}
                 for f in c.by_policy(SurfacePolicy.HOLD)],
        "timeline": [{"ts": e.ts, "stage": e.stage.value, "source": e.source, "detail": e.detail}
                     for e in c.events],
    }


def mass_personalization(c: Customer) -> dict:
    """The automated view (mass email + personalized website): only `say` facts may be
    inlined verbatim; `allude` facts may silently steer selection; `hold` is withheld."""
    return {
        "inlineable": [{"key": f.key, "value": f.value, "source": f.source}
                       for f in c.facts if f.mass_inlineable],
        "selection_signals": [f.key for f in c.facts
                              if f.selection_ok and f.surface_policy == SurfacePolicy.ALLUDE],
        "withheld": [f.key for f in c.facts if f.surface_policy == SurfacePolicy.HOLD],
    }
