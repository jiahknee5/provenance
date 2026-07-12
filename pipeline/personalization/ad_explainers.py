"""Marketer-facing "the thinking" explainers for every X.com ad variant.

For each catalogued ad variant (gauntlet 12 · planet 12 · skyfi 6) this module builds a
six-beat explainer a marketer can read next to the ad mockup:

  1. thought      — why this creative angle for this targeting bucket
  2. targeting    — the variant's real targeting config + why a marketer picks it
  3. development  — how the hook/copy/CTA are built from the variant's actual fields
  4. mechanic     — the exact click → classify_entry → resolve_ad_variant → message-match
  5. promise      — the variant's ACTUAL landing-page overrides, quoted
  6. imagery      — the real image intent (rules/<tenant>_image.yaml) the variant maps to

Every quoted string is read from the live catalogs (gauntlet_site / planet_site /
skyfi_site) or the tenant image YAML via image_intents — nothing invented (Art I).
The only authored text is the marketing rationale per targeting family, which explains
the mechanic; it never adds product claims. Deterministic — no LLM, no RNG, $0 offline.
"""
from __future__ import annotations

from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_intents as II
from pipeline.personalization import planet_site as PLS
from pipeline.personalization import skyfi_site as SS

# --------------------------------------------------------------------------- #
# Curated rationale per X Ads Manager targeting family (marketing language).
# Keys are the EXACT x_targeting_type strings the catalogs use.
# --------------------------------------------------------------------------- #
TARGETING_RATIONALE: dict[str, dict[str, str]] = {
    "Location targeting": {
        "thought": ("Geography is a proxy for shared context: the metros in the config "
                    "concentrate buyers living the same day-to-day problem, so the creative "
                    "opens on a regional pattern the reader recognizes as their own."),
        "pick": ("A marketer picks location targeting when the pain clusters "
                 "geographically — the ad can say “your region” honestly, and the "
                 "landing page can keep that promise without guessing about the person."),
    },
    "Language targeting": {
        "thought": ("Language-only targeting is the deliberate broad-reach play: no persona "
                    "assumptions survive the click, so the creative carries one universal "
                    "problem statement that works for every audience the click could contain."),
        "pick": ("A marketer picks language targeting for top-of-funnel awareness — maximum "
                 "reach, minimum inference. The variant must stay cross-audience by design."),
    },
    "Device, platform, & Wi-Fi targeting": {
        "thought": ("Delivery context is intent context: desktop, on office Wi-Fi, during "
                    "office hours signals research mode — so the creative talks like a vendor "
                    "evaluation, not an impulse scroll."),
        "pick": ("A marketer picks device/connection targeting to catch the buyer in "
                 "evaluation posture — the moment when proof and comparison tables beat "
                 "emotional hooks."),
    },
    "Age targeting": {
        "thought": ("An age band is a career-stage proxy, never a fact the page repeats: the "
                    "ad speaks to where the reader is in their arc, while the landing page "
                    "deliberately holds age (surface policy — a hold-tier fact)."),
        "pick": ("A marketer picks age targeting to match message to career stage in the ad "
                 "auction only — the demo fact stays in X Ads Manager and never reaches the "
                 "page copy."),
    },
    "Gender targeting": {
        "thought": ("All-genders is deliberate anti-targeting: the creative makes "
                    "merit-based selection the message itself, and the landing page holds "
                    "gender entirely (surface policy)."),
        "pick": ("A marketer picks broad gender targeting when the value proposition is "
                 "universal and the brand story benefits from saying so out loud."),
    },
    "Conversation targeting": {
        "thought": ("Conversation targeting catches people mid-thought — they are already "
                    "discussing the topic in the config, so the creative skips context-setting "
                    "and joins the thread they started."),
        "pick": ("A marketer picks conversation targeting for in-market relevance without "
                 "keywords: the audience self-selected by talking about the problem this week."),
    },
    "Event targeting": {
        "thought": ("Event targeting reaches the buyer inside a professional moment: the "
                    "creative references the job-to-be-done that put them at that event, so "
                    "the ad reads like a hallway conversation, not an interruption."),
        "pick": ("A marketer picks event targeting when budget cycles and buying committees "
                 "gather in one place — relevance is bought by the calendar, not the cookie."),
    },
    "Post Engager targeting": {
        "thought": ("Retargeting warm engagement: this audience has already met the brand, "
                    "so the creative continues the story — “you saw X, here's the rest” — "
                    "rather than restarting the pitch from zero."),
        "pick": ("A marketer picks post-engager retargeting because recognition is the "
                 "cheapest trust there is: the second touch converts on continuation, "
                 "and the landing page opens with welcome-back framing."),
    },
    "Keyword targeting": {
        "thought": ("Keyword targeting is the highest-intent signal in the catalog: the "
                    "reader engaged the exact phrases in the config, so the creative names "
                    "the problem back almost verbatim — message-match matters most here."),
        "pick": ("A marketer picks keyword targeting to buy declared intent — and accepts "
                 "the obligation that ad, headline, and hero must echo the same promise."),
    },
    "Movies & TV targeting": {
        "thought": ("Content affinity is an aspiration signal: watchers are not yet doers, "
                    "so the creative frames the product as the bridge from watching the "
                    "story to being in it."),
        "pick": ("A marketer picks Movies & TV targeting to reach motivated spectators — "
                 "an audience warmed by the genre but never pitched by the category."),
    },
    "Interest targeting": {
        "thought": ("Interest targeting buys relevance at scale: affinity for the space is "
                    "known, intent is not — so the creative leads with the strongest "
                    "credibility fact in the variant and lets self-selection do the rest."),
        "pick": ("A marketer picks interest targeting to fill the top of a considered "
                 "funnel with people who already care about the category."),
    },
    "Follower look-alikes targeting": {
        "thought": ("Look-alikes borrow trust: the audience is modeled on followers of "
                    "respected accounts in the config, so the creative speaks in the register "
                    "those leaders use — peer language, not vendor language."),
        "pick": ("A marketer picks follower look-alikes to inherit an audience's taste "
                 "graph — the halo of who they follow shapes what the ad may assume."),
    },
}

