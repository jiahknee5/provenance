"""/apt/dev — "Preview as visitor" (W8-A menu merge).

Formerly a console-launcher menu (cards into each tenant's /dev surfaces); that
duplicated the apt sidebar item-for-item, so the cards are gone. The page is now
the PREVIEW step of the marketer workflow: pick an identity, simulate an entry
channel, or open the live page. Consoles stay reachable from the sidebar
("Page sections") and the console's own "Technical view →" link.
"""
from __future__ import annotations

from urllib.parse import urlencode

from starlette.requests import Request

from app.gauntlet import MOUNTS as GAUNTLET_MOUNTS
from app.gauntlet import entry_links as gauntlet_entry_links
from app.planet import MOUNTS as PLANET_MOUNTS
from app.planet import entry_links as planet_entry_links
from app.skyfi import MOUNTS as SKYFI_MOUNTS
from app.skyfi import entry_links as skyfi_entry_links
from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import planet_site as PS
from pipeline.personalization import skyfi_site as SS

_SITES: tuple[dict, ...] = (
    {
        "id": "gauntlet",
        "name": "GauntletAI",
        "domain": "gauntletai.com",
        "tagline": "AI hiring fellowship — entry channel × IP tier × CRM identity.",
        "sample_email": GS.sample_login_email,
        "entry_links": gauntlet_entry_links,
        "mounts": GAUNTLET_MOUNTS["portal"],
    },
    {
        "id": "planet",
        "name": "Planet",
        "domain": "planet.com",
        "tagline": "Earth observation — adds a location signal on top of channel, IP, and identity.",
        "sample_email": PS.sample_login_email,
        "entry_links": planet_entry_links,
        "mounts": PLANET_MOUNTS["portal"],
    },
    {
        "id": "skyfi",
        "name": "SkyFi",
        "domain": "skyfi.com",
        "tagline": "On-demand satellite imagery — location × industry at basin scale; "
                   "exact-AOI only when declared first-party.",
        "sample_email": SS.sample_login_email,
        "entry_links": skyfi_entry_links,
        "mounts": SKYFI_MOUNTS["portal"],
    },
)
_BY_ID = {s["id"]: s for s in _SITES}
_DEFAULT = "gauntlet"
_HUB_PATH = "/apt/dev"


def _qs(request: Request, *, site: str, as_state: str | None = None, drop: tuple[str, ...] = ()) -> str:
    skip = {"site", "as", *drop}
    pairs: list[tuple[str, str]] = [("site", site)]
    if as_state:
        pairs.append(("as", as_state))
    for k, v in request.query_params.multi_items():
        if k not in skip:
            pairs.append((k, v))
    return "?" + urlencode(pairs)


def _as_state(request: Request, site: dict) -> str:
    forced = request.query_params.get("as", "").strip()
    cookie_name = f"{site['id']}_email"
    cookie = (request.cookies.get(cookie_name) or "").strip()
    if forced == "anon":
        return "anon"
    if forced == "known":
        return "known"
    return "known" if cookie else "anon"


_DEMO_HUB_PATH = "/apt/demo"


def build_hub_view(request: Request) -> dict:
    from pipeline.personalization import demo_nav as NAV

    site_id = request.query_params.get("site", _DEFAULT).strip().lower()
    site = _BY_ID.get(site_id, _BY_ID[_DEFAULT])
    m = site["mounts"]
    as_state = _as_state(request, site)
    qs = _qs(request, site=site["id"], drop=("as",))
    toggle_anon = _HUB_PATH + _qs(request, site=site["id"], as_state="anon", drop=("as",))
    toggle_known = _HUB_PATH + _qs(request, site=site["id"], as_state="known", drop=("as",))
    # Website dropdown switches the tenant while preserving the identity preview.
    switch_hrefs = {
        s["id"]: _HUB_PATH + _qs(request, site=s["id"], as_state=as_state, drop=("as",))
        for s in _SITES
    }
    shell = NAV.console_shell_ctx(site["id"], "consoles", switch_hrefs=switch_hrefs, active_sub="hub")
    sample_email = site["sample_email"]()
    return {
        **shell,
        "hub_path": _HUB_PATH,
        "demo_hub_path": _DEMO_HUB_PATH,
        "site_name": site["name"],
        "site_domain": site["domain"],
        "site_tagline": site["tagline"],
        "as_state": as_state,
        "toggle_anon": toggle_anon,
        "toggle_known": toggle_known,
        "sample_email": sample_email,
        "entry_links": site["entry_links"](m),
        "live_href": f"{m['page']}{qs}",
        "g": m,
    }
