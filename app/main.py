"""Entrypoint (`uvicorn app.main:app`). One design (R38): the apt console shell.

  GET  /            — 302 → /apt/demo (the demo sitemap is the front door)
  GET  /lead        — the Helix Analytics lead-capture form (feeds /site/<token>)
  POST /submit      — create a Recipient -> SQLite, return a thank-you + magic link
  GET  /site/{token}— the ultra-personalized website channel (app/site.py; property T4)

Everything else mounts from the route modules imported below: the gauntlet/planet/skyfi
replica planes, the /apt tour + consoles, the observatory/costs dashboards, the gate-pinned
/showcase index, and the persuasion API.
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
    """The front door is the demo sitemap (R38: the legacy Attio-style home is retired)."""
    return RedirectResponse("/apt/demo")


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
from app import observatory as _observatory  # noqa: E402,F401
from app import persuasion as _persuasion  # noqa: E402,F401
from app import showcase as _showcase  # noqa: E402,F401
from app import gauntlet as _gauntlet  # noqa: E402,F401
from app import planet as _planet  # noqa: E402,F401
from app import skyfi as _skyfi  # noqa: E402,F401
from app import apt_dev as _apt_dev  # noqa: E402,F401
from app import apt_demo as _apt_demo  # noqa: E402,F401
from app import mockups as _mockups  # noqa: E402,F401
