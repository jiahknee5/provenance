"""Headline property T5 — the Assurance Lab proves the Gate beats a single judge.

Asserts inequalities and floors (not the deck's illustrative point values), per
Constitution Article VII. The key differentiator is number-drift: the number-blind single
judge catches none of it; the Gate's numeric lens catches it all.
"""
from __future__ import annotations

from pipeline.assurance.harness import run, run_per_channel
from pipeline.assurance.traps import generate


def test_t5_gate_beats_single_judge_at_low_false_reject(gate, library):
    rep = run(gate, generate(library))
    assert rep["n_traps"] >= 30                       # enough traps for a stable number
    assert rep["gate"]["false_reject"] <= 0.05        # fixed-FR operating point
    assert rep["gate"]["catch_rate"] >= 0.85
    # the Gate beats the baseline by a wide, principled margin
    assert rep["gate"]["catch_rate"] > rep["baseline"]["catch_rate"] + 0.4


def test_t5_single_judge_is_blind_to_number_drift(gate, library):
    rep = run(gate, generate(library))
    assert rep["gate"]["by_type"]["number_drift"] == 1.0        # Gate catches all
    assert rep["baseline"]["by_type"]["number_drift"] < 0.2     # baseline catches ~none


def test_t5_reported_per_channel_one_harness(gate, library):
    rep = run_per_channel(gate, library, save_name="assurance_test")
    assert set(rep["channels"]) == {"email", "website"}
    for ch, m in rep["channels"].items():
        assert m["gate_catch_rate"] > m["baseline_catch_rate"]
        assert m["gate_false_reject"] <= 0.05
