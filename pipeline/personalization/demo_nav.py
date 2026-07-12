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
from app.skyfi import MOUNTS as SKYFI_MOUNTS
from pipeline.personalization import cohort as CO
from pipeline.personalization import design_prompts as DP
from pipeline.personalization import planet_cohort as PCO
from pipeline.personalization import skyfi_cohort as SCO

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
    "skyfi": ("#060b16", "S"),
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
    "skyfi": {
        "name": "SkyFi",
        "domain": "skyfi.com",
        "tagline": "On-demand satellite imagery — location × industry at basin scale.",
        "audience_business": "Business",
        "audience_consumer": "Personal",
    },
}

# The shell + dropdown enumerate tenants from config — adding a tenant here (plus its
# MOUNTS branch below) is the whole registration; no template or route special-casing.
_TENANTS: tuple[str, ...] = tuple(_TENANT_META)
TENANTS = _TENANTS  # public alias — route modules validate ?site= against config

_IDENTITY_AS: dict[str, str] = {
    "anon": "anon",
    "known": "known",
    "login_maya": "known",
    "login_amara": "known",
    "token_liam": "known",
    "token_kofi": "known",
    "token_ingrid": "known",
}

_cache: dict[str, Any] | None = None


def _magic_tokens() -> dict[str, str]:
    return {
        "liam": CO.magic_token(CO.BY_ID["liam"]),
        "kofi": PCO.magic_token(PCO.BY_ID["kofi"]),
        "ingrid": SCO.magic_token(SCO.BY_ID["ingrid"]),
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
    if tenant == "skyfi":
        return SKYFI_MOUNTS["portal"]
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
    ads_variant_counts = {"gauntlet": "12 variants", "planet": "12 variants",
                          "skyfi": "6 variants"}
    for ch in _CHANNEL_ORDER:
        count = len([s for s in data["scenarios"] if s["tenant"] == tenant and s["channel"] == ch])
        count_label = ads_variant_counts.get(tenant, "ads") if ch == "ads" else (
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
    shell = console_shell_ctx(nav_site, "channels",
                              active_sub=None if is_new else "start")
    if is_new:
        # The onboarding state shows itself, not a tenant, in the switcher summary.
        shell["active"] = {"logo_bg": "#2E6FF5", "logo_ch": "+",
                           "name": "New website", "domain": "your-domain.com"}
        shell["tenants"] = [dict(t, active=False) for t in shell["tenants"]]
    return {
        **shell,
        "hub_path": _HUB_PATH,
        "ops_hub_path": _OPS_HUB_PATH,
        "site_view": active,
        "page_name": active["name"],
        "page_domain": active.get("domain", ""),
        "site": site,
        "is_new": is_new,
        "stats": {
            "tenants": len(all_tenants),
            "channels": len(_CHANNELS),
            "scenarios": len(data["scenarios"]),
        },
        "prompt_reference_count": len(DP.list_entries()),
    }


def console_shell_ctx(active_site: str, active_nav: str, *,
                      switch_hrefs: dict[str, str] | None = None,
                      active_sub: str | None = None) -> dict[str, Any]:
    """Sidebar/shell context for any page adopting the apt console shell.

    Returns the fields _apt_sidebar.html reads: brand, active (current website),
    tenants (dropdown options), add_new_href, nav (flat — topbar buttons),
    nav_tree (the 3-level marketer IA), active_group/active_sub.
    """
    all_t = _TENANTS
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
    # Level 3 under Campaigns → Channels: the tenant's four acquisition channels,
    # named the way a marketer names them (platform hint where one exists).
    _mk_label = {"direct": "Direct traffic", "search": "Organic search",
                 "ads": "Paid ads · X", "email": "Email · HubSpot"}
    def _ads_scenario_href(source: str) -> str | None:
        """Landing URL of this tenant's seeded ads scenario for a platform, if one exists."""
        for s in load_scenarios()["scenarios"]:
            if (s.get("tenant") == active_site
                    and str(s.get("channel", "")).startswith("ads")
                    and (s.get("query_params") or {}).get("utm_source") == source):
                return resolve_scenario_urls(s, m)["landing_url"]
        return None

    # Channels organized by SIGNAL CLASS (what arrives with the click), not by logo.
    # Only real destinations are links; unbuilt platforms render as honest "planned" chips.
    meta_href = _ads_scenario_href("meta")
    google_ads_href = _ads_scenario_href("google")
    channel_clusters = [
        {"label": None, "kids": [
            {"id": "direct", "label": "Direct traffic",
             "href": _channel_gallery_href(active_site, "direct", m)},
        ]},
        {"label": "Search", "kids": [
            {"id": "search", "label": "Organic search",
             "href": _channel_gallery_href(active_site, "search", m)},
        ] + ([{"id": "search-paid", "label": "Paid search · Google Ads",
               "href": google_ads_href}] if google_ads_href else
             [{"id": "search-paid", "label": "Paid search · Google Ads", "planned": True}])},
        {"label": "Social ads", "kids": [
            {"id": "ads", "label": "X Ads",
             "href": _channel_gallery_href(active_site, "ads", m)},
        ] + ([{"id": "ads-meta", "label": "Meta (FB · IG)", "href": meta_href}]
             if meta_href else
             [{"id": "ads-meta", "label": "Meta (FB · IG)", "planned": True}])
          + [{"id": "ads-linkedin", "label": "LinkedIn", "planned": True}]},
        {"label": "Other ads", "kids": [
            {"id": "ads-display", "label": "Display / retargeting", "planned": True},
            {"id": "ads-video", "label": "YouTube / video", "planned": True},
        ]},
        {"label": None, "kids": [
            {"id": "email", "label": "Email · HubSpot",
             "href": _channel_gallery_href(active_site, "email", m)},
        ]},
    ]
    # Level 3 under Personalization → Page sections: the sections this website's
    # registry actually declares — the nav mirrors the designer, per tenant.
    from pipeline.personalization import sections as SEC
    section_children = [
        {"id": s["id"], "label": s.get("label") or s["id"].title(),
         "href": f"{m['dev_business']}#sd-{s['id']}"}
        for s in SEC.list_sections(active_site)
    ]
    nav_tree = [
        {"group": "Campaigns", "key": "channels", "items": [
            {"id": "start", "icon": "◧", "label": "Overview", "href": f"{_HUB_PATH}?site={active_site}"},
            {"id": "channel-galleries", "icon": "▤", "label": "Channels",
             "href": f"{_HUB_PATH}?site={active_site}", "clusters": channel_clusters},
        ]},
        {"group": "Personalization", "key": "consoles", "items": [
            {"id": "designer", "icon": "◨", "label": "Page sections",
             "href": m["dev_business"], "children": section_children},
            {"id": "engineer", "icon": "⌗", "label": "Decision trace", "href": m["dev"]},
            {"id": "hub", "icon": "◑", "label": "Preview as visitor", "href": f"{_OPS_HUB_PATH}?site={active_site}"},
        ]},
        {"group": "Results", "key": "measure", "items": [
            {"id": "observatory", "icon": "◔", "label": "Live activity", "href": f"/observatory?site={active_site}"},
            {"id": "costs", "icon": "$", "label": "Spend", "href": f"/costs?site={active_site}"},
        ]},
        {"group": "Your website", "key": "live", "items": [
            {"id": "replica", "icon": "↗", "label": f"Open {meta['domain']}", "href": m["page"]},
        ]},
    ]
    # Back-compat: pages pass observatory/costs as active_nav.
    group_of = {"channels": "channels", "consoles": "consoles",
                "observatory": "measure", "costs": "measure"}
    active_group = group_of.get(active_nav, active_nav)
    if active_sub is None and active_nav in ("observatory", "costs"):
        active_sub = active_nav
    return {
        "brand": "apt",
        "active_nav": active_nav,
        "active_group": active_group,
        "active_sub": active_sub,
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
        "nav_tree": nav_tree,
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
    switch_hrefs = {
        t: _channel_gallery_href(t, channel, _mounts_for(t)) for t in _TENANTS
    }
    return {
        **console_shell_ctx(tenant, "channels", switch_hrefs=switch_hrefs, active_sub=channel),
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


# --------------------------------------------------------------------------- #
# Shared X-ads grid (W6-E) — ONE template (app/templates/ads_grid.html) renders the
# gauntlet ad-lp layout for every tenant. Brand tokens below are read from each
# tenant's established ad-page palette (gauntlet_ad_lp / planet_ads / skyfi_ads);
# category colors match the catalogs' section keys. Nothing here invents copy —
# every card field reads from the live AD_VARIANTS catalogs + W6-A explainers.
# --------------------------------------------------------------------------- #
_ADS_GRID_BRANDS: dict[str, dict[str, Any]] = {
    "gauntlet": {
        "fonts_href": ("https://fonts.googleapis.com/css2?family=Archivo:wght@600;700"
                       "&family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400"
                       "&display=swap"),
        "sans": "'Archivo','Inter',sans-serif", "ui": "'Inter',sans-serif",
        "mono": "'JetBrains Mono',monospace",
        "bg": "#0b0a08", "line2": "#37311f",
        "accent": "#c9a24b", "accent_t": "#d5b269", "ink": "#f4f2ed",
        "chip_bg": "rgba(18,16,12,.92)", "chip_ink": "#cfcabf",
        "avatar_ink": "#fff", "avatar_fallback": "GA",
        "cats": {"demographic": {"color": "#3b82f6", "ink": "#fff"},
                 "audience": {"color": "#a855f7", "ink": "#fff"}},
        "heading": "X Ads Manager Targeting — 12 Variants",
        "page_title": "Gauntlet X Ads — 12 Targeting Types",
    },
    "planet": {
        "fonts_href": ("https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700"
                       "&family=JetBrains+Mono:wght@400&display=swap"),
        "sans": "'Montserrat',sans-serif", "ui": "'Montserrat',sans-serif",
        "mono": "'JetBrains Mono',monospace",
        "bg": "#07090a", "line2": "#1f3355",
        "accent": "#009da5", "accent_t": "#00cbe6", "ink": "#eef3f9",
        "chip_bg": "rgba(8,14,26,.92)", "chip_ink": "#c2cddb",
        "avatar_ink": "#fff", "avatar_fallback": "PL",
        "cats": {"vertical": {"color": "#3fa34d", "ink": "#fff"},
                 "audience": {"color": "#8a5cf6", "ink": "#fff"}},
        "heading": "Planet X Ads — 12 Targeting Types",
        "page_title": "Planet X Ads — 12 Targeting Types",
    },
    "skyfi": {
        "fonts_href": ("https://fonts.googleapis.com/css2?family=Hanken+Grotesk:"
                       "wght@400;500;600;700;800&family=DM+Mono:wght@400;500&display=swap"),
        "sans": "'Hanken Grotesk',sans-serif", "ui": "'Hanken Grotesk',sans-serif",
        "mono": "'DM Mono',monospace",
        "bg": "#060b16", "line2": "#1f3355",
        "accent": "#fcc219", "accent_t": "#ffd75e", "ink": "#eef3f9",
        "chip_bg": "rgba(8,14,26,.92)", "chip_ink": "#c2cddb",
        "avatar_ink": "#171203", "avatar_fallback": "SF",
        "cats": {"vertical": {"color": "#fcc219", "ink": "#171203"}},
        "heading": "SkyFi X Ads — 6 Vertical Creatives",
        "page_title": "SkyFi X Ads — 6 Vertical Creatives",
    },
}


def build_ads_grid_view(tenant: str, m: dict[str, str], *,
                        dev_sample: str | None = None) -> dict[str, Any]:
    """Context for the ONE shared X-ads grid template (ads_grid.html).

    Per card: real targeting meta, the mini X-post, the UTM string, the
    generic→personalized hero shift, and the condensed W6-A thinking affordance
    linking to the single-ad page. Grid geometry adapts to the variant count
    (12 → 6×2 wide / 4×3 laptop; 6 → 3×2 wide / 2×3 laptop).
    """
    from pipeline.personalization import ad_explainers as AE
    from pipeline.personalization import gauntlet_site as GS
    from pipeline.personalization import planet_site as PLS
    from pipeline.personalization import skyfi_site as SS

    site = {"gauntlet": GS, "planet": PLS, "skyfi": SS}[tenant]
    brand = _ADS_GRID_BRANDS[tenant]
    generic_hero = site.generic_hero_headline()
    sections: list[dict[str, Any]] = []
    total = 0
    for sec in site.ad_grid_sections():
        items: list[dict[str, Any]] = []
        for v in sec["variants"]:
            if tenant == "skyfi":
                # SkyFi's catalog has no X Ads Manager targeting config — the six
                # creatives are vertical-led; segment + audience route are the
                # real fields (same framing skyfi_ads.html used).
                type_label = "Vertical creative"
                config_label = f"{v['segment']} · route {v['audience']}"
                fit_label = f"the {v['segment']} vertical"
            else:
                type_label = v["x_targeting_type"]
                config_label = v["x_targeting_example"]
                fit_label = v["audience_fit_label"]
            items.append({
                "variant": v,
                "type_label": type_label,
                "config_label": config_label,
                "fit_label": fit_label,
                "landing_url": site.variant_landing_url(v, m["page"]),
                "generic_hero": generic_hero,
                "personal_hero": site.variant_hero_headline(v),
                "single_url": f"{m['ad']}?v={v['variant_id']}",
                "explainer": AE.explainer_for(tenant, v, page_path=m["page"],
                                              dev_path=m["dev"]),
            })
        total += len(items)
        sections.append({"label": sec["label"], "category": sec["category"],
                         "variants": items})
    cols_wide = 6 if total >= 10 else 3
    cols_laptop = 4 if total >= 10 else 2
    grid = {
        "cols_wide": cols_wide, "rows_wide": -(-total // cols_wide),
        "cols_laptop": cols_laptop, "rows_laptop": -(-total // cols_laptop),
    }
    return {
        "page_title": brand["page_title"],
        "heading": brand["heading"],
        "brand": brand,
        "cats": [{"key": k, **c} for k, c in brand["cats"].items()],
        "grid": grid,
        "sections": sections,
        "generic_hero": generic_hero,
        "g": m,
        "dev_sample": dev_sample or m["dev"],
        "demo_hub_path": _HUB_PATH,
        "demo_flow_active": "scenario",
    }
