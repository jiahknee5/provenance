"""SkyFi (skyfi.com) replica — live entry-point + IP + CRM personalization for /skyfi (+ /skyfi/dev).

A faithful mock of a skyfi.com-style marketing site (space-dark #060b16, signal-yellow
#fcc219, Hanken Grotesk + DM Mono) whose copy blocks are personalization SLOTS filled
deterministically from the engine the repo already has:

  • classify_entry() — the four entry channels (ad / email / search / direct).
  • scene.detect()/resolve_ip() — the always-on IP layer: network type + tiers 0–3.
  • skyfi_cohort.match()/by_token() + segments.derive()/pick_archetype() — the known-visitor
    path (login or magic token) → CRM record → archetype → emphasis + say-level copy.

THE SKYFI THESIS — LOCATION × INDUSTRY. SkyFi sells on-demand satellite imagery: the
geography IS the product. A dedicated location stage turns geo-IP region × sector into a
basin/region-scale hero line — with the SIGNATURE GUARDRAIL (the sale, not a limit):

  · **basin/region scale only.** Exact-AOI / specific-asset pinpointing is `hold`
    (blocked arm `Ex`) — the anti-surveillance ceiling. We never demonstrate that we
    could point a satellite at YOUR site uninvited.
  · **UNLESS the AOI is declared first-party** (they drew it in the order flow — their
    own asset). Then, and only then, the exact AOI is `say` — and the receipt says
    honestly WHY: "you told us." That is the S09 flip.
  · **defense/gov is strict hold**: AOR/theater framing, never a specific asset,
    regardless of tier, login, or declaration.

Surface policy is enforced exactly as the repo defines it: `say` facts may be recited;
`allude` facts only SHAPE copy; `hold` facts never reach the page — the recite variants
appear only on /skyfi/dev, marked blocked. Deterministic — no LLM, no RNG, $0 offline.

Brand facts from .rapid/reference/skyfi-brand.md (captured 2026-07-12); copy is
structural/product-shaped only — no invented statistics.
"""
from __future__ import annotations

from pipeline.personalization import image_gen as IG
from pipeline.personalization import scene as SC
from pipeline.personalization import segments as SEG
from pipeline.personalization import skyfi_cohort as CO

IMAGE_TENANT = "skyfi"

# --------------------------------------------------------------------------- #
# Entry classification — the four channels
# --------------------------------------------------------------------------- #
AD_MEDIUMS = {"paid", "cpc", "ppc", "display"}
SEARCH_REFS = {"google", "bing", "ddg", "duckduckgo"}
SEARCH_HOSTS = ("google.", "bing.com", "duckduckgo.com", "ddg.gg")

CHANNEL_LABELS = {"ad": "Paid ad (UTM)", "email": "Email (UTM)",
                  "search": "Organic search", "direct": "Direct"}


def classify_entry(request) -> dict:
    """UTM + referrer → one of the four entry channels, with the rule that fired.
    Pure function of the request (query params + Referer header) — no network, no state."""
    q = request.query_params
    utm_source = q.get("utm_source", "")
    utm_medium = q.get("utm_medium", "").strip().lower()
    utm_campaign = q.get("utm_campaign", "").strip().lower()
    utm_content = q.get("utm_content", "").strip().lower()
    ref = q.get("ref", "").strip().lower()
    referer = request.headers.get("referer", "")
    token = q.get("e", "").strip()
    person = CO.by_token(token) if token else None

    if utm_medium in AD_MEDIUMS:
        channel = "ad"
        rule = f"utm_medium={utm_medium} ∈ {{paid, cpc, ppc, display}}"
        why = (f"the click carried ad UTMs (source={utm_source or '—'}, "
               f"campaign={utm_campaign or '—'}) — message-match the hero to the campaign")
    elif utm_medium == "email":
        channel = "email"
        rule = "utm_medium=email" + (" + e= magic token" if token else "")
        why = ("the click came from an email we sent" +
               (f" — the magic token identifies {person['vector']['name']} with no login"
                if person else " — warm framing, no identity until they log in"))
    elif ref in SEARCH_REFS or any(h in referer.lower() for h in SEARCH_HOSTS):
        channel = "search"
        rule = (f"?ref={ref} simulates a search referrer" if ref in SEARCH_REFS
                else "Referer header is a search engine")
        why = "search arrivals carry intent but no campaign promise — keep copy intent-neutral"
    else:
        channel = "direct"
        rule = "no UTM, no search referrer"
        why = "nothing about the click tells us anything — the IP layer is the only signal"

    signals = [
        {"label": "utm_source", "value": utm_source or "—"},
        {"label": "utm_medium", "value": utm_medium or "—"},
        {"label": "utm_campaign", "value": utm_campaign or "—"},
        {"label": "utm_content", "value": utm_content or "—"},
        {"label": "ref", "value": ref or "—"},
        {"label": "Referer header", "value": referer or "—"},
        {"label": "e (magic token)", "value": (token[:12] + "…") if token else "—"},
    ]
    return {"channel": channel, "channel_label": CHANNEL_LABELS[channel],
            "utm_source": utm_source, "utm_medium": utm_medium, "utm_campaign": utm_campaign,
            "utm_content": utm_content, "ref": ref, "referer": referer, "token": token,
            "token_person_id": person["id"] if person else None,
            "rule": rule, "why": why, "signals": signals}


def _campaign_intent(campaign: str) -> str | None:
    """Which audience a campaign name message-matches to. Deterministic keyword rule."""
    c = (campaign or "").lower()
    if any(w in c for w in ("defense", "gov", "aor", "sar-mission", "enterprise",
                            "insurance", "tasking-program")):
        return "enterprise"
    if any(w in c for w in ("monitor", "site", "aoi", "order", "archive", "field",
                            "progress", "on-demand", "selfserve", "self-serve")):
        return "selfserve"
    return None


# --------------------------------------------------------------------------- #
# X.com ad variants — six vertical creatives on SkyFi's UC2 verticals.
# Each carries utm_campaign=x-{slug} and utm_content=sv01–sv06. Copy is truth-bounded:
# product-shaped claims only, no invented stats. Defense holds the AOR register.
# --------------------------------------------------------------------------- #
def _v(id_, variant_id, segment, utm_campaign, *,
       trigger, body, cta_label,
       h1_pre, h1_blue, sub, hero_eyebrow="",
       cta_primary, cta_secondary, compare_emphasis,
       order=None, how_intro=None, pricing_body=None,
       cta_heading=None, cta_sub=None, hold_note=None):
    """Build one ad variant dict with paired ad copy + landing-page overrides."""
    return {
        "id": id_,
        "variant_id": variant_id,
        "category": "vertical",
        "segment": segment,
        "audience": _SEGMENT_ROUTE.get(segment, "neutral"),
        "utm_campaign": utm_campaign,
        "utm_source": "x",
        "utm_medium": "paid",
        "hold_note": hold_note,
        "ad": {"handle": "skyfi", "display": "SkyFi",
               "trigger": trigger, "body": body, "cta_label": cta_label,
               "text": f"{trigger} {body}"},
        "page": {
            "hero_eyebrow": hero_eyebrow or "From your X ad",
            "h1_pre": h1_pre, "h1_blue": h1_blue, "sub": sub,
            "cta_primary": cta_primary, "cta_secondary": cta_secondary,
            "compare_emphasis": compare_emphasis, "order": order,
            "how_intro": how_intro, "pricing_body": pricing_body,
            "cta_heading": cta_heading, "cta_sub": cta_sub,
        },
    }


_SEGMENT_ROUTE = {"mining": "selfserve", "construction": "selfserve",
                  "agriculture": "selfserve", "energy": "selfserve",
                  "insurance": "enterprise", "defense": "enterprise"}

