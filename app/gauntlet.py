"""GauntletAI replica routes — the live personalized site + its /dev decisions page.

  GET  /gauntlet         — pixel-faithful gauntletai.com replica; every copy block is a
                           personalization slot (entry UTM/referrer × IP tier × login/CRM)
  POST /gauntlet/login   — email form in the replica's nav → session cookie (synthetic
                           cohort emails unlock the CRM path; any work email escalates
                           via first-party domain resolution)
  GET  /gauntlet/logout  — clears the cookie
  GET  /dev              — the decisioning companion
  GET  /dev/business     — marketing/sales narrative (same state as /dev)
  GET  /dev/image-decisions — hero image decision guide
       (aliases: /image-decisions, /gauntlet/image-decisions)

  Portal mount (johnnycchung.com/gauntletapt via Vercel rewrite):
  GET  /gauntletapt, /gauntletapt/login, /gauntletapt/logout, /gauntletapt/dev,
       /gauntletapt/dev/business, /gauntletapt/dev/image-decisions
       (alias: /gauntletapt/image-decisions)

State lives entirely in (query params + one cookie), so both pages are rebuilt
deterministically per request — CONSTITUTION reproducibility, no server-side sessions.
"""
from __future__ import annotations

from urllib.parse import urlencode

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.server import app, templates
from pipeline.personalization import gauntlet_dev_business as GDB
from pipeline.personalization import gauntlet_image_decisions as GID
from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_gen as IG

_COOKIE = "gauntlet_email"

# Legacy paths for local dev + tests; portal mount for johnnycchung.com/gauntletapt.
MOUNTS: dict[str, dict[str, str]] = {
    "legacy": {
        "page": "/gauntlet",
        "login": "/gauntlet/login",
        "logout": "/gauntlet/logout",
        "dev": "/dev",
        "dev_business": "/dev/business",
        "ad": "/gauntlet/ad",
        "ad_lp": "/gauntlet/ad-lp",
        "image_decisions": "/dev/image-decisions",
        "static": "/static",
        "hero_api": "/api/gauntlet/hero-image",
    },
    "portal": {
        "page": "/gauntletapt",
        "login": "/gauntletapt/login",
        "logout": "/gauntletapt/logout",
        "dev": "/gauntletapt/dev",
        "dev_business": "/gauntletapt/dev/business",
        "ad": "/gauntletapt/ad",
        "ad_lp": "/gauntletapt/ad-lp",
        "image_decisions": "/gauntletapt/dev/image-decisions",
        "static": "/gauntletapt/static",
        "hero_api": "/gauntletapt/api/hero-image",
    },
}


def entry_links(m: dict[str, str]) -> list[tuple[str, str]]:
    page = m["page"]
    return [
        ("X ads grid", m["ad_lp"]),
        ("Ad", f"{page}?utm_source=x&utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09"),
        ("Email", f"{page}?utm_source=hubspot&utm_medium=email&utm_campaign=cohort-april&e="
                  + GS.sample_magic_token()),
        ("Search", f"{page}?ref=google"),
        ("Direct", page),
    ]


# Showcase card still links to the legacy mount.
ENTRY_LINKS = entry_links(MOUNTS["legacy"])


def _cookie_email(request: Request) -> str:
    return (request.cookies.get(_COOKIE) or "").strip()


def _qs(request: Request, drop: tuple[str, ...] = ()) -> str:
    pairs = [(k, v) for k, v in request.query_params.multi_items() if k not in drop]
    return ("?" + urlencode(pairs)) if pairs else ""


def _cookie_path(m: dict[str, str]) -> str:
    # Portal /dev lives under the mount prefix; legacy /dev is at root — cookie must
    # reach both the page and its /dev companion.
    if m["dev"].startswith(m["page"]):
        return m["page"]
    return "/"


def _safe_next(nxt: str, m: dict[str, str]) -> str:
    page = m["page"]
    if not nxt.startswith(page):
        return page
    return nxt


def _mount_static_url(url: str | None, m: dict[str, str]) -> str | None:
    """Portal mount serves assets under /gauntletapt/static, not /static."""
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
    return {**page, "hero_image": hero}


