"""The composer send-check engine — the Gate verifies every line before it can ship.

Deterministic, $0/offline: the send-check scans a draft for facts whose surface policy is
`hold` (income, churn, competitor-shopping, life-events, …) — facts we may hold for targeting
but must never recite. Any hit blocks the send with the fact + its source. The creepiness
invariant (T-P2b): a `hold` fact can never reach copy.

R38 (T-09): the /composer page is retired with the legacy plane; `check()` stays as the
engine entry point (asserted by `test_full_suite.py::test_composer_clears_clean_and_blocks_held`).
"""
from __future__ import annotations

# hold-fact triggers → (what it is, where it came from). Mirrors the HOLD signals in
# pipeline.personalization.signals (broker / identity-graph / sensitive OAuth).
HOLD_TRIGGERS = [
    ({"income", "salary", "net worth", "make $", "afford", "earn "}, "modeled income / net worth", "broker append"),
    ({"comparing", "competitor", "other bootcamp", "shopping around", "side-by-side", "vs "}, "cross-site comparison shopping", "DMP (bought)"),
    ({"churn", "might leave", "at risk of", "price-sensitive"}, "churn-risk score", "internal model"),
    ({"baby", "newborn", "pregnan", "new parent", "expecting"}, "life-event: new parent", "broker trigger"),
    ({"separated", "divorce", "recently single"}, "life-event: separation", "broker trigger"),
    ({"home value", "homeowner", "your house", "your home is worth"}, "property / home value", "property records (broker)"),
    ({"i can see", "we noticed you", "cookies cleared", "your device"}, "device recognition", "fingerprint (observed)"),
]

def check(msg: str) -> dict:
    low = (msg or "").lower()
    hits = [{"label": label, "source": source}
            for kws, label, source in HOLD_TRIGGERS if any(k in low for k in kws)]
    return {"blocked": bool(hits), "hits": hits}
