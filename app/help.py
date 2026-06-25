"""In-app Help corpus, served under /help.

Content lives in ``app/help_corpus.json`` as structured blocks and is rendered by
``help.html`` (index) + ``help_article.html`` (article), so styling stays token-clean and
consistent with the Quiet Workspace. The corpus is accurate to the codebase
(CONSTITUTION Art. I/VIII — it describes only what actually exists).

  GET /help          — the corpus index, grouped by category
  GET /help/{slug}   — a single article (unknown slug → redirect to /help)
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.server import app, templates

# fixed display order for the index; anything else falls under a trailing "More" group
CATEGORIES = ["Start here", "Pipeline & trust", "Data & provenance", "Using the surfaces", "Methodology"]
_CORPUS = Path(__file__).with_name("help_corpus.json")


def _load() -> list[dict]:
    return json.loads(_CORPUS.read_text()) if _CORPUS.exists() else []


@app.get("/help", response_class=HTMLResponse)
def help_index(request: Request):
    articles = _load()
    known = set(CATEGORIES)
    groups = [{"category": c, "articles": [a for a in articles if a.get("category") == c]}
              for c in CATEGORIES]
    groups = [g for g in groups if g["articles"]]
    extra = [a for a in articles if a.get("category") not in known]
    if extra:
        groups.append({"category": "More", "articles": extra})
    return templates.TemplateResponse(request, "help.html",
                                      {"groups": groups, "count": len(articles)})


@app.get("/help/{slug}", response_class=HTMLResponse)
def help_article(request: Request, slug: str):
    articles = _load()
    by_slug = {a["slug"]: a for a in articles}
    a = by_slug.get(slug)
    if not a:
        return RedirectResponse("/help")
    same = [x for x in articles if x.get("category") == a.get("category")]
    i = same.index(a)
    prev = same[i - 1] if i > 0 else None
    nxt = same[i + 1] if i < len(same) - 1 else None
    related = [by_slug[s] for s in a.get("related", []) if s in by_slug]
    return templates.TemplateResponse(request, "help_article.html",
                                      {"a": a, "prev": prev, "next": nxt, "related": related})
