"""Agent graph & decision trees surface — the live routing made visible.

Surfaces the visitor→personalization decision tree + the agent-graph mapping (deterministic
router, LLM leaves, one Gate) as a navigable page on the Quiet-Workspace shell. The exhibit
itself is the self-contained /static/mockups/decision-tree.html, embedded same-origin.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates


@app.get("/graph", response_class=HTMLResponse)
def graph(request: Request):
    return templates.TemplateResponse(request, "graph.html", {})
