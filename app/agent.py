"""The Agent surface — the deterministic navigator in place of a dashboard (PRD §5, SPEC §C).

  GET /agent?q=…        — ask/route over optimizer · assurance · drift · records; renders
                          the result as provenance-carrying cards. $0/offline/deterministic.
  GET /api/agent/run    — the same as JSON.

No LLM in this path; the optional NL layer (key-gated) would only map free text to these
same intents — the intents do the work and carry the provenance either way.
"""
from __future__ import annotations

import re

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.server import app, templates
from pipeline.agent import intents as A


def _md(s: str | None) -> str:
    """Tiny inline markdown → safe HTML for summary/note (**bold**, `code`)."""
    if not s:
        return ""
    s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r'<code style="background:var(--fill);border-radius:4px;padding:1px 5px;font-size:.92em">\1</code>', s)
    return s


@app.get("/agent", response_class=HTMLResponse)
def agent(request: Request, q: str = ""):
    result = A.run(q) if q else None
    if result:
        result["summary_html"] = _md(result.get("summary"))
        result["note_html"] = _md(result.get("note"))
    return templates.TemplateResponse(request, "agent.html",
                                      {"q": q, "result": result, "suggestions": A.INTENTS})


@app.get("/api/agent/run")
def api_agent_run(q: str = ""):
    return JSONResponse(A.run(q) if q else {"intents": [i["id"] for i in A.INTENTS]})
