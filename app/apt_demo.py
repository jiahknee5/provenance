"""Workspace stage pages (S0/S1/S2/S5 — IA-MAP, PRD-MARKETER-IA).

  GET /apt/demo             — workspace Home: status + journey J1 checklist (R43)
  GET /apt/connect          — S1 Connect: websites & install status
  GET /apt/channel/{name}   — S2 channel setup page, one data-driven template (R42);
                              sidebar channel items land here, never on a landing
                              page or gallery (those are marked Preview drills)
  GET /apt/launch           — S5 Launch: staged-changes review + simulated apply (R41)
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.server import app, templates
from pipeline.personalization import channel_setup as CS
from pipeline.personalization import demo_nav as NAV
from pipeline.personalization import sections as SEC


def _site_from(request: Request) -> str:
    site = request.query_params.get("site", "").strip().lower()
    return site if site in NAV.TENANTS else NAV.TENANTS[0]


@app.get("/apt/demo", response_class=HTMLResponse)
def apt_demo_sitemap(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "apt_demo_sitemap.html", NAV.build_sitemap_view(request))


@app.get("/apt/channel/{channel}", response_class=HTMLResponse)
def apt_channel_setup(request: Request, channel: str) -> HTMLResponse:
    try:
        ctx = CS.build_channel_view(request, channel)
    except KeyError:
        qs = f"?{request.query_params}" if request.query_params else ""
        return RedirectResponse(f"/apt/demo{qs}", status_code=302)
    return templates.TemplateResponse(request, "apt_channel.html", ctx)


@app.get("/apt/connect", response_class=HTMLResponse)
def apt_connect(request: Request) -> HTMLResponse:
    site = _site_from(request)
    websites = []
    for t in NAV.TENANTS:
        meta = NAV._TENANT_META[t]
        bg, ch = NAV._TENANT_LOGO[t]
        m = NAV._mounts_for(t)
        websites.append({
            "id": t, "name": meta["name"], "domain": meta["domain"],
            "logo_bg": bg, "logo_ch": ch,
            "sections": len(SEC.list_sections(t)),
            "channels_href": f"/apt/channel/direct?site={t}",
            "live_href": m["page"],
            "active": t == site,
        })
    return templates.TemplateResponse(request, "apt_connect.html", {
        **NAV.console_shell_ctx(site, "live", active_sub="connect"),
        "websites": websites,
        "site": site,
    })


@app.get("/apt/launch", response_class=HTMLResponse)
def apt_launch(request: Request) -> HTMLResponse:
    site = _site_from(request)
    m = NAV._mounts_for(site)
    meta = NAV._TENANT_META[site]
    return templates.TemplateResponse(request, "apt_launch.html", {
        **NAV.console_shell_ctx(site, "launch", active_sub="launch"),
        "site": site,
        "site_name": meta["name"],
        "site_domain": meta["domain"],
        "designer_href": m["dev_business"],
        "live_href": m["page"],
    })
