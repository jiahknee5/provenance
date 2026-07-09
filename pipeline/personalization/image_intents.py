"""Structured hero image intents — conversion goals, design research, guardrails.

Each intent maps a visitor context to a visual strategy that supports (not competes with)
the page headline and drives a specific CTA. Deterministic selection only — no LLM."""
from __future__ import annotations

from typing import Any, TypedDict

GAUNTLET_GOLD = "#c9a227"

# Visual metaphors for objection themes — abstract only, never literal objection text.
OBJECTION_METAPHORS: dict[str, str] = {
    "open_market_hire": "empty interview chair beside a glowing terminal — hiring stall abstract",
    "ten_weeks_long": "compressed timeline contrast — hourglass beside sustained observation metaphor",
    "placement_fees": "investment vs idle pilot — stalled dashboard beside active deployment glow",
    "internal_upskill": "split path — team learning lane beside net-new hire lane, abstract",
    "wrong_stack": "multi-stack production floor — adaptability under pressure, abstract",
    "bootcamp_burned": "weekend cert vs sustained shipping — contrast before/after, abstract",
    "no_time_away": "calendar tension beside immersive cohort energy — trade-off abstract",
    "ld_budget_committed": "course stack fading, team champions returning with shipped systems",
    "six_weeks_revert": "fading slide deck beside persistent production deployment",
    "roi_unproven": "ROI clarity — team transformation with measurable deployment metaphor",
    "need_hires_not_training": "hire track emphasis — proven engineer shipping under scrutiny",
    "cant_take_10_weeks": "full-time immersion trade — terminal glow at dusk, abstract",
    "selection_rate_low": "high bar selection — many paths, one lit proving ground",
    "already_senior": "senior engineer at terminal shipping — capstone energy, not classroom",
    "learn_on_job": "ticket queue beside production pressure terminal — gap revealed abstract",
    "opportunity_cost": "sideline observer vs active shipper — career leap abstract",
}

# Industry → environment type (allude only — never company names).
INDUSTRY_ENV: dict[str, str] = {
    "technology": "modern enterprise engineering workspace",
    "financial services": "regulated fintech engineering floor",
    "healthcare": "health-tech engineering operations center",
    "retail": "commerce platform engineering hub",
    "manufacturing": "industrial IoT engineering lab",
    "general": "professional engineering workspace",
}

