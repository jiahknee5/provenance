"""Hero image decision guide — /gauntletapt/image-decisions.

Deterministic view model: intent taxonomy, pipeline, two-tier strategy, live comparisons.
No LLM; reads rules/gauntlet_image.yaml + image_gen resolution for thumbnails."""
from __future__ import annotations

from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II

# Narrative enrichments — conversion psychology (not in YAML; stable doc copy).
_VISITOR_FEELS: dict[str, str] = {
    "peer_proof": (
        "This looks like my world — credible peers already shipping, not a generic stock photo."
    ),
    "loss_avoidance": (
        "Something valuable is stalling while others move — I should act before the gap widens."
    ),
    "authority": (
        "Serious buyers evaluate proof here — this program survives scrutiny, not slide-deck theater."
    ),
    "aspiration": (
        "That could be me at the terminal — immersive, high-bar, worth the leap."
    ),
    "roi_clarity": (
        "Our L&D spend could become internal champions, not another certificate stack."
    ),
    "retarget_warm": (
        "I already started this journey — low friction to pick up where I left off."
    ),
    "message_match": (
        "The page continues what the ad promised — no bait-and-switch, I clicked for a reason."
    ),
}

_WHY_IT_WORKS: dict[str, str] = {
    "peer_proof": (
        "Matched-environment social proof raises processing fluency: one focal scene that feels "
        "industry-native without naming the visitor's employer — trust before the headline asks for it."
    ),
    "loss_avoidance": (
        "Prospect-theory loss framing (abstract stall vs warm deployment) pairs with hire-track "
        "objections — urgency without surveillance or invented scarcity."
    ),
    "authority": (
        "B2B committees need evaluative gravitas: demo-day scrutiny metaphor signals proof-first "
        "culture and aligns with hire CTAs on corporate routes."
    ),
    "aspiration": (
        "Identity aspiration + self-selection for Challenger routes: terminal-shipping energy "
        "filters tire-kickers and lifts apply intent on individual paths."
    ),
    "roi_clarity": (
        "HR/L&D buyers need organizational ROI in visual form — champions returning with shipped "
        "systems, not spreadsheets — supporting Catalyst CTAs."
    ),
    "retarget_warm": (
        "Cialdini consistency: continuation cues reduce cognitive dissonance after an ad engager "
        "click — same gold accent path forward, no creepy 'we saw you' copy."
    ),
    "message_match": (
        "Ad-to-landing consistency (Cialdini) cuts bounce: abstract metaphor echoes the ad "
        "promise so the hero supports the personalized headline instead of fighting it."
    ),
}

# Canonical live demo URL per intent (UTM params that fire selection rules).
_INTENT_DEMO_VARIANT: dict[str, str] = {
    "peer_proof": "",  # direct — no ad variant
    "loss_avoidance": "x-keyword",  # compound rule + hire objection
    "authority": "x-device",
    "aspiration": "x-interest",
    "roi_clarity": "x-event",
    "retarget_warm": "x-engager",
    "message_match": "x-keyword",
}

_ACTION_LABELS: dict[str, str] = {
    "hire_cta": "Hire Proven Talent",
    "catalyst_cta": "Upskill Your Team",
    "challenger_cta": "Apply to Challenger",
    "program_overview": "Explore the program",
}

_THUMB_GRADIENTS: dict[str, str] = {
    "peer_proof": "linear-gradient(135deg,#0f1419 0%,#1a2332 45%,#2a3444 100%)",
    "loss_avoidance": "linear-gradient(90deg,#1a1f2e 0%,#1a1f2e 48%,#2a2418 52%,#3d3218 100%)",
    "authority": "linear-gradient(135deg,#0d1520 0%,#1a2840 50%,#c9a22733 100%)",
    "aspiration": "linear-gradient(135deg,#0a0e14 0%,#14202a 40%,#c9a22755 100%)",
    "roi_clarity": "linear-gradient(135deg,#1c1914 0%,#2a241c 50%,#c9a22744 100%)",
    "retarget_warm": "linear-gradient(135deg,#1a1510 0%,#2a2218 60%,#c9a22766 100%)",
    "message_match": "linear-gradient(135deg,#12100c 0%,#1e1a14 45%,#c9a22755 100%)",
}


