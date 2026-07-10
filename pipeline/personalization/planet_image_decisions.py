"""Hero image decision guide — /planetapt/dev/image-decisions.

Deterministic view model: intent taxonomy, pipeline, two-tier strategy, live comparisons.
No LLM; reads rules/planet_image.yaml + image_gen resolution (tenant="planet")."""
from __future__ import annotations

from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II
from pipeline.personalization import planet_site as PS
from pipeline.personalization import scene as SC
from pipeline.personalization.brain_simulator import (
    BRAIN_TARGET_LABELS,
    REGION_SIMULATOR_MAP,
    brain_target_mapping_table,
    example_receipt_snippet,
)

TENANT = "planet"

# The cohort login the warm script uses for the "known" states — a synthetic
# customer email that resolves to a CRM archetype (see planet_cohort).
WARM_KNOWN_EMAIL = PS.sample_login_email()

# Narrative enrichments — conversion psychology (not in YAML; stable doc copy).
_VISITOR_FEELS: dict[str, str] = {
    "regional_truth": (
        "That's my kind of ground — and they already image it every day. The claim is "
        "checkable, so the rest of the page earns trust."
    ),
    "change_proof": (
        "Change is happening whether I watch or not — the window to act is while the "
        "clearing is still small."
    ),
    "mission_authority": (
        "This is a map-room, not a demo — serious missions already run on this coverage."
    ),
    "archive_advantage": (
        "The before-picture already exists — nobody can reconstruct that after the event "
        "except the operator who was already watching."
    ),
    "aspiration_research": (
        "That time series could be my figure 1 — the archive is an instrument I can "
        "actually afford."
    ),
    "retarget_warm": (
        "The constellation kept passing while I was away — low friction to pick up where "
        "I left off."
    ),
    "message_match": (
        "The page continues what the ad promised — no bait-and-switch, I clicked for a reason."
    ),
}

_WHY_IT_WORKS: dict[str, str] = {
    "regional_truth": (
        "Truthful message-match on geography: Planet is the only operator imaging the whole "
        "landmass daily, so a region-scale visual of the visitor's kind of terrain is both "
        "personal and verifiable — trust before the headline asks for it. Guardrail: "
        "landscape scale only, never street or property scale."
    ),
    "change_proof": (
        "Prospect-theory loss framing (the clearing that finished, the stall nobody saw) "
        "pairs with archive/tasking objections — urgency without invented scarcity or "
        "disaster porn."
    ),
    "mission_authority": (
        "Mission committees need evaluative gravitas: theater-scale dusk littoral with a calm "
        "telemetry grid signals operational seriousness — and the theater register keeps the "
        "visitor's own location out of frame (anti-surveillance guardrail)."
    ),
    "archive_advantage": (
        "The time-machine claim is Planet's structural moat: a filmstrip of daily history "
        "visualizes the one thing tasked competitors cannot backfill, supporting claims and "
        "compliance CTAs."
    ),
    "aspiration_research": (
        "Identity aspiration + accessibility for the research route: science-poster beauty "
        "plus a free program lowers the perceived barrier and lifts application intent."
    ),
    "retarget_warm": (
        "Cialdini consistency: continuation cues reduce dissonance after a crisis-post "
        "engager click — the ground-track resumes, no creepy 'we saw you' copy."
    ),
    "message_match": (
        "Ad-to-landing consistency cuts bounce: the segment's satellite metaphor (crop "
        "quilt, dark wake, canopy seam) echoes the ad promise so the hero supports the "
        "personalized headline instead of fighting it."
    ),
}

# Canonical live demo URL per intent (UTM params that fire selection rules).
_INTENT_DEMO_VARIANT: dict[str, str] = {
    "regional_truth": "",           # direct — no ad variant (the default story)
    "change_proof": "v04",          # forestry EUDR — change objections
    "mission_authority": "v02",     # defense lookalike
    "archive_advantage": "v03",     # insurance event
    "aspiration_research": "v11",   # early-career researcher
    "retarget_warm": "v08",         # crisis post-engager
    "message_match": "v01",         # crop-belt location ad
}

