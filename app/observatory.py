"""The Provenance Observatory — the live, watchable view of a pipeline run.

Serves the dashboard (the node graph + tooling, the architecture diagram, the phase
ribbon, the per-node input→decision→output evals, the P1-P5 health panel) and the
data contract the surface polls:

    GET /observatory                 — the dashboard (honest empty state if no run traced)
    GET /api/observe/events?since=N  — append-only ledger, events with seq > N (poll-since-seq)
    GET /api/observe/nodes           — the topology (node graph + tooling + edges)
    GET /api/observe/evals           — per-node I/O contract + the events each node emitted
    GET /api/observe/meta            — phases, lanes, profile/seed, P1-P5 verdicts

Reads only the persisted ledger in data/demo/observe/ (decision R5: live = deterministic
seeded replay), so the dashboard works after the fact and degrades honestly when empty.
Poll-since-seq also tails a trace that is still being written by another process.
"""
from __future__ import annotations

import json

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.server import app, templates
from pipeline.common.config import (OBSERVE_DIR, DB_PATH, PROFILES_DB_PATH, CLAIMS_DIR,
                                    RULES_DIR)
from pipeline.enrichment import catalog as enrich_catalog
from pipeline.enrichment.store import ProfileStore


def _load(name: str, default=None):
    p = OBSERVE_DIR / name
    return json.loads(p.read_text()) if p.exists() else default


# the database locations the operator asked to see surfaced
DB_LOCATIONS = [
    {"name": "provenance.sqlite", "path": str(DB_PATH),
     "holds": "recipients · form_events · cta_events · verdict_cache · llm_cache"},
    {"name": "profiles.sqlite", "path": str(PROFILES_DB_PATH),
     "holds": "synthesized profiles + every fact receipt (source · basis · verdict)"},
    {"name": "claims/library.json", "path": str(CLAIMS_DIR / "library.json"),
     "holds": "versioned claim-evidence graph"},
    {"name": "observe/*.jsonl", "path": str(OBSERVE_DIR),
     "holds": "append-only observability event ledger (one per lane)"},
    {"name": "helix_tenant.yaml", "path": str(RULES_DIR / "helix_tenant.yaml"),
     "holds": "human-owned claim policy + enrichment-source policy"},
]


def _events(since: int = 0) -> list[dict]:
    out: list[dict] = []
    for p in sorted(OBSERVE_DIR.glob("*.jsonl")):
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            if e.get("seq", 0) > since:
                out.append(e)
    out.sort(key=lambda e: e["seq"])
    return out


@app.get("/observatory", response_class=HTMLResponse)
def observatory(request: Request):
    meta = _load("meta.json")
    if not meta:
        return templates.TemplateResponse(request, "observatory.html", {"empty": True})
    return templates.TemplateResponse(request, "observatory.html", {
        "empty": False,
        "meta": meta,
        "topology": _load("topology.json", {}),
        "evals": _load("node_evals.json", {}),
    })


@app.get("/api/observe/events")
def api_events(since: int = 0):
    evs = _events(since)
    last = evs[-1]["seq"] if evs else since
    return JSONResponse({"events": evs, "last_seq": last})


@app.get("/api/observe/nodes")
def api_nodes():
    return JSONResponse(_load("topology.json", {}))


@app.get("/api/observe/evals")
def api_evals():
    return JSONResponse(_load("node_evals.json", {}))


@app.get("/api/observe/meta")
def api_meta():
    return JSONResponse(_load("meta.json") or {"empty": True})


@app.get("/api/observe/enrichment")
def api_enrichment():
    return JSONResponse(_load("enrichment.json") or {"empty": True})


@app.get("/api/observe/profiles")
def api_profiles():
    """The profile DB, readable — every synthesized fact + its source/basis/verdict receipt."""
    store = ProfileStore()
    return JSONResponse({"summary": store.summary(), "facts": store.all_facts(),
                         "db_locations": DB_LOCATIONS})


@app.get("/enrichment-catalog", response_class=HTMLResponse)
def enrichment_catalog(request: Request):
    """Every data source we could enrich with, paid or free, honest about cost + basis."""
    return templates.TemplateResponse(request, "enrichment_catalog.html", {
        "grouped": enrich_catalog.grouped(),
        "enrichment": _load("enrichment.json"),
        "db_locations": DB_LOCATIONS,
    })
