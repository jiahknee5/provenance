"""Review queue API — advisory for AMBER; blocking only for non-advisory rejections."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.server import app, templates
from pipeline.domain.review import ReviewStatus, ReviewStore


class ReviewDecisionBody(BaseModel):
    decision: str
    notes: str = ""
    assigned_to: str = ""


_store = ReviewStore()


@app.get("/api/reviews")
def api_list_reviews():
    pending = [r.model_dump() for r in _store.list_pending()]
    return JSONResponse({"reviews": pending, "count": len(pending)})


@app.post("/api/reviews")
def api_request_review(object_type: str, object_id: str, advisory: bool = True):
    review = _store.request_review(object_type, object_id, advisory=advisory)
    return JSONResponse(review.model_dump())


@app.patch("/api/reviews/{review_id}")
def api_decide_review(review_id: str, body: ReviewDecisionBody):
    try:
        status = ReviewStatus(body.decision)
    except ValueError:
        return JSONResponse({"error": f"invalid decision {body.decision!r}"}, status_code=400)
    review = _store.decide(review_id, status, notes=body.notes, assigned_to=body.assigned_to)
    if review is None:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(review.model_dump())


@app.get("/assurance/reviews", response_class=HTMLResponse)
def assurance_reviews_panel(request: Request):
    """Minimal review queue card for the Assurance surface."""
    pending = _store.list_pending()
    return templates.TemplateResponse(request, "review_queue.html", {"reviews": pending})
