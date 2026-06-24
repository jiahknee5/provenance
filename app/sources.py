"""Sources surface — every data source we could enrich from, honest about cost + basis.

Reuses the enrichment catalog (pipeline.enrichment.catalog) on the Quiet-Workspace shell.
The 'basis' column is the lawful posture; 'freshness' feeds the Drift TTL. (PRD §5 Catalog)
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.enrichment import catalog as cat

_GROUP_LABEL = {"free": "Free · low-cost", "paid": "Paid append", "engagement": "Engagement"}


@app.get("/sources", response_class=HTMLResponse)
def sources(request: Request):
    grouped = cat.grouped()
    groups = [{"key": k, "label": _GROUP_LABEL.get(k, k.title()), "rows": grouped[k]}
              for k in ("free", "paid", "engagement") if grouped.get(k)]
    return templates.TemplateResponse(request, "sources.html", {"groups": groups})
