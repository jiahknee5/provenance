"""Planet (planet.com) replica routes — the live personalized site + its /dev decisions pages.

  GET  /planet          — planet.com-style replica; every copy block is a personalization
                          slot (entry UTM/referrer × IP tier × LOCATION × login/CRM)
  POST /planet/login    — email form in the replica's nav → session cookie (synthetic
                          customer-cohort emails unlock the CRM path; any work email
                          escalates via first-party domain resolution)
  GET  /planet/logout   — clears the cookie
  GET  /planet/dev      — the decisioning companion (incl. the Location signal stage)
  GET  /planet/dev/business — marketing/sales narrative (same state as /planet/dev)
  GET  /planet/dev/image-decisions — hero image decision guide
  GET  /planet/ads      — JUST the X ad variations: all 12 full X-post mockups
  GET  /planet/ads-lp   — the landing-page variations in small form: 12 compact LP previews
  GET  /planet/ad?v=…   — one X ad mockup (no match → redirect to /planet/ads);
                          /planet/ads?v=… renders the same single mockup

  Portal mount (johnnycchung.com/planetapt via Vercel rewrite):
  GET  /planetapt, /planetapt/login, /planetapt/logout, /planetapt/dev,
       /planetapt/dev/business, /planetapt/dev/image-decisions,
       /planetapt/ads, /planetapt/ads-lp, /planetapt/ad
       (alias: /planetapt/image-decisions)

State lives entirely in (query params + one cookie), so both pages are rebuilt
deterministically per request — CONSTITUTION reproducibility, no server-side sessions.
"""
from __future__ import annotations

from urllib.parse import urlencode

from fastapi import Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.server import app, templates
from pipeline.personalization import ad_explainers as AE
from pipeline.personalization import image_gen as IG
from pipeline.personalization import planet_dev_business as PDB
from pipeline.personalization import planet_image_decisions as PID
from pipeline.personalization import planet_site as PS

_COOKIE = "planet_email"

# Legacy paths for local dev + tests; portal mount for johnnycchung.com/planetapt.
MOUNTS: dict[str, dict[str, str]] = {
    "legacy": {
        "page": "/planet",
        "login": "/planet/login",
        "logout": "/planet/logout",
        "dev": "/planet/dev",
        "dev_business": "/planet/dev/business",
        "ad": "/planet/ad",
        "ads": "/planet/ads",
        "ads_lp": "/planet/ads-lp",
        "direct_gallery": "/planet/direct",
        "email_gallery": "/planet/email",
        "image_decisions": "/planet/dev/image-decisions",
        "static": "/static",
        "hero_api": "/api/planet/hero-image",
    },
    "portal": {
        "page": "/planetapt",
        "login": "/planetapt/login",
        "logout": "/planetapt/logout",
        "dev": "/planetapt/dev",
        "dev_business": "/planetapt/dev/business",
        "ad": "/planetapt/ad",
        "ads": "/planetapt/ads",
        "ads_lp": "/planetapt/ads-lp",
        "direct_gallery": "/planetapt/direct",
        "email_gallery": "/planetapt/email",
        "image_decisions": "/planetapt/dev/image-decisions",
        "static": "/planetapt/static",
        "hero_api": "/planetapt/api/hero-image",
    },
}


def entry_links(m: dict[str, str]) -> list[tuple[str, str]]:
    page = m["page"]
    return [
        ("X ads", m["ads"]),
        ("LP variants", m["ads_lp"]),
        ("Ad", f"{page}?utm_source=x&utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01"),
        ("Email", f"{page}?utm_source=hubspot&utm_medium=email&utm_campaign=crisis-responders&e="
                  + PS.sample_magic_token()),
        ("Search", f"{page}?ref=google"),
        ("Direct", page),
        ("Direct gallery", m["direct_gallery"]),
        ("Email gallery", m["email_gallery"]),
    ]