def _variant_by_id(vid: str) -> dict | None:
    if not vid:
        return None
    return GS.AD_BY_VARIANT_ID.get(vid)


def _demo_landing_url(intent_id: str, page_path: str) -> str:
    vid = _INTENT_DEMO_VARIANT.get(intent_id, "")
    if not vid:
        return page_path
    v = _variant_by_id(vid)
    if not v:
        return page_path
    return GS.variant_landing_url(v, page_path)


def _default_drives_action(intent_id: str, config: dict) -> str:
    action_map = config.get("action_map") or {}
    route_defaults = action_map.get("route_defaults") or {}
    by_intent = {
        "peer_proof": action_map.get("default", "program_overview"),
        "loss_avoidance": "hire_cta",
        "authority": route_defaults.get("b2b_hire", "hire_cta"),
        "aspiration": route_defaults.get("individual", "challenger_cta"),
        "roi_clarity": route_defaults.get("b2b_upskill", "catalyst_cta"),
        "retarget_warm": action_map.get("default", "program_overview"),
        "message_match": "hire_cta",
    }
    return by_intent.get(intent_id, action_map.get("default", "program_overview"))


def _build_intent_card(intent: dict, *, page_path: str, config: dict) -> dict:
    iid = intent["id"]
    drives = _default_drives_action(iid, config)
    return {
        "id": iid,
        "conversion_goal": intent.get("conversion_goal", intent.get("goal", "")),
        "sales_technique": intent["sales_technique"],
        "visitor_feels": _VISITOR_FEELS.get(iid, ""),
        "drives_action": drives,
        "drives_action_label": _ACTION_LABELS.get(drives, drives.replace("_", " ")),
        "visual_metaphor": intent["visual_metaphor"],
        "mood": intent["mood"],
        "why_it_works": _WHY_IT_WORKS.get(iid, ""),
        "design_principles": intent.get("design_principles") or [],
        "live_url": _demo_landing_url(iid, page_path),
        "live_label": _variant_by_id(_INTENT_DEMO_VARIANT.get(iid, ""))["x_targeting_type"]
        if _INTENT_DEMO_VARIANT.get(iid) and _variant_by_id(_INTENT_DEMO_VARIANT[iid])
        else "Direct visit (no UTM)",
        "thumb_gradient": _THUMB_GRADIENTS.get(iid, _THUMB_GRADIENTS["peer_proof"]),
    }