AD_VARIANTS: list[dict] = [
    _v("x-mining", "sv01", "mining", "x-monitor-your-site",
       trigger="Monitor your site from orbit — no drone crew, no flight plan.",
       body=("Draw the basin you operate in, see what the archive already holds, and task "
             "a fresh capture when you need one. Priced by the square kilometer, upfront."),
       cta_label="See your basin →",
       hero_eyebrow="You clicked the monitor-your-site ad",
       h1_pre="Monitor Your Site, ", h1_blue="From Orbit",
       sub=("Weekly eyes on pits, haul roads, and stockpiles without mobilizing a crew — "
            "archive imagery in minutes, new tasking on demand, quoted upfront."),
       cta_primary="Browse Imagery", cta_secondary="Task a Satellite",
       compare_emphasis="task",
       how_intro=("From basin to briefing without a site visit: search the archive over "
                  "your operating region, then task the next pass."),
       cta_heading="Your basin is a search away",
       cta_sub="Draw the AOI, see the price — imagery follows."),
    _v("x-construction", "sv02", "construction", "x-construction-progress",
       trigger="Progress documentation that doesn't wait for the monthly flyover.",
       body=("Order imagery of active sites on your schedule — same order flow for the "
             "archive baseline and the fresh capture."),
       cta_label="See progress monitoring →",
       hero_eyebrow="You clicked the construction-progress ad",
       h1_pre="Every Site, ", h1_blue="Every Milestone",
       sub=("Baseline from the archive, fresh captures per milestone — progress "
            "documentation across every active site in one order flow."),
       cta_primary="Browse Imagery", cta_secondary="Task a Satellite",
       compare_emphasis="task",
       cta_heading="Document the build from above",
       cta_sub="Archive baseline plus milestone captures, one workflow."),
    _v("x-agriculture", "sv03", "agriculture", "x-ag-field-check",
       trigger="Check the whole growing region without driving a single block.",
       body=("Archive imagery over your growing region in minutes, optical or SAR when "
             "the clouds don't cooperate."),
       cta_label="See your region →",
       hero_eyebrow="You clicked the field-check ad",
       h1_pre="The Season, ", h1_blue="Seen Weekly",
       sub=("Region-scale condition checks from the archive, SAR when it's overcast, and "
            "new tasking when a block needs a closer look."),
       cta_primary="Browse Imagery", cta_secondary="Task a Satellite",
       compare_emphasis="archive",
       cta_heading="Your growing region is in the archive",
       cta_sub="Search it in seconds — task when you need fresh."),
    _v("x-insurance", "sv04", "insurance", "x-insurance-before-after",
       trigger="The before-picture is already in the archive.",
       body=("Pull the pre-event state of an exposure region in minutes, then task the "
             "after-pass — before/after pairs without a field visit."),
       cta_label="See claims imagery →",
       hero_eyebrow="You clicked the before/after ad",
       h1_pre="Before and After, ", h1_blue="Without the Wait",
       sub=("Archive imagery holds the pre-event state of the regions you underwrite; "
            "post-event tasking completes the pair — one platform, quoted upfront."),
       cta_primary="Talk to Tasking Ops", cta_secondary="Browse Imagery",
       compare_emphasis="archive",
       order=["hero", "compare", "how", "pricing", "cta"],
       cta_heading="Underwrite with the archive, settle with the tasking",
       cta_sub="Before/after pairs at region scale, on demand."),
    _v("x-energy", "sv05", "energy", "x-energy-corridor",
       trigger="Every mile of corridor, checked from the archive.",
       body=("Quarterly encroachment checks over rights-of-way from imagery that already "
             "exists — task a fresh pass only where something changed."),
       cta_label="See corridor monitoring →",
       hero_eyebrow="You clicked the corridor ad",
       h1_pre="Corridors Checked, ", h1_blue="Crews Spared",
       sub=("Archive sweeps over your rights-of-way at basin scale, fresh tasking only "
            "where the change is — fewer truck rolls, same certainty."),
       cta_primary="Browse Imagery", cta_secondary="Task a Satellite",
       compare_emphasis="archive",
       cta_heading="Check the corridor before rolling a truck",
       cta_sub="Archive first, tasking where it matters."),
    _v("x-defense", "sv06", "defense", "x-defense-aor",
       trigger="Commercial imagery and SAR across the AOR — one procurement, many providers.",
       body=("Multi-provider optical and SAR tasking over theaters of interest, ordered "
             "through one flow. AOR-scale coverage — this page will never reference a "
             "specific asset or your own location."),
       cta_label="See the defense brief →",
       hero_eyebrow="You clicked the defense ad",
       h1_pre="The AOR, ", h1_blue="On Order",
       sub=("Multi-provider optical and SAR across your area of responsibility — "
            "commercial augmentation ordered like a product, not a program."),
       cta_primary="Talk to Tasking Ops", cta_secondary="Browse Imagery",
       compare_emphasis="task",
       order=["hero", "compare", "how", "pricing", "cta"],
       cta_heading="Theater-scale coverage, product-scale ordering",
       cta_sub="AOR framing only — never a specific asset.",
       hold_note=("Defense register: AOR/theater framing only — a specific asset or the "
                  "visitor's own location is never referenced (strict hold)")),
]

AD_BY_CAMPAIGN = {v["utm_campaign"]: v for v in AD_VARIANTS}
AD_BY_VARIANT_ID = {v["variant_id"]: v for v in AD_VARIANTS}


def resolve_ad_variant(entry: dict) -> dict | None:
    """Map UTM campaign + content to one of the catalogued X.com ad variants."""
    if entry.get("channel") != "ad":
        return None
    content = (entry.get("utm_content") or "").strip().lower()
    if content and content in AD_BY_VARIANT_ID:
        return AD_BY_VARIANT_ID[content]
    campaign = (entry.get("utm_campaign") or "").strip().lower()
    if campaign and campaign in AD_BY_CAMPAIGN:
        return AD_BY_CAMPAIGN[campaign]
    return None


def variant_landing_url(variant: dict, page_path: str = "/skyfi") -> str:
    """Full landing-page URL with the variant's UTM params."""
    q = (f"utm_source={variant['utm_source']}&utm_medium={variant['utm_medium']}"
         f"&utm_campaign={variant['utm_campaign']}&utm_content={variant['variant_id']}")
    return f"{page_path}?{q}"


def generic_hero_headline() -> str:
    return GENERIC["hero"]["h1_pre"] + GENERIC["hero"]["h1_blue"]


# --------------------------------------------------------------------------- #
# The generic page — product-shaped claims only (brand ref: skyfi-brand.md).
# --------------------------------------------------------------------------- #
GENERIC = {
    "hero": {
        "eyebrow": "",
        "h1_pre": "Earth Intelligence, ", "h1_blue": "On Demand",
        "sub": ("Order and task satellite imagery and SAR from the world's top providers. "
                "Search the archive, task a new capture, and download geospatial data in "
                "one platform."),
        "cta_primary": "Browse Imagery", "cta_secondary": "Task a Satellite",
        "location_line": "",
    },
    "how": {
        "h_pre": "From AOI to Answer, ", "h_blue": "In One Flow",
        "intro": ("Draw the area you care about, choose archive or new tasking, and get "
                  "analysis-ready delivery — no sales call required."),
    },
    "pricing": {
        "eyebrow": "Pricing by AOI",
        "heading": "Priced by the square kilometer, not the sales call",
        "body": ("Draw the AOI, see the price. Existing imagery and new tasking are quoted "
                 "upfront for exactly the area you order — no minimums designed for "
                 "governments."),
        "cta": "Price your AOI →",
    },
    "cta": {
        "heading": "Your AOI is a search away",
        "sub": "Draw the area you care about — see what the archive already holds.",
        "cta_primary": "Browse Imagery", "cta_secondary": "Talk to Us",
    },
}

HOW_CARDS = [
    ("Draw your AOI", "Drop a polygon on the map — your area of interest is the unit of "
                      "everything: search, pricing, delivery."),
    ("Search or task", "Existing archive imagery in minutes, or task a new optical or SAR "
                       "capture from the provider network."),
    ("Download & integrate", "Analysis-ready delivery to your workspace or API — the same "
                             "GeoTIFF your GIS already speaks."),
]

COMPARE_ROWS = [
    ("Source", "Archive — already captured", "Fresh capture, tasked for you"),
    ("Speed", "Minutes to download", "Provider pass-dependent"),
    ("Best for", "History, baselines, before-states", "Current conditions, new looks"),
    ("Sensors", "Optical + SAR archive", "Optical, SAR, and more on order"),
    ("Pricing", "Per-km² archive rates, shown upfront", "Per-task quote, shown upfront"),
    ("Next step", "Search your AOI", "Task a satellite"),
]

# real-site section order — reorders per audience, structure never changes
DEFAULT_ORDER = ["hero", "how", "pricing", "compare", "cta"]
ORDER_BY_AUDIENCE = {
    "enterprise": ["hero", "compare", "how", "pricing", "cta"],
    "selfserve": ["hero", "how", "pricing", "compare", "cta"],
    "neutral": DEFAULT_ORDER,
}

# Archetype → SkyFi CTA (segments.ARCHETYPES ctas are education-flavored; map honestly).
ARCH_CTA = {
    "outcomes_first": "See it on your AOI →",
    "cost_confident": "Price your AOI →",
    "fast_track": "Task a satellite →",
    "explorer": "Browse the archive →",
    "welcome_back": "Continue your order →",
    "prestige": "Talk to tasking ops →",
}

# --------------------------------------------------------------------------- #
# LOCATION × INDUSTRY — the SkyFi differentiator. Region (geo-IP, tier-gated) ×
# sector → a basin/region-scale line. Guardrails (the sale, not a limit):
#   basin/region scale only · exact-AOI = hold (arm Ex) UNLESS declared first-party
#   ("you told us" receipt, S09) · defense/gov = strict hold (AOR register).
# --------------------------------------------------------------------------- #
SECTOR_LINES = {
    "mining": "Fresh imagery over {region}'s mining basins — searchable now, taskable today.",
    "agriculture": "Every growing region in {region} is in the archive — and taskable today.",
    "construction": "Build corridors across {region}, documented capture by capture.",
    "energy": "{region}'s corridors and basins, checked from the archive.",
    "insurance": "The before-picture of {region} is already in the archive.",
    "logistics": "{region}'s ports and corridors, imaged on demand.",
    "real_estate": "Site candidates across {region}, compared from above.",
}
DEFAULT_SECTOR_LINE = "The archive already covers {region} — search it in seconds."
AOR_LINE = "Coverage across your area of responsibility — theater scale, never your own site."

