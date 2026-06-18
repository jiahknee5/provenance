"""Per-module tests for the Claims Library and the compliance rules engine."""
from __future__ import annotations

from pipeline.common.schemas import Verdict
from pipeline.library import seed_data


def test_every_claim_binds_to_a_span(library):
    assert len(library.claims) == len(seed_data.CLAIMS)
    for cid in library.claims:
        bound = library.bound_evidence(cid)
        assert bound and bound in library.source(library.claim(cid).source_id).text


def test_dependency_graph_is_exact(library):
    assert sorted(library.claims_for_source("s_pricing")) == ["c_nofee", "c_price"]


def test_source_change_bumps_version_and_flags_only_dependents(library):
    v0 = library.source_version("s_pricing")
    affected = library.apply_source_change(
        "s_pricing",
        "Helix Analytics is priced at $0.15 per patient record. "
        "There is no implementation fee for systems under 200 beds.")
    assert library.source_version("s_pricing") != v0
    assert sorted(affected) == ["c_nofee", "c_price"]
    assert library.is_drifted("c_price") and library.is_drifted("c_nofee")
    assert not library.is_drifted("c_tco")


def test_planted_lie_blocked_by_rule(rules):
    out = rules.apply(seed_data.PLANTED_LIE_TEXT, None)
    assert out.verdict == Verdict.RED
    assert "no_guaranteed_outcomes" in out.flags


def test_rules_version_changes_when_hold_flips(rules, library):
    tco = library.claim("c_tco")
    v0 = rules.rules_version()
    assert rules.apply(tco.text, tco).verdict == Verdict.AMBER  # roi disclaimer, hold off
    v1 = rules.set_hold("mlr_hold_tco", True)
    assert v1 != v0
    assert rules.apply(tco.text, tco).verdict == Verdict.RED
