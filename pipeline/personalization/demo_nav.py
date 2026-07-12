"""Demo navigation — scenario catalog loader + sitemap view builder.

rules/demo_scenarios.yaml holds curated entry scenarios for the visitor tour plane.
This module resolves magic-token templates and mount prefixes; it does not alter
personalization logic (classify_entry / build_page stay unchanged).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import yaml
from starlette.requests import Request

from app.gauntlet import MOUNTS as GAUNTLET_MOUNTS
from app.planet import MOUNTS as PLANET_MOUNTS
from pipeline.personalization import cohort as CO
from pipeline.personalization import design_prompts as DP
from pipeline.personalization import planet_cohort as PCO

SCENARIOS_PATH = Path(__file__).resolve().parents[2] / "rules" / "demo_scenarios.yaml"
_HUB_PATH = "/apt/demo"
_OPS_HUB_PATH = "/apt/dev"

_CHANNELS: tuple[str, ...] = ("ads", "direct", "email", "search")
_CHANNEL_LABELS: dict[str, str] = {
    "ads": "Ads",
    "direct": "Direct",
    "email": "Email",
    "search": "Search",
}
_CHANNEL_DESC: dict[str, str] = {
    "ads": "Paid social — UTM stack + variant message-match.",
    "direct": "Typed URL — IP tier and network type only.",
    "email": "HubSpot cohort — magic token or logged-in CRM.",
    "search": "Organic referrer — intent-neutral entry.",
}

# Display order = data-richness ascending (direct < search < ads < email).
_CHANNEL_ORDER: tuple[str, ...] = ("direct", "search", "ads", "email")
# Which real marketing platform each channel maps to (drives the badge + accent).
_CHANNEL_PLATFORM: dict[str, str] = {
    "direct": "Anonymous", "search": "Google", "ads": "X Ads", "email": "HubSpot",
}
_CHANNEL_ICON: dict[str, str] = {"direct": "⌁", "search": "⌕", "ads": "◎", "email": "✉"}
_CHANNEL_SUB: dict[str, str] = {
    "direct": "Typed the URL", "search": "Organic referrer",
    "ads": "Paid campaign", "email": "HubSpot cohort",
}
_CHANNEL_SIGNAL: dict[str, int] = {"direct": 1, "search": 2, "ads": 3, "email": 4}
_CHANNEL_SIGNAL_LABEL: dict[str, str] = {
    "direct": "low", "search": "medium", "ads": "high", "email": "richest",
}
_CHANNEL_LONG: dict[str, str] = {
    "direct": "Cold visit — no campaign, no login. The IP layer is the only signal: "
              "network type, region, corporate netblock.",
    "search": "Arrived from a search engine. Adds intent from the referrer on top of the "
              "IP layer — intent-neutral hero, region-aware.",
    "ads": "Paid click with the full UTM stack + ad variant. The hero message-matches the "
           "exact campaign creative the visitor clicked.",
    "email": "Warmest arrival. A magic token identifies the person from CRM before they "
             "log in — name, account, and history, all gated.",
}
# Sidebar account-switcher swatch per tenant (bg, initial).
_TENANT_LOGO: dict[str, tuple[str, str]] = {
    "gauntlet": ("#111827", "G"), "planet": ("#0b6b3a", "P"),
}

_TENANT_META: dict[str, dict[str, str]] = {
    "gauntlet": {
        "name": "GauntletAI",
        "domain": "gauntletai.com",
        "tagline": "AI hiring fellowship — entry channel × IP tier × CRM identity.",
        "audience_business": "Companies",
        "audience_consumer": "Individuals",
    },
    "planet": {
        "name": "Planet",
        "domain": "planet.com",
        "tagline": "Earth observation — location signal on channel, IP, and identity.",
        "audience_business": "Enterprise",
        "audience_consumer": "Self-serve",
    },
}

_IDENTITY_AS: dict[str, str] = {
    "anon": "anon",
    "known": "known",
    "login_maya": "known",
    "login_amara": "known",
    "token_liam": "known",
    "token_kofi": "known",
}

_cache: dict[str, Any] | None = None


def _magic_tokens() -> dict[str, str]:
    return {
        "liam": CO.magic_token(CO.BY_ID["liam"]),
        "kofi": PCO.magic_token(PCO.BY_ID["kofi"]),
    }


def _resolve_templates(text: str) -> str:
    tokens = _magic_tokens()
    out = text
    for key, val in tokens.items():
        out = out.replace(f"${{magic:{key}}}", val)
    return out


def _mounts_for(tenant: str) -> dict[str, str]:
    if tenant == "planet":
        return PLANET_MOUNTS["portal"]
    return GAUNTLET_MOUNTS["portal"]


def _channel_gallery_href(tenant: str, channel: str, m: dict[str, str]) -> str:
    page = m["page"]
    if channel == "ads":
        return m.get("ad_lp") or m.get("ads") or page
    if channel == "direct":
        return f"{page}/direct"
    if channel == "email":
        return f"{page}/email"
    if channel == "search":
        return f"{page}?ref=google"
    raise ValueError(f"unknown channel {channel!r}")


def load_scenarios(path: Path | None = None) -> dict[str, Any]:
    """Load and cache demo_scenarios.yaml with magic tokens resolved in patterns."""
    global _cache
    p = path or SCENARIOS_PATH
    key = str(p)
    if _cache is not None and _cache.get("_path") == key:
        return _cache
    raw = yaml.safe_load(p.read_text()) or {}
    scenarios: list[dict[str, Any]] = []
    for row in raw.get("scenarios") or []:
        s = dict(row)
        qp = s.get("query_params") or {}
        s["query_params"] = {
            k: _resolve_templates(str(v)) for k, v in qp.items()
        }
        for field in ("landing_url_pattern", "console_deep_link_pattern"):
            if field in s:
                s[field] = _resolve_templates(str(s[field]))
        scenarios.append(s)
    data = {
        "_path": key,
        "version": raw.get("version", 1),
        "tenants": list(raw.get("tenants") or []),
        "scenarios": scenarios,
    }
    validate_scenarios(data)
    _cache = data
    return data


def validate_scenarios(data: dict[str, Any]) -> None:
    seen: set[str] = set()
    for s in data.get("scenarios") or []:
        sid = s.get("id")
        if not sid:
            raise ValueError("demo_scenarios: scenario missing id")
        if sid in seen:
            raise ValueError(f"demo_scenarios: duplicate id {sid!r}")
        seen.add(sid)


def _as_from_hint(identity_hint: str) -> str:
    return _IDENTITY_AS.get(identity_hint, "anon")


def resolve_scenario_urls(scenario: dict[str, Any], mounts: dict[str, str] | None = None) -> dict[str, str]:
    """Expand landing_url_pattern and console_deep_link_pattern for a scenario."""
    m = mounts or _mounts_for(scenario["tenant"])
    subs = {
        "mount_page": m["page"],
        "mount_dev": m["dev"],
        "mount_dev_business": m["dev_business"],
        "as": _as_from_hint(str(scenario.get("identity_hint", "anon"))),
    }
    qp = dict(scenario.get("query_params") or {})
    ip = scenario.get("ip_override")
    if ip:
        qp["ip"] = ip
    subs["query"] = urlencode(qp)
    landing = str(scenario.get("landing_url_pattern", "{mount_page}"))
    console = str(scenario.get("console_deep_link_pattern", "{mount_dev}?as={as}"))
    for key, val in subs.items():
        landing = landing.replace("{" + key + "}", val)
        console = console.replace("{" + key + "}", val)
    return {"landing_url": landing, "console_deep_link": console}


def scenarios_for(
    tenant: str,
    channel: str | None = None,
    audience: str | None = None,
    *,
    data: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Filter scenarios; each row includes resolved landing + console URLs."""
    catalog = data or load_scenarios()
    out: list[dict[str, Any]] = []
    for s in catalog["scenarios"]:
        if s.get("tenant") != tenant:
            continue
        if channel and s.get("channel") != channel:
            continue
        aud = s.get("audience", "all")
        if audience and aud not in (audience, "all"):
            continue
        mounts = _mounts_for(tenant)
        urls = resolve_scenario_urls(s, mounts)
        out.append({**s, **urls})
    featured = [x for x in out if x.get("featured")]
    rest = [x for x in out if not x.get("featured")]
    return featured + rest


