"""Hero image decision guide — /gauntletapt/image-decisions.

Deterministic view model: intent taxonomy, pipeline, two-tier strategy, live comparisons.
No LLM; reads rules/gauntlet_image.yaml + image_gen resolution for thumbnails."""
from __future__ import annotations

from pipeline.personalization import cohort as CO
from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II
from pipeline.personalization.brain_simulator import (
    BRAIN_TARGET_LABELS,
    REGION_SIMULATOR_MAP,
    brain_target_mapping_table,
    example_receipt_snippet,
)

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
            "id": "brain_sim",
            "label": "Brain simulator",
            "summary": "Optional best-of-N scoring when brain_simulator.enabled in YAML",
            "detail": (
                "Gauntlet ships brain_target mappings but scoring is tenant-opt-in "
                "(brain_simulator.enabled: false by default). When enabled, same "
                "generate → score → select loop as Planet via BrainSimulatorScorer."
            ),
            "code": "brain_simulator.BrainSimulatorScorer.select_best()",
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
        "thumb_gradient": _THUMB_GRADIENTS.get(primary, _THUMB_GRADIENTS["peer_proof"]),
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


def decided_vs_rejected(*, page_path: str, dev_path: str,
                        static_prefix: str = "/static",
                        hero_api: str = "/api/gauntlet/hero-image") -> dict:
    """Best-of-N winner + rejected candidates for image-decisions gallery."""
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
            "Gauntlet brain_simulator is off by default. Enable in rules/gauntlet_image.yaml, "
            f"then warm with BRAIN_SIM_BEST_OF_N=3 or hit <code>{hero_api}?generate=true</code>."
        ),
        "honest_framing": (
            "When enabled: simulator-scored candidates — predicted optimization, "
            "not measured brain data."
        ),
    }


# --------------------------------------------------------------------------- #
# Part 6 · Pre-cached vs live — shared state list + cache decision graph
# --------------------------------------------------------------------------- #
WARM_KNOWN_EMAIL = "maya.chen@gauntletai.com"


def demo_cache_states() -> list[tuple[str, dict, str | None] | tuple[str, dict, str | None, str]]:
    """Every catalogued demo state × surface — single source of truth is the
    version-controlled manifest rules/gauntlet_prebuild.yaml.

    scripts/warm_hero_cache.py and the /dev/business console read the same
    manifest, so the guide, the console, and the warmer can never drift apart.
    Under S3.3 [PANEL] only the `prebuild: true` short lists are baked by the
    warm script (PB.prebuild_states, K=8/target); the guide's inventory shows
    ALL catalogued states — unflagged ones generate realtime on first visit,
    governed by the daily spend ceiling."""
    from pipeline.personalization import prebuild as PB
    out: list[tuple[str, dict, str | None, str]] = []
    for r in PB.manifest_all_states():
        sid = r["surface_id"]
        label = r["label"] if sid == IG.DEFAULT_SURFACE_ID else f"{r['label']} · {sid}"
        out.append((label, r["params"], r["email"], sid))
    return out


def cache_inventory() -> dict:
    """LIVE cache status per warmed demo state — deterministic disk read, no API calls."""
    rows = []
    cached_n = 0
    for entry in demo_cache_states():
        if len(entry) == 4:
            label, params, email, surface_id = entry
        else:
            label, params, email = entry
            surface_id = IG.DEFAULT_SURFACE_ID
        page = GS.build_page(_Req(dict(params)), email=email)
        ctx = IG.build_image_ctx(page)
        resolved = IG._resolve_prompts(ctx, surface_id=surface_id)
        hit = IG._load_cached(resolved["gen_disk_key"]) is not None
        cached_n += 1 if hit else 0
        surf = IG.surface_spec(surface_id)
        rows.append({
            "label": label,
            "surface_id": surface_id,
            "surface_label": surf["label"],
            "tier": resolved["tier"],
            "disk_key": resolved["gen_disk_key"][:12] + "…",
            "cached": hit,
            "status": ("cached · served inline, instant" if hit
                       else "miss · would generate live (~30s)"),
        })
    return {"rows": rows, "cached": cached_n, "total": len(rows)}


