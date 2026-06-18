"""The golden eval suite is itself a test — every curated case must hit its expectation.

Node-level steps (Library, the Gate, the Enrichment Gate) + the end-to-end lifecycle eval
are self-contained (no run artifacts needed). The workflow-level steps (Optimizer/Drift/
Assurance/Website) are scored from a run's artifacts and verified on the dashboard.
"""
from __future__ import annotations

from pipeline.evals.golden import lifecycle_eval, run_golden
from pipeline.library.library import ClaimsLibrary

SELF_CONTAINED = {"library", "gate", "enrich_gate"}


def test_node_level_golden_cases_pass():
    report = run_golden([])
    failures = []
    for step in report["steps"]:
        if step["step"] not in SELF_CONTAINED:
            continue
        for case in step["cases"]:
            if not case["pass"]:
                failures.append(f"{step['step']} / {case['name']}: got {case['output']} "
                                f"expected {case['expected']}")
    assert not failures, "golden cases failed:\n" + "\n".join(failures)


def test_every_gate_case_has_a_graph_log():
    report = run_golden([])
    gate = next(s for s in report["steps"] if s["step"] == "gate")
    for case in gate["cases"]:
        assert case["graph_log"], f"{case['name']} captured no graph log"


def test_lifecycle_eval_passes():
    result = lifecycle_eval(ClaimsLibrary.from_seed())
    assert result["pass"], [c for c in result["checks"] if not c["pass"]]
    assert result["graph_log"], "lifecycle eval captured no graph log"