_ACTION_LABELS: dict[str, str] = {
    "sales_cta": "Talk to Sales",
    "trial_cta": "Start Free Trial",
    "research_cta": "Apply for Research Access",
    "platform_overview": "Explore the platform",
}

_THUMB_GRADIENTS: dict[str, str] = {
    "regional_truth": "linear-gradient(135deg,#04080f 0%,#0a1a2e 45%,#12314f 100%)",
    "change_proof": "linear-gradient(90deg,#06101c 0%,#06101c 48%,#0e2b1c 52%,#1e5a38 100%)",
    "mission_authority": "linear-gradient(135deg,#050a14 0%,#0c1c33 50%,#3ba1ff33 100%)",
    "archive_advantage": "linear-gradient(135deg,#04080f 0%,#0b1626 40%,#3ba1ff44 100%)",
    "aspiration_research": "linear-gradient(135deg,#061018 0%,#0d2436 50%,#3ba1ff55 100%)",
    "retarget_warm": "linear-gradient(135deg,#0c0f16 0%,#1a2333 60%,#3ba1ff66 100%)",
    "message_match": "linear-gradient(135deg,#060a12 0%,#101b2c 45%,#3ba1ff55 100%)",
}


def _variant_by_id(vid: str) -> dict | None:
    if not vid:
        return None
    return PS.AD_BY_VARIANT_ID.get(vid)


def _demo_landing_url(intent_id: str, page_path: str) -> str:
    vid = _INTENT_DEMO_VARIANT.get(intent_id, "")
    if not vid:
        return page_path
    v = _variant_by_id(vid)
    if not v:
        return page_path
    return PS.variant_landing_url(v, page_path)


def _default_drives_action(intent_id: str, config: dict) -> str:
    action_map = config.get("action_map") or {}
    route_defaults = action_map.get("route_defaults") or {}
    by_intent = {
        "regional_truth": action_map.get("default", "platform_overview"),
        "change_proof": route_defaults.get("selfserve", "trial_cta"),
        "mission_authority": route_defaults.get("enterprise", "sales_cta"),
        "archive_advantage": route_defaults.get("enterprise", "sales_cta"),
        "aspiration_research": route_defaults.get("research", "research_cta"),
        "retarget_warm": route_defaults.get("selfserve", "trial_cta"),
        "message_match": action_map.get("default", "platform_overview"),
    }
    return by_intent.get(intent_id, action_map.get("default", "platform_overview"))


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
        "thumb_gradient": _THUMB_GRADIENTS.get(iid, _THUMB_GRADIENTS["regional_truth"]),
    }