# Showcase card still links to the legacy mount.
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
    """Portal mount serves assets under /planetapt/static, not /static."""
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
    if hero.get("motion_url"):
        hero["motion_url"] = _mount_static_url(hero["motion_url"], m)
    motion_receipt = hero.get("motion_receipt") or {}
    if motion_receipt.get("frames"):
        frames = []
        for fr in motion_receipt["frames"]:
            fr = dict(fr)
            if fr.get("image_url"):
                fr["image_url"] = _mount_static_url(fr["image_url"], m)
            frames.append(fr)
        motion_receipt = {**motion_receipt, "frames": frames}
        hero["motion_receipt"] = motion_receipt
    dev = dict(hero.get("dev") or {})
    if dev.get("motion", {}).get("frames"):
        mdev = dict(dev["motion"])
        mframes = []
        for fr in mdev["frames"]:
            fr = dict(fr)
            if fr.get("image_url"):
                fr["image_url"] = _mount_static_url(fr["image_url"], m)
            mframes.append(fr)
        mdev["frames"] = mframes
        if mdev.get("url"):
            mdev["url"] = _mount_static_url(mdev["url"], m)
        dev["motion"] = mdev
        hero["dev"] = dev
    return {**page, "hero_image": hero}


def _render_planet(request: Request, m: dict[str, str]) -> HTMLResponse:
    email = _cookie_email(request)
    page = _page_with_mount_urls(PS.build_page(request, email=email or None), m)
    page["nav"]["ads"] = m["ads"]
    page["nav"]["ads_lp"] = m["ads_lp"]
    return templates.TemplateResponse(request, "planet_site.html", {
        "page": page, "qs": _qs(request), "dev_qs": _qs(request), "g": m,
        "hero_api_url": m["hero_api"],
    })


def _resolve_single_variant(request: Request) -> dict | None:
    campaign = request.query_params.get("campaign", "").strip().lower()
    vid = request.query_params.get("v", "").strip().lower()
    if vid and vid in PS.AD_BY_VARIANT_ID:
        return PS.AD_BY_VARIANT_ID[vid]
    if campaign and campaign in PS.AD_BY_CAMPAIGN:
        return PS.AD_BY_CAMPAIGN[campaign]
    return None


def _render_ad(request: Request, m: dict[str, str]) -> HTMLResponse:
    """Single X ad mockup — ?v= / ?campaign=; no match → redirect to the /ads grid."""
    variant = _resolve_single_variant(request)
    if variant is None:
        return RedirectResponse(m["ads"], status_code=302)
    return templates.TemplateResponse(request, "planet_ad.html", {
        "variant": variant,
        "landing_url": PS.variant_landing_url(variant, m["page"]),
        "explainer": AE.explainer_for("planet", variant, page_path=m["page"],
                                      dev_path=m["dev"]),
        "g": m,
    })


def _render_ads(request: Request, m: dict[str, str]) -> HTMLResponse:
    """JUST the X ad variations — a grid of all 12 full X-post mockups.
    ?v= / ?campaign= keeps single-ad rendering working on this path too."""
    variant = _resolve_single_variant(request)
    if variant is not None:
        return templates.TemplateResponse(request, "planet_ad.html", {
            "variant": variant,
            "landing_url": PS.variant_landing_url(variant, m["page"]),
            "explainer": AE.explainer_for("planet", variant, page_path=m["page"],
                                          dev_path=m["dev"]),
            "g": m,
        })
    sections = []
    for sec in PS.ad_grid_sections():
        variants = []
        for v in sec["variants"]:
            variants.append({
                "variant": v,
                "landing_url": PS.variant_landing_url(v, m["page"]),
                "single_url": f"{m['ad']}?v={v['variant_id']}",
                "explainer": AE.explainer_for("planet", v, page_path=m["page"],
                                              dev_path=m["dev"]),
            })
        sections.append({"label": sec["label"], "category": sec["category"], "variants": variants})
    return templates.TemplateResponse(request, "planet_ads.html", {
        "demo_flow_active": "scenario",
        "sections": sections,
        "demo_hub_path": "/apt/demo",
        "g": m,
    })


