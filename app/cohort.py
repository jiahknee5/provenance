"""The cohort personalization demo.

  GET /lp?email=&tier=      — Step 1: scan QR → enter a gauntletai email → matched against
                              our cohort DB (Vector + HubSpot + Clay) → a personalized landing.
  GET /admin/landings       — Step 2: a gallery of the 10 seed users.
  GET /admin/landing/{id}   — one user's landing (live, in an iframe) + their personalized
                              email + the full "how this page was built" explanation.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.personalization import cohort, landing, segments


@app.get("/lp", response_class=HTMLResponse)
def lp(request: Request, email: str = "", tier: int = 2, token: str = ""):
    # three ways to identify the visitor → the same DB record → the same personalized page:
    #   token  = magic-link clicked from an email we sent (no login, no form)
    #   email  = typed at the QR, or verified via Google sign-in
    person = cohort.by_token(token) if token else (cohort.match(email) if email else None)
    if person:
        return templates.TemplateResponse(request, "landing.html",
                                          {"d": landing.build_landing(cohort.view(person), tier)})
    base = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(request, "lp_entry.html", {
        "qr": _qr_svg(base + "/lp"), "lp_url": base + "/lp",
        "emails": [p["email"] for p in cohort.COHORT], "bad": bool(email)})


def _qr_svg(url: str) -> str:
    try:
        import segno
        return segno.make(url, error="m").svg_inline(scale=4, dark="#0b1018", light="#ffffff")
    except Exception:
        return ""


@app.get("/admin/landings", response_class=HTMLResponse)
def admin_landings(request: Request):
    rows = []
    for p in cohort.COHORT:
        v = cohort.view(p)
        rows.append({"id": p["id"], "name": v["name"], "email": p["email"],
                     "title": p["vector"]["job_title"], "company": p["vector"]["company"],
                     "submitted": v["submitted"],
                     "archetype": segments.pick_archetype(v, segments.derive(v))})
    return templates.TemplateResponse(request, "admin_landings.html",
                                      {"rows": rows, "core": cohort.CORE_SOURCES})


@app.get("/admin/landing/{pid}", response_class=HTMLResponse)
def admin_landing(request: Request, pid: str, tier: int = 2):
    p = cohort.BY_ID.get(pid)
    if not p:
        return HTMLResponse("<h2>Unknown user.</h2>", status_code=404)
    base = str(request.base_url).rstrip("/")
    magic_link = f"{base}/lp?token={cohort.magic_token(p)}"
    return templates.TemplateResponse(request, "admin_landing.html", {
        "d": landing.build_landing(cohort.view(p), tier),
        "magic_link": magic_link, "magic_qr": _qr_svg(magic_link),
        "users": [{"id": x["id"], "name": x["vector"]["name"]} for x in cohort.COHORT]})