def pipeline_steps() -> list[dict]:
    return [
        {
            "id": "signals",
            "label": "Signals",
            "summary": "Entry channel, ad variant, audience route, objections, tier-gated firmographics",
            "detail": (
                "build_image_ctx(page) collects channel, ad_variant_id, audience_route, "
                "top_objections, industry/region (tier-gated), hero CTA, archetype — plus _hold "
                "fields used only for guardrail stripping, never emitted."
            ),
            "code": "image_gen.build_image_ctx()",
        },
        {
            "id": "intent",
            "label": "Intent select",
            "summary": "Deterministic YAML rules — primary_rules elif chain, then additive fallbacks",
            "detail": (
                "select_image_intent() returns primary + secondary intents with rank, why, "
                "signals_used, and rule_fired — no LLM in routing."
            ),
            "code": "image_intents.select_image_intent()",
        },
        {
            "id": "two_tier",
            "label": "Two-tier base + delta",
            "summary": "Segment base (~100 tokens) + optional personalization delta (~40–60% shorter)",
            "detail": (
                "Tier 1: intent + ad/audience layers only (segment_ctx strips objection/industry/region). "
                "Tier 2: objection metaphor, industry env, region mood, CRM archetype when tier gates pass."
            ),
            "code": "image_gen._resolve_prompts()",
        },
        {
            "id": "prompt",
            "label": "Prompt",
            "summary": "StructuredPrompt → base, delta, or combined API string",
            "detail": (
                "Composition + visual_metaphor from intent templates; personalization_layers "
                "allude-only; drives_action links to page CTA slot ids."
            ),
            "code": "image_intents.build_structured_prompt()",
        },
        {
            "id": "guardrails",
            "label": "Guardrails",
            "summary": "Tier gates, hold-tier strip, global must_avoid, prompt safety assert",
            "detail": (
                "apply_guardrails() strips industry below tier 2, region below tier 1; "
                "GLOBAL_MUST_AVOID enforced; _assert_prompt_safe() blocks PII patterns."
            ),
            "code": "image_intents.apply_guardrails()",
        },
        {
            "id": "cache",
            "label": "Cache",
            "summary": "Semantic segment keys + SHA-256 disk cache per prompt/model",
            "detail": (
                "segment_cache_key: gauntlet:base:{ad} or gauntlet:base:{intent}:{route}. "
                "delta_cache_key: gauntlet:delta:{hash(signals)}. "
                "Disk: data/demo/image_cache/ → /static/generated/."
            ),
            "code": "image_gen.get_hero_image()",
        },
        {
            "id": "render",
            "label": "Render",
            "summary": "Non-blocking page load; async API fills cache for repeat visitors",
            "detail": (
                "build_page checks cache only (generate=False). Client fetch to hero-image API "
                "with generate=True. Fallback: gallery → CSS gradient. Full receipt on /dev."
            ),
            "code": "image_gen.resolve_hero_image()",
        },
    ]


def two_tier_strategy() -> dict:
    return {
        "tier1": {
            "label": "Segment base (pre-cacheable)",
            "cache_key_patterns": [
                "{tenant}:base:{ad_variant_id} — paid ad visitor (12 Gauntlet variants)",
                "{tenant}:base:{intent_id}:{audience_route} — direct / no ad variant",
            ],
            "layers": sorted(II.TIER1_LAYERS),
            "prompt_fn": "assemble_base_prompt()",
            "token_note": "~100 tokens — intent, composition, mood, ad/audience layers only",
            "disk_key": "sha256(model + base_prompt)[:32]",
        },
        "tier2": {
            "label": "Personalization delta",
            "signals": [
                "Top objection → objection_theme metaphor",
                "Industry environment (tier ≥ 2)",
                "Region mood (tier ≥ 1)",
                "CRM/login archetype",
            ],
            "layers": sorted(II.TIER2_LAYER_SOURCES),
            "prompt_fn": "assemble_delta_prompt() / assemble_combined_prompt()",
            "token_note": "~40–60% fewer tokens than full single-tier prompt",
            "disk_key": "{tenant}:delta:{hash(sorted tier-2 signals)}",
        },
        "resolution": [
            "Check full cache (combined prompt hash)",
            "Segment-only miss → check base cache",
            "base+delta miss with warm base → combined prompt generation",
            "base miss → generate base, cache, then delta if needed",
            "Receipt: tier, base_cache_key, delta_cache_key, tokens_saved_estimate",
        ],
        "pregen_cmd": "PYTHONPATH=. python -m scripts.pregen_segment_images",
    }


def _mount_thumb(url: str | None, static_prefix: str) -> str | None:
    if not url or not url.startswith("/static/"):
        return url
    if static_prefix == "/static":
        return url
    return static_prefix + url[len("/static"):]


class _Req:
    """Minimal request stand-in for offline build_page() — same pattern as tests."""
    client = None

    def __init__(self, params: dict | None = None):
        self.query_params = params or {}
        self.headers = {}


def _mount_thumb(url: str | None, static_prefix: str) -> str | None:
    if not url or not url.startswith("/static/"):
        return url
    if static_prefix == "/static":
        return url
    return static_prefix + url[len("/static"):]


