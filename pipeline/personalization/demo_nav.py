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
    channels = []
    for ch in _CHANNELS:
        count = len([s for s in data["scenarios"] if s["tenant"] == tenant and s["channel"] == ch])
        channels.append({
            "id": ch,
            "label": _CHANNEL_LABELS[ch],
            "desc": _CHANNEL_DESC[ch],
            "href": _channel_gallery_href(tenant, ch, m),
            "scenario_count": count,
        })
    return {
        "id": tenant,
        "name": meta["name"],
        "domain": meta["domain"],
        "tagline": meta["tagline"],
        "audience_business": meta["audience_business"],
        "audience_consumer": meta["audience_consumer"],
        "channels": channels,
        "ops_href": f"{_OPS_HUB_PATH}?site={tenant}",
    }


def build_sitemap_view(request: Request) -> dict[str, Any]:
    data = load_scenarios()
    tenants = [_tenant_section(t, data) for t in data.get("tenants") or ("gauntlet", "planet")]
    prompt_count = len(DP.list_entries())
    return {
        "hub_path": _HUB_PATH,
        "ops_hub_path": _OPS_HUB_PATH,
        "tenants": tenants,
        "scenario_count": len(data["scenarios"]),
        "prompt_reference_count": prompt_count,
        "version": data.get("version", 1),
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