def pipeline_steps() -> list[dict]:
    return [
        {
            "id": "signals",
            "label": "Signals",
            "summary": "Entry channel, ad variant + segment, audience route, objections, "
                       "tier-gated region (the location signal) and industry",
            "detail": (
                "build_image_ctx(page) collects channel, ad_variant_id, audience_route, "
                "top_objections, industry/region (tier-gated), hero CTA, archetype — plus _hold "
                "fields used only for guardrail stripping, never emitted. For Planet, region is "
                "the star signal: it becomes the region_mood layer of the satellite-view prompt."
            ),
            "code": "image_gen.build_image_ctx()",
        },
        {
            "id": "intent",
            "label": "Intent select",
            "summary": "Deterministic YAML rules — primary_rules elif chain, then additive fallbacks",
            "detail": (
                "select_image_intent() returns primary + secondary intents with rank, why, "
                "signals_used, and rule_fired — no LLM in routing. Config: rules/planet_image.yaml."
            ),
            "code": "image_intents.select_image_intent()",
        },
        {
            "id": "two_tier",
            "label": "Two-tier base + delta",
            "summary": "Segment base (~100 tokens) + optional personalization delta (~40–60% shorter)",
            "detail": (
                "Tier 1: intent + ad/audience layers only (segment_ctx strips objection/industry/region). "
                "Tier 2: objection metaphor, industry env, region mood (the location signal), CRM "
                "archetype when tier gates pass."
            ),
            "code": "image_gen._resolve_prompts()",
        },
        {
            "id": "prompt",
            "label": "Prompt",
            "summary": "StructuredPrompt → base, delta, or combined API string",
            "detail": (
                "Composition + visual_metaphor from intent templates (satellite-view grammar); "
                "personalization_layers allude-only; drives_action links to page CTA slot ids."
            ),
            "code": "image_intents.build_structured_prompt()",
        },
        {
            "id": "guardrails",
            "label": "Guardrails",
            "summary": "Tier gates, hold-tier strip, anti-surveillance must_avoid, prompt safety assert",
            "detail": (
                "apply_guardrails() strips industry below tier 2, region below tier 1; "
                "GLOBAL_MUST_AVOID plus Planet's own rules (no street/property scale, no "
                "identifiable homes, no targeting imagery); _assert_prompt_safe() blocks PII."
            ),
            "code": "image_intents.apply_guardrails()",
        },
        {
            "id": "brain_sim",
            "label": "Brain simulator",
            "summary": "Generate N candidates → Tribe v2 (or proxy_v1) score → cache winner",
            "detail": (
                "When brain_simulator.enabled, async generation requests best-of-N candidates, "
                "scores each against the intent's brain_target cortical regions, caches the "
                "winner, and persists rejected candidates (images + scores) on the manifest. "
                "Receipt logs brain_score, region_scores, candidates_evaluated, candidates[]. "
                "Predicted response optimization — not measured visitor brain data."
            ),
            "code": "brain_simulator.BrainSimulatorScorer.select_best()",
        },
        {
            "id": "cache",
            "label": "Cache",
            "summary": "Semantic segment keys + SHA-256 disk cache per prompt/model",
            "detail": (
                "segment_cache_key: planet:base:{ad} or planet:base:{intent}:{route}. "
                "delta_cache_key: planet:delta:{hash(signals)}. "
                "Disk: data/demo/image_cache/ → /static/generated/."
            ),
            "code": "image_gen.get_hero_image()",
        },
        {
            "id": "render",
            "label": "Render",
            "summary": "Non-blocking page load; async API fills cache for repeat visitors",
            "detail": (
                "build_page checks cache only (generate=False). Client fetch to the hero-image API "
                "with generate=True. Fallback: gallery → CSS gradient. Full receipt on /planet/dev."
            ),
            "code": "image_gen.resolve_hero_image()",
        },
    ]


def two_tier_strategy() -> dict:
    return {
        "tier1": {
            "label": "Segment base (pre-cacheable)",
            "cache_key_patterns": [
                "planet:base:{ad_variant_id} — paid ad visitor (12 Planet variants)",
                "planet:base:{intent_id}:{audience_route} — direct / no ad variant",
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
                "Region mood — the location signal (tier ≥ 1)",
                "CRM/login archetype",
            ],
            "layers": sorted(II.TIER2_LAYER_SOURCES),
            "prompt_fn": "assemble_delta_prompt() / assemble_combined_prompt()",
            "token_note": "~40–60% fewer tokens than full single-tier prompt",
            "disk_key": "planet:delta:{hash(sorted tier-2 signals)}",
        },
        "resolution": [
            "Check full cache (combined prompt hash)",
            "Segment-only miss → check base cache",
            "base+delta miss with warm base → combined prompt generation",
            "base miss → generate base, cache, then delta if needed",
            "Receipt: tier, base_cache_key, delta_cache_key, tokens_saved_estimate",
        ],
        "pregen_cmd": "PYTHONPATH=. python -m scripts.pregen_segment_images --tenant planet",
    }


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

    page = PS.build_page(req)
    ctx = IG.build_image_ctx(page)
    sel = IG.select_image_intent(ctx, tenant=TENANT)
    structured = IG.build_image_prompt(ctx, tenant=TENANT)
    hero = IG.resolve_hero_image(page, generate=False, tenant=TENANT)
    receipt = hero.get("receipt") or {}
    primary = sel["primary"]["intent_id"]
    url = _mount_thumb(hero.get("url") or receipt.get("url"), static_prefix)
    gallery = IG.candidate_gallery_from_receipt(receipt, static_prefix=static_prefix)
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
        "thumb_gradient": _THUMB_GRADIENTS.get(primary, _THUMB_GRADIENTS["regional_truth"]),
        "landing_url": landing,
        "dev_url": dev_url,
        "source": receipt.get("source", "gradient"),
        "tier": receipt.get("tier", "base_only"),
        "candidate_gallery": gallery,
    }