def _render_ads_lp(request: Request, m: dict[str, str]) -> HTMLResponse:
    """The landing-page variations in SMALL FORM — 12 compact LP preview cards."""
    sections = []
    for sec in PS.ad_grid_sections():
        variants = []
        for v in sec["variants"]:
            vp = v["page"]
            order = vp.get("order") or PS.ORDER_BY_AUDIENCE[v["audience"]]
            variants.append({
                "variant": v,
                "landing_url": PS.variant_landing_url(v, m["page"]),
                "generic_hero": PS.generic_hero_headline(),
                "personal_hero": PS.variant_hero_headline(v),
                "sub": vp["sub"],
                "order": order,
                "emphasis": vp.get("compare_emphasis") or "—",
                "cta_primary": vp["cta_primary"],
                "single_url": f"{m['ad']}?v={v['variant_id']}",
                "explainer": AE.explainer_for("planet", v, page_path=m["page"],
                                              dev_path=m["dev"]),
            })
        sections.append({"label": sec["label"], "category": sec["category"], "variants": variants})
    return templates.TemplateResponse(request, "planet_ad_lp.html", {
        "demo_flow_active": "scenario",
        "sections": sections,
        "generic_hero": PS.generic_hero_headline(),
        "default_order": PS.DEFAULT_ORDER,
        "g": m,
    })


def _dev_email_and_page(request: Request, m: dict[str, str]) -> tuple[str, str | None, dict, str]:
    """Shared state for /dev and /dev/business — same query params + cookie."""
    as_state = request.query_params.get("as", "")
    cookie = _cookie_email(request)
    if as_state == "anon":
        email = None
    elif as_state == "known":
        email = cookie or PS.sample_login_email()
    else:
        email = cookie or None
    page = _page_with_mount_urls(PS.build_page(request, email=email), m)
    qs = _qs(request, drop=("as",))
    resolved = as_state or ("known" if email else "anon")
    return resolved, email, page, qs


def _dev_toggles(dev_path: str, qs: str, as_state: str) -> tuple[str, str]:
    sep = "&" if qs else "?"
    return f"{dev_path}{qs}{sep}as=anon", f"{dev_path}{qs}{sep}as=known"


def _render_dev(request: Request, m: dict[str, str]) -> HTMLResponse:
    as_state, email, page, qs = _dev_email_and_page(request, m)
    toggle_anon, toggle_known = _dev_toggles(m["dev"], qs, as_state)
    from pipeline.personalization import demo_nav as _NAV
    return templates.TemplateResponse(request, "planet_dev.html", {
        **_NAV.console_shell_ctx("planet", "consoles", active_sub="engineer"),
        "demo_flow_active": "engineer",
        "page": page, "pmap": PS.process_map(page),
        "as_state": as_state,
        "qs": qs, "toggle_anon": toggle_anon,
        "toggle_known": toggle_known,
        "entry_links_raw": entry_links(m),
        "sample_email": PS.sample_login_email(),
        "static_prefix": m["static"],
        "g": m})


def _render_image_decisions(request: Request, m: dict[str, str]) -> HTMLResponse:
    view = PID.build_image_decisions_view(
        page_path=m["page"],
        dev_path=m["dev"],
        static_prefix=m["static"],
    )
    return templates.TemplateResponse(request, "planet_image_decisions.html", {
        "g": m,
        "static_prefix": m["static"],
        **view,
    })


def _render_dev_business(request: Request, m: dict[str, str]) -> HTMLResponse:
    as_state, email, page, qs = _dev_email_and_page(request, m)
    biz_path = m["dev_business"]
    toggle_anon, toggle_known = _dev_toggles(biz_path, qs, as_state)
    from pipeline.personalization import demo_nav as _NAV
    return templates.TemplateResponse(request, "planet_dev_business.html", {
        **_NAV.console_shell_ctx("planet", "consoles", active_sub="designer"),
        "demo_flow_active": "marketer",
        "page": page, "biz": PDB.build_business_dev_view(page),
        "as_state": as_state,
        "qs": qs, "toggle_anon": toggle_anon,
        "toggle_known": toggle_known,
        "entry_links_raw": entry_links(m),
        "sample_email": PS.sample_login_email(),
        "static_prefix": m["static"],
        "g": m})


def _render_channel_gallery(request: Request, m: dict[str, str], channel: str) -> HTMLResponse:
    from pipeline.personalization import demo_nav as NAV

    view = NAV.build_channel_gallery_view(request, "planet", channel, m)
    return templates.TemplateResponse(request, "demo_channel_gallery.html", view)


