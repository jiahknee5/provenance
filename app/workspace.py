"""Workspace surfaces on the Quiet-Workspace shell — Home + Records.

Thin view layer over the existing cohort data (pipeline.personalization.cohort);
proves the design system end-to-end with a real record table. (PRD §5, SPEC §F P2)

Records are filterable (view=) and sortable (sort=) server-side, and a record can be
created (POST /records/new) — every control does real work, nothing is decorative.
"""
from __future__ import annotations

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.server import app, templates
from pipeline.personalization import cohort as C

# lifecycle → tag-pill class + label (the only colour in the system)
_PILL = {"customer": ("g", "Customer"), "sql": ("b", "SQL"), "mql": ("a", "MQL"),
         "lead": ("v", "Lead"), "visitor": ("", "Visitor")}
_AVC = ["#2E6FF5", "#6B4BD6", "#1E8A53", "#B5731B", "#C0354B"]

# filter views (the Records tabs + Workspace Filter menu) — predicate on the lifecycle label
VIEWS = [
    ("all", "All records", lambda r: True),
    ("customers", "Customers", lambda r: r["lifecycle_lbl"] == "Customer"),
    ("qualified", "Qualified (SQL+MQL)", lambda r: r["lifecycle_lbl"] in ("SQL", "MQL")),
    ("leads", "Leads", lambda r: r["lifecycle_lbl"] == "Lead"),
    ("visitors", "Visitors", lambda r: r["lifecycle_lbl"] == "Visitor"),
]
_VIEW = {k: pred for k, _, pred in VIEWS}
# sort options (the Sort menu) — (key, reverse)
SORTS = [("score", "Lead score", (lambda r: r["score"], True)),
         ("name", "Name (A→Z)", (lambda r: r["name"].lower(), False)),
         ("company", "Company (A→Z)", (lambda r: r["company"].lower(), False))]
_SORT = {k: spec for k, _, spec in SORTS}


def _row(i: int, p: dict) -> dict:
    v = C.view(p)
    li, hs = v["linkedin"], v["hubspot"]
    cls, lbl = _PILL.get(hs["lifecycle"], ("", hs["lifecycle"].title()))
    return {
        "id": v["id"], "name": v["name"], "company": li["company"] or "—", "title": li["title"],
        "industry": li["industry"], "lifecycle_cls": cls, "lifecycle_lbl": lbl,
        "score": hs["lead_score"], "av": (v["name"][:1] or "?").upper(),
        "avc": _AVC[i % len(_AVC)], "source": hs.get("source", "—"),
    }


def _rows(sort: str = "score", view: str = "all") -> list[dict]:
    rows = [_row(i, p) for i, p in enumerate(C.COHORT)]
    rows = [r for r in rows if _VIEW.get(view, _VIEW["all"])(r)]
    key, rev = _SORT.get(sort, _SORT["score"])
    rows.sort(key=key, reverse=rev)
    return rows


def _stats(rows: list[dict]) -> dict:
    qualified = sum(1 for r in rows if r["lifecycle_lbl"] in ("SQL", "MQL"))
    customers = sum(1 for r in rows if r["lifecycle_lbl"] == "Customer")
    return {"records": len(rows), "qualified": qualified, "customers": customers}


def _view_label(view: str) -> str:
    return next((label for k, label, _ in VIEWS if k == view), "All records")


@app.get("/workspace", response_class=HTMLResponse)
def workspace(request: Request, sort: str = "score", view: str = "all"):
    return templates.TemplateResponse(request, "workspace.html", {
        "rows": _rows(sort, view), "stats": _stats(_rows()),
        "sort": sort, "view": view, "view_label": _view_label(view), "views": VIEWS, "sorts": SORTS,
    })


@app.get("/records", response_class=HTMLResponse)
def records(request: Request, sort: str = "score", view: str = "all", created: str = ""):
    rec = C.BY_ID.get(created) if created else None
    return templates.TemplateResponse(request, "records.html", {
        "rows": _rows(sort, view), "total": len(C.COHORT),
        "sort": sort, "view": view, "view_label": _view_label(view), "views": VIEWS, "sorts": SORTS,
        "created_id": created if rec else "", "created_name": (rec["vector"]["name"] if rec else ""),
    })


@app.get("/records/new", response_class=HTMLResponse)
def records_new_form(request: Request):
    return templates.TemplateResponse(request, "records_new.html", {
        "lifecycles": ["lead", "mql", "sql", "customer", "visitor"],
    })


@app.post("/records/new")
def records_new(name: str = Form(...), email: str = Form(...), company: str = Form(""),
                title: str = Form(""), industry: str = Form(""), lifecycle: str = Form("lead"),
                lead_score: int = Form(0), source: str = Form("manual")):
    rec = C.add(name=name, email=email, company=company, title=title, industry=industry,
                lifecycle=lifecycle, lead_score=lead_score, source=source)
    # Agency/forgiveness: land on Records with an undo affordance for what was just created.
    return RedirectResponse(f"/records?sort=name&created={rec['id']}", status_code=303)


@app.post("/records/undo")
def records_undo(rid: str = Form(...)):
    """Undo a just-created record (WWDC26 Agency: easy recovery from any action)."""
    C.remove(rid)
    return RedirectResponse("/records?sort=name", status_code=303)
