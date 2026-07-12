"""Super-personalization tests — the invariants that make the demo honest.

The headline guarantee mirrors the funnel's "creepiness invariant", one layer up: the
*tasteful* page may only ever state `say` facts, may only *steer* on `allude` facts, and
may never surface a `hold` fact at all — while the *creepy* page is exactly the same data
with the surface policy switched off, every line carrying its provenance. And the tiers are
monotonic: signing in / paying a broker only ever *adds* knowable facts.
"""
from __future__ import annotations

from pipeline.customer.schemas import SurfacePolicy
from pipeline.personalization import render
from pipeline.personalization import signals as S

ALL_TIERS = [t["id"] for t in S.TIERS]


# --- catalog integrity ------------------------------------------------------
def test_catalog_is_well_formed():
    seen = set()
    for s in S.CATALOG:
        assert s.id not in seen, f"duplicate signal id {s.id}"
        seen.add(s.id)
        assert s.source in S.SOURCE_META, f"{s.id}: unknown source {s.source}"
        assert s.tier in S.TIER_ORDER, f"{s.id}: unknown tier {s.tier}"
        assert 1 <= s.creepiness <= 5, f"{s.id}: creepiness out of range"
        assert isinstance(s.surface, SurfacePolicy)
        assert s.value and s.creepy and s.vendor and s.how, f"{s.id}: missing copy/provenance"


# --- tier monotonicity: higher tiers only ADD knowable facts ----------------
def test_tiers_are_monotonic():
    prev: set[str] = set()
    for t in ALL_TIERS:
        ids = {s.id for s in S.available_at(t)}
        assert prev <= ids, f"tier {t} dropped a previously-available fact"
        prev = ids
    assert {s.id for s in S.available_at("everything")} == {s.id for s in S.CATALOG}


# --- the Google jump is real (answers "how much more enrichment?") ----------
def test_google_login_unlocks_oauth_and_strictly_more():
    email_ids = {s.id for s in S.available_at("email")}
    google_ids = {s.id for s in S.available_at("google")}
    assert email_ids < google_ids                      # strictly more
    new = google_ids - email_ids
    assert new, "Google sign-in added nothing"
    assert all(S.CATALOG_BY_ID[i].source == S.OAUTH for i in new)   # …and it's all OAuth
    assert not any(s.source == S.OAUTH for s in S.available_at("email"))  # none before sign-in


# --- the headline guarantee: tasteful never surfaces a `hold` fact ----------
def test_tasteful_never_surfaces_a_hold_fact():
    for tier in ALL_TIERS:
        data = render.build(tier, "tasteful")
        text = " ".join(l["text"] for l in data["page"]["lines"])
        avail = S.available_at(tier)
        # no hold fact's value OR its creepy sentence may appear verbatim in the copy
        for s in avail:
            if s.surface == SurfacePolicy.HOLD:
                assert s.value not in text, f"{tier}: hold fact value leaked: {s.id}"
                assert s.creepy not in text, f"{tier}: hold creepy line leaked: {s.id}"
        # every signal a tasteful line references is say/allude — never hold
        for line in data["page"]["lines"]:
            for sid in line.get("from", []):
                assert S.CATALOG_BY_ID[sid].surface != SurfacePolicy.HOLD
        # lines marked 'say' may only cite `say` signals
        for line in data["page"]["lines"]:
            if line.get("policy") == "say":
                for sid in line.get("from", []):
                    assert S.CATALOG_BY_ID[sid].surface == SurfacePolicy.SAY


# --- creepy mode = the same data, policy off (surfaces everything available) -
def test_creepy_surfaces_every_available_fact_with_provenance():
    for tier in ALL_TIERS:
        data = render.build(tier, "creepy")
        shown = {ln["signal_id"] for blk in data["page"]["blocks"] for ln in blk["lines"]}
        assert shown == {s.id for s in S.available_at(tier)}        # nothing held back
        for blk in data["page"]["blocks"]:
            for ln in blk["lines"]:
                # every creepy line carries where-it-came-from
                assert ln["source_label"] and ln["vendor"] and ln["cost"]


# --- creepy ⊇ tasteful: creepy surfaces a superset of what tasteful states ---
def test_creepy_is_a_superset_of_tasteful():
    for tier in ALL_TIERS:
        t = render.build(tier, "tasteful")
        c = render.build(tier, "creepy")
        said = {sid for l in t["page"]["lines"] for sid in l.get("from", [])}
        shown = {ln["signal_id"] for blk in c["page"]["blocks"] for ln in blk["lines"]}
        assert said <= shown


# --- the ledger disposition is exactly the policy decision ------------------
def test_ledger_disposition_matches_policy():
    data = render.build("everything", "tasteful")
    by_id = {r["id"]: r for r in data["ledger"]}
    for s in S.CATALOG:                       # everything is available at the top tier
        want = {SurfacePolicy.SAY: "said", SurfacePolicy.ALLUDE: "steer",
                SurfacePolicy.HOLD: "withheld"}[s.surface]
        assert by_id[s.id]["disposition"] == want
    # creepy flips all-available to 'shown'
    creep = {r["id"]: r for r in render.build("everything", "creepy")["ledger"]}
    assert all(creep[s.id]["disposition"] == "shown" for s in S.CATALOG)
    # locked when the tier hasn't unlocked it
    anon = {r["id"]: r for r in render.build("anonymous", "tasteful")["ledger"]}
    assert anon["g_calendar"]["disposition"] == "locked"


# --- counts tell the story: withheld grows as knowledge grows ---------------
def test_withheld_count_grows_with_tier():
    withheld = [render.build(t, "tasteful")["counts"]["withheld"] for t in ALL_TIERS]
    assert withheld[-1] > withheld[0]                 # we know far more than we say
    assert render.build("everything", "tasteful")["counts"]["paid"] > 0   # broker/idgraph used


# --- determinism: same inputs → byte-identical render -----------------------
def test_render_is_deterministic():
    import json
    for tier in ("anonymous", "google", "everything"):
        for mode in ("tasteful", "creepy"):
            a = json.dumps(render.build(tier, mode), sort_keys=True, default=str)
            b = json.dumps(render.build(tier, mode), sort_keys=True, default=str)
            assert a == b


# --- bad input degrades to the safe default, never errors -------------------
def test_bad_input_falls_back():
    d = render.build("nonsense", "nonsense")
    assert d["tier"] == "anonymous" and d["mode"] == "tasteful"
