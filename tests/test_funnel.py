"""The funnel test suite — every way a customer enters, and what happens, made runnable.

Each test walks a path through the funnel and asserts the invariants that make the customer
record safe to use: identity stitches, every fact carries the right surface policy, and the
"creepiness" guarantee holds — no `hold` fact ever reaches mass copy or gets surfaced as
something a rep may say.
"""
from __future__ import annotations

import pytest

from pipeline.customer import funnel
from pipeline.customer.schemas import Stage, SurfacePolicy
from pipeline.customer.store import CustomerStore


def _fact(c, key):
    return next((f for f in c.facts if f.key == key), None)


def _full_journey(consent: bool = True):
    """A → G: ad → signup → email → return → class signup → attend → questions → admissions."""
    c = funnel.new_visitor("vis_001")
    funnel.ad_click(c, "Intro to AI Engineering")
    funnel.web_signup(c, "Sam Lee", "sam@personal.example",
                      goal="switch into AI engineering", background="2 yrs backend",
                      consent=consent)
    funnel.email_event(c, "open", "nurture_1")
    funnel.email_event(c, "click", "nurture_1", link="/classes")
    funnel.web_return(c, viewed_class="intro_night")
    token = funnel.class_signup(c, "Intro to AI Engineering — night cohort")
    funnel.class_attend(c, "Intro to AI Engineering — night cohort", attended=True, minutes=85)
    funnel.class_question(c, "Do you help with job placement after the program?", "text")
    funnel.class_question(c, "How much does it cost and are there scholarships?", "voice")
    funnel.admissions_note(c, "Seems anxious about leaving a stable job", "concern:schedule")
    return c, token


# --- Path A: ad → web signup (identity + consent unlock) -------------------
def test_path_ad_to_signup():
    c = funnel.new_visitor("vis_A")
    funnel.ad_click(c, "Weekend Build Intensive")
    assert c.stage == Stage.ANONYMOUS
    ad = next(f for f in c.facts if f.source == "ad")
    assert ad.surface_policy == SurfacePolicy.HOLD                       # no consent yet
    funnel.web_signup(c, "Pat", "pat@x.example", goal="build a startup", consent=True)
    assert c.stage == Stage.LEAD and c.email == "pat@x.example"
    assert _fact(c, "goal").surface_policy == SurfacePolicy.SAY          # they told us
    ad = next(f for f in c.facts if f.source == "ad")
    assert ad.surface_policy == SurfacePolicy.ALLUDE                     # consent unlocked behavioral


# --- Path B: email → return → class signup issues the login ----------------
def test_path_class_signup_issues_magic_link():
    c, token = _full_journey()
    assert token and c.magic_token == token        # the class login is the magic-link token
    assert _fact(c, "intent:class").surface_policy == SurfacePolicy.SAY
    assert c.stage in (Stage.ATTENDEE, Stage.RELATIONSHIP)


# --- Path C: in-class questions — text vs voice ----------------------------
def test_text_question_is_say_voice_is_allude():
    c, _ = _full_journey()
    text_q = _fact(c, "interest:career_outcomes")     # the job-placement text question
    voice_q = _fact(c, "concern:affordability")       # the cost question asked by voice
    assert text_q.surface_policy == SurfacePolicy.SAY
    assert voice_q.surface_policy == SurfacePolicy.ALLUDE


# --- Path D: admissions note + sensitivity ---------------------------------
def test_admissions_note_allude_and_sensitive_hold():
    c, _ = _full_journey()
    assert _fact(c, "concern:schedule").surface_policy == SurfacePolicy.ALLUDE  # rep note
    funnel.admissions_note(c, "Mentioned a custody situation", "family")        # sensitive key
    assert _fact(c, "family").surface_policy == SurfacePolicy.HOLD


# --- The creepiness invariant (the headline guarantee) ---------------------
def test_creepiness_invariant():
    c, _ = _full_journey()
    funnel.admissions_note(c, "Going through a divorce", "family")  # sensitive → hold
    mass = funnel.mass_personalization(c)
    rep = funnel.rep_briefing(c)

    # 1) nothing in mass copy except facts the customer stated directly (say)
    say_keys = {f.key for f in c.facts if f.surface_policy == SurfacePolicy.SAY}
    assert {f["key"] for f in mass["inlineable"]} <= say_keys
    # 2) no hold fact anywhere it could be surfaced
    hold_keys = {f.key for f in c.facts if f.surface_policy == SurfacePolicy.HOLD}
    assert not ({f["key"] for f in mass["inlineable"]} & hold_keys)
    assert not (set(mass["selection_signals"]) & hold_keys)
    assert not ({f["key"] for f in rep["say"]} & hold_keys)
    assert not ({f["key"] for f in rep["allude"]} & hold_keys)
    # 3) the sensitive fact is held, never alluded to
    assert "family" in {h["key"] for h in rep["hold"]}
    # 4) behavioral facts (ad/email) are allude — never recited as "say"
    assert _fact(c, "engagement:email_open").surface_policy == SurfacePolicy.ALLUDE


def test_allude_facts_carry_an_adjacent_opener():
    c, _ = _full_journey()
    rep = funnel.rep_briefing(c)
    assert rep["allude"], "expected some allude facts"
    for a in rep["allude"]:
        assert a["opener"] and "?" in a["opener"]   # an actual adjacent-topic question


def test_no_consent_holds_everything():
    c, _ = _full_journey(consent=False)
    assert all(f.surface_policy == SurfacePolicy.HOLD for f in c.facts)
    assert funnel.mass_personalization(c)["inlineable"] == []


# --- Identity resolution across sessions (store) ---------------------------
def test_identity_resolution(tmp_path):
    store = CustomerStore(path=tmp_path / "cust.sqlite")
    c, token = _full_journey()
    store.save(c)
    assert store.resolve(visitor_id="vis_001") == c.customer_id
    assert store.resolve(email="sam@personal.example") == c.customer_id
    assert store.resolve(magic_token=token) == c.customer_id
    assert len(store.facts_for(c.customer_id)) == len(c.facts)


# --- Determinism: a journey replays byte-identical -------------------------
def test_journey_is_deterministic():
    a, _ = _full_journey()
    b, _ = _full_journey()
    assert a.model_dump_json() == b.model_dump_json()