def _tenant_section(tenant: str, data: dict[str, Any]) -> dict[str, Any]:
    meta = _TENANT_META[tenant]
    m = _mounts_for(tenant)
    logo_bg, logo_ch = _TENANT_LOGO[tenant]
    channels = []
    for ch in _CHANNEL_ORDER:
        count = len([s for s in data["scenarios"] if s["tenant"] == tenant and s["channel"] == ch])
        count_label = "12 variants" if ch == "ads" else (
            f"{count} scenario" if count == 1 else f"{count} scenarios")
        channels.append({
            "id": ch,
            "label": _CHANNEL_LABELS[ch],
            "sub": _CHANNEL_SUB[ch],
            "desc": _CHANNEL_LONG[ch],
            "platform": _CHANNEL_PLATFORM[ch],
            "icon": _CHANNEL_ICON[ch],
            "signal": _CHANNEL_SIGNAL[ch],
            "signal_label": _CHANNEL_SIGNAL_LABEL[ch],
            "href": _channel_gallery_href(tenant, ch, m),
            "count_label": count_label,
        })
    return {
        "id": tenant,
        "name": meta["name"],
        "domain": meta["domain"],
        "logo_bg": logo_bg,
        "logo_ch": logo_ch,
        "channels": channels,
        "replica_href": m["page"],
        "consoles_href": f"{_OPS_HUB_PATH}?site={tenant}",
    }