def _render_gauntlet(request: Request, m: dict[str, str]) -> HTMLResponse:
    email = _cookie_email(request)
    page = _page_with_mount_urls(GS.build_page(request, email=email or None), m)
    page["nav"]["ad_lp"] = m["ad_lp"]
    return templates.TemplateResponse(request, "gauntlet_site.html", {
        "page": page, "qs": _qs(request), "dev_qs": _qs(request), "g": m,
        "hero_api_url": m["hero_api"],
    })


def _render_ad_lp(request: Request, m: dict[str, str]) -> HTMLResponse:
    sections = []
    for sec in GS.ad_grid_sections():
        variants = []
        for v in sec["variants"]:
            variants.append({
                "variant": v,
                "landing_url": GS.variant_landing_url(v, m["page"]),
                "generic_hero": GS.generic_hero_headline(),
                "personal_hero": GS.variant_hero_headline(v),
            })
        sections.append({"label": sec["label"], "category": sec["category"], "variants": variants})
    return templates.TemplateResponse(request, "gauntlet_ad_lp.html", {
        "sections": sections,
        "generic_hero": GS.generic_hero_headline(),
        "g": m,
    })


def _render_ad(request: Request, m: dict[str, str]) -> HTMLResponse:
    campaign = request.query_params.get("campaign", "").strip().lower()
    vid = request.query_params.get("v", "").strip().lower()
    variant = None
    if vid and vid in GS.AD_BY_VARIANT_ID:
        variant = GS.AD_BY_VARIANT_ID[vid]
    elif campaign and campaign in GS.AD_BY_CAMPAIGN:
        variant = GS.AD_BY_CAMPAIGN[campaign]
    if variant is None:
        return RedirectResponse(m["ad_lp"], status_code=302)
    return templates.TemplateResponse(request, "gauntlet_ad.html", {
        "variant": variant,
        "landing_url": GS.variant_landing_url(variant, m["page"]),
        "g": m,
    })


def _dev_email_and_page(request: Request, m: dict[str, str]) -> tuple[str, str | None, dict, str]:
    """Shared state for /dev and /dev/business — same query params + cookie."""
    as_state = request.query_params.get("as", "")
    cookie = _cookie_email(request)
    if as_state == "anon":
        email = None
    elif as_state == "known":
        email = cookie or GS.sample_login_email()
    else:
        email = cookie or None
    page = _page_with_mount_urls(GS.build_page(request, email=email), m)
    qs = _qs(request, drop=("as",))
    resolved = as_state or ("known" if email else "anon")
    return resolved, email, page, qs


def _dev_toggles(dev_path: str, qs: str, as_state: str) -> tuple[str, str]:
    sep = "&" if qs else "?"
    return f"{dev_path}{qs}{sep}as=anon", f"{dev_path}{qs}{sep}as=known"


def _render_dev(request: Request, m: dict[str, str]) -> HTMLResponse:
    as_state, email, page, qs = _dev_email_and_page(request, m)
    toggle_anon, toggle_known = _dev_toggles(m["dev"], qs, as_state)
    return templates.TemplateResponse(request, "gauntlet_dev.html", {
        "page": page, "pmap": GS.process_map(page),
        "as_state": as_state,
        "qs": qs, "toggle_anon": toggle_anon,
        "toggle_known": toggle_known,
        "entry_links_raw": entry_links(m),
        "sample_email": GS.sample_login_email(),
        "static_prefix": m["static"],
        "g": m})


def _render_image_decisions(request: Request, m: dict[str, str]) -> HTMLResponse:
    view = GID.build_image_decisions_view(
        page_path=m["page"],
        dev_path=m["dev"],
        static_prefix=m["static"],
    )
    return templates.TemplateResponse(request, "gauntlet_image_decisions.html", {
        "g": m,
        "static_prefix": m["static"],
        **view,
    })


def _render_dev_business(request: Request, m: dict[str, str]) -> HTMLResponse:
    as_state, email, page, qs = _dev_email_and_page(request, m)
    biz_path = m["dev_business"]
    toggle_anon, toggle_known = _dev_toggles(biz_path, qs, as_state)
    return templates.TemplateResponse(request, "gauntlet_dev_business.html", {
        "page": page, "biz": GDB.build_business_dev_view(page),
        "as_state": as_state,
        "qs": qs, "toggle_anon": toggle_anon,
        "toggle_known": toggle_known,
        "entry_links_raw": entry_links(m),
        "sample_email": GS.sample_login_email(),
        "static_prefix": m["static"],
        "g": m})


