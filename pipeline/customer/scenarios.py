"""Funnel scenarios — the data behind the funnel dashboard.

Builds representative customer journeys with the funnel touchpoints, runs the same
invariants the test suite asserts (so the dashboard shows live pass/fail that can go red),
and assembles: the funnel paths, one fully-walked journey (timeline + facts + both views),
and the surface-policy legend. Also persists the walked journey so customers.sqlite is real.
"""
from __future__ import annotations

from pipeline.customer import funnel
from pipeline.customer.schemas import SurfacePolicy
from pipeline.customer.store import CustomerStore

LEGEND = [
    {"policy": "say", "label": "Say",
     "plain": "The customer stated this to us directly — a rep may reference it, and it may appear in mass copy.",
     "engine": "source ∈ {web_form, class_signup, class_question_text}; consent on file."},
    {"policy": "allude", "label": "Allude",
     "plain": "Behavioral / inferred / voice / a rep's own note — a rep may only raise an adjacent topic; never stated, but it can steer which class we feature.",
     "engine": "source ∈ {ad, email, web_return, class_question_voice, rep_note, external}."},
    {"policy": "hold", "label": "Hold",
     "plain": "Sensitive or non-consented — known internally, never surfaced, alluded to, or used anywhere.",
     "engine": "key ∈ sensitive_keys, or consent absent → hold (overrides source)."},
]


def _sp(c, key):
    f = next((x for x in c.facts if x.key == key), None)
    return f.surface_policy if f else None


def _path(name, entry, steps, captures, checks):
    return {"name": name, "entry": entry, "steps": steps, "captures": captures,
            "checks": checks, "pass": all(ck["pass"] for ck in checks)}


def paths() -> list[dict]:
    out = []

    # A — ad → signup (consent unlock)
    c = funnel.new_visitor("vis_pa")
    funnel.ad_click(c, "Weekend Build Intensive")
    before_hold = _sp(c, "concern:schedule") == SurfacePolicy.HOLD
    funnel.web_signup(c, "Pat", "pat@x.example", goal="build a startup", consent=True)
    out.append(_path(
        "Ad → website → sign up for more info", "Click-through ad",
        ["clicked ad (anonymous visitor)", "filled the 'more info' form + consent"],
        ["interest (behavioral → hold until consent, then allude)", "goal (declared → say)"],
        [{"name": "behavioral fact starts hold, unlocks to allude on consent",
          "pass": before_hold and _sp(c, "concern:schedule") == SurfacePolicy.ALLUDE},
         {"name": "declared goal is say", "pass": _sp(c, "goal") == SurfacePolicy.SAY}]))

    # B — email → return → class signup issues the login
    c = funnel.new_visitor("vis_pb")
    funnel.web_signup(c, "Sam", "sam@x.example", consent=True)
    funnel.email_event(c, "click", "nurture_1", link="/classes")
    funnel.web_return(c, viewed_class="intro_night")
    token = funnel.class_signup(c, "Intro to AI Engineering — night cohort")
    out.append(_path(
        "Email → click → return → sign up for a class", "Nurture email",
        ["clicked the email", "returned to the site", "registered for the night class"],
        ["email engagement (allude)", "intent:class (declared → say)", "magic-link login issued"],
        [{"name": "class signup issues the magic-link login (one identity)", "pass": bool(token) and c.magic_token == token},
         {"name": "class intent is say", "pass": _sp(c, "intent:class") == SurfacePolicy.SAY}]))

    # C — in-class questions: text vs voice
    c = funnel.new_visitor("vis_pc")
    funnel.web_signup(c, "Sam", "sam@x.example", consent=True)
    funnel.class_signup(c, "Intro to AI Engineering — night cohort")
    funnel.class_attend(c, "Intro to AI Engineering — night cohort", minutes=85)
    funnel.class_question(c, "Do you help with job placement?", "text")
    funnel.class_question(c, "How much does it cost — any scholarships?", "voice")
    out.append(_path(
        "Attend the night class → ask questions (text & voice)", "Night class",
        ["attended the live class", "asked a question by text", "asked a question by voice"],
        ["career-outcomes interest (text → say)", "affordability concern (voice → allude)"],
        [{"name": "text question is say (on the record)", "pass": _sp(c, "interest:career_outcomes") == SurfacePolicy.SAY},
         {"name": "voice question is allude (sensitive capture)", "pass": _sp(c, "concern:affordability") == SurfacePolicy.ALLUDE}]))

    # D — admissions note + sensitivity
    c = funnel.new_visitor("vis_pd")
    funnel.web_signup(c, "Sam", "sam@x.example", consent=True)
    funnel.admissions_note(c, "Anxious about leaving a stable job", "concern:schedule")
    funnel.admissions_note(c, "Going through a divorce", "family")
    out.append(_path(
        "1:1 admissions emails with Drew Rice", "Admissions officer",
        ["Drew logs an observation", "Drew logs a sensitive personal detail"],
        ["rep note (allude — don't quote it back)", "family detail (sensitive → hold)"],
        [{"name": "rep note is allude", "pass": _sp(c, "concern:schedule") == SurfacePolicy.ALLUDE},
         {"name": "sensitive detail is held, never surfaced", "pass": _sp(c, "family") == SurfacePolicy.HOLD}]))

    # E — no consent holds everything
    c = funnel.new_visitor("vis_pe")
    funnel.ad_click(c, "Intro to AI Engineering")
    funnel.web_signup(c, "Nó", "no@x.example", goal="explore", consent=False)
    out.append(_path(
        "Signs up WITHOUT consent", "Website (no consent)",
        ["clicked ad", "submitted form but declined consent"],
        ["everything captured but held"],
        [{"name": "no consent → every fact is hold", "pass": all(f.surface_policy == SurfacePolicy.HOLD for f in c.facts)},
         {"name": "nothing is inlineable in mass copy", "pass": funnel.mass_personalization(c)["inlineable"] == []}]))

    return out