def build_sitemap_view(request: Request) -> dict[str, Any]:
    data = load_scenarios()
    all_tenants = tuple(data.get("tenants") or ("gauntlet", "planet"))
    site = request.query_params.get("site", "").strip().lower()
    is_new = site == "new"
    if not is_new and site not in all_tenants:
        site = all_tenants[0]
    nav_site = all_tenants[0] if is_new else site
    if is_new:
        active = {
            "id": "new", "name": "New website", "domain": "your-domain.com",
            "logo_bg": "#2E6FF5", "logo_ch": "+", "channels": [],
            "replica_href": "#", "consoles_href": "#",
        }
    else:
        active = _tenant_section(site, data)
    tenants = []
    for t in all_tenants:
        meta = _TENANT_META[t]
        logo_bg, logo_ch = _TENANT_LOGO[t]
        tenants.append({
            "id": t, "name": meta["name"], "domain": meta["domain"],
            "logo_bg": logo_bg, "logo_ch": logo_ch,
            "href": f"{_HUB_PATH}?site={t}", "active": (not is_new and t == site),
        })
    return {
        "hub_path": _HUB_PATH,
        "ops_hub_path": _OPS_HUB_PATH,
        "active": active,
        "site": site,
        "is_new": is_new,
        "tenants": tenants,
        "add_new_href": f"{_HUB_PATH}?site=new",
        "stats": {
            "tenants": len(all_tenants),
            "channels": len(_CHANNELS),
            "scenarios": len(data["scenarios"]),
        },
        "nav": {
            "channels": f"{_HUB_PATH}?site={nav_site}",
            "consoles": f"{_OPS_HUB_PATH}?site={nav_site}",
            "observatory": "/observatory",
            "costs": "/costs",
            "replica": active["replica_href"],
        },
        "prompt_reference_count": len(DP.list_entries()),
    }


