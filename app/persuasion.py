"""Persuasion overlay surface (the UC3 closing layer).

  GET /api/persuasion/strategies          — the persuasion principles available
  GET /api/persuasion/plan?token=&strategy= — a Gate-bounded copy plan for a known visitor:
        which provable claims to lead with, the framing headline + CTA, and what the Gate
        DROPPED (the visible truth boundary). Every claim carries its source; nothing ships
        that the Gate can't prove.
"""
from __future__ import annotations

from fastapi.responses import JSONResponse

from app.context import ctx
from app.server import app
from pipeline.generation import recipients as rec
from pipeline.personalization import persuasion


@app.get("/api/persuasion/strategies")
def persuasion_strategies() -> JSONResponse:
    return JSONResponse({"strategies": persuasion.list_strategies()})


@app.get("/api/persuasion/plan")
def persuasion_plan(token: str, strategy: str = "") -> JSONResponse:
    r = rec.by_token(token)
    if not r:
        return JSONResponse({"error": "unknown token"}, status_code=404)
    c = ctx()
    plan = persuasion.build_plan(c.gate, c.library, r, strategy=strategy or None)
    return JSONResponse(plan.to_dict())