def cache_decision_graph() -> list[dict]:
    """Top-to-bottom decision graph for get_hero_image() — every branch describable."""
    return [
        {
            "label": "Request lands",
            "code": "image_gen.build_image_ctx()",
            "reads": ["channel", "ad_variant_id", "audience_route", "tier",
                      "top_objection", "industry/region"],
            "branches": [],
            "output": "Deterministic image ctx — same visitor state ⇒ same prompts ⇒ same cache keys",
            "note": "",
        },
        {
            "label": "Build prompts — tier split",
            "code": "image_gen._resolve_prompts()",
            "reads": ["segment_cache_key", "delta_cache_key"],
            "branches": [
                {"label": "base_only", "kind": "",
                 "desc": ("Segment signals only — semantic key gauntlet:base:<ad-id> "
                          "or gauntlet:base:<intent>:<route>; one prompt, one image.")},
                {"label": "base+delta", "kind": "",
                 "desc": ("Tier-2 signals present (objection / industry / region / archetype) — "
                          "delta key = hash of the sorted signals; combined prompt on top of the base.")},
            ],
            "output": "gen prompt → disk key = sha256(model + prompt)[:32]",
            "note": "",
        },
        {
            "label": "Disk cache?",
            "code": "image_gen._load_cached(gen_disk_key)",
            "reads": ["data/demo/image_cache/manifest.json", "images/<key>.jpg"],
            "branches": [
                {"label": "hit → pre-cached", "kind": "pre",
                 "desc": ("Image is on disk — the 30 warmed demo states ship inside the deploy "
                          "image, so these render inline, instantly. Anything generated live "
                          "since the last deploy also lands here.")},
                {"label": "miss → live path", "kind": "live",
                 "desc": "Nothing on disk for this prompt — fall through to the API-key gate."},
            ],
            "output": "hit: receipt + URL, done · miss: continue below",
            "note": "",
        },
        {
            "label": "API key?",
            "code": "image_gen._api_key()",
            "reads": ["IMAGE_GEN_API_KEY"],
            "branches": [
                {"label": "no key → gallery", "kind": "",
                 "desc": ("Curated CC gallery — only when an industry actually resolved "
                          "(tier ≥ 2); otherwise the CSS gradient. Never blocks the page.")},
                {"label": "no key + no industry → gradient", "kind": "",
                 "desc": "CSS gradient fallback — instant, no network, receipt still logged."},
                {"label": "key set → pending", "kind": "live",
                 "desc": ("Page ships the gradient with status pending; the site's client JS "
                          "calls the hero-image API to generate asynchronously.")},
            ],
            "output": "gallery / gradient (offline) or pending → async generation",
            "note": "",
        },
        {
            "label": "Live generation (async)",
            "code": "hero-image API · generate=True",
            "reads": ["gen prompt", "Gemini (~30s)"],
            "branches": [
                {"label": "base_only miss", "kind": "live",
                 "desc": "One image: generate the base prompt, cache to disk."},
                {"label": "base+delta miss", "kind": "live",
                 "desc": ("Two images: generate the segment base first (cached under its own "
                          "key for base_only visitors), then the combined base+delta image.")},
            ],
            "output": ("Cached to data/demo/image_cache/ — every later visitor in this state "
                       "gets it inline, until the next deploy wipes the ephemeral filesystem"),
            "note": ("The first visitor in a live state sees the gradient while generation "
                     "runs; nobody ever waits on the image API."),
        },
    ]


def precached_vs_live() -> dict:
    """View model for Part 6 — plain-English preamble, graph, live inventory, ops rule."""
    return {
        "preamble": (
            "Pre-cached = the 30 demo states below, generated once by the warm script and "
            "baked into the deploy image — those hero backgrounds render inline, instantly. "
            "Live = any state outside that set (a real corporate IP resolving an industry, "
            "another cohort login, a new ad variant): the first visitor sees the CSS gradient "
            "while the image generates once (~30s, Gemini), then it stays cached on disk for "
            "every later visitor — until the next deploy, because Railway's filesystem is "
            "ephemeral. The warm script plus the .dockerignore exception for "
            "data/demo/image_cache/ are what let the pre-cached set survive deploys."
        ),
        "ops_rule": "railway run python -m scripts.warm_hero_cache",
        "graph": cache_decision_graph(),
        "inventory": cache_inventory(),
    }


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


def brain_simulator_view(config: dict) -> dict:
    enabled = bool((config.get("brain_simulator") or {}).get("enabled"))
    return {
        "enabled": enabled,
        "backend_note": (
            "Tribe v2 when installed; proxy_v1 otherwise. Gauntlet defaults to disabled — "
            "set brain_simulator.enabled: true in rules/gauntlet_image.yaml to activate."
        ),
        "honest_framing": (
            "Predicted visual-response optimization via simulator — not measured brain data "
            "and not a claim that images stimulate the visitor's cortex."
        ),
        "loop": [
            "Generate N candidates (N=3 async when enabled; N=1 pregen unless BRAIN_SIM_BEST_OF_N)",
            "Score with BrainSimulatorScorer per intent brain_target",
            "Penalize guardrail-violation proxies; select highest brain_score",
            "Cache winner; persist rejected candidates when enabled",
            "Log brain_score, region_scores, candidates[] on receipt",
        ],
        "target_labels": BRAIN_TARGET_LABELS,
        "region_map": REGION_SIMULATOR_MAP,
        "intent_mapping": brain_target_mapping_table(config),
        "example_receipt": example_receipt_snippet(),
        "env_var": "BRAIN_SIM_BEST_OF_N",
    }


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
        "brain_simulator": brain_simulator_view(config),
        "comparisons": intent_comparisons(page_path, dev_path=dev_path, static_prefix=static_prefix),
        "live_examples": live_examples(page_path, dev_path=dev_path, static_prefix=static_prefix),
        "decided_rejected": decided_vs_rejected(
            page_path=page_path, dev_path=dev_path, static_prefix=static_prefix,
        ),
        "precached": precached_vs_live(),
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
                "brain_simulator", "brain_target", "brain_score", "brain_region_scores",
                "candidates_evaluated", "winner_index", "candidates",
                "prompt", "model", "vendor", "cache_key", "generated_at", "license",
            ],
        },
        "accent_color": brand.get("accent_color", "#c9a227"),
    }
