"""Drift Monitor — surgical re-verification + pool mutation (extends headline T3).

The legal-hold flip is the campaign-2 transition: it re-Gates only the held claim and
pauses only the variants that assert it; the rest keep sending.
"""
from __future__ import annotations

from pipeline.drift.monitor import DriftMonitor
from pipeline.generation.variants import build_action_pool


def test_legal_hold_flip_is_surgical_and_pauses_only_roi(gate, library, rules):
    pool, _ = build_action_pool(gate, "email", "c1", constrained=True)
    assert "cfo__core__email__A" in pool.active("cfo__core")  # ROI variant sendable, hold off

    dm = DriftMonitor(gate, library, rules)
    rep = dm.fire_legal_hold("mlr_hold_tco", True, [pool], name="t_hold")

    assert rep.affected_claims == ["c_tco"]              # only the held claim re-checked
    assert rep.recomputed_ids == ["c_tco"]               # surgical
    assert rep.before["c_tco"] == "amber" and rep.after["c_tco"] == "red"
    # the ROI variant (uses c_tco) is paused; the pricing variant keeps sending
    assert "cfo__core__email__A" not in pool.active("cfo__core")
    assert "cfo__core__email__B" in pool.active("cfo__core")
    assert "cfo__core__email__A" in rep.paused_variants


def test_source_change_drift_is_surgical(gate, library, rules):
    pool, _ = build_action_pool(gate, "email", "c1", constrained=True)
    dm = DriftMonitor(gate, library, rules)
    rep = dm.fire_source_change(
        "s_pricing",
        "Helix Analytics is priced at $0.15 per patient record. "
        "There is no implementation fee for systems under 200 beds.",
        [pool], name="t_source")

    assert sorted(rep.affected_claims) == ["c_nofee", "c_price"]
    assert sorted(set(rep.recomputed_ids)) == ["c_nofee", "c_price"]   # nothing else re-Gated
    assert rep.after["c_price"] == "red" and rep.after["c_nofee"] != "red"


def test_campaign2_pool_excludes_held_variant_after_drift(gate, library, rules):
    pool1, _ = build_action_pool(gate, "email", "c1", constrained=True)
    DriftMonitor(gate, library, rules).fire_legal_hold("mlr_hold_tco", True, [pool1], name="t2")
    # a fresh post-drift pool for campaign 2 simply doesn't clear the ROI variant
    pool2, _ = build_action_pool(gate, "email", "c2", constrained=True)
    assert "cfo__core__email__A" not in pool2.active("cfo__core")
    assert "cfo__core__email__B" in pool2.active("cfo__core")
    assert not any(v.endswith("__LIE") for v in pool2.all_variant_ids())
