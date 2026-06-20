"""Cohort personalization — segments, archetypes, tier gating, and the landing build.

Sources are now the real stack: Vector (de-anon traffic) + HubSpot (forms/CRM) + Clay
(enrichment). `cohort.view()` normalizes them for the segment/landing engine.
"""
from __future__ import annotations

from pipeline.personalization import cohort, landing, segments

ARCHETYPES = set(segments.ARCHETYPES)


def _v(pid):
    return cohort.view(cohort.BY_ID[pid])


def test_cohort_has_records():
    assert len(cohort.COHORT) >= 10                      # 10 sample + the operator's test record
    assert cohort.match("johnny.c.chung@gmail.com")      # the operator can test the flow on himself


def test_email_match():
    assert cohort.match("maya.chen@gauntletai.com")["id"] == "maya"
    assert cohort.match("MAYA.CHEN@GAUNTLETAI.COM")["id"] == "maya"
    assert cohort.match("nobody@elsewhere.com") is None


def test_some_users_are_vector_only():
    """The de-anon showcase: visitors we identified with no form submitted."""
    vector_only = [p for p in cohort.COHORT if not p["hubspot"]["submitted"]]
    assert vector_only, "expected at least one Vector-only (no-form) visitor"
    for p in vector_only:
        assert p["vector"]["name"] and p["vector"]["job_title"]   # still fully identified


def test_every_user_gets_a_valid_archetype_and_eight_families():
    for p in cohort.COHORT:
        v = cohort.view(p)
        segs = segments.derive(v)
        assert set(segs) == {f[0] for f in segments.FAMILIES}
        assert segments.pick_archetype(v, segs)["id"] in ARCHETYPES


def test_all_six_archetypes_are_represented():
    got = {segments.pick_archetype(cohort.view(p), segments.derive(cohort.view(p)))["id"]
           for p in cohort.COHORT}
    assert got == ARCHETYPES, f"missing: {ARCHETYPES - got}"


def test_tier_one_is_say_only():
    for p in cohort.COHORT:
        for ln in landing.build_landing(cohort.view(p), tier=1)["personal_lines"]:
            assert ln["surface"] == "say"


def test_vector_firmographic_is_allude_not_say():
    """We de-anonymized it — never recite it as if they told us."""
    lines = landing.build_landing(_v("maya"), tier=2)["personal_lines"]
    vector_lines = [l for l in lines if "Vector" in l["from"]]
    assert vector_lines and all(l["surface"] != "say" for l in vector_lines)


def test_tier_four_reveals_deanon_and_is_monotonic():
    t1 = landing.build_landing(_v("allen"), 1)["personal_lines"]
    t4 = landing.build_landing(_v("allen"), 4)["personal_lines"]
    assert len(t4) > len(t1)
    assert any("de-anonymized" in l["text"] for l in t4)             # the reveal
    assert all(l["surface"] != "creepy" for l in t1)


def test_landing_has_hero_sections_email_and_explanation():
    d = landing.build_landing(_v("grace"), tier=2)
    assert d["hero"]["headline"] and d["sections"] and d["email_preview"]["subject"]
    srcs = {dp["source"] for dp in d["explanation"]["data_points"]}
    assert srcs == {"vector", "hubspot", "clay"}


def test_design_is_inferred_and_varies():
    designs = {p["id"]: landing.build_landing(cohort.view(p), 2)["design"] for p in cohort.COHORT}
    assert len({d["mode"] for d in designs.values()}) == 2
    assert len({d["voice"] for d in designs.values()}) >= 3
    assert len({d["accent"] for d in designs.values()}) >= 4


def test_landing_is_deterministic():
    assert landing.build_landing(_v("liam"), 3) == landing.build_landing(_v("liam"), 3)


def test_magic_link_round_trip():
    """A link from an email (opaque token) resolves to the same record as the email."""
    for p in cohort.COHORT:
        tok = cohort.magic_token(p)
        assert tok.startswith("mt_") and cohort.by_token(tok) is p
    assert cohort.by_token("mt_bogus") is None
