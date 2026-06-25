"""Archive — surfaces kept for reference but out of the core workflow.

The PRD (§5) restructured the app into eight core surfaces; several earlier Lab/demo views were
meant to be *subsumed* by them (Records reframes funnel/cohort/admin_landings; Composer reframes
personalize/site) but still existed as standalone pages. To keep the app simple and aligned to the
core requirements, those live here — the routes still work, they're just off the main nav.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates

ARCHIVE = [
    {"group": "Superseded by a core surface", "note": "Folded into the main workflow (PRD §5).", "items": [
        {"name": "Personalize", "route": "/personalize", "by": "Composer + Live demo",
         "desc": "Tiered “what a site could know on load” (anonymous → broker → CRM), tasteful vs creepy, with the provenance ledger."},
        {"name": "Funnel", "route": "/funnel", "by": "Records",
         "desc": "Every way a customer enters, what’s captured at each step, and who may use it."},
        {"name": "Cohort gallery", "route": "/admin/landings", "by": "Records",
         "desc": "A gallery of the seed users, each with an archetype and a personalized landing."},
        {"name": "Enrichment catalog", "route": "/enrichment-catalog", "by": "Sources",
         "desc": "Every data source we could enrich with, paid or free, honest about cost and basis."},
    ]},
    {"group": "Demo & lab views", "note": "Focused exhibits built to show one idea.", "items": [
        {"name": "Inspector", "route": "/inspector", "by": "Assurance",
         "desc": "Claim-ledger lights, the regret contrast (constrained vs unconstrained twin), the blocked-lie panel, and the drift log — from a recorded run."},
        {"name": "Observatory", "route": "/observatory", "by": "Agent graph",
         "desc": "The pipeline run as a node graph — each stage’s input, output, and decision."},
        {"name": "Google sign-in", "route": "/google", "by": None,
         "desc": "What a Google login actually gives, in honest tiers, building a personalized page from the verified email."},
        {"name": "Lead form", "route": "/lead", "by": None,
         "desc": "The lead-capture form that seeds a record."},
    ]},
    {"group": "Internal decks", "note": "Reference material, not product surfaces.", "items": [
        {"name": "Enablement deck", "route": "/talk", "by": None,
         "desc": "GTM-is-engineering / trust-is-the-last-edge — the internal narrative."},
        {"name": "Engineering writeup", "route": "/guide", "by": None,
         "desc": "The copy-research swarm → the two-axis Gate (verify_copy / message / sequence)."},
    ]},
]


@app.get("/archive", response_class=HTMLResponse)
def archive(request: Request):
    return templates.TemplateResponse(request, "archive.html",
                                      {"groups": ARCHIVE, "count": sum(len(g["items"]) for g in ARCHIVE)})