def _hero_image_json(request: Request, m: dict[str, str]) -> dict:
    email = _cookie_email(request)
    page = PS.build_page(request, email=email or None)
    hero = IG.resolve_hero_image(page, generate=True, tenant=PS.IMAGE_TENANT)
    receipt = hero.get("receipt") or {}
    motion_receipt = hero.get("motion_receipt") or {}
    return {
        "status": hero.get("status", "ready"),
        "url": _mount_static_url(hero.get("url"), m),
        "still_url": _mount_static_url(hero.get("still_url") or hero.get("url"), m),
        "motion_url": _mount_static_url(hero.get("motion_url"), m),
        "motion_status": hero.get("motion_status"),
        "motion_type": hero.get("motion_type"),
        "receipt": receipt,
        "motion_receipt": motion_receipt,
        "source": receipt.get("source"),
        "cost_usd": receipt.get("cost_usd") or receipt.get("estimated_cost_usd"),
        "estimated_cost_usd": receipt.get("estimated_cost_usd") or receipt.get("cost_usd"),
    }


def _register_mount(m: dict[str, str]) -> None:
    page, login, logout, dev = m["page"], m["login"], m["logout"], m["dev"]
    dev_business = m["dev_business"]
    ad, ads, ads_lp = m["ad"], m["ads"], m["ads_lp"]
    image_decisions = m["image_decisions"]
    hero_api = m["hero_api"]
    cookie_path = _cookie_path(m)

    @app.get(page, response_class=HTMLResponse)
    def planet_page(request: Request) -> HTMLResponse:
        return _render_planet(request, m)

    @app.get(ad, response_class=HTMLResponse)
    def planet_ad(request: Request) -> HTMLResponse:
        return _render_ad(request, m)

    @app.get(ads, response_class=HTMLResponse)
    def planet_ads(request: Request) -> HTMLResponse:
        return _render_ads(request, m)

    @app.get(ads_lp, response_class=HTMLResponse)
    def planet_ads_lp(request: Request) -> HTMLResponse:
        return _render_ads_lp(request, m)

    @app.get(m["direct_gallery"], response_class=HTMLResponse)
    def planet_direct_gallery(request: Request) -> HTMLResponse:
        return _render_channel_gallery(request, m, "direct")

    @app.get(m["email_gallery"], response_class=HTMLResponse)
    def planet_email_gallery(request: Request) -> HTMLResponse:
        return _render_channel_gallery(request, m, "email")

    @app.post(login)
    def planet_login(request: Request, email: str = Form(...), next: str = Form("")) -> RedirectResponse:
        nxt = _safe_next(next or m["page"], m)
        resp = RedirectResponse(nxt, status_code=303)
        resp.set_cookie(_COOKIE, email.strip(), httponly=True, samesite="lax", path=cookie_path)
        return resp

    @app.get(logout)
    def planet_logout(request: Request) -> RedirectResponse:
        nxt = _safe_next(request.query_params.get("next") or m["page"], m)
        resp = RedirectResponse(nxt, status_code=303)
        resp.delete_cookie(_COOKIE, path=cookie_path)
        return resp

    @app.get(dev, response_class=HTMLResponse)
    def planet_dev(request: Request) -> HTMLResponse:
        return _render_dev(request, m)

    @app.get(dev_business, response_class=HTMLResponse)
    def planet_dev_business(request: Request) -> HTMLResponse:
        return _render_dev_business(request, m)

    @app.get(image_decisions, response_class=HTMLResponse)
    def planet_image_decisions(request: Request) -> HTMLResponse:
        return _render_image_decisions(request, m)

    @app.get(hero_api)
    def planet_hero_image(request: Request) -> JSONResponse:
        return JSONResponse(_hero_image_json(request, m))

    # Legacy portal API path — kept for bookmarks/tests; portal HTML uses mount-prefixed path.
    if hero_api.startswith(m["page"] + "/api/"):
        legacy_api = "/api" + hero_api[len(m["page"]):]

        @app.get(legacy_api)
        def planet_hero_image_legacy(request: Request) -> JSONResponse:
            return JSONResponse(_hero_image_json(request, m))


for _mount in MOUNTS.values():
    _register_mount(_mount)


# Pre-/dev alias for the image-decisions guide — canonical is {dev}/image-decisions.
@app.get("/planet/image-decisions", response_class=HTMLResponse)
def planet_image_decisions_legacy_alias(request: Request) -> HTMLResponse:
    return _render_image_decisions(request, MOUNTS["legacy"])


@app.get("/planetapt/image-decisions", response_class=HTMLResponse)
def planet_image_decisions_portal_alias(request: Request) -> HTMLResponse:
    return _render_image_decisions(request, MOUNTS["portal"])