# SkyFi's six creatives are vertical (industry) plays, not X targeting types.
SKYFI_VERTICAL_RATIONALE: dict[str, str] = {
    "mining": ("Mining is a geography-first sale: the operation IS a basin, so the creative "
               "sells eyes-on-site without the site visit — and honors the scale ceiling "
               "(basin/region only, never a single pit)."),
    "construction": ("Construction buyers are deadline-driven documentarians: the creative "
                     "sells progress proof on the buyer's schedule, not the flyover's."),
    "agriculture": ("Agriculture is region-scale by nature: the creative sells the whole "
                    "growing region seen weekly, with SAR as the honest answer to cloud cover."),
    "insurance": ("Insurance buys evidence, not imagery: the creative leads with the archive "
                  "as the before-picture that already exists — loss framing that is literally true."),
    "energy": ("Energy corridors are linear assets measured in truck rolls: the creative "
               "sells archive-first checks so crews roll only where something changed."),
    "defense": ("Defense is the register-discipline play: AOR/theater framing only, "
                "multi-provider procurement as the hook — the creative proves restraint "
                "is the product (never a specific asset, never the visitor's location)."),
}

SKYFI_VERTICAL_PICK = ("A marketer picks vertical (industry) creative on X because SkyFi's "
                       "buyer is defined by the ground they manage, not a demographic — the "
                       "sector supplies the message, the order flow stays identical.")

_BEAT_TITLES: list[tuple[str, str]] = [
    ("thought", "The thought process for this ad"),
    ("targeting", "Targeting type — and why"),
    ("development", "How the ad is developed — and why"),
    ("mechanic", "How it leads to the landing page"),
    ("promise", "What to expect on the landing page (copy)"),
    ("imagery", "What to expect in the landing-page imagery"),
]

# --------------------------------------------------------------------------- #
# Tenant registry — site module + defaults. h1 accent key differs per brand.
# --------------------------------------------------------------------------- #
_TENANTS: dict[str, dict] = {
    "gauntlet": {"site": GS, "h1_key": "h1_gold", "domain": "gauntletai.com",
                 "page_path": "/gauntlet", "dev_path": "/dev"},
    "planet": {"site": PLS, "h1_key": "h1_blue", "domain": "planet.com",
               "page_path": "/planet", "dev_path": "/planet/dev"},
    "skyfi": {"site": SS, "h1_key": "h1_blue", "domain": "skyfi.com",
              "page_path": "/skyfi", "dev_path": "/skyfi/dev"},
}


def _image_route(tenant: str, variant: dict) -> str:
    """The audience_route the image layer sees when this ad is clicked (segment level)."""
    if tenant == "gauntlet":
        # Same mapping build_page uses: audience_fit → b2b_hire/b2b_upskill/individual.
        return GS._audience_route(variant["audience"], variant, None)
    return variant.get("audience", "neutral")