# Cohort industry label → sector key (deterministic keyword map).
_INDUSTRY_SECTOR = {
    "mining": "mining", "agriculture": "agriculture", "construction": "construction",
    "energy": "energy", "utilities": "energy", "insurance": "insurance",
    "real estate": "real_estate", "logistics": "logistics",
}


def _sector_for(det: dict, ad_variant: dict | None, ident: dict | None) -> str | None:
    """Sector precedence: ad segment > CRM industry keyword > reverse-IP bucket."""
    if ad_variant:
        return ad_variant["segment"]
    if ident and ident.get("kind") == "cohort":
        ind = (ident["view"]["linkedin"].get("industry") or "").lower()
        if any(w in ind for w in ("defense", "gov", "military", "aerospace")):
            return "defense"
        for kw, sector in _INDUSTRY_SECTOR.items():
            if kw in ind:
                return sector
        return None
    key = det.get("industry")
    if key and key in SECTOR_LINES:
        return key
    return None


def _is_defense(sector: str | None, ident: dict | None) -> bool:
    if sector == "defense":
        return True
    if ident and ident.get("kind") == "cohort":
        ind = (ident["view"]["linkedin"].get("industry") or "").lower()
        return any(w in ind for w in ("defense", "gov", "military"))
    return False


def location_signal(det: dict, tier: int, ad_variant: dict | None,
                    ident: dict | None = None) -> dict:
    """Deterministic location×industry decision:
    {line, mode, policy, rule, why, segment, region, blocked_say, receipt}.

    Precedence: defense strict hold > declared first-party AOI (say — S09 flip) >
    basin/region line (allude) > hold (tier 0 / no region)."""
    sector = _sector_for(det, ad_variant, ident)
    region, city = det.get("region"), det.get("city")

    # 1 · defense/gov — STRICT hold. AOR register beats everything, even a declaration.
    if _is_defense(sector, ident):
        return {"line": AOR_LINE, "mode": "aor", "segment": "defense", "region": None,
                "rule": "sector=defense/gov → AOR register (strict hold, guardrail)",
                "policy": "allude",
                "why": ("defense audiences get theater/AOR framing only — never a specific "
                        "asset, never their own location, regardless of tier or login"),
                "blocked_say": (f"Tomorrow's pass covers {city or region} — here's your "
                                "installation from above" if (city or region) else None),
                "receipt": None}

    # 2 · declared first-party AOI — the S09 flip: exact scale allowed BECAUSE they told us.
    aoi = None
    if ident and ident.get("kind") == "cohort":
        aoi = (ident["view"].get("declared") or {}).get("aoi")
    if aoi:
        return {"line": f"Your AOI on file — {aoi['label']} — has fresh coverage available.",
                "mode": "declared_aoi", "segment": sector, "region": region,
                "rule": "declared first-party AOI on record → exact scale unlocks (say)",
                "policy": "say",
                "why": ("exact-AOI rendering is allowed for THIS one basis only: they drew "
                        "the boundary themselves in the order flow — first-party, "
                        "declared, their own asset (S09)"),
                "blocked_say": None,
                "receipt": {"basis": "declared_first_party",
                            "aoi_label": aoi["label"],
                            "aoi_scale": aoi.get("scale", "site"),
                            "registered": aoi.get("registered"),
                            "source": aoi.get("source", "AOI drawn in the SkyFi order flow"),
                            "say_reason": "You told us — this AOI was declared as your own "
                                          "asset, so exact-scale is honest, not surveillance."}}

    # 3 · basin/region line — the truthful scale ceiling (arm Ex holds exact site).
    if tier >= 1 and region:
        template = SECTOR_LINES.get(sector or "", DEFAULT_SECTOR_LINE)
        return {"line": template.format(region=region), "mode": "region", "segment": sector,
                "region": region,
                "rule": f"tier ≥ 1 + region resolved → sector template ({sector or 'default'}) "
                        "at basin/region scale",
                "policy": "allude",
                "why": ("the archive genuinely covers the visitor's region, so a "
                        "basin/region-scale claim is true — exact-site pinpointing is held "
                        "(arm Ex): we never demonstrate uninvited precision"),
                "blocked_say": (f"We can task tomorrow's pass over your exact site at "
                                f"{city + ', ' if city else ''}{region} — no need to tell "
                                "us where you operate"),
                "receipt": None}

    # 4 · nothing usable — hold.
    return {"line": "", "mode": "none", "segment": sector, "region": None,
            "rule": "tier 0 or no region — no location claim ships",
            "policy": "hold",
            "why": ("no location confidence (VPN / hosting / private IP) — a wrong basin "
                    "claim would break the exact trust the AOI ceiling builds"),
            "blocked_say": None, "receipt": None}


# --------------------------------------------------------------------------- #
# The builder
# --------------------------------------------------------------------------- #
def _resolve_visitor(request, ip_override: str) -> tuple[dict, bool]:
    """The always-on IP layer: the visitor's own IP, or an entered ?ip= (like /showcase)."""
    det = SC.detect(request)
    if ip_override:
        rv = SC.resolve_ip(ip_override)
        rv["request_signals"] = det.get("request_signals", [])
        return rv, True
    return det, False


def _identity(email: str | None, entry: dict) -> dict | None:
    """Who the visitor is, if anyone: login email (say) or the email magic token (say).
    Cohort hit → the full CRM record; unknown work email → first-party domain resolution."""
    via = None
    person = None
    if email:
        person, via = CO.match(email), "login"
    if person is None and entry.get("token_person_id"):
        person, via = CO.BY_ID[entry["token_person_id"]], "magic token"
        email = person["email"]
    if person:
        v = CO.view(person)
        segs = SEG.derive(v)
        arch = SEG.pick_archetype(v, segs)
        return {"kind": "cohort", "via": via, "email": person["email"], "view": v,
                "first": v["name"].split()[0], "segments": segs, "archetype": arch,
                "crm": person}
    if email:
        res = SC.resolve_email(email)
        return {"kind": "resolved", "via": "login", "email": email, "view": None,
                "first": None, "segments": None, "archetype": None, "resolved": res}
    return None


def _audience(entry: dict, det: dict, ident: dict | None,
              variant: dict | None = None) -> tuple[str, str, str]:
    """Route the page to an audience: enterprise (tasking ops / programs), selfserve
    (order-flow), or neutral. Returns (audience, rule, why)."""
    if variant:
        return (variant["audience"],
                f"ad variant {variant['id']} (utm_campaign={variant['utm_campaign']})",
                "the X.com ad names the vertical — message-match the emphasis to that promise")
    intent = _campaign_intent(entry.get("utm_campaign"))
    if intent:
        return intent, f"utm_campaign={entry['utm_campaign']} message-matches {intent}", \
            "the campaign promise decides the emphasis — mission/insurance campaigns lead " \
            "with tasking ops, order-flow campaigns with self-serve"
    if ident and ident["kind"] == "cohort":
        li = ident["view"]["linkedin"]
        ind = (li.get("industry") or "").lower()
        if li.get("seniority") == "exec" or any(w in ind for w in ("defense", "insurance")):
            return "enterprise", f"CRM: seniority={li.get('seniority')} · industry={li.get('industry')}", \
                "a senior leader or mission buyer evaluates programs — tasking-ops framing"
        return "selfserve", f"CRM: seniority={li.get('seniority')} — an operating team", \
            "the CRM record describes a practitioner — order-flow framing"
    if ident and ident["kind"] == "resolved" and ident["resolved"].get("company"):
        return "enterprise", f"work-email domain → {ident['resolved']['company']}", \
            "a work email identifies a company — enterprise framing"
    net = det.get("network_type", "")
    if net in ("corporate", "corporate (via VPN)"):
        return "enterprise", f"network type = {net}", \
            "a corporate netblock is a B2B signal — emphasize tasking ops"
    if net in ("residential", "consumer ISP", "mobile"):
        return "selfserve", f"network type = {net}", \
            "a residential/mobile visitor is likelier hands-on — emphasize the order flow"
    return "neutral", f"network type = {net or 'unknown'} — no audience signal", \
        "VPN/hosting/unknown networks say nothing about who's visiting — the real-site default ships"


def _ind_label(det: dict) -> str:
    key = det.get("industry")
    return SC.BY_KEY[key]["label"].lower() if key else ""


