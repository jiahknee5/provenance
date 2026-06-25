"""Entrypoint (`uvicorn app.main:app`). Registers the form routes and pulls in the
website + inspector route modules.

  GET  /            — the real, working lead-capture form (Helix Analytics)
  POST /submit      — create a Recipient -> SQLite, return a thank-you + magic link
  GET  /site/{token}— the ultra-personalized website channel (app/site.py)
  GET  /personalize — the provenance-tagged super-personalization demo (app/personalize.py)
  GET  /inspector   — the demo inspector UI (app/inspector.py)
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.server import app, templates
from pipeline.common.schemas import Recipient
from pipeline.enrichment.engine import enrich
from pipeline.enrichment.store import ProfileStore
from pipeline.generation import recipients as rec


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """The main page — an Attio-landing-style home featuring the live demo (the front door)."""
    return templates.TemplateResponse(request, "home.html", {})


@app.get("/talk")
def talk():
    """Internal enablement deck (GTM-is-engineering / trust-is-the-last-edge), served from static."""
    return RedirectResponse("/static/talk/deck.html")


@app.get("/guide")
def guide():
    """Engineering writeup: the copy-research swarm → the two-axis Gate (verify_copy/message/sequence)."""
    return RedirectResponse("/static/mockups/copy-research-guide.html")


@app.get("/lead", response_class=HTMLResponse)
def form(request: Request):
    return templates.TemplateResponse(request, "form.html", {
        "roles": rec.ROLE_TITLES, "sizes": rec.SIZES,
        "regions": rec.REGIONS, "heard": rec.HEARD,
    })


@app.post("/submit", response_class=HTMLResponse)
def submit(request: Request,
           name: str = Form(...), email: str = Form(...), company: str = Form(...),
           role: str = Form(...), company_size: str = Form(...), region: str = Form(...),
           urgency: str = Form("medium"), heard_via: str = Form(""),
           consent: bool = Form(False)):
    token = secrets.token_hex(8)
    r = Recipient(
        recipient_id=f"web_{token[:8]}", token=token, name=name.strip(), email=email.strip(),
        company=company.strip(), role=role, company_size=company_size, region=region,
        use_case=rec.ROLE_USE_CASES.get(role, "evaluate Helix Analytics"),
        urgency=urgency, consent=consent, heard_via=heard_via,
        segment=rec.segment(role, company_size),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    rec.insert_one(r)
    # touchpoint T2: enrich from other sources + synthesize a gated profile (data-provenance)
    profile = enrich(r, store=ProfileStore())
    return templates.TemplateResponse(request, "thanks.html", {
        "r": r,
        "enrich": {"usable": len(profile.usable_facts), "blocked": len(profile.blocked_facts),
                   "signals": list(profile.signals)},
    })


# attach the website + inspector + observatory + assurance routes
from app import site as _site  # noqa: E402,F401
from app import inspector as _inspector  # noqa: E402,F401
from app import observatory as _observatory  # noqa: E402,F401
from app import assurance as _assurance  # noqa: E402,F401
from app import optimizer as _optimizer  # noqa: E402,F401
from app import funnel as _funnel  # noqa: E402,F401
from app import personalize as _personalize  # noqa: E402,F401
from app import cohort as _cohort  # noqa: E402,F401
from app import google_login as _google_login  # noqa: E402,F401
from app import demo as _demo  # noqa: E402,F401
from app import workspace as _workspace  # noqa: E402,F401
from app import agent as _agent  # noqa: E402,F401
from app import sources as _sources  # noqa: E402,F401
from app import composer as _composer  # noqa: E402,F401
from app import policies as _policies  # noqa: E402,F401
from app import graph as _graph  # noqa: E402,F401
from app import help as _help  # noqa: E402,F401
from app import archive as _archive  # noqa: E402,F401
