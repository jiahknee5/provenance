"""Re-run the golden evals against the current run's recorded ledger (no full pipeline re-run).

Run:  python -m scripts.evals
Writes data/demo/observe/golden_evals.json and prints the per-step pass tally.
"""
from __future__ import annotations

import json

from pipeline.common.config import OBSERVE_DIR
from pipeline.evals.golden import run_golden


def _read_ledger() -> list[dict]:
    evs: list[dict] = []
    for p in sorted(OBSERVE_DIR.glob("*.jsonl")):
        for line in p.read_text().splitlines():
            if line.strip():
                evs.append(json.loads(line))
    evs.sort(key=lambda e: e["seq"])
    return evs


def main() -> dict:
    golden = run_golden(_read_ledger())
    (OBSERVE_DIR / "golden_evals.json").write_text(json.dumps(golden, indent=2, default=str))
    s = golden["summary"]
    print(f"golden {s['passed']}/{s['total']} · lifecycle {'✓' if golden['lifecycle']['pass'] else '✗'}")
    for step in golden["steps"]:
        p = sum(1 for c in step["cases"] if c["pass"])
        mark = "✓" if p == len(step["cases"]) else "✗"
        print(f"  {mark} {p}/{len(step['cases'])}  {step['label']}")
    return golden


if __name__ == "__main__":
    main()
