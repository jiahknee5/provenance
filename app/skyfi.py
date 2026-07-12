"""SkyFi (skyfi.com) replica routes — the live personalized site + its /dev console.

  GET  /skyfi           — skyfi.com-style replica; every copy block is a personalization
                          slot (entry UTM/referrer × IP tier × LOCATION×INDUSTRY × login/CRM)
  POST /skyfi/login     — email form in the replica's nav → session cookie (synthetic
                          customer-cohort emails unlock the CRM path; any work email
                          escalates via first-party domain resolution)
  GET  /skyfi/logout    — clears the cookie
  GET  /skyfi/dev       — the decisioning console (incl. the Location × industry stage
                          and the declared-AOI / arm-Ex policy panel)
  GET  /skyfi/dev/business — the per-section marketer designer (S5/T-07b): one card per
                          rules/skyfi_sections.yaml section, sd-* DOM contract, staged
                          drawer + dev/audit fold — same visitor state as /skyfi/dev.
  GET  /skyfi/direct    — direct-entry scenario gallery (demo_nav, config-driven)
  GET  /skyfi/email     — email-entry scenario gallery

  Portal mount (johnnycchung.com/skyfiapt via Vercel rewrite):
  GET  /skyfiapt, /skyfiapt/login, /skyfiapt/logout, /skyfiapt/dev,
       /skyfiapt/dev/business, /skyfiapt/direct, /skyfiapt/email

State lives entirely in (query params + one cookie), so both pages are rebuilt
deterministically per request — CONSTITUTION reproducibility, no server-side sessions.
"""
from __future__ import annotations

from urllib.parse import urlencode

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.server import app, templates
from pipeline.personalization import image_gen as IG
from pipeline.personalization import skyfi_dev_business as SDB
from pipeline.personalization import skyfi_site as SS

_COOKIE = "skyfi_email"

# Legacy paths for local dev + tests; portal mount for johnnycchung.com/skyfiapt.
MOUNTS: dict[str, dict[str, str]] = {
    "legacy": {
        "page": "/skyfi",
        "login": "/skyfi/login",
        "logout": "/skyfi/logout",
        "dev": "/skyfi/dev",
        "dev_business": "/skyfi/dev/business",
        "direct_gallery": "/skyfi/direct",
        "email_gallery": "/skyfi/email",
        "static": "/static",
        "hero_api": "/api/skyfi/hero-image",
    },
    "portal": {
        "page": "/skyfiapt",
        "login": "/skyfiapt/login",
        "logout": "/skyfiapt/logout",
        "dev": "/skyfiapt/dev",
        "dev_business": "/skyfiapt/dev/business",
        "direct_gallery": "/skyfiapt/direct",
        "email_gallery": "/skyfiapt/email",
        "static": "/skyfiapt/static",
        "hero_api": "/skyfiapt/api/hero-image",
    },
}


def entry_links(m: dict[str, str]) -> list[tuple[str, str]]:
    page = m["page"]
    return [
        ("Ad", f"{page}?utm_source=x&utm_medium=paid&utm_campaign=x-monitor-your-site&utm_content=sv01"),
        ("Email", f"{page}?utm_source=hubspot&utm_medium=email&utm_campaign=tasking-program&e="
                  + SS.sample_magic_token()),
        ("Search", f"{page}?ref=google"),
        ("Direct", page),
        ("Direct gallery", m["direct_gallery"]),
        ("Email gallery", m["email_gallery"]),
    ]


# Demo cards link to the legacy mount.
ENTRY_LINKS = entry_links(MOUNTS["legacy"])


def _cookie_email(request: Request) -> str:
    return (request.cookies.get(_COOKIE) or "").strip()


def _qs(request: Request, drop: tuple[str, ...] = ()) -> str:
    pairs = [(k, v) for k, v in request.query_params.multi_items() if k not in drop]
    return ("?" + urlencode(pairs)) if pairs else ""


def _cookie_path(m: dict[str, str]) -> str:
    if m["dev"].startswith(m["page"]):
        return m["page"]
    return "/"


def _safe_next(nxt: str, m: dict[str, str]) -> str:
    page = m["page"]
    if not nxt.startswith(page):
        return page
    return nxt


def _mount_static_url(url: str | None, m: dict[str, str]) -> str | None:
    """Portal mount serves assets under /skyfiapt/static, not /static."""
    if not url or not url.startswith("/static/"):
        return url
    prefix = m["static"]
    if prefix == "/static":
        return url
    return prefix + url[len("/static"):]


def _page_with_mount_urls(page: dict, m: dict[str, str]) -> dict:
    hero = dict(page.get("hero_image") or {})
    if hero.get("url"):
        hero["url"] = _mount_static_url(hero["url"], m)
    if hero.get("still_url"):
        hero["still_url"] = _mount_static_url(hero["still_url"], m)
    return {**page, "hero_image": hero}


def _render_skyfi(request: Request, m: dict[str, str]) -> HTMLResponse:
    email = _cookie_email(request)
    page = _page_with_mount_urls(SS.build_page(request, email=email or None), m)
    return templates.TemplateResponse(request, "skyfi_site.html", {
        "page": page, "qs": _qs(request), "dev_qs": _qs(request), "g": m,
        "hero_api_url": m["hero_api"],
    })