def build_page(request, email: str | None = None, overrides: dict | None = None) -> dict:
    """Compose entry channel × IP tier × location×industry × identity/CRM into the
    replica's page contract + the full decision trace. Deterministic: same inputs →
    same page, same trace. Offline $0."""
    overrides = overrides or {}
    q = request.query_params
    ip_override = overrides.get("ip", q.get("ip", ""))

    entry = classify_entry(request)
    det, ip_forced = _resolve_visitor(request, ip_override)
    ident = _identity(email, entry)
    ad_variant = resolve_ad_variant(entry)
    audience, aud_rule, aud_why = _audience(entry, det, ident, ad_variant)

    tier, tier_label = det.get("tier", 0), det.get("tier_label", SC.TIER_LABELS[0])
    region, industry = det.get("region"), _ind_label(det)
    company, city = det.get("company"), det.get("city")

    trace: list[dict] = []

    def t(stage, signals, rule, disposition, output, why):
        trace.append({"stage": stage, "signals": signals, "rule": rule,
                      "disposition": disposition, "output": output, "why": why})

    t("Entry classify", [s["label"] + "=" + s["value"] for s in entry["signals"] if s["value"] != "—"] or ["(none)"],
      entry["rule"], "observed", f"channel = {entry['channel_label']}", entry["why"])

    if ad_variant:
        sigs = [
            f"utm_campaign={ad_variant['utm_campaign']}",
            f"utm_content={ad_variant['variant_id']}",
            f"segment={ad_variant['segment']}",
        ]
        why = ("the paid click carried a catalogued X.com campaign — every copy slot "
               "message-matches this variant")
        if ad_variant.get("hold_note"):
            sigs.append(f"hold_policy={ad_variant['hold_note']}")
            why += f" · {ad_variant['hold_note']}"
        t("Ad variant resolve", sigs, "AD_BY_CAMPAIGN / AD_BY_VARIANT_ID lookup",
          "observed", f"variant = {ad_variant['id']} · segment {ad_variant['segment']}", why)

    ip_sig = [f"ip={det.get('ip') or '—'}", f"network={det.get('network_type', '—')}"]
    if region:
        ip_sig.append(f"region={region}")
    if company:
        ip_sig.append(f"company={company}")
    if industry:
        ip_sig.append(f"industry={industry}")
    t("IP resolve + classify", ip_sig,
      "reverse-IP (ip-api) → network flags → deterministic router (scene._classify)",
      "allude", f"network {det.get('network_type', 'private / unreachable')}",
      det.get("reason") or "corporate IP with a resolved sector — firmographic copy may ship (allude framing only)")

    conf = det.get("confidence", {"location": "none", "company": "none", "industry": "none"})
    t("Tier route", [f"confidence: location={conf['location']} · company={conf['company']} · industry={conf['industry']}"],
      "industry resolved → 2 · geo only → 1 · nothing usable → 0 (scene.TIER_LABELS)",
      "observed", f"tier {tier} · {tier_label}",
      "the tier gates which copy path runs — never what we recite")

    # --- LOCATION × INDUSTRY — the SkyFi decision stage (incl. the S09 flip) -----
    loc = location_signal(det, tier, ad_variant, ident)
    loc_sigs = [f"region={loc['region'] or region or '—'}", f"tier={tier}",
                f"sector={loc['segment'] or '—'}", f"mode={loc['mode']}"]
    if loc.get("receipt"):
        loc_sigs.append(f"declared_aoi={loc['receipt']['aoi_label']}")
    t("Location signal", loc_sigs, loc["rule"], loc["policy"],
      (f"“{loc['line']}”" if loc["line"] else "no location claim"),
      loc["why"])

    if ident and ident["kind"] == "cohort":
        v = ident["view"]
        t("Identity", [f"{ident['via']} → {ident['email']}"],
          "skyfi_cohort.match(email)" if ident["via"] == "login" else "skyfi_cohort.by_token(e)",
          "say", f"{v['name']} — CRM record found (HubSpot {v['hubspot']['lifecycle']}, "
                 f"score {v['hubspot']['lead_score']}, {v['hubspot']['visits']} visits)",
          "they identified themselves — name and declared facts unlock at say level; "
          "Vector/Clay enrichment stays allude/hold")
        t("Segments → archetype",
          [f"{fam}: " + ", ".join(s["label"] for s in d["segments"]) for fam, d in ident["segments"].items()],
          "segments.derive() → pick_archetype()", "allude",
          f"archetype = {ident['archetype']['label']} ({ident['archetype']['reason']})",
          "behavioral + enriched segments choose emphasis and section order — they are never recited")
    elif ident and ident["kind"] == "resolved":
        r = ident["resolved"]
        t("Identity", [f"login → {ident['email']}"], "resolve_email(): domain → company (first-party)",
          "say", f"company = {r.get('company') or '—'} (tier {r.get('tier', 0)})",
          r.get("reason") or "a work email is a declared identity — the domain names the company, say level")
    else:
        t("Identity", ["(no login, no token)"], "skyfi_cohort.match / by_token", "hold",
          "anonymous", "no identity offered — nothing personal may be said")

    t("Audience route", [aud_rule], "ad variant > campaign intent > CRM > work-email domain > network type",
      "allude", f"audience = {audience}", aud_why)

    # ------------------------------------------------------------------ #
    # Copy slots. Each slot records generic vs shipped (+ the say variant the policy blocks).
    # ------------------------------------------------------------------ #
    diff: list[dict] = []

    def slot(sid, label, generic, shipped, source, policy, blocked_say=None, why=""):
        diff.append({"slot": sid, "label": label, "generic": generic, "shipped": shipped,
                     "changed": generic != shipped, "source": source, "policy": policy,
                     "blocked_say": blocked_say, "why": why})
        return shipped

    hero = dict(GENERIC["hero"])
    how = dict(GENERIC["how"])
    pricing = dict(GENERIC["pricing"])
    cta = dict(GENERIC["cta"])

    # --- hero eyebrow: the one always-on personalization line ---------------
    eyebrow, eyebrow_src, eyebrow_pol = "", "—", "say"
    blocked_eyebrow = None
    if ident and ident["kind"] == "cohort":
        eyebrow = f"Welcome back, {ident['first']}"
        eyebrow_src, eyebrow_pol = f"identity via {ident['via']} (say)", "say"
        li = ident["view"]["linkedin"]
        blocked_eyebrow = (f"{ident['view']['name']} — {li['title']} at {li['company']} — "
                           "we de-anonymized your visit") if li.get("company") else None
    elif ident and ident["kind"] == "resolved" and ident["resolved"].get("company"):
        eyebrow = f"For your team at {ident['resolved']['company']}"
        eyebrow_src, eyebrow_pol = "work-email domain (first-party, say)", "say"
    elif tier >= 2 and industry:
        eyebrow = f"For {industry} operators" + (f" in {region}" if region else "")
        eyebrow_src, eyebrow_pol = "reverse-IP firmographic (allude — shapes, never recites)", "allude"
        blocked_eyebrow = f"{company} — we see your {industry} operation in {city or region}"
    elif tier == 1 and region:
        eyebrow = f"Coverage over {region}, on demand"
        eyebrow_src, eyebrow_pol = "geo-IP region (allude) — the archive-coverage claim", "allude"
    elif entry["channel"] == "email":
        eyebrow = "Straight from your inbox — welcome back"
        eyebrow_src, eyebrow_pol = "email UTM (first-party send)", "allude"
    elif ad_variant:
        eyebrow = ad_variant["page"]["hero_eyebrow"]
        eyebrow_src = f"ad variant {ad_variant['id']} message-match"
        eyebrow_pol = "allude"
    hero["eyebrow"] = slot("hero_eyebrow", "Hero eyebrow", "", eyebrow, eyebrow_src, eyebrow_pol,
                           blocked_say=blocked_eyebrow,
                           why="the always-on line: say-level identity beats first-party domain "
                               "beats IP firmographics beats geo")

    # --- hero location line: THE SkyFi signal (basin scale / declared AOI / AOR) ---
    hero["location_line"] = slot(
        "hero_location", "Hero location line", "", loc["line"],
        ("defense AOR register (strict hold guardrail)" if loc["mode"] == "aor"
         else "declared first-party AOI (say — “you told us”)" if loc["mode"] == "declared_aoi"
         else "geo-IP region × sector template (allude, basin scale)" if loc["mode"] == "region"
         else "no location confidence"),
        loc["policy"],
        blocked_say=loc["blocked_say"],
        why="the geography IS the product — basin/region scale ships because it's true; "
            "exact-AOI is held (arm Ex) unless the visitor declared the AOI themselves")

    # --- hero headline + sub: message-match to the campaign / declared goal --
    h1_pre, h1_blue, sub = hero["h1_pre"], hero["h1_blue"], hero["sub"]
    h_src, h_pol = "—", "say"
    if ad_variant:
        vp = ad_variant["page"]
        h1_pre, h1_blue, sub = vp["h1_pre"], vp["h1_blue"], vp["sub"]
        h_src = f"ad variant {ad_variant['id']} (utm_campaign={ad_variant['utm_campaign']})"
        h_pol = "allude"
    elif entry["channel"] == "ad" and _campaign_intent(entry["utm_campaign"]) == "enterprise":
        h1_pre, h1_blue = "Tasking at ", "Program Scale"
        sub = ("Multi-provider optical and SAR ordered through one flow — commercial "
               "capacity for missions, claims, and programs, quoted upfront.")
        h_src, h_pol = f"ad message-match (utm_campaign={entry['utm_campaign']})", "allude"
    elif entry["channel"] == "ad" and _campaign_intent(entry["utm_campaign"]) == "selfserve":
        h1_pre, h1_blue = "Your AOI, ", "Your Order"
        sub = ("Draw the area, see the price, get the imagery — archive in minutes, "
               "new tasking on demand.")
        h_src, h_pol = f"ad message-match (utm_campaign={entry['utm_campaign']})", "allude"
    elif ident and ident["kind"] == "cohort":
        goal = ident["view"]["declared"].get("goal", "")
        if goal:
            sub = f"You told us you want to {goal} — draw the AOI and go."
            h_src, h_pol = "HubSpot form · interest reason (declared → say)", "say"
        else:
            arch = ident["archetype"]
            sub = f"Tuned for {arch['for']} — " + hero["sub"][0].lower() + hero["sub"][1:]
            h_src, h_pol = f"archetype {arch['label']} (modeled → allude)", "allude"
    hero["h1_pre"], hero["h1_blue"] = h1_pre, h1_blue
    hero["sub"] = slot("hero_sub", "Hero headline + sub", GENERIC["hero"]["sub"], sub, h_src, h_pol,
                       blocked_say=(f"Your modeled income is {ident['view']['deep']['income_band']} — "
                                    "we pre-sized your imagery budget"
                                    if ident and ident["kind"] == "cohort"
                                    and ident["view"]["deep"].get("income_band") else None),
                       why="ad clicks message-match the campaign promise; a declared goal may be "
                           "recited verbatim (say); modeled income is hold — never shipped")
    diff[-1]["generic"] = GENERIC["hero"]["h1_pre"] + GENERIC["hero"]["h1_blue"] + " · " + GENERIC["hero"]["sub"]
    diff[-1]["shipped"] = h1_pre + h1_blue + " · " + sub
    diff[-1]["changed"] = diff[-1]["generic"] != diff[-1]["shipped"]

    # --- hero CTAs: primary/secondary order follows the audience ------------
    ctas = {"enterprise": ("Talk to Tasking Ops", "Browse Imagery"),
            "selfserve": ("Browse Imagery", "Task a Satellite"),
            "neutral": ("Browse Imagery", "Task a Satellite")}[audience]
    if ad_variant:
        vp = ad_variant["page"]
        ctas = (vp["cta_primary"], vp["cta_secondary"])
    if ident and ident["kind"] == "cohort":
        arch_cta = ARCH_CTA.get(ident["archetype"]["id"], ctas[0])
        ctas = (arch_cta, ctas[0] if ctas[0] != arch_cta else ctas[1])
    hero["cta_primary"], hero["cta_secondary"] = ctas
    slot("hero_cta", "Hero CTAs",
         GENERIC["hero"]["cta_primary"] + " / " + GENERIC["hero"]["cta_secondary"],
         ctas[0] + " / " + ctas[1],
         ("archetype CTA (CRM)" if ident and ident["kind"] == "cohort" else f"audience = {audience}"),
         "allude", why="emphasis only — both paths stay on the page")

    # --- how-it-works intro: firmographic + location allusion ----------------
    intro = how["intro"]
    hw_src, hw_pol = "—", "say"
    if ad_variant and ad_variant["page"].get("how_intro"):
        intro = ad_variant["page"]["how_intro"]
        hw_src, hw_pol = f"ad variant {ad_variant['id']} message-match", "allude"
    elif tier >= 2 and industry:
        intro = (f"Built for {industry} workflows — draw the AOI over the ground you "
                 "operate, then choose archive or new tasking.")
        hw_src, hw_pol = "reverse-IP industry (allude)", "allude"
    elif loc["mode"] == "region" and loc["region"]:
        intro = (GENERIC["how"]["intro"] + f" {loc['region']} is already searchable — "
                 "at basin scale, today.")
        hw_src, hw_pol = "geo-IP region (allude) — the archive-coverage claim", "allude"
    elif ident and ident["kind"] == "cohort" and ident["view"]["linkedin"].get("technical"):
        intro = (GENERIC["how"]["intro"] + " You work in the data — delivery lands "
                 "straight in your stack.")
        hw_src, hw_pol = "Clay technical flag (enriched → allude)", "allude"
    how["intro"] = slot("how_intro", "How-it-works intro", GENERIC["how"]["intro"], intro,
                        hw_src, hw_pol,
                        blocked_say=(f"{company}'s sites could use this" if company else None),
                        why="industry and region may shape the frame (allude); the company "
                            "name may not be recited")

    # --- pricing / AOI callout ------------------------------------------------
    pr_body = pricing["body"]
    pr_src, pr_pol = "—", "say"
    if ad_variant and ad_variant["page"].get("pricing_body"):
        pr_body = ad_variant["page"]["pricing_body"]
        pr_src, pr_pol = f"ad variant {ad_variant['id']} message-match", "allude"
    elif ident and ident["kind"] == "cohort" and ident["archetype"]["id"] == "cost_confident":
        pr_body = (GENERIC["pricing"]["body"] + " Start with a single small AOI — the "
                   "quote is the whole commitment.")
        pr_src, pr_pol = "archetype Cost-confident (modeled → allude)", "allude"
    elif loc["mode"] == "declared_aoi":
        pr_body = (GENERIC["pricing"]["body"] + " Your declared AOI is already on file — "
                   "the next capture is one click.")
        pr_src, pr_pol = "declared first-party AOI (say)", "say"
    pricing["body"] = slot("pricing_body", "Pricing / AOI callout", GENERIC["pricing"]["body"],
                           pr_body, pr_src, pr_pol,
                           why="the archetype may add a framing line; the segment itself is "
                               "never named — a declared AOI may be referenced because they "
                               "told us")
    pricing["emphasis"] = bool(loc["mode"] == "declared_aoi"
                               or (ident and ident["kind"] == "cohort"
                                   and ident["archetype"]["id"] == "cost_confident"))

    # --- comparison table: column emphasis follows the audience/sector -------
    compare_emphasis = {"enterprise": "task", "selfserve": "archive", "neutral": None}[audience]
    if loc.get("segment") == "insurance":
        compare_emphasis = "archive"   # loss-aversion, honest: the before-picture exists
    if ad_variant:
        compare_emphasis = ad_variant["page"]["compare_emphasis"]
    slot("compare_emphasis", "Comparison table emphasis", "none (equal columns)",
         compare_emphasis or "none (equal columns)",
         (f"ad variant {ad_variant['id']}" if ad_variant
          else "sector = insurance (before-picture emphasis)" if loc.get("segment") == "insurance"
          else f"audience = {audience}"),
         "allude",
         why="emphasis highlights a column — the table's facts are identical for everyone")

    # --- final CTA -----------------------------------------------------------
    f_head, f_sub = cta["heading"], cta["sub"]
    f_src, f_pol = "—", "say"
    if ad_variant and ad_variant["page"].get("cta_heading"):
        f_head = ad_variant["page"]["cta_heading"]
        f_sub = ad_variant["page"].get("cta_sub") or cta["sub"]
        f_src, f_pol = f"ad variant {ad_variant['id']} message-match", "allude"
    elif loc["mode"] == "declared_aoi":
        f_head, f_sub = "Your AOI is on file", \
            "Fresh coverage of your declared area is one click away — you told us where."
        f_src, f_pol = "declared first-party AOI (say — “you told us”)", "say"
    elif ident and ident["kind"] == "cohort" and ident["archetype"]["id"] == "welcome_back":
        f_head, f_sub = "Pick up where you left off", \
            "Your workspace is saved — the archive kept filling while you were away."
        f_src, f_pol = "HubSpot past-customer (first-party → allude)", "allude"
    elif ident and ident["kind"] == "cohort" and ident["view"]["hubspot"].get("abandoned"):
        f_head, f_sub = "Finish your order", \
            "Your tasking order is most of the way there — the quote is already priced."
        f_src, f_pol = "HubSpot abandoned action (behavioral → allude)", "allude"
    elif loc["mode"] == "region" and loc["region"]:
        f_sub = f"{loc['region']} is already in the archive. Go look."
        f_src, f_pol = "geo-IP region (allude) — location close", "allude"
    cta["heading"], cta["sub"] = f_head, f_sub
    slot("final_cta", "Final CTA block", GENERIC["cta"]["heading"] + " · " + GENERIC["cta"]["sub"],
         f_head + " · " + f_sub, f_src, f_pol,
         blocked_say=(f"You bailed at the {ident['view']['hubspot']['abandoned']} on "
                      f"{ident['view']['hubspot']['visits']} visits — go back"
                      if ident and ident["kind"] == "cohort" and ident["view"]["hubspot"].get("abandoned") else None),
         why="behavioral facts steer the close but are alluded to, never itemized — a "
             "declared AOI may be recited because they told us")

    order = (ad_variant["page"].get("order") if ad_variant and ad_variant["page"].get("order")
             else ORDER_BY_AUDIENCE[audience])
    t("Surface policy", [f"{d['slot']}: {d['policy']}" for d in diff],
      "say = recite · allude = shape only · hold = never ships (docs/04-workflow)",
      "mixed", f"{sum(1 for d in diff if d['changed'])} of {len(diff)} slots personalized",
      "every personalized slot carries its source + policy; the say-level recite variants are "
      "blocked and appear only on /skyfi/dev")
    t("Compose", [f"order = {' → '.join(order)}"],
      f"section order for audience = {audience}", "allude",
      " → ".join(order),
      "same sections, same facts — only emphasis and order move; the structure is identical "
      "before and after login")

    hero_image = IG.resolve_hero_image({
        "entry": entry, "det": det, "identity": ident, "ad_variant": ad_variant,
        "audience": audience, "audience_route": audience, "tier": tier,
        "objections": {"prioritized": []},
        "sections": {"hero": hero, "compare": {"emphasis": compare_emphasis}},
    }, generate=False, tenant=IMAGE_TENANT)
    img_receipt = hero_image.get("receipt") or {}
    img_sigs, img_out, img_why = IG.hero_image_trace(img_receipt)
    t("Hero image resolve", img_sigs,
      "disk cache → (async API if keyed) → scene.image_for gallery → CSS gradient",
      "say", img_out, img_why)

    ledger = _ledger(entry, det, ident, loc)
    ledger.extend(IG.hero_image_ledger_rows(img_receipt))
    login_state = bool(ident and ident.get("via") == "login")
    return {
        "entry": entry, "det": det, "ip_forced": ip_forced, "identity": ident,
        "audience": audience, "audience_rule": aud_rule,
        "audience_route": audience,
        "tier": tier, "tier_label": tier_label, "confidence": conf,
        "location": loc,
        "sections": {"hero": hero,
                     "how": {**how, "cards": list(HOW_CARDS)},
                     "pricing": pricing,
                     "compare": {"rows": COMPARE_ROWS, "emphasis": compare_emphasis},
                     "cta": cta},
        "order": order,
        "nav": {"login_state": login_state,
                "login_email": ident["email"] if ident else "",
                "first": ident["first"] if ident and ident.get("first") else "",
                "known": bool(ident)},
        "login_state": login_state,
        "ad_variant": ad_variant,
        "trace": trace, "copy_diff": diff, "ledger": ledger,
        "hero_image": hero_image,
    }