INTENT_CATALOG: list[dict[str, Any]] = [
    {
        "id": "peer_proof",
        "goal": "Trust → click CTA",
        "design_principles": [
            "Matched-peer environment without literal faces",
            "Social proof via workspace cues, not testimonials",
            "Single focal point — processing fluency",
            "Dark moody base; gold accent zone for headline legibility",
        ],
        "sales_technique": "matched-peer social proof (Cialdini)",
        "allowed_signals": ["industry", "audience_route", "network_corporate", "ad_variant"],
        "blocked_signals": ["visitor_name", "company_name", "exact_city", "income", "gender", "age"],
        "composition_template": (
            "Wide cinematic backdrop: {environment} at dusk, warm monitor glow suggesting "
            "peers already shipping — empty foreground for headline overlay, gold accent rim light."
        ),
        "color_rules": f"Dark charcoal base, warm gold accent ({GAUNTLET_GOLD}), muted teal secondary",
        "visual_metaphor": "industry-matched engineering floor — capability implied by environment",
        "mood": "credible, peer-aligned, calm confidence",
    },
    {
        "id": "loss_avoidance",
        "goal": "Urgency → apply/hire",
        "design_principles": [
            "Abstract loss frame — stalled state, not fear-mongering",
            "Before/after contrast without literal people",
            "Empty chair or idle dashboard as focal metaphor",
            "Supports headline; does not compete for attention",
        ],
        "sales_technique": "loss aversion / cost of inaction (prospect theory)",
        "allowed_signals": ["top_objection", "audience_route", "ad_variant"],
        "blocked_signals": ["invented_urgency", "surveillance", "literal_objection_text"],
        "composition_template": (
            "Split-tone wide backdrop: left — dim stalled dashboard or empty chair; right — "
            "warm gold deployment glow. Abstract only. Foreground dark for headline."
        ),
        "color_rules": f"Cool desaturated stall zone vs warm gold ({GAUNTLET_GOLD}) resolution zone",
        "visual_metaphor": "{objection_metaphor}",
        "mood": "urgent but dignified — opportunity closing, not panic",
    },
    {
        "id": "authority",
        "goal": "B2B hire decision",
        "design_principles": [
            "Demo-day / production deploy metaphor",
            "Scrutiny and observation — buyers evaluating proof",
            "Clean hierarchy, one focal point",
            "Enterprise gravitas without logo wall",
        ],
        "sales_technique": "authority + scrutiny framing (B2B committee buy-in)",
        "allowed_signals": ["audience_route_b2b_hire", "ad_device", "ad_lookalike", "tier_2+"],
        "blocked_signals": ["fake_logos", "named_executives", "company_names"],
        "composition_template": (
            "Wide stage-like engineering demo environment — observation gallery implied by lighting, "
            "production deploy screens glowing gold, abstract audience silhouettes without faces."
        ),
        "color_rules": f"Deep navy-charcoal, gold spotlight ({GAUNTLET_GOLD}), crisp white highlights",
        "visual_metaphor": "demo-day scrutiny — capability observed under production pressure",
        "mood": "evaluative, serious, proof-first",
    },
    {
        "id": "aspiration",
        "goal": "Individual Challenger apply",
        "design_principles": [
            "Engineer at terminal shipping — capstone energy",
            "Individual determination, not classroom",
            "Warm gold terminal glow as aspiration anchor",
            "Clean composition — one hero focal point",
        ],
        "sales_technique": "identity aspiration + self-selection (Challenger route)",
        "allowed_signals": ["audience_route_individual", "ad_interest", "ad_age", "ad_movies"],
        "blocked_signals": ["age_recitation", "gender", "income", "employer"],
        "composition_template": (
            "Single engineer silhouette (no face detail) at a glowing terminal shipping code — "
            "capstone energy, stacks of abstract deployed systems in soft focus behind."
        ),
        "color_rules": f"Dark workspace, terminal gold ({GAUNTLET_GOLD}), energetic teal code accents",
        "visual_metaphor": "career leap — shipping AI-native systems under real pressure",
        "mood": "determined, immersive, forward-leaning",
    },
    {
        "id": "roi_clarity",
        "goal": "HR/L&D buy-in",
        "design_principles": [
            "Team transformation visual — champions returning",
            "Abstract ROI — shipped systems not spreadsheets",
            "Warm, organizational scale without headcount claims",
            "Gold accent zone for headline support",
        ],
        "sales_technique": "organizational ROI + champion return (HR/L&D buyer)",
        "allowed_signals": ["ad_event", "audience_fit_hr", "ld_budget_objection"],
        "blocked_signals": ["dollar_amounts", "income", "company_name"],
        "composition_template": (
            "Team transformation arc: engineers returning from immersive cohort to internal "
            "AI champions — abstract silhouettes, shipped pipeline glow, no org chart text."
        ),
        "color_rules": f"Organizational warm neutrals, gold champion highlight ({GAUNTLET_GOLD})",
        "visual_metaphor": "L&D spend becomes internal AI champions — not certificate stack",
        "mood": "practical, transformative, board-ready",
    },
    {
        "id": "retarget_warm",
        "goal": "Post-engager click",
        "design_principles": [
            "Familiar brand moment — continuation not restart",
            "Warm welcome-back energy without naming visitor",
            "Echo prior engagement (selection rate, proof model)",
            "Single focal point, dark moody base",
        ],
        "sales_technique": "consistency + continuation (Cialdini commitment)",
        "allowed_signals": ["ad_engager", "hubspot_abandoned", "channel_ad"],
        "blocked_signals": ["behavioral_surveillance", "visit_count", "abandoned_step_text"],
        "composition_template": (
            "Warm continuation scene — familiar Gauntlet gold accent on proof-model imagery, "
            "path forward lit, prior context implied by glowing milestone markers not text."
        ),
        "color_rules": f"Warm return palette anchored on brand gold ({GAUNTLET_GOLD})",
        "visual_metaphor": "pick up where you left off — path continues forward",
        "mood": "welcoming, familiar, low-friction",
    },
    {
        "id": "message_match",
        "goal": "Ad click-through",
        "design_principles": [
            "Visual echoes ad promise (Cialdini consistency)",
            "Keyword/hiring → interview room abstract",
            "No text in image — promise via metaphor only",
            "Headline-supporting hierarchy",
        ],
        "sales_technique": "message-match / consistency principle",
        "allowed_signals": ["ad_variant", "utm_campaign", "ad_keyword", "ad_targeting_type"],
        "blocked_signals": ["ad_copy_literal", "company_names", "PII"],
        "composition_template": (
            "Visual continuation of ad promise: {ad_metaphor} — abstract interview-to-proof "
            "transition, gold accent linking ad click to landing headline zone."
        ),
        "color_rules": f"Ad-aligned mood with Gauntlet gold bridge ({GAUNTLET_GOLD})",
        "visual_metaphor": "{ad_metaphor}",
        "mood": "consistent, expected, trust-building",
    },
]