def _dev_email_and_page(request: Request, m: dict[str, str]) -> tuple[str, str | None, dict, str]:
    """Shared state for /dev — same query params + cookie as the replica."""
    as_state = request.query_params.get("as", "")
    cookie = _cookie_email(request)
    if as_state == "anon":
        email = None
    elif as_state == "known":
        email = cookie or SS.sample_login_email()
    else:
        email = cookie or None
    page = _page_with_mount_urls(SS.build_page(request, email=email), m)
    qs = _qs(request, drop=("as",))
    resolved = as_state or ("known" if email else "anon")
    return resolved, email, page, qs


def _dev_toggles(dev_path: str, qs: str) -> tuple[str, str]:
    sep = "&" if qs else "?"
    return f"{dev_path}{qs}{sep}as=anon", f"{dev_path}{qs}{sep}as=known"


def _render_dev(request: Request, m: dict[str, str]) -> HTMLResponse:
    as_state, email, page, qs = _dev_email_and_page(request, m)
    toggle_anon, toggle_known = _dev_toggles(m["dev"], qs)
    from pipeline.personalization import demo_nav as _NAV
    return templates.TemplateResponse(request, "skyfi_dev.html", {
        **_NAV.console_shell_ctx("skyfi", "consoles", active_sub="engineer"),
        "demo_flow_active": "engineer",
        "page": page, "pmap": SS.process_map(page),
        "as_state": as_state,
        "qs": qs, "toggle_anon": toggle_anon,
        "toggle_known": toggle_known,
        "entry_links_raw": entry_links(m),
        "sample_email": SS.sample_login_email(),
        "static_prefix": m["static"],
        "g": m})


def _render_dev_business(request: Request, m: dict[str, str]) -> HTMLResponse:
    as_state, email, page, qs = _dev_email_and_page(request, m)
    toggle_anon, toggle_known = _dev_toggles(m["dev_business"], qs)
    from pipeline.personalization import demo_nav as _NAV
    return templates.TemplateResponse(request, "skyfi_dev_business.html", {
        **_NAV.console_shell_ctx("skyfi", "consoles", active_sub="designer"),
        "demo_flow_active": "marketer",
        "page": page, "biz": SDB.build_business_dev_view(page),
        "as_state": as_state,
        "qs": qs, "toggle_anon": toggle_anon,
        "toggle_known": toggle_known,
        "entry_links_raw": entry_links(m),
        "sample_email": SS.sample_login_email(),
        "static_prefix": m["static"],
        "g": m})


def _render_channel_gallery(request: Request, m: dict[str, str], channel: str) -> HTMLResponse:
    from pipeline.personalization import demo_nav as NAV

    view = NAV.build_channel_gallery_view(request, "skyfi", channel, m)
    return templates.TemplateResponse(request, "demo_channel_gallery.html", view)


def _hero_image_json(request: Request, m: dict[str, str]) -> dict:
    email = _cookie_email(request)
    page = SS.build_page(request, email=email or None)
    hero = IG.resolve_hero_image(page, generate=True, tenant=SS.IMAGE_TENANT)
    receipt = hero.get("receipt") or {}
    return {
        "status": hero.get("status", "ready"),
        "url": _mount_static_url(hero.get("url"), m),
        "still_url": _mount_static_url(hero.get("still_url") or hero.get("url"), m),
        "receipt": receipt,
        "source": receipt.get("source"),
        "cost_usd": receipt.get("cost_usd") or receipt.get("estimated_cost_usd"),
        "estimated_cost_usd": receipt.get("estimated_cost_usd") or receipt.get("cost_usd"),
    }


def _register_mount(m: dict[str, str]) -> None:
    page, login, logout, dev = m["page"], m["login"], m["logout"], m["dev"]
    dev_business = m["dev_business"]
    hero_api = m["hero_api"]
    cookie_path = _cookie_path(m)

    @app.get(page, response_class=HTMLResponse)
    def skyfi_page(request: Request) -> HTMLResponse:
        return _render_skyfi(request, m)

    @app.get(m["direct_gallery"], response_class=HTMLResponse)
    def skyfi_direct_gallery(request: Request) -> HTMLResponse:
        return _render_channel_gallery(request, m, "direct")

    @app.get(m["email_gallery"], response_class=HTMLResponse)
    def skyfi_email_gallery(request: Request) -> HTMLResponse:
        return _render_channel_gallery(request, m, "email")

    @app.post(login)
    def skyfi_login(request: Request, email: str = Form(...), next: str = Form("")) -> RedirectResponse:
        nxt = _safe_next(next or m["page"], m)
        resp = RedirectResponse(nxt, status_code=303)
        resp.set_cookie(_COOKIE, email.strip(), httponly=True, samesite="lax", path=cookie_path)
        return resp

    @app.get(logout)
    def skyfi_logout(request: Request) -> RedirectResponse:
        nxt = _safe_next(request.query_params.get("next") or m["page"], m)
        resp = RedirectResponse(nxt, status_code=303)
        resp.delete_cookie(_COOKIE, path=cookie_path)
        return resp

    @app.get(dev, response_class=HTMLResponse)
    def skyfi_dev(request: Request) -> HTMLResponse:
        return _render_dev(request, m)

    @app.get(dev_business, response_class=HTMLResponse)
    def skyfi_dev_business(request: Request) -> HTMLResponse:
        return _render_dev_business(request, m)

    @app.get(hero_api)
    def skyfi_hero_image(request: Request) -> JSONResponse:
        return JSONResponse(_hero_image_json(request, m))


for _mount in MOUNTS.values():
    _register_mount(_mount)