# --------------------------------------------------------------------------- #
# Signal ledger for /skyfi/dev — source · vendor · disposition (incl. AOI receipt)
# --------------------------------------------------------------------------- #
_DISPOSITION = {"say": "said", "allude": "steer", "hold": "held", "observed": "observed"}


def _ledger(entry: dict, det: dict, ident: dict | None, loc: dict | None = None) -> list[dict]:
    rows: list[dict] = []

    def add(label, value, source, vendor, policy):
        rows.append({"label": label, "value": value if value not in (None, "") else "—",
                     "source": source, "vendor": vendor, "policy": policy,
                     "disposition": _DISPOSITION.get(policy, policy)})

    add("Entry channel", entry["channel_label"], "observed", "UTM / Referer parse", "observed")
    for s in entry["signals"]:
        if s["value"] != "—":
            add(s["label"], s["value"], "observed", "query string / Referer header", "allude")
    for cc in det.get("captured", []):
        add(cc["label"], cc["value"], "observed", "ip-api.com" + (" → PDL" if cc["group"] == "resolved" else ""),
            cc["policy"])
    for cc in det.get("request_signals", []):
        add(cc["label"], cc["value"], "observed", "HTTP headers", cc["policy"])
    if loc and loc.get("line"):
        add("Location line", loc["line"], "derived", "geo-IP region × sector template", loc["policy"])
    if loc and loc.get("receipt"):
        r = loc["receipt"]
        add("Declared AOI (receipt)", f"{r['aoi_label']} · registered {r['registered']}",
            "declared", r["source"], "say")
    if loc and loc.get("blocked_say"):
        add("Location recite (blocked, arm Ex)", loc["blocked_say"], "derived",
            "exact-AOI precision — anti-surveillance ceiling", "hold")
    if ident and ident["kind"] == "cohort":
        raw = ident["crm"]
        v, hs, cl = raw["vector"], raw["hubspot"], raw["clay"]
        add("Email", ident["email"], "declared", f"{ident['via']}", "say")
        add("Name", v["name"], "declared" if ident["via"] == "login" else "first_party",
            "login identity", "say")
        add("Vector — title / company", f"{v['job_title']} · {v['company']}",
            "first_party", "Vector de-anonymization", "allude")
        add("HubSpot — lifecycle / score", f"{hs['lifecycle']} · score {hs['lead_score']} · {hs['visits']} visits",
            "first_party", "HubSpot CRM", "allude")
        if hs.get("submitted") and hs.get("interest_reason"):
            add("Declared goal", f"“{hs['interest_reason']}”", "declared", "HubSpot form", "say")
        if hs.get("declared_aoi"):
            add("Declared AOI", hs["declared_aoi"]["label"], "declared",
                hs["declared_aoi"].get("source", "SkyFi order flow"), "say")
        if hs.get("abandoned"):
            add("Abandoned action", hs["abandoned"], "first_party", "HubSpot form analytics", "allude")
        add("Clay — seniority / industry", f"{cl['seniority']} · {cl['industry']}",
            "broker", "Clay enrichment waterfall", "allude")
        if cl.get("income_band"):
            add("Clay — modeled income", cl["income_band"], "broker", "Clay enrichment waterfall", "hold")
    elif ident and ident["kind"] == "resolved":
        for cc in ident["resolved"].get("captured", []):
            add(cc["label"], cc["value"], "declared", "work-email domain → PDL", cc["policy"])
    return rows


