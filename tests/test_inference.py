"""Per-module tests for the verifier primitives (NLI, ensemble, calibration).

The load-bearing one: a number-drifted claim is nearly identical lexically, so a
similarity-only judge passes it while the number-aware ensemble catches it. That is the
honest reason the Gate beats a single judge (T5).
"""
from __future__ import annotations

from pipeline.gate.calibrate import IsotonicCalibrator
from pipeline.gate.ensemble import JudgeEnsemble, single_judge_baseline
from pipeline.gate.nli import LexicalNLI

EVIDENCE = ("Northwind Health cut total cost of ownership by 47% over 18 months "
            "in a deployed case study.")


def test_verbatim_claim_is_entailed():
    nli = LexicalNLI()
    r = nli.score("cut total cost of ownership by 47%", EVIDENCE)
    assert r.label == "entailment"
    assert r.entail_prob >= 0.8


def test_number_drift_fools_single_judge_but_not_ensemble():
    drifted = "cut total cost of ownership by 57%"
    # a number-blind similarity judge sees almost no difference
    assert single_judge_baseline(drifted, EVIDENCE) >= 0.9
    # the numeric lens vetoes it
    assert JudgeEnsemble().judge(drifted, EVIDENCE).votes["numeric"] <= 0.1
    assert LexicalNLI().score(drifted, EVIDENCE).label == "contradiction"


def test_unsupported_superlative_flagged():
    claim = "the only guaranteed way to cut total cost of ownership by 47%"
    assert JudgeEnsemble().judge(claim, EVIDENCE).votes["superlative"] <= 0.2


def test_calibration_is_monotonic():
    cal = IsotonicCalibrator().fit([0.1, 0.2, 0.3, 0.6, 0.7, 0.9, 0.95],
                                   [0, 0, 0, 1, 1, 1, 1])
    preds = [cal.predict(s) for s in [0.05, 0.25, 0.5, 0.8, 0.99]]
    assert preds == sorted(preds)
    assert preds[0] <= 0.2 and preds[-1] >= 0.8
