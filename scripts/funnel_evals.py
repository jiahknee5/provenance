"""Build the funnel dashboard data (customer journeys + surface-policy views).

Run:  python -m scripts.funnel_evals
Writes data/demo/observe/funnel.json and prints the per-path pass tally.
"""
from __future__ import annotations

import json

from pipeline.common.config import OBSERVE_DIR
from pipeline.customer.scenarios import report


def main() -> dict:
    rep = report()
    (OBSERVE_DIR / "funnel.json").write_text(json.dumps(rep, indent=2, default=str))
    s = rep["summary"]
    print(f"funnel paths {s['passed']}/{s['total']} · invariant "
          f"{'✓' if rep['journey']['invariant']['pass'] else '✗'} · "
          f"customers {rep['store']['customers']}")
    for p in rep["paths"]:
        print(f"  {'✓' if p['pass'] else '✗'}  {p['name']}")
    return rep


if __name__ == "__main__":
    main()
