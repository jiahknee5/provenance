"""The Google-login demo's honesty guards.

The whole point is that a Google login does NOT return "everything Google knows" — so the
tiers must classify data truthfully: the basic profile tier must not claim age/income/
location, and the sensitive "ultra" facts must live in the not-from-Google / bought tiers.
"""
from __future__ import annotations

from pipeline.personalization import google as G


def test_four_tiers():
    o = G.overview()
    assert [t["id"] for t in o["tiers"]] == ["granted", "extra_scope", "not_api", "bought"]
    assert o["total"] == sum(o["counts"].values())


def test_granted_tier_does_not_overclaim():
    """A plain Google login returns profile/email only — never age/income/location/home."""
    import re
    words = set(re.findall(r"[a-z]+", " ".join(
        i["label"].lower() for i in G.overview()["items_by_tier"]["granted"])))
    assert not (words & {"income", "age", "home", "location", "vehicle", "salary"})


def test_ultra_personal_lives_in_not_from_login_tiers():
    o = G.overview()
    bought = " ".join(i["label"].lower() for i in o["items_by_tier"]["bought"])
    assert "income" in bought and "age" in bought          # the payoff is the bought tier
    assert o["not_login"] >= 8                             # most personal facts are NOT from the login


def test_extra_scope_items_carry_a_scope():
    for it in G.overview()["items_by_tier"]["extra_scope"]:
        assert it["scope"], f"{it['label']} should name the OAuth scope it needs"
