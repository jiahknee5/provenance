"""Composer — write outreach; the Gate verifies every line before it can ship (PRD §5, P2).

Deterministic, $0/offline: the send-check scans the draft for facts whose surface policy is
`hold` (income, churn, competitor-shopping, life-events, …) — facts we may hold for targeting
but must never recite. Any hit blocks the send with the fact + its source. The creepiness
invariant (T-P2b): a `hold` fact can never reach copy.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates

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

# A policy-safe, personalized draft for the persona (say declared + allude behaviour; no hold).
SAFE_DRAFT = ("Hi Maya — you mentioned wanting to move into AI without going broke. "
              "The evening cohort puts the financing options right up front, so it fits around "
              "a full-time job. Want me to send the next start dates?")


def check(msg: str) -> dict:
    low = (msg or "").lower()
    hits = [{"label": label, "source": source}
            for kws, label, source in HOLD_TRIGGERS if any(k in low for k in kws)]
    return {"blocked": bool(hits), "hits": hits}


@app.get("/composer", response_class=HTMLResponse)
def composer(request: Request, msg: str = ""):
    res = check(msg) if msg.strip() else None
    return templates.TemplateResponse(request, "composer.html",
                                      {"msg": msg or SAFE_DRAFT, "res": res})