INTENT_BY_ID = {i["id"]: i for i in INTENT_CATALOG}

# Ad variant → message-match visual metaphor (abstract).
AD_METAPHORS: dict[str, str] = {
    "x-keyword": "abstract interview room dissolving into sustained proof observation",
    "x-event": "conference hallway leading to immersive cohort transformation",
    "x-engager": "familiar proof-model milestone path continuing forward",
    "x-interest": "engineer selection gauntlet — lit proving ground ahead",
    "x-conversation": "scaling team velocity — collaborative AI shipping floor",
    "x-location": "tech-hub engineering floor under production pressure",
    "x-device": "desktop due-diligence environment — proof surviving scrutiny",
    "x-age": "senior engineer capstone terminal — career leap energy",
    "x-lookalike": "talent density — elite builder observation environment",
    "x-movies": "documentary viewer becoming shipper — terminal activation",
    "x-language": "direct US engineering path — clean minimal workspace",
    "x-gender": "merit-only selection — execution-focused proving ground",
}

# Objection id → pairs_with for action linkage.
OBJECTION_CTA_PAIR: dict[str, str] = {
    "open_market_hire": "hire_cta",
    "ten_weeks_long": "hire_cta",
    "placement_fees": "hire_cta",
    "ld_budget_committed": "catalyst_cta",
    "no_time_away": "catalyst_cta",
    "roi_unproven": "catalyst_cta",
    "cant_take_10_weeks": "challenger_cta",
    "selection_rate_low": "challenger_cta",
    "already_senior": "challenger_cta",
}


class PersonalizationLayer(TypedDict):
    layer: str
    value: str
    source: str
    disposition: str


class ImageIntentPick(TypedDict):
    intent_id: str
    rank: int
    why: str
    signals_used: list[str]
    disposition: str


class ImageIntentSelection(TypedDict):
    primary: ImageIntentPick
    secondary: ImageIntentPick | None
    intents: list[ImageIntentPick]


class StructuredPrompt(TypedDict, total=False):
    intent_id: str
    secondary_intent_id: str | None
    conversion_goal: str
    sales_technique: str
    personalization_layers: list[PersonalizationLayer]
    composition: str
    visual_metaphor: str
    mood: str
    accent_color: str
    must_include: list[str]
    must_avoid: list[str]
    drives_action: str
    pairs_with_objection: str | None
    guardrails_applied: list[str]
    guardrails_blocked: list[str]
    selection: ImageIntentSelection
    full_prompt: str


def _pick(intent_id: str, rank: int, why: str, signals: list[str],
          disposition: str = "allude") -> ImageIntentPick:
    return {
        "intent_id": intent_id,
        "rank": rank,
        "why": why,
        "signals_used": signals,
        "disposition": disposition,
    }


def _top_objections(ctx: dict) -> list[str]:
    return list(ctx.get("top_objections") or [])


def _ad_id(ctx: dict) -> str | None:
    return ctx.get("ad_variant_id")


