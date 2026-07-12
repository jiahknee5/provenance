"""Tests for the /demo surface — provenance completeness, the no-hold-in-copy invariant,
bandit convergence (and the un-pullable creepy arm), monitor shape, and the cloner's
inject/fallback (offline, via monkeypatched fetch)."""
from __future__ import annotations

from pipeline.personalization import cloner
from pipeline.personalization import demo_scenarios as DS
from pipeline.personalization import demo_sim


# --- provenance is never lost -------------------------------------------------
def test_every_gated_variant_carries_its_data():
    for s in DS.SCENARIOS:
        gated = DS.gated_variants(s)
        assert len(gated) == 3, f"scenario {s.id} should have 3 gated variants"
        for v in gated:
            assert v.data_used, f"{v.id} has no data_used — provenance lost"
            for d in v.data_used:
                assert d.source in DS.SOURCE_LABEL, f"{v.id}: unknown source {d.source}"
                assert d.policy in (DS.SAY, DS.ALLUDE, DS.HOLD)


def test_no_gated_variant_recites_a_hold_fact():
    for s in DS.SCENARIOS:
        for v in DS.gated_variants(s):
            assert not v.uses_hold_in_copy, f"{v.id} recites a HOLD fact in copy"


def test_each_scenario_has_a_blocked_creepy_arm_on_a_hold_fact():
    for s in DS.SCENARIOS:
        b = DS.blocked_variant(s)
        assert b is not None and b.blocked, f"scenario {s.id} missing a blocked arm"
        assert any(d.policy == DS.HOLD for d in b.data_used), \
            f"{b.id} should rely on a HOLD fact (that's why it's blocked)"


def test_every_variant_kpi_is_a_real_master_kpi():
    for s in DS.SCENARIOS:
        for v in s.variants:
            assert v.kpi in DS.KPIS, f"{v.id} targets unknown KPI {v.kpi}"


# --- the bandit learns, and can never pull the creepy arm ---------------------
def test_bandit_converges_to_intended_winners():
    m = demo_sim.build()
    assert m["all_converged"] is True
    winners = {sc["id"]: sc["learned_winner"] for sc in m["scenarios"]}
    assert winners == {"A": "A1", "B": "B2", "C": "C1"}


def test_blocked_arm_never_selected():
    m = demo_sim.build()
    for sc in m["scenarios"]:
        assert sc["blocked_arm"]["selections"] == 0, \
            f"scenario {sc['id']} selected its blocked arm — policy breach"


def test_simulation_is_deterministic():
    assert demo_sim.build()["scenarios"] == demo_sim.build()["scenarios"]


# --- monitor shape + health rails ---------------------------------------------
def test_kpi_tree_covers_all_master_kpis():
    m = demo_sim.build()
    assert len(m["kpi_tree"]) == len(DS.KPI_GROUPS)
    keys = {k["key"] for g in m["kpi_tree"] for k in g["kpis"]}
    assert keys == set(DS.KPIS)


def test_health_rails_clean():
    h = demo_sim.build()["health"]
    assert h["provenance"]["coverage_pct"] == 100
    assert h["provenance"]["hold_in_copy"] == []
    assert h["provenance"]["no_source"] == []
    assert h["hallucination"]["ungated_arms"] == 3
    assert h["hallucination"]["selected"] == 0


# --- cloner: high-fidelity inject + graceful fallback (offline) ---------------
_FIXTURE = ('<html><head><title>Real</title>'
            '<meta http-equiv="refresh" content="0;url=https://elsewhere.example">'
            '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'">'
            '</head><body><h1>Original page</h1>'
            '<script>track();</script></body></html>')


def test_cloner_is_high_fidelity_keeps_scripts(monkeypatch):
    """High fidelity = keep the page's own scripts/CSS so it renders like the real site;
    only redirects + CSP are neutralized, and our hero is injected."""
    monkeypatch.setattr(cloner, "fetch_raw",
                        lambda url, cache=None: {"ok": True, "status": 200, "html": _FIXTURE, "error": ""})
    s = DS.scenario("A")
    v = DS.gated_variants(s)[0]
    out = cloner.clone("https://example.com", "A", v)
    assert out["cloned"] is True
    assert "prov-demo-overlay" in out["html"]   # personalization hero injected
    assert v.headline in out["html"]
    assert "Original page" in out["html"]        # real content preserved
    assert "<script" in out["html"].lower()      # scripts KEPT (fidelity)
    assert "<base href=" in out["html"]          # origin base injected
    assert "http-equiv=\"refresh\"" not in out["html"].lower().replace("'", '"')  # redirect neutralized
    assert "content-security-policy" not in out["html"].lower()  # CSP neutralized (so our hero renders)


def test_cloner_falls_back_when_fetch_fails(monkeypatch):
    monkeypatch.setattr(cloner, "fetch_raw",
                        lambda url, cache=None: {"ok": False, "status": 0, "html": "", "error": "boom"})
    s = DS.scenario("B")
    v = DS.gated_variants(s)[0]
    out = cloner.clone("https://example.com", "B", v)
    assert out["cloned"] is False
    assert "prov-demo-overlay" in out["html"]  # still shows the personalization hero
    assert v.headline.replace("{brand}", "Example") in out["html"]  # brand-filled copy


# --- copy adapts to the cloned site (the bug fix) -----------------------------
def test_brand_from_url():
    assert cloner.brand_from_url("https://www.nike.com") == "Nike"
    assert cloner.brand_from_url("python.org") == "Python"
    assert cloner.brand_from_url("https://www.gauntletai.com") == "Gauntlet AI"


def test_injected_copy_is_brand_templated_not_hardcoded(monkeypatch):
    """The injected copy must reference the CLONED site, not a hardcoded brand."""
    monkeypatch.setattr(cloner, "fetch_raw",
                        lambda url, cache=None: {"ok": True, "status": 200, "html": _FIXTURE, "error": ""})
    s = DS.scenario("B")
    v = next(x for x in DS.gated_variants(s) if "{brand}" in x.headline + x.sub)
    out = cloner.clone("https://example.com", "B", v)
    assert "{brand}" not in out["html"]   # placeholder fully substituted
    assert "Example" in out["html"]        # filled from example.com, not gauntletai


def test_no_gauntletai_specific_copy_in_spec():
    """The variant copy must be brand-generic (no hardcoded gauntletai/AI-cohort terms)."""
    blob = " ".join(
        (v.headline + " " + v.sub + " " + v.cta).lower()
        for sc in DS.SCENARIOS for v in sc.variants)
    for term in ("gauntlet", "ai cohort", "intro to python", "scholarship", "graduate outcomes"):
        assert term not in blob, f"copy still references '{term}'"
