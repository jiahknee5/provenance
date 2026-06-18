"""The ultra-personalized website channel.

GET /site/{token} retrieves the recipient at launch (opaque token, no PII in URL), picks
the A/B-winning verified variant for their segment, runs every claim through the SAME Gate
(same verdict cache as email -> same claim_id, same verdict), and renders ONLY the
Gate-passed claims. A red claim never reaches the DOM. The CTA feeds the bandit.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.context import ctx
from app.server import app, templates
from pipeline.common.db import connect
from pipeline.common.schemas import MessageLedger, Verdict
from pipeline.enrichment.engine import enrich, personalize
from pipeline.enrichment.store import ProfileStore
from pipeline.generation import recipients as rec
from pipeline.generation.variants import build_variants


def render_site_data(gate, library, recipient, variant) -> dict:
    """Pure builder (testable without the server). Returns shown/blocked claims + ledger."""
    enriched, ledger_claims = [], []
    for cid in variant.claim_ids:
        node = library.claim(cid)
        cv = gate.verify_claim(node.text, node)
        ledger_claims.append(cv)
        enriched.append({
            "claim_id": cid, "text": node.text, "verdict": cv.verdict.value,
            "confidence": cv.confidence, "rule_flags": cv.rule_flags,
            "source_title": library.source(node.source_id).title,
            "evidence": library.bound_evidence(cid) if not library.is_drifted(cid) else "(source updated — re-verifying)",
        })
    ledger = MessageLedger(recipient_id=recipient.recipient_id, channel="website",
                           variant_id=variant.variant_id, segment=recipient.segment,
                           html=variant.headline, claims=ledger_claims,
                           generated_at=datetime.now(timezone.utc).isoformat())
    return {
        "variant": variant,
        "shown": [c for c in enriched if c["verdict"] != Verdict.RED.value],
        "blocked": [c for c in enriched if c["verdict"] == Verdict.RED.value],
        "ledger": ledger,
    }


def _variant_for(segment: str, arm: str):
    by_arm = {v.arm_label: v for v in build_variants("website")[segment]}
    return by_arm.get(arm) or by_arm["A"]


@app.get("/site/{token}", response_class=HTMLResponse)
def site(request: Request, token: str):
    r = rec.by_token(token)
    if not r:
        return HTMLResponse("<h2>Link not found.</h2>", status_code=404)
    c = ctx()
    variant = _variant_for(r.segment, c.winner(r.segment))
    data = render_site_data(c.gate, c.library, r, variant)
    # touchpoint T5: load the gated profile (enrich on demand for the seeded recipients)
    store = ProfileStore()
    profile = store.get(r.recipient_id) or enrich(r, store=store)
    pers = personalize(r, profile, variant.headline)
    return templates.TemplateResponse(request, "site.html", {
        "r": r, "variant": variant, "shown": data["shown"], "blocked": data["blocked"],
        "use_case": r.use_case, "personalization": pers["personalization"],
        "facts_withheld": pers["facts_blocked"],
    })


@app.get("/site/{token}/cta", response_class=HTMLResponse)
def site_cta(request: Request, token: str):
    r = rec.by_token(token)
    if not r:
        return HTMLResponse("<h2>Link not found.</h2>", status_code=404)
    arm = ctx().winner(r.segment)
    vid = f"{r.segment}__website__{arm}"
    conn = connect()
    try:
        conn.execute("INSERT INTO cta_events (recipient_id,channel,campaign,variant_id,clicked,ts) "
                     "VALUES (?,?,?,?,?,?)",
                     (r.recipient_id, "website", "site", vid, 1,
                      datetime.now(timezone.utc).isoformat()))
        conn.commit()
    finally:
        conn.close()
    return templates.TemplateResponse(request, "site_cta.html", {"r": r})