def _image_selection(tenant: str, variant: dict) -> tuple[dict, dict, dict]:
    """(config, selection, primary intent) for the ad-click segment context —
    exactly the tier-1 ctx image_gen uses (no objections/industry/region yet)."""
    config = II.load_image_config(tenant)
    ctx = {
        "channel": "ad",
        "ad_variant_id": variant["id"],
        "audience_route": _image_route(tenant, variant),
        "tier": 0,
        "top_objections": [],
        "industry": "general",
        "region": None,
        "archetype_id": None,
    }
    selection = II.select_image_intent(ctx, config)
    intent = config["intent_by_id"][selection["primary"]["intent_id"]]
    return config, selection, intent


def _h1(variant: dict, h1_key: str) -> str:
    p = variant["page"]
    return p["h1_pre"] + (p.get(h1_key) or "")


def _who(tenant: str, variant: dict) -> str:
    if tenant == "skyfi":
        return f"the {variant['segment']} vertical"
    return variant["audience_fit_label"]


def _beat(key: str, title: str, body: str, points: list[str]) -> dict:
    return {"key": key, "title": title, "body": body,
            "points": [p for p in points if p]}


def explainer_for(tenant: str, variant: dict, *,
                  page_path: str | None = None,
                  dev_path: str | None = None) -> dict:
    """Six-beat marketer explainer for one catalogued ad variant.

    Returns {thought, targeting, development, mechanic, promise, imagery,
    beats (ordered list of the same dicts), landing_url, dev_url, condensed, …}.
    Every quoted field is read from the variant/catalog/YAML — nothing invented.
    """
    reg = _TENANTS[tenant]
    site = reg["site"]
    page_path = page_path or reg["page_path"]
    dev_path = dev_path or reg["dev_path"]

    ad = variant["ad"]
    page = variant["page"]
    who = _who(tenant, variant)
    h1 = _h1(variant, reg["h1_key"])
    landing_url = site.variant_landing_url(variant, page_path)
    utm_qs = (f"utm_source={variant['utm_source']}&utm_medium={variant['utm_medium']}"
              f"&utm_campaign={variant['utm_campaign']}&utm_content={variant['variant_id']}")
    dev_url = f"{dev_path}?{utm_qs}&as=anon"

    ttype = variant.get("x_targeting_type")
    texample = variant.get("x_targeting_example")

    # ---- 1 · thought process ------------------------------------------------
    if tenant == "skyfi":
        family_thought = SKYFI_VERTICAL_RATIONALE[variant["segment"]]
        pick_why = SKYFI_VERTICAL_PICK
        targeting_label = "Vertical creative"
    else:
        fam = TARGETING_RATIONALE[ttype]
        family_thought = fam["thought"]
        pick_why = fam["pick"]
        targeting_label = ttype
    thought_body = (f"{family_thought} This variant aims that logic at {who}: the ad "
                    f"promise and the landing hero “{h1}” are written as one "
                    f"continuous argument, so the click never feels like a channel change.")
    beat_thought = _beat("thought", _BEAT_TITLES[0][1], thought_body, [
        f"Audience: {who}",
        f"Catalog id: {variant['id']} · {variant['variant_id']}",
        (f"Category: {variant['category']}" if variant.get("category") else ""),
    ])

    # ---- 2 · targeting type + why -------------------------------------------
    if tenant == "skyfi":
        targeting_body = (f"Targeting: vertical creative for the {variant['segment']} segment "
                          f"(catalog category “{variant['category']}”), routed "
                          f"{variant['audience']}. {pick_why}")
        targeting_points = [f"Segment: {variant['segment']}",
                            f"Audience route: {variant['audience']}",
                            f"Campaign: utm_campaign={variant['utm_campaign']}"]
    else:
        targeting_body = (f"Targeting type: {ttype}. X Ads Manager config: "
                          f"“{texample}”. {pick_why}")
        targeting_points = [f"X config: {texample}",
                            f"Best for: {who}",
                            f"Audience route: {variant['audience']}"]
    beat_targeting = _beat("targeting", _BEAT_TITLES[1][1], targeting_body, targeting_points)

    # ---- 3 · how the ad is developed ----------------------------------------
    proof = ad.get("proof")
    dev_body = (f"The hook opens on the bucket's reality — “{ad['trigger']}” — "
                f"then the body argues one idea for {who}"
                + (f", and the proof line carries the verifiable claim: “{proof}”"
                   if proof else "")
                + f". The CTA stays soft (“{ad['cta_label']}”): high-consideration "
                  f"audiences click curiosity, not commands. Audience routing "
                  f"({variant['audience']}) decides which sections the landing page "
                  f"emphasizes after the click.")
    beat_development = _beat("development", _BEAT_TITLES[2][1], dev_body, [
        f"Hook: “{ad['trigger']}”",
        (f"Proof: “{proof}”" if proof else ""),
        f"CTA label: “{ad['cta_label']}”",
        (f"Compare-table emphasis: {page['compare_emphasis']}"
         if page.get("compare_emphasis") else ""),
    ])

    # ---- 4 · mechanic: click → classify → resolve → message-match ------------
    mech_body = (f"The click carries {utm_qs}. classify_entry() reads utm_medium=paid → "
                 f"channel “ad”; resolve_ad_variant() matches "
                 f"utm_content={variant['variant_id']} in the catalog "
                 f"(utm_campaign={variant['utm_campaign']} is the fallback key) and this "
                 f"variant's page overrides ship — the hero message-matches the ad promise "
                 f"deterministically, same URL → same page.")
    beat_mechanic = _beat("mechanic", _BEAT_TITLES[3][1], mech_body, [
        f"Landing URL: {landing_url}",
        f"Lookup: AD_BY_VARIANT_ID[“{variant['variant_id']}”] → "
        f"{variant['id']}",
    ])

    # ---- 5 · the promise the page must keep ----------------------------------
    promise_body = (f"The page must keep the ad's promise. Hero: “{h1}” — "
                    f"sub: “{page['sub']}” Primary CTA “{page['cta_primary']}”, "
                    f"secondary “{page['cta_secondary']}”.")
    order = page.get("order")
    beat_promise = _beat("promise", _BEAT_TITLES[4][1], promise_body, [
        (f"Eyebrow: “{page['hero_eyebrow']}”" if page.get("hero_eyebrow") else ""),
        (f"Section order override: {' → '.join(order)}" if order else ""),
        (f"Hold policy: {variant['hold_note']}" if variant.get("hold_note") else ""),
    ])

    # ---- 6 · the imagery this audience will see ------------------------------
    config, selection, intent = _image_selection(tenant, variant)
    intent_id = intent["id"]
    metaphor = (config.get("ad_metaphors") or {}).get(variant["id"], "")
    mood = intent.get("mood", "")
    imagery_body = (f"rules/{tenant}_image.yaml maps this click to image intent "
                    f"“{intent_id}” — {selection['primary']['why']}. The ad-metaphor "
                    f"the hero renders: “{metaphor}” — mood “{mood}”.")
    imagery_points = [
        f"Intent: {intent_id} · conversion goal “{intent.get('conversion_goal', '')}”",
        f"Selection rule fired: {selection['rule_fired']}",
        (f"Secondary intent: {selection['secondary']['intent_id']}"
         if selection.get("secondary") else ""),
    ]
    if tenant == "planet":
        imagery_points.append(
            f"Sector angle: {variant['segment']} — landscape-scale satellite aesthetic; "
            f"regional landform may shade the scene (allude), never street scale.")
    if tenant == "skyfi":
        env = (config.get("industry_env") or {}).get(variant["segment"])
        imagery_points.append(
            f"Location × sector: {variant['segment']} at basin/region scale only — "
            f"exact-AOI pinpointing is hold (arm Ex)"
            + (f"; sector environment: “{env}”" if env else ""))
    if variant.get("hold_note"):
        imagery_points.append(f"Register guardrail: {variant['hold_note']}")
    beat_imagery = _beat("imagery", _BEAT_TITLES[5][1], imagery_body, imagery_points)

    beats = [beat_thought, beat_targeting, beat_development,
             beat_mechanic, beat_promise, beat_imagery]

    condensed = (f"{targeting_label} → {who}. "
                 f"{family_thought.split(': ')[0].split(' — ')[0]}. "
                 f"Imagery runs intent “{intent_id}” — {mood}.")

    return {
        "tenant": tenant,
        "id": variant["id"],
        "variant_id": variant["variant_id"],
        "thought": beat_thought,
        "targeting": beat_targeting,
        "development": beat_development,
        "mechanic": beat_mechanic,
        "promise": beat_promise,
        "imagery": beat_imagery,
        "beats": beats,
        "landing_url": landing_url,
        "dev_url": dev_url,
        "condensed": condensed,
    }


def explainers_for_tenant(tenant: str, *, page_path: str | None = None,
                          dev_path: str | None = None) -> dict[str, dict]:
    """variant_id → explainer for every catalogued variant of one tenant."""
    site = _TENANTS[tenant]["site"]
    return {v["variant_id"]: explainer_for(tenant, v, page_path=page_path,
                                           dev_path=dev_path)
            for v in site.AD_VARIANTS}