# --------------------------------------------------------------------------- #
# Process map for /skyfi/dev — the pipeline as a diagram. Pure function of the
# built page dict, so the diagram can never drift from what actually ran.
# --------------------------------------------------------------------------- #
NETWORK_BRANCHES = ["corporate", "corporate (via VPN)", "consumer ISP", "residential",
                    "mobile", "VPN / proxy", "hosting / cloud", "private / unreachable"]

LOCATION_BRANCHES = ["basin/region line (allude)", "declared AOI (say)",
                     "AOR register (defense hold)", "no claim (tier 0)"]
_LOC_TAKEN = {"region": "basin/region line (allude)", "declared_aoi": "declared AOI (say)",
              "aor": "AOR register (defense hold)", "none": "no claim (tier 0)"}


def _branches(options: list[str], taken: str | None) -> list[dict]:
    return [{"label": o, "taken": o == taken} for o in options]


def _kv(k: str, v, pol: str | None = None, fired: bool = False) -> dict:
    return {"k": k, "v": v if v not in (None, "") else "—", "pol": pol, "fired": fired}


def process_map(page: dict) -> dict:
    """The /skyfi/dev process diagram: {inputs, stages}. Eleven stages — the Gauntlet
    spine plus the Location × industry stage with the declared-AOI branch (the S09
    flip made visible). Skipped stages stay visible, marked skipped."""
    P = page
    entry, det, ident, ad = P["entry"], P["det"], P["identity"], P.get("ad_variant")
    loc = P.get("location") or {}
    sig = {s["label"]: s["value"] for s in entry["signals"]}

    inputs = [
        {"label": "Query string",
         "value": ", ".join(f"{s['label']}={s['value']}" for s in entry["signals"]
                            if s["value"] != "—" and s["label"] != "Referer header") or "(empty)",
         "feeds": "entry classify · ad variant · IP override"},
        {"label": "Referer header",
         "value": entry["referer"] or "(none)",
         "feeds": "entry classify (search detection)"},
        {"label": "Client IP + headers",
         "value": (det.get("ip") or "private / unreachable")
                  + (" · ?ip= override" if P.get("ip_forced") else ""),
         "feeds": "IP resolve · tier route · location signal"},
        {"label": "Login cookie / magic token",
         "value": (ident["email"] + f" (via {ident['via']})") if ident else "(none — anonymous)",
         "feeds": "identity · CRM · declared AOI"},
    ]

    stages: list[dict] = []

    def stage(id_, title, link, reads, rule, branches, output, why,
              skipped=False, skip_reason="", detail=None):
        stages.append({"id": id_, "title": title, "link": link, "reads": reads,
                       "rule": rule, "branches": branches, "output": output, "why": why,
                       "skipped": skipped, "skip_reason": skip_reason,
                       "detail": detail or []})

    # 1 · entry channel
    entry_detail = [_kv(s["label"], s["value"]) for s in entry["signals"]]
    entry_detail += [
        _kv("rule · ad", "utm_medium ∈ {paid, cpc, ppc, display}", fired=entry["channel"] == "ad"),
        _kv("rule · email", "utm_medium=email (+ optional e= magic token)", fired=entry["channel"] == "email"),
        _kv("rule · search", "?ref ∈ {google, bing, ddg} or a search-engine Referer", fired=entry["channel"] == "search"),
        _kv("rule · direct", "nothing matched — the click says nothing", fired=entry["channel"] == "direct"),
    ]
    stage("entry", "Entry classify", "#sec-entry",
          [f"utm_medium={sig.get('utm_medium', '—')}", f"utm_campaign={sig.get('utm_campaign', '—')}",
           f"ref={sig.get('ref', '—')}", f"e token={'present' if entry['token'] else '—'}"],
          entry["rule"],
          _branches(["ad", "email", "search", "direct"], entry["channel"]),
          f"channel = {entry['channel_label']}", entry["why"],
          detail=entry_detail)

    # 2 · ad variant
    is_ad = entry["channel"] == "ad"
    intent = _campaign_intent(entry.get("utm_campaign"))
    ad_taken = ("catalogued variant" if ad else
                ("campaign keyword intent" if intent else "no match") if is_ad else None)
    if ad:
        vp = ad["page"]
        overridden = [k for k in ("hero_eyebrow", "h1_pre", "sub", "cta_primary", "cta_secondary",
                                  "compare_emphasis", "order", "how_intro", "pricing_body",
                                  "cta_heading") if vp.get(k) not in (None, "", False)]
        ad_detail = [
            _kv("Variant", f"{ad['id']} ({ad['variant_id']}) · campaign {ad['utm_campaign']}"),
            _kv("Segment", ad["segment"]),
            _kv("Ad · trigger", ad["ad"]["trigger"]),
            _kv("Ad · body", ad["ad"]["body"]),
            _kv("Slots overridden", ", ".join(overridden)),
        ]
        if ad.get("hold_note"):
            ad_detail.append(_kv("Hold note", ad["hold_note"], pol="hold"))
    else:
        ad_detail = [
            _kv("Catalog", f"{len(AD_VARIANTS)} X.com variants across SkyFi's verticals"),
            _kv("Lookup order", "utm_content (sv01–sv06) first, then utm_campaign"),
            _kv("Keyword fallback", "campaign name keywords → enterprise / selfserve intent"),
        ]
        if is_ad and intent:
            ad_detail.append(_kv("Matched intent", f"utm_campaign={entry['utm_campaign']} → {intent}", fired=True))
    stage("advariant", "Ad variant resolve", "#sec-entry",
          [f"utm_campaign={sig.get('utm_campaign', '—')}", f"utm_content={sig.get('utm_content', '—')}"],
          "AD_BY_VARIANT_ID / AD_BY_CAMPAIGN lookup, else keyword intent",
          _branches(["catalogued variant", "campaign keyword intent", "no match"], ad_taken),
          (f"{ad['id']} · segment {ad['segment']}" if ad
           else (f"intent = {intent}" if is_ad and intent else "generic ad framing" if is_ad else "—")),
          "a catalogued X variant message-matches every copy slot to the ad promise",
          skipped=not is_ad, skip_reason="not a paid click — no ad promise to match",
          detail=ad_detail)

    # 3 · IP resolve → network type
    firmo = " · ".join(x for x in (
        f"company={det.get('company')}" if det.get("company") else "",
        f"region={det.get('region')}" if det.get("region") else "",
        f"industry={_ind_label(det)}" if _ind_label(det) else "") if x) or "no firmographics"
    ip_detail = ([_kv(cc["label"], f"{cc['value']} → drives {cc['drives']}", pol=cc.get("policy"))
                  for cc in det.get("captured", [])]
                 or [_kv("Captured", "nothing — private / unreachable IP resolves no signals")])
    ip_detail += [_kv(cc["label"], cc["value"], pol=cc.get("policy"))
                  for cc in det.get("request_signals", [])]
    if det.get("reason"):
        ip_detail.append(_kv("Router reason", det["reason"]))
    stage("ip", "IP resolve + classify", "#sec-tier",
          [f"ip={det.get('ip') or '—'}" + (" (?ip= override)" if P.get("ip_forced") else ""),
           f"isp={det.get('isp') or '—'}"],
          "reverse-IP (ip-api) → network flags → deterministic router (scene._classify)",
          _branches(NETWORK_BRANCHES, det.get("network_type") or "private / unreachable"),
          firmo, det.get("reason") or "network flags decide how much the IP is allowed to imply",
          detail=ip_detail)

    # 4 · tier route
    conf = P["confidence"]
    tier_detail = [
        _kv("Confidence · location", conf["location"]),
        _kv("Confidence · company", conf["company"]),
        _kv("Confidence · industry", conf["industry"]),
        _kv("tier 0 · neutral", "nothing usable — real-site default ships", fired=P["tier"] == 0),
        _kv("tier 1 · location-aware", "geo confidence high/medium, not hosting/VPN", fired=P["tier"] == 1),
        _kv("tier 2 · firmographic", "company + industry resolved", fired=P["tier"] == 2),
        _kv("tier 3 · firmographic + competitive", "tier 2 + competitive angle engaged", fired=P["tier"] == 3),
    ]
    stage("tier", "Tier route", "#sec-tier",
          [f"confidence: location={conf['location']} · company={conf['company']} · industry={conf['industry']}"],
          "industry resolved → 2 · geo only → 1 · nothing usable → 0",
          _branches([f"{k} · {v}" for k, v in SC.TIER_LABELS.items()],
                    f"{P['tier']} · {P['tier_label']}"),
          f"tier {P['tier']} · {P['tier_label']}",
          "the tier gates which copy path runs — never what we recite",
          detail=tier_detail)

    # 5 · LOCATION × INDUSTRY — SkyFi's first-class decision (the S09 flip visible)
    loc_detail = [
        _kv("Region (geo-IP)", loc.get("region") or det.get("region") or "—", pol="allude"),
        _kv("Sector", loc.get("segment") or "— (no sector — default line)"),
    ]
    for seg_key, template in SECTOR_LINES.items():
        loc_detail.append(_kv(f"template · {seg_key}", template,
                              fired=loc.get("mode") == "region" and loc.get("segment") == seg_key))
    loc_detail.append(_kv("template · default", DEFAULT_SECTOR_LINE,
                          fired=loc.get("mode") == "region"
                          and loc.get("segment") not in SECTOR_LINES))
    loc_detail.append(_kv("template · defense AOR", AOR_LINE, fired=loc.get("mode") == "aor",
                          pol="hold" if loc.get("mode") == "aor" else None))
    if loc.get("receipt"):
        r = loc["receipt"]
        loc_detail.append(_kv("Declared AOI receipt",
                              f"{r['aoi_label']} · registered {r['registered']} · "
                              f"{r['source']} — {r['say_reason']}",
                              pol="say", fired=True))
    if loc.get("blocked_say"):
        loc_detail.append(_kv("Blocked recite (exact-AOI, arm Ex)", f"“{loc['blocked_say']}”",
                              pol="hold"))
    loc_detail.append(_kv("Guardrail", "basin/region scale only — exact-AOI / specific-asset "
                                       "pinpointing is hold (arm Ex) unless declared "
                                       "first-party; defense/gov is strict hold (AOR)",
                          pol="hold"))
    stage("location", "Location × industry", "#sec-location",
          [f"region={loc.get('region') or det.get('region') or '—'}",
           f"tier={P['tier']}", f"sector={loc.get('segment') or '—'}",
           f"declared_aoi={'yes' if loc.get('receipt') else 'no'}"],
          loc.get("rule", "tier ≥ 1 + region → sector template; declared AOI → say; defense → AOR"),
          _branches(LOCATION_BRANCHES, _LOC_TAKEN.get(loc.get("mode", "none"))),
          (f"“{loc['line']}”" if loc.get("line") else "no location claim ships"),
          loc.get("why", "the geography is the product — basin scale is the honest ceiling"),
          detail=loc_detail)

    # 6 · identity
    id_taken = ("cohort CRM" if ident and ident["kind"] == "cohort"
                else "work-email resolved" if ident and ident["kind"] == "resolved"
                else "anonymous")
    if ident and ident["kind"] == "cohort":
        v = ident["view"]
        id_detail = [
            _kv("Identified via", f"{ident['via']} → {ident['email']}", pol="say"),
            _kv("Name", v["name"], pol="say"),
            _kv("Vector — de-anon", f"{v['linkedin']['title']} · {v['linkedin']['company']} · {v['linkedin']['location']}", pol="allude"),
            _kv("HubSpot — behavior", f"{v['hubspot']['lifecycle']} · score {v['hubspot']['lead_score']} · {v['hubspot']['visits']} visits", pol="allude"),
            _kv("Clay — enrichment", f"{v['linkedin']['seniority']} · {v['linkedin']['tenure']}y · {v['linkedin']['industry']}", pol="allude"),
        ]
        if v["declared"].get("goal"):
            id_detail.append(_kv("Declared goal", f"“{v['declared']['goal']}”", pol="say"))
        if v["declared"].get("aoi"):
            id_detail.append(_kv("Declared AOI", v["declared"]["aoi"]["label"], pol="say", fired=True))
        if v["hubspot"].get("abandoned"):
            id_detail.append(_kv("Abandoned action", v["hubspot"]["abandoned"], pol="allude"))
        if v["deep"].get("income_band"):
            id_detail.append(_kv("Modeled income", v["deep"]["income_band"], pol="hold"))
    elif ident and ident["kind"] == "resolved":
        r = ident["resolved"]
        id_detail = [
            _kv("Identified via", f"login → {ident['email']}", pol="say"),
            _kv("Domain → company", f"{r.get('company') or '—'} · tier {r.get('tier', 0)} ({r.get('tier_label', '—')})"),
        ]
        if r.get("reason"):
            id_detail.append(_kv("Why", r["reason"]))
    else:
        id_detail = [
            _kv("Cookie", "not set — no login this session"),
            _kv("Magic token", "absent — not an identified email click"),
            _kv("What would unlock", f"log in as {sample_login_email()} (cohort CRM) or any work email (domain resolution)"),
        ]
    stage("identity", "Identity", "#sec-crm",
          [f"cookie={'set' if ident and ident.get('via') == 'login' else '—'}",
           f"magic token={'present' if entry['token'] else '—'}"],
          "skyfi_cohort.match(email) / by_token(e), else resolve_email() first-party domain",
          _branches(["cohort CRM", "work-email resolved", "anonymous"], id_taken),
          (f"{ident['email']} via {ident['via']}" if ident else "anonymous"),
          ("they identified themselves — say-level facts unlock; enrichment stays allude/hold"
           if ident else "no identity offered — nothing personal may be said"),
          detail=id_detail)

    # 7 · segments → archetype (cohort only)
    is_cohort = bool(ident and ident["kind"] == "cohort")
    if is_cohort:
        arch = ident["archetype"]
        arch_detail = [_kv(f"{d['label']} ({d['source']})",
                           "; ".join(f"{s['label']} — {', '.join(s['evidence'])}" for s in d["segments"]) or "—",
                           pol="allude")
                       for fam, d in ident["segments"].items()]
        arch_detail += [
            _kv("Archetype picked", f"{arch['label']} — {arch['reason']}", fired=True),
            _kv("Drives", f"emphasis + CTA “{ARCH_CTA.get(arch['id'], arch['cta'])}”"),
        ]
    else:
        arch_detail = [_kv(a["label"], f"for {a['for']} — CTA “{ARCH_CTA.get(aid, a['cta'])}”")
                       for aid, a in SEG.ARCHETYPES.items()]
    stage("archetype", "Segments → archetype", "#sec-crm",
          ([f"{fam}: " + ", ".join(s["label"] for s in d["segments"])
            for fam, d in ident["segments"].items()] if is_cohort else ["(no CRM record)"]),
          "segments.derive() → pick_archetype()",
          _branches([a["label"] for a in SEG.ARCHETYPES.values()],
                    ident["archetype"]["label"] if is_cohort else None),
          (f"archetype = {ident['archetype']['label']}" if is_cohort else "—"),
          ("behavioral + enriched segments choose emphasis and CTA — never recited"
           if is_cohort else ""),
          skipped=not is_cohort, skip_reason="no CRM record — no segments to derive",
          detail=arch_detail)

    # 8 · audience route
    intent = _campaign_intent(entry.get("utm_campaign"))
    fired_rung = ("ad variant" if ad else
                  "campaign intent" if intent else
                  "CRM record" if is_cohort else
                  "work-email domain" if ident and ident["kind"] == "resolved" and ident["resolved"].get("company") else
                  "network type")
    aud_detail = [
        _kv("1 · ad variant", f"{ad['id']} → {ad['audience']}" if ad else "no catalogued ad variant",
            fired=fired_rung == "ad variant"),
        _kv("2 · campaign intent", f"utm_campaign={entry['utm_campaign']} → {intent}" if intent
            else "no campaign keyword match", fired=fired_rung == "campaign intent"),
        _kv("3 · CRM record",
            (f"seniority={ident['view']['linkedin'].get('seniority')} · industry “{ident['view']['linkedin'].get('industry') or '—'}”"
             if is_cohort else "no CRM record"), fired=fired_rung == "CRM record"),
        _kv("4 · work-email domain",
            (f"→ {ident['resolved']['company']}" if ident and ident["kind"] == "resolved"
             and ident["resolved"].get("company") else "no resolved work email"),
            fired=fired_rung == "work-email domain"),
        _kv("5 · network type", det.get("network_type") or "private / unreachable",
            fired=fired_rung == "network type"),
    ]
    stage("audience", "Audience route", "#sec-order",
          [P["audience_rule"]],
          "precedence: ad variant > campaign intent > CRM > work-email domain > network type",
          _branches(["enterprise", "selfserve", "neutral"], P["audience"]),
          f"audience = {P['audience']}",
          "enterprise → tasking-ops emphasis; selfserve → order-flow emphasis",
          detail=aud_detail)

    # 9 · surface policy gate — per-slot say / allude / hold
    diff = P["copy_diff"]
    changed = [d for d in diff if d["changed"]]
    n_say = sum(1 for d in changed if d["policy"] == "say")
    n_allude = sum(1 for d in changed if d["policy"] == "allude")
    n_blocked = sum(1 for d in diff if d.get("blocked_say"))
    pol_detail = [_kv(d["label"], f"{'personalized' if d['changed'] else 'generic'} · source: {d['source']}",
                      pol=d["policy"] if d["changed"] else None, fired=d["changed"])
                  for d in diff]
    pol_detail += [_kv(f"blocked · {d['slot']}", f"“{d['blocked_say']}”", pol="hold")
                   for d in diff if d.get("blocked_say")]
    stage("policy", "Surface policy gate", "#sec-slots",
          [f"{d['slot']}: {d['policy']}" for d in changed] or ["(all slots generic)"],
          "say = recite · allude = shape only · hold = never ships",
          [{"label": f"say — recited ({n_say})", "taken": n_say > 0},
           {"label": f"allude — shaped ({n_allude})", "taken": n_allude > 0},
           {"label": f"hold — blocked ({n_blocked})", "taken": n_blocked > 0}],
          f"{len(changed)} of {len(diff)} slots personalized · {n_blocked} say variants blocked",
          "every personalized slot carries its source + policy; blocked recites appear only on /skyfi/dev",
          detail=pol_detail)

    # 10 · compose
    compose_detail = [
        _kv(f"order · {aud}", " → ".join(order), fired=P["audience"] == aud and P["order"] == order)
        for aud, order in ORDER_BY_AUDIENCE.items()
    ]
    if ad and ad["page"].get("order"):
        compose_detail.append(_kv(f"order · ad override ({ad['id']})",
                                  " → ".join(ad["page"]["order"]),
                                  fired=P["order"] == ad["page"]["order"]))
    stage("compose", "Compose page", "#sec-order",
          [f"audience = {P['audience']}"
           + (f" · ad variant order override ({ad['id']})" if ad and ad["page"].get("order") else "")],
          "ORDER_BY_AUDIENCE, unless the ad variant overrides",
          [],
          " → ".join(P["order"]),
          "same sections, same facts — only emphasis and order move",
          detail=compose_detail)

    # 11 · hero image
    hi = P["hero_image"]
    ir = hi.get("receipt") or {}
    hid = hi.get("dev") or {}
    sel = hid.get("intent_selection") or {}
    src = ir.get("source", "gradient")
    hi_reads = [
        f"status={hi.get('status', 'ready')}",
        f"fallback={hi.get('fallback', 'gradient')}",
        f"intent={ir.get('intent_id', '—')}",
    ]
    if sel.get("rule_fired"):
        hi_reads.append(f"rule={sel['rule_fired'][:48]}")
    g_blocked = ir.get("guardrails_blocked") or []
    if g_blocked:
        hi_reads.append(f"guardrails_blocked={len(g_blocked)}")
    img_detail = []
    if sel.get("rule_fired"):
        img_detail.append(_kv("Intent rule fired", sel["rule_fired"], fired=True))
    img_detail += [_kv(k.replace("_", " ").capitalize(),
                       " → ".join(ir[k]) if k == "fallback_chain"
                       else (str(ir[k])[:220] + "…" if k == "prompt" and len(str(ir[k])) > 220
                             else ir[k]))
                   for k in ("intent_id", "secondary_intent_id", "conversion_goal", "drives_action",
                             "prompt", "model", "vendor", "cache_key", "license",
                             "fallback_chain", "generated_at")
                   if ir.get(k) not in (None, "", [])]
    img_detail += [_kv("Guardrail applied", g, pol="hold") for g in g_blocked]
    if not img_detail:
        img_detail = [_kv("Receipt", "gradient fallback — no cache hit, no API key, no gallery match")]
    stage("heroimg", "Hero image resolve", "#sec-hero-image",
          hi_reads,
          "select_image_intent → build_structured_prompt → guardrails → cache → API → gallery → gradient",
          _branches(["generated", "pending", "gallery", "gradient"], src),
          f"source = {src} · intent = {ir.get('intent_id', '—')}",
          ("structured prompt assembled from signals — page shell renders instantly; "
           "S02's realtime beat generates on first visit and caches by key"),
          detail=img_detail)

    return {"inputs": inputs, "stages": stages}


def sample_login_email() -> str:
    """The cohort email published on demo cards — the construction/EPC known account."""
    return "noor.haddad@terrafirmepc.com"


def sample_magic_token() -> str:
    """The magic token embedded in the sample email entry link — the defense/gov
    strict-hold contact (S07's demo beat)."""
    return CO.magic_token(CO.BY_ID["ingrid"])