def select_image_intent(ctx: dict) -> ImageIntentSelection:
    """Deterministic intent selection from the same signals as build_page."""
    ad_id = _ad_id(ctx)
    route = ctx.get("audience_route", "neutral")
    objections = _top_objections(ctx)
    top1 = objections[0] if objections else None

    picks: list[ImageIntentPick] = []

    # Rule: keyword ad + hire objection #1 → message_match + peer_proof
    if ad_id == "x-keyword" and top1 == "open_market_hire":
        picks.append(_pick("message_match", 1,
                           "keyword ad promise + #1 objection open_market_hire → visual continuity",
                           ["ad_keyword", "objection_open_market_hire"]))
        picks.append(_pick("peer_proof", 2,
                           "hire-track trust gap → matched-peer environment",
                           ["audience_route_b2b_hire", "objection_open_market_hire"]))

    # Rule: HR event + L&D budget objection → roi_clarity
    elif ad_id == "x-event" and top1 == "ld_budget_committed":
        picks.append(_pick("roi_clarity", 1,
                           "HR event ad + L&D budget objection → team transformation ROI visual",
                           ["ad_event", "objection_ld_budget_committed"]))

    # Rule: engineer interest + Challenger route → aspiration
    elif ad_id == "x-interest" and route == "individual":
        picks.append(_pick("aspiration", 1,
                           "interest-targeted ad + individual route → Challenger apply energy",
                           ["ad_interest", "audience_route_individual"]))

    # Rule: post engager → retarget_warm
    elif ad_id == "x-engager":
        picks.append(_pick("retarget_warm", 1,
                           "post-engager retarget → continuation not restart",
                           ["ad_engager"]))

    # Fallbacks by route / ad
    if not picks:
        if ad_id:
            picks.append(_pick("message_match", 1,
                               f"paid ad variant {ad_id} → message-match visual continuity",
                               [f"ad_{ad_id.replace('x-', '')}", "channel_ad"]))
        if route == "b2b_hire":
            picks.append(_pick("authority", len(picks) + 1,
                               "B2B hire route → scrutiny/observation metaphor",
                               ["audience_route_b2b_hire"]))
        elif route == "b2b_upskill":
            picks.append(_pick("roi_clarity", len(picks) + 1,
                               "B2B upskill route → team transformation visual",
                               ["audience_route_b2b_upskill"]))
        elif route == "individual":
            picks.append(_pick("aspiration", len(picks) + 1,
                               "individual route → Challenger aspiration",
                               ["audience_route_individual"]))
        if top1 and top1 in OBJECTION_METAPHORS:
            meta = OBJECTION_METAPHORS[top1]
            if "loss" in meta or top1 in ("open_market_hire", "placement_fees", "cant_take_10_weeks"):
                picks.append(_pick("loss_avoidance", len(picks) + 1,
                                   f"top objection {top1} → abstract loss-frame metaphor",
                                   [f"objection_{top1}"]))
            else:
                picks.append(_pick("peer_proof", len(picks) + 1,
                                   f"top objection {top1} → peer-trust environment",
                                   [f"objection_{top1}"]))
        if not picks:
            picks.append(_pick("peer_proof", 1,
                               "neutral context → credible peer environment default",
                               ["default_peer_proof"]))

    # Deduplicate by intent_id keeping best rank
    seen: dict[str, ImageIntentPick] = {}
    for p in picks:
        if p["intent_id"] not in seen or p["rank"] < seen[p["intent_id"]]["rank"]:
            seen[p["intent_id"]] = p
    ordered = sorted(seen.values(), key=lambda x: x["rank"])
    for i, p in enumerate(ordered):
        p["rank"] = i + 1

    primary = ordered[0]
    secondary = ordered[1] if len(ordered) > 1 else None
    return {"primary": primary, "secondary": secondary, "intents": ordered}


def _resolve_drives_action(ctx: dict, top_objection: str | None) -> str:
    cta = (ctx.get("cta_primary") or "").lower()
    if top_objection and top_objection in OBJECTION_CTA_PAIR:
        return OBJECTION_CTA_PAIR[top_objection]
    if "challenger" in cta or "apply" in cta:
        return "challenger_cta"
    if "upskill" in cta or "catalyst" in cta:
        return "catalyst_cta"
    if "hire" in cta:
        return "hire_cta"
    route = ctx.get("audience_route", "neutral")
    if route == "individual":
        return "challenger_cta"
    if route == "b2b_upskill":
        return "catalyst_cta"
    if route == "b2b_hire":
        return "hire_cta"
    return "program_overview"