def intent_comparisons(page_path: str, *, dev_path: str,
                       static_prefix: str = "/static") -> list[dict]:
    """Three side-by-side pairs — distinct intent strategies for conversion."""
    pairs = [
        {
            "title": "Ad promise vs cold arrival",
            "subtitle": "message_match continuity after a crop-belt click vs regional_truth default on direct",
            "left_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-location-crop-belts", "utm_content": "v01",
            },
            "right_params": {},
        },
        {
            "title": "Mission gravitas vs research aspiration",
            "subtitle": "defense theater register vs archive-as-instrument on the academic route",
            "left_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-lookalike-defense", "utm_content": "v02",
            },
            "right_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-age-early-career", "utm_content": "v11",
            },
        },
        {
            "title": "Evidence archive vs warm continuation",
            "subtitle": "insurance before-picture filmstrip vs crisis-engager retarget_warm",
            "left_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-event-insurance", "utm_content": "v03",
            },
            "right_params": {
                "utm_source": "x", "utm_medium": "paid",
                "utm_campaign": "x-engager-crisis", "utm_content": "v08",
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


# Three single-scenario examples for Part 5 (crop belt / defense / researcher).
LIVE_EXAMPLES: list[dict] = [
    {
        "title": "Crop-belt location ad · Agronomy",
        "subtitle": "x-location-crop-belts / v01",
        "params": {
            "utm_source": "x", "utm_medium": "paid",
            "utm_campaign": "x-location-crop-belts", "utm_content": "v01",
        },
    },
    {
        "title": "Defense lookalike ad · GEOINT",
        "subtitle": "x-lookalike-defense / v02",
        "params": {
            "utm_source": "x", "utm_medium": "paid",
            "utm_campaign": "x-lookalike-defense", "utm_content": "v02",
        },
    },
    {
        "title": "Early-career age ad · Researcher",
        "subtitle": "x-age-early-career / v11",
        "params": {
            "utm_source": "x", "utm_medium": "paid",
            "utm_campaign": "x-age-early-career", "utm_content": "v11",
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


def decided_vs_rejected(*, page_path: str, dev_path: str,
                        static_prefix: str = "/static",
                        hero_api: str = "/api/planet/hero-image") -> dict:
    """Best-of-N winner + rejected candidates for image-decisions Part 6."""
    scenarios: list[dict] = []
    for ex in LIVE_EXAMPLES:
        cell = _comparison_cell(ex["params"], page_path=page_path,
                                dev_path=dev_path, static_prefix=static_prefix)
        gal = cell["candidate_gallery"]
        scenarios.append({
            "title": ex["title"],
            "subtitle": ex["subtitle"],
            "intent_id": cell["intent_id"],
            "landing_url": cell["landing_url"],
            "dev_url": cell["dev_url"],
            **gal,
        })
    for pair in intent_comparisons(page_path, dev_path=dev_path, static_prefix=static_prefix):
        for side_key in ("left", "right"):
            cell = pair[side_key]
            gal = cell["candidate_gallery"]
            scenarios.append({
                "title": f"{pair['title']} · {cell['intent_label']}",
                "subtitle": pair["subtitle"],
                "intent_id": cell["intent_id"],
                "landing_url": cell["landing_url"],
                "dev_url": cell["dev_url"],
                **gal,
            })
    with_data = [s for s in scenarios if s.get("has_candidates")]
    return {
        "scenarios": scenarios,
        "with_data_count": len(with_data),
        "total_scenarios": len(scenarios),
        "empty_hint": (
            "No best-of-N candidate provenance for this state yet. Warm or generate with "
            f"BRAIN_SIM_BEST_OF_N=3 — e.g. <code>PYTHONPATH=. BRAIN_SIM_BEST_OF_N=3 "
            f"python -m scripts.warm_hero_cache --tenant planet --force-regen</code> "
            f"or hit the async hero API (<code>{hero_api}?generate=true</code>)."
        ),
        "honest_framing": (
            "Simulator-scored candidates — predicted visual-response optimization, "
            "not measured visitor brain data."
        ),
    }


def guardrails_view(config: dict) -> dict:
    defaults = (config.get("prompt_defaults") or {}).get("must_avoid") or []
    brand_extra = (config.get("brand") or {}).get("must_avoid_additions") or []
    return {
        "must_avoid": list(dict.fromkeys(defaults + brand_extra + list(II.GLOBAL_MUST_AVOID))),
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
        {"label": "X ad variant + segment", "source": "AD_VARIANTS", "examples": "x-agriculture, x-defense, x-maritime…"},
        {"label": "Audience route", "source": "_audience_route()", "examples": "enterprise, selfserve, research"},
        {"label": "Objections", "source": "prioritize_objections()", "examples": "tasked_competitor, cloud_cover…"},
        {"label": "CRM / login", "source": "planet_cohort archetype", "examples": "archetype_id when known lead"},
        {"label": "Location (IP tier)", "source": "scene.reverse_ip()",
         "examples": "region_mood @ tier≥1 — the Planet signal; industry @ tier≥2"},
    ]


def brain_simulator_view(config: dict) -> dict:
    enabled = bool((config.get("brain_simulator") or {}).get("enabled"))
    return {
        "enabled": enabled,
        "backend_note": (
            "Tribe v2 encoding model when installed; otherwise proxy_v1 "
            "(saliency, structure, prompt-alignment proxies mapped to ROI scores)."
        ),
        "honest_framing": (
            "Predicted visual-response optimization via brain simulator — not literal "
            "stimulation of the visitor's cortex and not measured EEG/fMRI."
        ),
        "loop": [
            "Generate N candidates (default N=3 on async hero API; N=1 on pregen unless BRAIN_SIM_BEST_OF_N set)",
            "Score each with BrainSimulatorScorer against intent brain_target + brain_regions",
            "Penalize guardrail violations (surveillance crosshair, face-skin, text-grid proxies)",
            "Select highest brain_score; cache winner; persist rejected candidates for provenance",
            "Log brain_simulator, brain_score, region_scores, candidates[] on manifest receipt",
        ],
        "target_labels": BRAIN_TARGET_LABELS,
        "region_map": REGION_SIMULATOR_MAP,
        "intent_mapping": brain_target_mapping_table(config),
        "example_receipt": example_receipt_snippet(),
        "env_var": "BRAIN_SIM_BEST_OF_N",
    }


def build_image_decisions_view(*, page_path: str = "/planetapt",
                               page_base: str | None = None,
                               dev_path: str = "/planetapt/dev",
                               static_prefix: str = "/static") -> dict:
    """Full template context for planet_image_decisions.html."""
    page_path = page_base or page_path
    config = II.load_image_config(TENANT)
    brand = config.get("brand") or {}
    intents = [_build_intent_card(i, page_path=page_path, config=config) for i in config["intents"]]
    guard = guardrails_view(config)
    return {
        "brand_name": brand.get("name", "Planet"),
        "pipeline": pipeline_steps(),
        "signals_in": signals_in(),
        "intent_table": intent_taxonomy_table(config),
        "intents": intents,
        "guardrails": guard,
        "two_tier": two_tier_strategy(),
        "brain_simulator": brain_simulator_view(config),
        "comparisons": intent_comparisons(page_path, dev_path=dev_path, static_prefix=static_prefix),
        "live_examples": live_examples(page_path, dev_path=dev_path, static_prefix=static_prefix),
        "decided_rejected": decided_vs_rejected(
            page_path=page_path, dev_path=dev_path, static_prefix=static_prefix,
        ),
        "provenance": {
            "config_path": config.get("_path", "rules/planet_image.yaml"),
            "framework_doc": "docs/04-workflow/ACTION-IMAGE-PERSONALIZATION.md",
            "dev_panel": "Hero background — data & decisioning",
            "dev_path": dev_path,
            "proved": [
                "Intent id, rank, rule_fired, signals_used",
                "Conversion goal, sales_technique, drives_action",
                "Personalization layers incl. region_mood (allude disposition)",
                "Full prompt, cache keys (base + delta), model, vendor",
                "Guardrails applied / blocked (anti-surveillance rules)",
                "Fallback chain: cache → API → gallery → gradient",
            ],
            "inferred": [
                "Region from geo-IP (tier-gated, may be wrong — then no claim ships)",
                "Industry from reverse-IP (tier-gated, may be wrong)",
                "Objection ranking from signal weights (heuristic, not stated by visitor)",
                "Visual metaphor interpretation by image model",
            ],
            "receipt_fields": [
                "intent_id", "conversion_goal", "sales_technique", "drives_action",
                "personalization_layers", "guardrails_applied", "guardrails_blocked",
                "tier", "base_cache_key", "delta_cache_key", "tokens_saved_estimate",
                "brain_simulator", "brain_target", "brain_score", "brain_region_scores",
                "candidates_evaluated", "winner_index", "candidates",
                "prompt", "model", "vendor", "cache_key", "generated_at", "license",
            ],
        },
        "accent_color": brand.get("accent_color", "#3ba1ff"),
    }


def demo_cache_states() -> list[tuple[str, dict, str | None]]:
    """The Planet demo states the warm script pre-generates — single source of truth.

    scripts/warm_hero_cache.py --tenant planet imports this list. Unlike Gauntlet,
    Planet almost always ships a base+delta hero (an objection nearly always fires,
    and geo-IP region is the star signal), so warming only the segment bases is not
    enough — the combined images are what production actually serves. States:
      · all 12 catalogued X ad variants (anon + known cohort login)
      · direct / search / email entries (anon + known)
      · every verified example-account IP (anon) — the LOCATION / region variants
        the /dev IP picker surfaces (region_mood + tier-2 industry deltas)

    Each tuple is (label, query_params, email); the warmer walks the real
    PS.build_page() → image_gen path so the disk cache keys match production
    exactly (region-name guardrail stripping, PDL industry resolution, and all)."""
    states: list[tuple[str, dict, str | None]] = []
    for v in PS.AD_VARIANTS:
        params = {"utm_source": "x", "utm_medium": "paid",
                  "utm_campaign": v["utm_campaign"], "utm_content": v["variant_id"]}
        states.append((f"ad {v['variant_id']} {v['id']} · anon", params, None))
        states.append((f"ad {v['variant_id']} {v['id']} · known", params, WARM_KNOWN_EMAIL))
    entries = [
        ("direct", {}),
        ("search", {"ref": "google"}),
        ("email", {"utm_source": "hubspot", "utm_medium": "email",
                   "utm_campaign": "crisis-responders", "e": PS.sample_magic_token()}),
    ]
    for label, params in entries:
        states.append((f"{label} · anon", params, None))
        states.append((f"{label} · known", params, WARM_KNOWN_EMAIL))
    for group in SC.EXAMPLE_ACCOUNTS.get("groups", []):
        for row in group.get("rows", []):
            states.append((f"ip {row['company']} ({row['ip']})", {"ip": row["ip"]}, None))
    return states