def walked_journey(persist: bool = True) -> dict:
    """One customer end-to-end (A→G), with the timeline + facts + both views + the invariant."""
    c = funnel.new_visitor("vis_demo")
    funnel.ad_click(c, "Intro to AI Engineering")
    funnel.web_signup(c, "Sam Lee", "sam@personal.example",
                      goal="switch into AI engineering", background="2 yrs backend", consent=True)
    funnel.email_event(c, "open", "nurture_1")
    funnel.email_event(c, "click", "nurture_1", link="/classes")
    funnel.web_return(c, viewed_class="intro_night")
    funnel.class_signup(c, "Intro to AI Engineering — night cohort")
    funnel.class_attend(c, "Intro to AI Engineering — night cohort", minutes=85)
    funnel.class_question(c, "Do you help with job placement after the program?", "text")
    funnel.class_question(c, "How much does it cost and are there scholarships?", "voice")
    funnel.admissions_note(c, "Seems anxious about leaving a stable job", "concern:schedule")
    funnel.admissions_note(c, "Going through a divorce", "family")

    if persist:
        CustomerStore().save(c)

    by_key = {f.key: f for f in c.facts}
    timeline = [{
        "ts": e.ts, "stage": e.stage.value, "source": e.source, "detail": e.detail,
        "facts": [{"key": k, "value": by_key[k].value, "source": by_key[k].source,
                   "surface_policy": by_key[k].surface_policy.value}
                  for k in e.fact_keys if k in by_key],
    } for e in c.events]

    rep = funnel.rep_briefing(c)
    mass = funnel.mass_personalization(c)

    hold_keys = {f.key for f in c.facts if f.surface_policy == SurfacePolicy.HOLD}
    say_keys = {f.key for f in c.facts if f.surface_policy == SurfacePolicy.SAY}
    invariant = {
        "name": "No held/sensitive fact ever reaches mass copy or a rep's “say”; behavioral is allude-only.",
        "pass": (not ({f["key"] for f in mass["inlineable"]} & hold_keys)
                 and {f["key"] for f in mass["inlineable"]} <= say_keys
                 and not (set(mass["selection_signals"]) & hold_keys)
                 and not ({f["key"] for f in rep["say"]} & hold_keys)),
    }
    return {"customer": {"name": c.name, "email": c.email, "stage": c.stage.value,
                         "magic_token": c.magic_token},
            "timeline": timeline, "rep_view": rep, "mass_view": mass, "invariant": invariant}


def report() -> dict:
    ps = paths()
    return {
        "paths": ps,
        "summary": {"passed": sum(1 for p in ps if p["pass"]), "total": len(ps)},
        "journey": walked_journey(),
        "legend": LEGEND,
        "store": CustomerStore().summary(),
    }
