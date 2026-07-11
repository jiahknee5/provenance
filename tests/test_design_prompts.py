"""Design prompt database — loader and resolve_example tests."""
from __future__ import annotations

import pytest

from pipeline.personalization import design_prompts as DP

KNOWN_IMAGE_IDS = [
    "gauntlet.hero.peer_proof.direct",
    "gauntlet.hero.message_match.ad",
    "gauntlet.hero.authority.direct",
    "gauntlet.hero.aspiration.ad",
    "gauntlet.og.message_match.ad",
    "planet.hero.regional_truth.tier0",
    "planet.hero.regional_truth.region",
    "planet.hero.change_proof.tier0",
    "planet.hero.change_proof.region",
]

SAMPLE_RESOLVED_IDS = [
    "gauntlet.hero.peer_proof.direct",
    "gauntlet.hero.message_match.ad",
    "planet.hero.regional_truth.tier0",
    "gauntlet.og.message_match.ad",
]


def test_db_loads():
    db = DP.load_db(reload=True)
    assert db["version"] == 1
    assert "entries" in db
    assert len(db["entries"]) >= 11
    assert "gauntlet" in db.get("tenants", {})
    assert "planet" in db.get("tenants", {})


def test_known_entry_ids_exist():
    for entry_id in KNOWN_IMAGE_IDS:
        entry = DP.get_entry(entry_id)
        assert entry is not None, entry_id
        assert entry["id"] == entry_id
        assert entry.get("kind", "image") == "image"


def test_example_resolved_non_empty_for_samples():
    for entry_id in SAMPLE_RESOLVED_IDS:
        entry = DP.get_entry(entry_id)
        assert entry is not None
        resolved = (entry.get("example_resolved") or "").strip()
        assert len(resolved) > 80, entry_id


def test_list_entries_filters_tenant():
    gauntlet = DP.list_entries(tenant="gauntlet", kind="image")
    planet = DP.list_entries(tenant="planet", kind="image")
    assert all(e["tenant"] == "gauntlet" for e in gauntlet)
    assert all(e["tenant"] == "planet" for e in planet)
    assert len(gauntlet) >= 6
    assert len(planet) >= 4


def test_list_entries_filters_surface_and_channel():
    og = DP.list_entries(tenant="gauntlet", surface="og")
    assert og and all(e["surface"] == "og" for e in og)

    ad = DP.list_entries(tenant="gauntlet", channel="ad", kind="image")
    assert ad and all(e["channel"] in ("ad", "any") for e in ad)


def test_resolve_example_matches_pipeline():
    entry_id = "gauntlet.hero.peer_proof.direct"
    entry = DP.get_entry(entry_id)
    live = DP.resolve_example(entry_id)
    assert "peer_proof" in live
    assert "Trust" in live
    stored = (entry or {}).get("example_resolved") or ""
    assert stored.split("Drives action")[0] in live or live.split("Drives action")[0] in stored


def test_resolve_example_with_context_override():
    prompt = DP.resolve_example(
        "planet.hero.regional_truth.region",
        {"tier": 0, "region": None},
    )
    assert "regional_truth" in prompt
    assert "region_mood" not in prompt


def test_copy_slot_raises_on_resolve():
    with pytest.raises(ValueError, match="copy slot"):
        DP.resolve_example("gauntlet.copy.hero.headline")


def test_placeholders_documented():
    ph = DP.placeholders()
    assert "environment" in ph
    assert "ad_metaphor" in ph


def test_intent_index():
    intents = DP.intent_index(tenant="gauntlet", surface="hero")
    assert "peer_proof" in intents
    assert "message_match" in intents
