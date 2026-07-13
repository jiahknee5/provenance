"""Channel setup pages (S2, IA-MAP archetype "Channel setup") — R42.

ONE data-driven template per channel × tenant, rendered from
rules/demo_scenarios.yaml + the channel constants in demo_nav. Sidebar channel
items land HERE (PRODUCT plane); galleries and landing pages demote to
explicitly-marked Preview drills. No per-tenant forks (R42).
"""
from __future__ import annotations

from starlette.requests import Request

from pipeline.personalization import demo_nav as NAV

CHANNELS: tuple[str, ...] = NAV._CHANNEL_ORDER  # direct, search, ads, email

# What arrives with this click — marketer-worded signal inventory per channel.
_SIGNALS: dict[str, list[str]] = {
    "direct": [
        "Network type & region, resolved from the IP",
        "Corporate netblock, when the visitor is on an office network",
        "Returning-visitor cookie, if they have logged in before",
    ],
    "search": [
        "The search referrer — the visitor came looking",
        "Network type & region, resolved from the IP",
        "No keyword — search engines don't share it, and apt never pretends otherwise",
    ],
    "ads": [
        "The full UTM stack — campaign, source, medium",
        "The exact ad variant clicked (the message-match key)",
        "Network type & region, resolved from the IP",
    ],
    "email": [
        "Who they are — magic token from the send, or CRM login",
        "Lifecycle stage, declared goals, and history (all policy-gated)",
        "Everything the lighter channels carry (IP layer, cookies)",
    ],
}

# How message-match works on this channel — the setup story.
_MESSAGE_MATCH: dict[str, str] = {
    "direct": "With only the IP layer, apt stays conservative: region-aware relevance "
              "where confidence is high, generic-but-true copy everywhere else. "
              "Low signal means low claim.",
    "search": "Search arrivals get an intent-neutral hero with region-aware trims. "
              "apt never fakes a 'we saw what you searched' moment — engines don't "
              "share the query.",
    "ads": "The landing hero message-matches the exact creative that was clicked — "
           "same promise, same vocabulary, with a receipt binding the claim to its "
           "source. Each ad variant maps to a landing state you can preview below.",
    "email": "The warmest channel. What the person told us renders at say level "
             "(quoted back); everything merely inferred stays allude or hold. The "
             "magic token personalizes the first paint, before any login.",
}

# Guardrails: one channel-generic line + the tenant's signature rule.
_CHANNEL_GUARDRAIL: dict[str, str] = {
    "direct": "Nothing personal is asserted from an IP alone — firmographics may shape "
              "emphasis (allude), never be recited.",
    "search": "No keyword pretence. Region relevance only at the scale the IP supports.",
    "ads": "The page may only promise what the ad promised — message-match is a truth "
           "constraint, not just a conversion trick.",
    "email": "PII renders only at say level with a lawful basis. Income and sensitive "
             "traits are hold — blocked before render, visible only in the console.",
}
_TENANT_GUARDRAIL: dict[str, str] = {
    "gauntlet": "GauntletAI signature rule: never name a competitor, never recite an "
                "employer — comparisons stay generic, firmographics allude.",
    "planet": "Planet signature rule: location stays at region scale; defense "
              "creatives use the theater of interest, never the visitor's location.",
    "skyfi": "SkyFi signature rule: basin/region scale only — an exact site appears "
             "only when the customer declared that AOI first-party.",
}

# Platform rows per channel: (label, utm_source to detect a live scenario, planned-note).
_PLATFORMS: dict[str, list[dict[str, str | None]]] = {
    "direct": [],
    "search": [
        {"label": "Organic search", "source": None, "live": "always"},
        {"label": "Paid search · Google Ads", "source": "google", "live": None},
    ],
    "ads": [
        {"label": "X Ads", "source": "x", "live": None},
        {"label": "Meta (FB · IG)", "source": "meta", "live": None},
        {"label": "LinkedIn", "source": "linkedin", "live": None},
        {"label": "Display / retargeting", "source": "display", "live": None},
        {"label": "YouTube / video", "source": "youtube", "live": None},
    ],
    "email": [
        {"label": "Email · HubSpot", "source": None, "live": "always"},
    ],
}


def _marketer_console_url(console_url: str, m: dict[str, str]) -> str:
    """Scenario deep links target the engineer console; send marketers to theirs."""
    dev, biz = m["dev"], m["dev_business"]
    if console_url.startswith(dev) and not console_url.startswith(biz):
        return biz + console_url[len(dev):]
    return console_url


def build_channel_view(request: Request, channel: str) -> dict:
    """Context for apt_channel.html — one channel × active tenant."""
    if channel not in CHANNELS:
        raise KeyError(channel)
    data = NAV.load_scenarios()
    tenants = tuple(data.get("tenants") or NAV.TENANTS)
    site = request.query_params.get("site", "").strip().lower()
    if site not in tenants:
        site = tenants[0]
    m = NAV._mounts_for(site)
    meta = NAV._TENANT_META[site]

    def _in_family(scenario_channel: str) -> bool:
        # Scenario channels carry the platform (ads-x, ads-meta, ads-google).
        # Paid search (ads-google) lives on the Search page, matching the
        # sidebar clusters; the Ads page owns the social/display family.
        if channel == "search":
            return scenario_channel in ("search", "ads-google")
        if channel == "ads":
            return scenario_channel.startswith("ads") and scenario_channel != "ads-google"
        return scenario_channel == channel

    rows = []
    sources_live: set[str] = set()
    for s in data["scenarios"]:
        sc = str(s.get("channel") or "")
        if s.get("tenant") != site or not _in_family(sc):
            continue
        urls = NAV.resolve_scenario_urls(s, m)
        if "-" in sc:
            sources_live.add(sc.split("-", 1)[1])
        src = (s.get("query_params") or {}).get("utm_source")
        if src:
            sources_live.add(str(src))
        rows.append({
            "id": s["id"],
            "title": s.get("title") or s["id"],
            "story": s.get("story") or "",
            "audience": s.get("audience") or "",
            "featured": bool(s.get("featured")),
            "preview_url": urls["landing_url"],
            "decisions_url": _marketer_console_url(urls["console_deep_link"], m),
        })
    rows.sort(key=lambda r: (not r["featured"], r["id"]))

    platforms = []
    for p in _PLATFORMS[channel]:
        live = p["live"] == "always" or (p["source"] in sources_live)
        platforms.append({"label": p["label"], "live": live})

    gallery_href = NAV._channel_gallery_href(site, channel, m)
    shell = NAV.console_shell_ctx(site, "channels", active_sub=channel)
    return {
        **shell,
        "channel": channel,
        "channel_label": NAV._CHANNEL_LABELS[channel],
        "channel_sub": NAV._CHANNEL_SUB[channel],
        "channel_long": NAV._CHANNEL_LONG[channel],
        "platform": NAV._CHANNEL_PLATFORM[channel],
        "signal_strength": NAV._CHANNEL_SIGNAL[channel],
        "signal_label": NAV._CHANNEL_SIGNAL_LABEL[channel],
        "signals": _SIGNALS[channel],
        "message_match": _MESSAGE_MATCH[channel],
        "guardrails": [_CHANNEL_GUARDRAIL[channel], _TENANT_GUARDRAIL[site]],
        "platforms": platforms,
        "scenarios": rows,
        "gallery_href": gallery_href,
        "ads_grid_href": m.get("ads") if channel == "ads" else None,
        "site": site,
        "site_name": meta["name"],
        "site_domain": meta["domain"],
        "live_href": m["page"],
        "designer_href": m["dev_business"],
    }
