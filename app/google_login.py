"""The "Sign in with Google" demo — what a Google login actually gives, in honest tiers,
and (the real point) using the VERIFIED email as the key to load our own database and build
a personalized website.

  GET /google                — login screen (real Google button if OAuth configured; plus a
                               demo picker to "sign in as" a cohort member).
  GET /google?email=…        — signed in: the tiered dossier (bought/inferred is the payoff),
                               and — if that email is in our DB — their personalized website,
                               loaded on login.
  GET /google/callback       — real OAuth → verified email → same DB lookup + personalization.

Default = demo (synthetic, offline, safe). Real OAuth only when GOOGLE_CLIENT_ID/SECRET set.
"""
from __future__ import annotations

import urllib.parse

from fastapi import Request
from fastapi.responses import HTMLResponse

from app.server import app, templates
from pipeline.common import config
from pipeline.personalization import cohort, google as G, landing

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO = "https://openidconnect.googleapis.com/v1/userinfo"


def _auth_url(request: Request) -> str:
    redirect = str(request.base_url).rstrip("/") + "/google/callback"
    return GOOGLE_AUTH + "?" + urllib.parse.urlencode({
        "client_id": config.GOOGLE_CLIENT_ID, "redirect_uri": redirect,
        "response_type": "code", "scope": "openid email profile",
        "access_type": "online", "prompt": "consent"})


def _signed_in(request, email, profile):
    """Render the dossier + (if the verified email is in our DB) the personalized website."""
    person = cohort.match(email) if email else None
    matched = cohort.view(person) if person else None
    return templates.TemplateResponse(request, "google_login.html", {
        "data": G.overview(email, profile), "real": config.google_oauth_ready(), "signed_in": True,
        "profile": profile, "email": email,
        "matched": matched,
        "site_email": person["email"] if person else "",
        "landing": landing.build_landing(matched, 2) if matched else None,
    })


@app.get("/google", response_class=HTMLResponse)
def google_page(request: Request, signed_in: int = 0, email: str = ""):
    if signed_in or email:
        return _signed_in(request, email, None)
    return templates.TemplateResponse(request, "google_login.html", {
        "data": G.overview(), "real": config.google_oauth_ready(), "signed_in": False,
        "auth_url": _auth_url(request) if config.google_oauth_ready() else "",
        "demo_emails": [p["email"] for p in cohort.COHORT]})


@app.get("/google/callback", response_class=HTMLResponse)
def google_callback(request: Request, code: str = "", error: str = ""):
    profile = None
    if code and config.google_oauth_ready():
        try:
            import httpx
            redirect = str(request.base_url).rstrip("/") + "/google/callback"
            with httpx.Client(timeout=10) as c:
                tok = c.post(GOOGLE_TOKEN, data={
                    "code": code, "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET, "redirect_uri": redirect,
                    "grant_type": "authorization_code"}).json()
                ui = c.get(GOOGLE_USERINFO, headers={
                    "Authorization": f"Bearer {tok.get('access_token', '')}"}).json()
            profile = {"name": ui.get("name"), "email": ui.get("email"), "picture": ui.get("picture"),
                       "locale": ui.get("locale"), "sub": ui.get("sub"), "verified": ui.get("email_verified")}
        except Exception:
            profile = None
    return _signed_in(request, profile["email"] if profile else "", profile)