def _hero_image_json(request: Request, m: dict[str, str]) -> dict:
    email = _cookie_email(request)
    page = GS.build_page(request, email=email or None)
    hero = IG.resolve_hero_image(page, generate=True)
    receipt = hero.get("receipt") or {}
    return {
        "status": hero.get("status", "ready"),
        "url": _mount_static_url(hero.get("url"), m),
        "receipt": receipt,
        "source": receipt.get("source"),
    }


def _register_mount(m: dict[str, str]) -> None:
    page, login, logout, dev = m["page"], m["login"], m["logout"], m["dev"]
    dev_business = m["dev_business"]
    ad, ad_lp = m["ad"], m["ad_lp"]
    image_decisions = m["image_decisions"]
    hero_api = m["hero_api"]
    cookie_path = _cookie_path(m)

    @app.get(page, response_class=HTMLResponse)
    def gauntlet_page(request: Request) -> HTMLResponse:
        return _render_gauntlet(request, m)

    @app.get(ad, response_class=HTMLResponse)
    def gauntlet_ad(request: Request) -> HTMLResponse:
        return _render_ad(request, m)

    @app.get(ad_lp, response_class=HTMLResponse)
    def gauntlet_ad_lp(request: Request) -> HTMLResponse:
        return _render_ad_lp(request, m)

    @app.post(login)
    def gauntlet_login(request: Request, email: str = Form(...), next: str = Form("")) -> RedirectResponse:
        nxt = _safe_next(next or m["page"], m)
        resp = RedirectResponse(nxt, status_code=303)
        resp.set_cookie(_COOKIE, email.strip(), httponly=True, samesite="lax", path=cookie_path)
        return resp

    @app.get(logout)
    def gauntlet_logout(request: Request) -> RedirectResponse:
        nxt = _safe_next(request.query_params.get("next") or m["page"], m)
        resp = RedirectResponse(nxt, status_code=303)
        resp.delete_cookie(_COOKIE, path=cookie_path)
        return resp

    @app.get(dev, response_class=HTMLResponse)
    def gauntlet_dev(request: Request) -> HTMLResponse:
        return _render_dev(request, m)

    @app.get(dev_business, response_class=HTMLResponse)
    def gauntlet_dev_business(request: Request) -> HTMLResponse:
        return _render_dev_business(request, m)

    @app.get(image_decisions, response_class=HTMLResponse)
    def gauntlet_image_decisions(request: Request) -> HTMLResponse:
        return _render_image_decisions(request, m)

    @app.get(hero_api)
    def gauntlet_hero_image(request: Request) -> JSONResponse:
        return JSONResponse(_hero_image_json(request, m))

    # Legacy portal API path — kept for bookmarks/tests; portal HTML uses mount-prefixed path.
    if hero_api.startswith(m["page"] + "/api/"):
        legacy_api = "/api" + hero_api[len(m["page"]):]
        @app.get(legacy_api)
        def gauntlet_hero_image_legacy(request: Request) -> JSONResponse:
            return JSONResponse(_hero_image_json(request, m))


for _mount in MOUNTS.values():
    _register_mount(_mount)


# Root-level /ad-lp alias (links to legacy /gauntlet landing URLs).
@app.get("/ad-lp", response_class=HTMLResponse)
def ad_lp_root(request: Request) -> HTMLResponse:
    return _render_ad_lp(request, MOUNTS["legacy"])


# Legacy alias — /gauntlet/dev/business mirrors /dev/business (same handler).
@app.get("/gauntlet/dev/business", response_class=HTMLResponse)
def gauntlet_dev_business_legacy_alias(request: Request) -> HTMLResponse:
    return _render_dev_business(request, MOUNTS["legacy"])


# Pre-/dev aliases for the image-decisions guide — canonical is {dev}/image-decisions.
@app.get("/image-decisions", response_class=HTMLResponse)
def image_decisions_root_alias(request: Request) -> HTMLResponse:
    return _render_image_decisions(request, MOUNTS["legacy"])


@app.get("/gauntlet/image-decisions", response_class=HTMLResponse)
def gauntlet_image_decisions_legacy_alias(request: Request) -> HTMLResponse:
    return _render_image_decisions(request, MOUNTS["legacy"])


@app.get("/gauntletapt/image-decisions", response_class=HTMLResponse)
def gauntlet_image_decisions_portal_alias(request: Request) -> HTMLResponse:
    return _render_image_decisions(request, MOUNTS["portal"])