def _comparison_cell(params: dict | None, *, page_path: str, dev_path: str,
                     static_prefix: str = "/static") -> dict:
    req = _Req(params or {})

    page = GS.build_page(req)
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx)
    structured = IG.build_image_prompt(ctx)
    hero = IG.resolve_hero_image(page, generate=False)
    receipt = hero.get("receipt") or {}
    primary = sel["primary"]["intent_id"]
    url = _mount_thumb(hero.get("url") or receipt.get("url"), static_prefix)
    qs = ""
    if params:
        from urllib.parse import urlencode
        qs = "?" + urlencode(params)
    landing = f"{page_path}{qs}"
    dev_url = f"{dev_path}{qs}#sec-hero-image"
    return {
        "intent_id": primary,
        "intent_label": primary.replace("_", " ").title(),
        "conversion_goal": structured.get("conversion_goal", ""),
        "drives_action": structured.get("drives_action", receipt.get("drives_action", "")),
        "visual_metaphor": (structured.get("visual_metaphor") or "")[:120],
        "mood": structured.get("mood", ""),
        "why": sel["primary"].get("why", ""),
        "thumb_url": url,
        "thumb_gradient": _THUMB_GRADIENTS.get(primary, _THUMB_GRADIENTS["peer_proof"]),
        "landing_url": landing,
        "dev_url": dev_url,
        "source": receipt.get("source", "gradient"),
        "tier": receipt.get("tier", "base_only"),
    }


def intent_comparisons(page_path: str, *, dev_path: str,
                       static_prefix: str = "/static") -> list[dict]:
    """Three side-by-side pairs — distinct intent strategies for conversion."""
    pairs = [
        {
            "title": "Ad promise vs cold arrival",
            "subtitle": "message_match continuity after a keyword click vs peer_proof default on direct",
            "left_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09",
            },
            "right_params": {},
        },
        {
            "title": "Engineer aspiration vs buyer authority",
            "subtitle": "individual Challenger energy vs B2B scrutiny on device-targeted hire track",
            "left_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-interest-ai-ml", "utm_content": "v11",
            },
            "right_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-device-wifi-office", "utm_content": "v03",
            },
        },
        {
            "title": "Loss frame vs organizational ROI",
            "subtitle": "hire-track loss_avoidance secondary vs HR event roi_clarity primary",
            "left_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09",
            },
            "right_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-event-hrtech", "utm_content": "v07",
            },
        },
    ]
    out = []
    for p in pairs:
        out.append({
            "title": p["title"],
            "subtitle": p["subtitle"],
            "left": _comparison_cell(p["left_params"], page_path=page_path,
                                     dev_path=dev_path, static_prefix=static_prefix),
            "right": _comparison_cell(p["right_params"], page_path=page_path,
                                      dev_path=dev_path, static_prefix=static_prefix),
        })
    return out


# Three single-scenario examples for Part 5 (keyword / HR event / engineer interest).
LIVE_EXAMPLES: list[dict] = [
    {
        "title": "Keyword ad · CTO hire",
        "subtitle": "x-keyword-ai-hiring / v09",
        "params": {
            "utm_source": "x", "utm_medium": "paid",
            "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09",
        },
    },
    {
        "title": "HR event ad · L&D buyer",
        "subtitle": "x-event-hrtech / v07",
        "params": {
            "utm_source": "x", "utm_medium": "paid",
            "utm_campaign": "x-event-hrtech", "utm_content": "v07",
        },
    },
    {
        "title": "Interest ad · Engineer",
        "subtitle": "x-interest-ai-ml / v11",
        "params": {
            "utm_source": "x", "utm_medium": "paid",
            "utm_campaign": "x-interest-ai-ml", "utm_content": "v11",
        },
    },
]


def live_examples(page_path: str, *, dev_path: str, static_prefix: str = "/static") -> list[dict]:
    rows = []
    for ex in LIVE_EXAMPLES:
        cell = _comparison_cell(ex["params"], page_path=page_path,
                                dev_path=dev_path, static_prefix=static_prefix)
        rows.append({"title": ex["title"], "subtitle": ex["subtitle"], **cell})
    return rows


