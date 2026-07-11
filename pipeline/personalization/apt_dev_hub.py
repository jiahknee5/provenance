"""Unified /apt/dev hub — site picker + links into each tenant's existing consoles.

Does not replace /gauntletapt/dev or /planetapt/dev; those pages stay unchanged.
"""
from __future__ import annotations

from urllib.parse import urlencode

from starlette.requests import Request

from app.gauntlet import MOUNTS as GAUNTLET_MOUNTS
from app.gauntlet import entry_links as gauntlet_entry_links
from app.planet import MOUNTS as PLANET_MOUNTS
from app.planet import entry_links as planet_entry_links
from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import planet_site as PS

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
    cookie_name = "gauntlet_email" if site["id"] == "gauntlet" else "planet_email"
    cookie = (request.cookies.get(cookie_name) or "").strip()
    if forced == "anon":
        return "anon"
    if forced == "known":
        return "known"
    return "known" if cookie else "anon"


_DEMO_HUB_PATH = "/apt/demo"


def _console_cards(m: dict[str, str], qs: str, as_state: str) -> list[dict]:
    as_q = f"{qs}&as={as_state}" if "?" in qs else f"{qs}?as={as_state}"
    cards = [
        {
            "title": "Marketer console",
            "desc": "Campaign-ops view — workflow, copy slots, image guardrails, staged YAML diffs.",
            "href": f"{m['dev_business']}{as_q}",
            "kind": "primary",
        },
        {
            "title": "Engineer console",
            "desc": "Full decision trace, 11-stage process map, plain-English story, audit ledger.",
            "href": f"{m['dev']}{as_q}",
            "kind": "primary",
        },
        {
            "title": "Image decisions",
            "desc": "Pipeline guide — intents, guardrails, pre-cached vs live inventory.",
            "href": m["image_decisions"],
            "kind": "secondary",
        },
        {
            "title": "Live replica",
            "desc": "The personalized page a visitor sees — same query params, no console chrome.",
            "href": f"{m['page']}{qs}",
            "kind": "secondary",
        },
    ]
    if m.get("ads"):
        cards.append({
            "title": "X ads grid",
            "desc": "All 12 paid-social mockups with per-variant landing links.",
            "href": m["ads"],
            "kind": "secondary",
        })
    if m.get("ads_lp"):
        cards.append({
            "title": "LP variants",
            "desc": "Compact landing-page previews for every ad variant.",
            "href": m["ads_lp"],
            "kind": "secondary",
        })
    if m.get("ad_lp"):
        cards.append({
            "title": "X ads grid",
            "desc": "12-variant catalog with message-match landing URLs.",
            "href": m["ad_lp"],
            "kind": "secondary",
        })
    return cards


def build_hub_view(request: Request) -> dict:
    site_id = request.query_params.get("site", _DEFAULT).strip().lower()
    site = _BY_ID.get(site_id, _BY_ID[_DEFAULT])
    m = site["mounts"]
    as_state = _as_state(request, site)
    qs = _qs(request, site=site["id"], drop=("as",))
    toggle_anon = _HUB_PATH + _qs(request, site=site["id"], as_state="anon", drop=("as",))
    toggle_known = _HUB_PATH + _qs(request, site=site["id"], as_state="known", drop=("as",))
    site_toggles = [
        {
            "id": s["id"],
            "name": s["name"],
            "domain": s["domain"],
            "href": _HUB_PATH + _qs(request, site=s["id"], as_state=as_state, drop=("as",)),
            "on": s["id"] == site["id"],
        }
        for s in _SITES
    ]
    sample_email = site["sample_email"]()
    return {
        "hub_path": _HUB_PATH,
        "demo_hub_path": _DEMO_HUB_PATH,
        "site": site,
        "site_id": site["id"],
        "site_name": site["name"],
        "site_domain": site["domain"],
        "site_tagline": site["tagline"],
        "site_toggles": site_toggles,
        "as_state": as_state,
        "qs": qs,
        "toggle_anon": toggle_anon,
        "toggle_known": toggle_known,
        "sample_email": sample_email,
        "entry_links": site["entry_links"](m),
        "console_cards": _console_cards(m, qs, as_state),
        "g": m,
    }
