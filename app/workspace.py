"""Workspace surfaces on the Quiet-Workspace shell — Home + Records.

Thin view layer over the existing cohort data (pipeline.personalization.cohort);
proves the design system end-to-end with a real record table. (PRD §5, SPEC §F P2)
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.personalization import cohort as C

# lifecycle → tag-pill class + label (the only colour in the system)
_PILL = {"customer": ("g", "Customer"), "sql": ("b", "SQL"), "mql": ("a", "MQL"),
         "lead": ("v", "Lead"), "visitor": ("", "Visitor")}
_AVC = ["#2E6FF5", "#6B4BD6", "#1E8A53", "#B5731B", "#C0354B"]


def _rows() -> list[dict]:
    rows = []
    for i, p in enumerate(C.COHORT):
        v = C.view(p)
        li, hs = v["linkedin"], v["hubspot"]
        cls, lbl = _PILL.get(hs["lifecycle"], ("", hs["lifecycle"].title()))
        rows.append({
            "name": v["name"], "company": li["company"] or "—", "title": li["title"],
            "industry": li["industry"], "lifecycle_cls": cls, "lifecycle_lbl": lbl,
            "score": hs["lead_score"], "av": (v["name"][:1] or "?").upper(),
            "avc": _AVC[i % len(_AVC)], "source": hs.get("source", "—"),
        })
    return rows


def _stats(rows: list[dict]) -> dict:
    qualified = sum(1 for r in rows if r["lifecycle_lbl"] in ("SQL", "MQL"))
    customers = sum(1 for r in rows if r["lifecycle_lbl"] == "Customer")
    return {"records": len(rows), "qualified": qualified, "customers": customers}


@app.get("/workspace", response_class=HTMLResponse)
def workspace(request: Request):
    rows = _rows()
    return templates.TemplateResponse(request, "workspace.html",
                                      {"rows": rows, "stats": _stats(rows)})


@app.get("/records", response_class=HTMLResponse)
def records(request: Request):
    return templates.TemplateResponse(request, "records.html", {"rows": _rows()})