def guardrails_view(config: dict) -> dict:
    defaults = (config.get("prompt_defaults") or {}).get("must_avoid") or []
    return {
        "must_avoid": list(dict.fromkeys(defaults + list(II.GLOBAL_MUST_AVOID))),
        "tier_gates": (config.get("guardrails") or {}).get("tier_gates") or {},
    }


def intent_taxonomy_table(config: dict) -> list[dict]:
    return [
        {
            "id": i["id"],
            "goal": i.get("conversion_goal", ""),
            "technique": i.get("sales_technique", ""),
            "mood": i.get("mood", ""),
            "metaphor": i.get("visual_metaphor", ""),
        }
        for i in config.get("intents") or []
    ]


def signals_in() -> list[dict]:
    return [
        {"label": "Entry / UTM", "source": "classify_entry()", "examples": "utm_campaign, ref, channel"},
        {"label": "X ad variant", "source": "AD_VARIANTS", "examples": "x-keyword, x-event, x-interest…"},
        {"label": "Audience route", "source": "_audience_route()", "examples": "b2b_hire, b2b_upskill, individual"},
        {"label": "Objections", "source": "prioritize_objections()", "examples": "open_market_hire, ld_budget_committed…"},
        {"label": "CRM / login", "source": "cohort archetype", "examples": "archetype_id when known lead"},
        {"label": "IP tier", "source": "scene.reverse_ip()", "examples": "industry @ tier≥2, region @ tier≥1"},
    ]


def build_image_decisions_view(*, page_path: str = "/gauntletapt",
                               page_base: str | None = None,
                               dev_path: str = "/gauntletapt/dev",
                               static_prefix: str = "/static") -> dict:
    """Full template context for gauntlet_image_decisions.html."""
    page_path = page_base or page_path
    config = II.load_image_config("gauntlet")
    brand = config.get("brand") or {}
    intents = [_build_intent_card(i, page_path=page_path, config=config) for i in config["intents"]]
    guard = guardrails_view(config)
    return {
        "brand_name": brand.get("name", "GauntletAI"),
        "pipeline": pipeline_steps(),
        "signals_in": signals_in(),
        "intent_table": intent_taxonomy_table(config),
        "intents": intents,
        "guardrails": guard,
        "two_tier": two_tier_strategy(),
        "comparisons": intent_comparisons(page_path, dev_path=dev_path, static_prefix=static_prefix),
        "live_examples": live_examples(page_path, dev_path=dev_path, static_prefix=static_prefix),
        "provenance": {
            "config_path": config.get("_path", "rules/gauntlet_image.yaml"),
            "framework_doc": "docs/04-workflow/ACTION-IMAGE-PERSONALIZATION.md",
            "dev_panel": "⑥ Hero background — data & decisioning",
            "dev_path": dev_path,
            "proved": [
                "Intent id, rank, rule_fired, signals_used",
                "Conversion goal, sales_technique, drives_action",
                "Personalization layers (allude disposition)",
                "Full prompt, cache keys (base + delta), model, vendor",
                "Guardrails applied / blocked",
                "Fallback chain: cache → API → gallery → gradient",
            ],
            "inferred": [
                "Industry from reverse-IP (tier-gated, may be wrong)",
                "Objection ranking from signal weights (heuristic, not stated by visitor)",
                "Visual metaphor interpretation by image model",
            ],
            "receipt_fields": [
                "intent_id", "conversion_goal", "sales_technique", "drives_action",
                "personalization_layers", "guardrails_applied", "guardrails_blocked",
                "tier", "base_cache_key", "delta_cache_key", "tokens_saved_estimate",
                "prompt", "model", "vendor", "cache_key", "generated_at", "license",
            ],
        },
        "accent_color": brand.get("accent_color", "#c9a227"),
    }