def build_structured_prompt(ctx: dict, selection: ImageIntentSelection) -> StructuredPrompt:
    """Assemble StructuredPrompt from intent templates + ctx (guardrails applied downstream)."""
    primary_id = selection["primary"]["intent_id"]
    intent = INTENT_BY_ID[primary_id]
    secondary_id = selection["secondary"]["intent_id"] if selection.get("secondary") else None

    ad_id = _ad_id(ctx) or ""
    objections = _top_objections(ctx)
    top1 = objections[0] if objections else None
    industry_key = ctx.get("industry") or "general"
    environment = INDUSTRY_ENV.get(industry_key, INDUSTRY_ENV["general"])
    objection_metaphor = OBJECTION_METAPHORS.get(top1 or "", "stalled initiative beside active deployment")
    ad_metaphor = AD_METAPHORS.get(ad_id, "AI engineering proof environment — abstract continuity")

    layers: list[PersonalizationLayer] = []

    if industry_key != "general":
        layers.append({
            "layer": "industry",
            "value": environment,
            "source": "reverse-IP industry (tier-gated)",
            "disposition": "allude",
        })

    region = ctx.get("region")
    if region:
        layers.append({
            "layer": "region_mood",
            "value": f"{region} regional tone — no landmarks",
            "source": "geo-IP region",
            "disposition": "allude",
        })

    if ad_id:
        layers.append({
            "layer": "ad_message_match",
            "value": ad_metaphor,
            "source": f"ad variant {ad_id}",
            "disposition": "allude",
        })

    if top1:
        layers.append({
            "layer": "objection_theme",
            "value": objection_metaphor,
            "source": f"objection #{1} {top1}",
            "disposition": "allude",
        })

    if ctx.get("audience_route"):
        layers.append({
            "layer": "audience_route",
            "value": ctx["audience_route"],
            "source": "build_page audience route",
            "disposition": "allude",
        })

    composition = intent["composition_template"].format(
        environment=environment,
        objection_metaphor=objection_metaphor,
        ad_metaphor=ad_metaphor,
    )
    visual_metaphor = intent["visual_metaphor"].format(
        objection_metaphor=objection_metaphor,
        ad_metaphor=ad_metaphor,
    )

    must_include = [
        "cinematic wide 16:9 hero backdrop",
        "dark moody atmosphere supporting headline overlay",
        f"warm gold accent lighting ({GAUNTLET_GOLD})",
        "single clear focal point — processing fluency",
        f"conversion goal: {intent['goal']}",
    ]
    if secondary_id:
        sec = INTENT_BY_ID[secondary_id]
        must_include.append(f"secondary visual cue: {sec['visual_metaphor']}")

    must_avoid = [
        "NO faces of real people or identifiable individuals",
        "NO company logos or brand marks",
        "NO text, words, letters, or numbers in the image",
        "NO visitor names, employer names, or PII",
        "NO surveillance, creepy, or behavioral-tracking imagery",
        "NO literal objection quotes or ad copy as text overlay",
        "NO maps, addresses, or exact city landmarks",
        "NO demographic or compensation modeling cues",
    ]

    drives_action = _resolve_drives_action(ctx, top1)

    return {
        "intent_id": primary_id,
        "secondary_intent_id": secondary_id,
        "conversion_goal": intent["goal"],
        "sales_technique": intent["sales_technique"],
        "personalization_layers": layers,
        "composition": composition,
        "visual_metaphor": visual_metaphor,
        "mood": intent["mood"],
        "accent_color": GAUNTLET_GOLD,
        "must_include": must_include,
        "must_avoid": must_avoid,
        "drives_action": drives_action,
        "pairs_with_objection": top1,
        "guardrails_applied": [],
        "guardrails_blocked": [],
        "selection": selection,
        "full_prompt": "",  # filled after guardrail pass
    }


def assemble_full_prompt(structured: StructuredPrompt) -> str:
    """Flatten StructuredPrompt into API-ready text."""
    parts = [
        "Cinematic wide hero backdrop for an AI engineering talent program marketing site.",
        f"Primary intent: {structured['intent_id']} — {structured['conversion_goal']}.",
        f"Sales technique: {structured['sales_technique']}.",
        f"Composition: {structured['composition']}",
        f"Visual metaphor: {structured['visual_metaphor']}",
        f"Mood: {structured['mood']}. Accent color {structured['accent_color']}.",
    ]
    if structured.get("secondary_intent_id"):
        parts.append(f"Secondary intent cue: {structured['secondary_intent_id']}.")
    for layer in structured.get("personalization_layers") or []:
        parts.append(f"{layer['layer']} ({layer['disposition']}): {layer['value']}.")
    parts.append("Must include: " + "; ".join(structured.get("must_include") or []) + ".")
    parts.append("Must avoid: " + "; ".join(structured.get("must_avoid") or []) + ".")
    parts.append(f"Drives action: {structured.get('drives_action', 'program_overview')}.")
    return " ".join(parts)