def console_shell_ctx(active_site: str, active_nav: str, *,
                      switch_hrefs: dict[str, str] | None = None) -> dict[str, Any]:
    """Sidebar/shell context for any page adopting the apt console shell.

    Returns the fields _apt_sidebar.html reads: brand, active (current website),
    tenants (dropdown options), add_new_href, nav, active_nav.
    """
    all_t = ("gauntlet", "planet")
    meta = _TENANT_META[active_site]
    bg, ch = _TENANT_LOGO[active_site]
    m = _mounts_for(active_site)
    active = {"logo_bg": bg, "logo_ch": ch, "name": meta["name"], "domain": meta["domain"]}
    tenants = []
    for t in all_t:
        tm = _TENANT_META[t]
        tbg, tch = _TENANT_LOGO[t]
        href = (switch_hrefs or {}).get(t) or f"{_HUB_PATH}?site={t}"
        tenants.append({
            "id": t, "name": tm["name"], "logo_bg": tbg, "logo_ch": tch,
            "href": href, "active": t == active_site,
        })
    return {
        "brand": "apt",
        "active_nav": active_nav,
        "active": active,
        "tenants": tenants,
        "add_new_href": f"{_HUB_PATH}?site=new",
        "nav": {
            "channels": f"{_HUB_PATH}?site={active_site}",
            "consoles": f"{_OPS_HUB_PATH}?site={active_site}",
            "observatory": "/observatory",
            "costs": "/costs",
            "replica": m["page"],
        },
    }


_CHANNEL_GALLERY: dict[str, dict[str, str]] = {
    "direct": {
        "label": "Direct",
        "title": "Direct entry gallery",
        "desc": "Typed URL — IP tier and network type are the only arrival signals.",
    },
    "email": {
        "label": "Email",
        "title": "Email entry gallery",
        "desc": "HubSpot cohort sends — magic token or logged-in CRM before landing.",
    },
}


def _data_chips(scenario: dict[str, Any]) -> list[str]:
    chips: list[str] = [str(t) for t in (scenario.get("tags") or [])]
    hint = str(scenario.get("identity_hint") or "")
    if hint and hint not in chips:
        chips.append(hint.replace("_", " "))
    ip = scenario.get("ip_override")
    if ip:
        chips.append(f"ip={ip}")
    for key in ("utm_campaign", "utm_content", "utm_source", "ref"):
        val = (scenario.get("query_params") or {}).get(key)
        if val:
            chips.append(f"{key}={val}")
    return chips[:8]


def _gallery_card(scenario: dict[str, Any], mounts: dict[str, str]) -> dict[str, Any]:
    dev_biz = mounts["dev_business"]
    console = scenario["console_deep_link"]
    biz_console = console.replace(mounts["dev"], dev_biz, 1)
    return {
        "id": scenario["id"],
        "title": scenario["title"],
        "story": scenario["story"],
        "chips": _data_chips(scenario),
        "landing_url": scenario["landing_url"],
        "console_deep_link": console,
        "console_business_link": biz_console,
        "featured": bool(scenario.get("featured")),
        "email_preview": scenario.get("email_preview"),
    }


def build_channel_gallery_view(
    request: Request,
    tenant: str,
    channel: str,
    mounts: dict[str, str],
) -> dict[str, Any]:
    """View model for /{mount}/direct or /{mount}/email gallery pages."""
    if channel not in _CHANNEL_GALLERY:
        raise ValueError(f"unknown gallery channel {channel!r}")
    meta = _TENANT_META[tenant]
    audience_param = request.query_params.get("audience")
    if audience_param in ("business", "consumer"):
        audience = audience_param
        rows = scenarios_for(tenant, channel, audience)
    else:
        audience = "all"
        rows = scenarios_for(tenant, channel, None)
    ch_meta = _CHANNEL_GALLERY[channel]
    gallery_path = f"{mounts['page']}/{channel}"
    cards = [_gallery_card(s, mounts) for s in rows]
    tab_base = gallery_path
    return {
        "demo_flow_active": "scenario",
        "hub_path": _HUB_PATH,
        "tenant": tenant,
        "tenant_name": meta["name"],
        "tenant_domain": meta["domain"],
        "channel": channel,
        "channel_label": ch_meta["label"],
        "title": ch_meta["title"],
        "desc": ch_meta["desc"],
        "gallery_path": gallery_path,
        "audience": audience,
        "audience_business": meta["audience_business"],
        "audience_consumer": meta["audience_consumer"],
        "tab_business_href": f"{tab_base}?audience=business",
        "tab_consumer_href": f"{tab_base}?audience=consumer",
        "tab_all_href": tab_base,
        "cards": cards,
        "card_count": len(cards),
        "mounts": mounts,
    }
