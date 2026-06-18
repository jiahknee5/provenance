"""Assurance harness — run the trap set through the REAL Gate and a single-judge
baseline, then report decomposed reliability (not one pass-rate).

The single-judge baseline is a number-blind similarity judge: it misses number-drift and
compliance traps (the material ones) while the Gate's numeric + rule lenses catch them.
That is the honest reason the ensemble beats a single judge (T5).
"""
from __future__ import annotations

import json
from collections import defaultdict

from pipeline.common import observe
from pipeline.common.config import RUNS_DIR
from pipeline.common.schemas import Verdict
from pipeline.gate.calibrate import IsotonicCalibrator
from pipeline.gate.ensemble import single_judge_baseline
from pipeline.generation.variants import build_variants
from pipeline.assurance.traps import Trap, generate

BASELINE_THRESHOLD = 0.5   # baseline "caught" if topical similarity < threshold


def _ece(probs: list[float], labels: list[int], bins: int = 5) -> tuple[float, list[dict]]:
    """Expected Calibration Error of P(sayable) vs actual sayable, + reliability bins."""
    buckets: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for p, y in zip(probs, labels):
        idx = min(bins - 1, int(p * bins))
        buckets[idx].append((p, y))
    ece, diagram, n = 0.0, [], len(probs)
    for i, b in enumerate(buckets):
        if not b:
            diagram.append({"conf_mid": round((i + 0.5) / bins, 2), "accuracy": None, "count": 0})
            continue
        conf = sum(p for p, _ in b) / len(b)
        acc = sum(y for _, y in b) / len(b)
        ece += (len(b) / n) * abs(conf - acc)
        diagram.append({"conf_mid": round(conf, 3), "accuracy": round(acc, 3), "count": len(b)})
    return round(ece, 4), diagram


def run(gate, traps: list[Trap]) -> dict:
    by_mut = defaultdict(int)
    for t in traps:
        by_mut[t.mutation] += 1
    observe.emit("assurance", "INPUT", node="assurance",
                 tool="adversarial trap generator (4 mutations) + the real Gate + single-judge baseline",
                 detail=f"{len(traps)} traps through the Gate vs a number-blind single judge",
                 input={"n_traps": len(traps), "by_mutation": dict(by_mut)})
    items = []
    for t in traps:
        cv = gate.verify_claim(t.text, None)
        hits = gate.retriever.retrieve(t.text, k=1)
        base = single_judge_baseline(t.text, hits[0]["text"] if hits else "")
        items.append({
            "trap_id": t.trap_id, "mutation": t.mutation, "label": t.label,
            "severity": t.severity, "source": t.source_claim_id,
            "gate_verdict": cv.verdict.value, "gate_confidence": cv.confidence,
            "gate_caught": cv.verdict == Verdict.RED,
            "base_score": round(base, 3), "base_caught": base < BASELINE_THRESHOLD,
        })

    bad = [it for it in items if it["label"] == 1]
    clean = [it for it in items if it["label"] == 0]

    def rate(xs, key):
        return round(sum(1 for x in xs if x[key]) / len(xs), 4) if xs else 0.0

    by_type = defaultdict(lambda: [0, 0])
    base_by_type = defaultdict(lambda: [0, 0])
    for it in bad:
        by_type[it["mutation"]][0] += it["gate_caught"]
        by_type[it["mutation"]][1] += 1
        base_by_type[it["mutation"]][0] += it["base_caught"]
        base_by_type[it["mutation"]][1] += 1
    by_severity = defaultdict(lambda: [0, 0])
    for it in bad:
        by_severity[it["severity"]][0] += it["gate_caught"]
        by_severity[it["severity"]][1] += 1

    # calibration: fit on (raw confidence, is-sayable) then report ECE of calibrated probs
    raw = [it["gate_confidence"] for it in items]
    y_sayable = [1 - it["label"] for it in items]    # clean = sayable = 1
    cal = IsotonicCalibrator().fit(raw, y_sayable)
    calibrated = [cal.predict(s) for s in raw]
    ece, diagram = _ece(calibrated, y_sayable)

    result = {
        "n_traps": len(bad), "n_clean": len(clean),
        "gate": {
            "catch_rate": rate(bad, "gate_caught"),
            "false_reject": rate(clean, "gate_caught"),
            "by_type": {k: round(v[0] / v[1], 3) for k, v in by_type.items()},
            "by_severity": {k: round(v[0] / v[1], 3) for k, v in by_severity.items()},
        },
        "baseline": {
            "catch_rate": rate(bad, "base_caught"),
            "false_reject": rate(clean, "base_caught"),
            "by_type": {k: round(v[0] / v[1], 3) for k, v in base_by_type.items()},
        },
        "ece": ece, "reliability_bins": diagram, "items": items,
    }
    observe.emit("assurance", "DECISION", node="assurance",
                 detail=f"Gate catch {result['gate']['catch_rate']*100:.0f}% vs single-judge "
                        f"{result['baseline']['catch_rate']*100:.0f}% at "
                        f"{result['gate']['false_reject']*100:.0f}% false-reject",
                 decision={"gate_catch": result["gate"]["catch_rate"],
                           "baseline_catch": result["baseline"]["catch_rate"],
                           "gate_false_reject": result["gate"]["false_reject"],
                           "gate_by_type": result["gate"]["by_type"],
                           "baseline_by_type": result["baseline"]["by_type"]},
                 output={"ece": ece, "n_traps": len(bad), "n_clean": len(clean)})
    return result


def run_per_channel(gate, library, save_name: str = "assurance") -> dict:
    """One harness, results sliced per channel (same Gate, same claims — not two labs)."""
    traps = generate(library)
    overall = run(gate, traps)
    by_index = {it["trap_id"]: it for it in overall["items"]}

    channels = {}
    for channel in ("email", "website"):
        claim_set = {cid for vs in build_variants(channel).values() for v in vs for cid in v.claim_ids}
        sliced = [by_index[t.trap_id] for t in traps if t.source_claim_id in claim_set]
        bad = [x for x in sliced if x["label"] == 1]
        clean = [x for x in sliced if x["label"] == 0]
        channels[channel] = {
            "n_traps": len(bad), "n_clean": len(clean),
            "gate_catch_rate": round(sum(x["gate_caught"] for x in bad) / len(bad), 4) if bad else 0.0,
            "gate_false_reject": round(sum(x["gate_caught"] for x in clean) / len(clean), 4) if clean else 0.0,
            "baseline_catch_rate": round(sum(x["base_caught"] for x in bad) / len(bad), 4) if bad else 0.0,
        }
    overall["channels"] = channels
    (RUNS_DIR / f"{save_name}.json").write_text(json.dumps(overall, indent=2))
    return overall
