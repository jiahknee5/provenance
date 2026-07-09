"""Structured hero image intents — config-driven, tenant-agnostic framework.

Each tenant defines intents + signal rules in rules/<tenant>_image.yaml.
GauntletAI is the reference implementation (rules/gauntlet_image.yaml).

Deterministic selection only — no LLM. See docs/04-workflow/ACTION-IMAGE-PERSONALIZATION.md.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, TypedDict

import yaml

from pipeline.common.config import RULES_DIR

TENANT_CONFIG_FILES: dict[str, str] = {
    "gauntlet": "gauntlet_image.yaml",
}

_CONFIG_CACHE: dict[str, dict[str, Any]] = {}


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
    rule_fired: str


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
    tenant: str


# Global guardrails — inviolable across all tenants (CONSTITUTION Art III).
GLOBAL_MUST_AVOID = [
    "NO faces of real people or identifiable individuals",
    "NO company logos or brand marks",
    "NO text, words, letters, or numbers in the image",
    "NO visitor names, employer names, or PII",
    "NO surveillance, creepy, or behavioral-tracking imagery",
]

HOLD_STRIP_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b"), "visitor_name"),
    (re.compile(r"\bat\s+[A-Z][A-Za-z0-9&.\- ]{2,40}\b"), "employer_name"),
    (re.compile(r"\b(income|salary|compensation)\s*(band|range|level)?\b", re.I), "income"),
    (re.compile(r"\b(age|aged)\s*\d{1,2}[-–]\d{1,2}\b", re.I), "age"),
    (re.compile(r"\b(male|female|man|woman|non-?binary)\b", re.I), "gender"),
    (re.compile(r"\b\d{5}(-\d{4})?\b"), "zip_code"),
]


def load_image_config(tenant: str = "gauntlet", *, path: Path | None = None) -> dict[str, Any]:
    """Load tenant image personalization config from rules/<tenant>_image.yaml."""
    if tenant in _CONFIG_CACHE and path is None:
        return _CONFIG_CACHE[tenant]
    if path is None:
        fname = TENANT_CONFIG_FILES.get(tenant, f"{tenant}_image.yaml")
        path = RULES_DIR / fname
    if not path.exists():
        raise FileNotFoundError(f"image config not found: {path}")
    cfg = yaml.safe_load(path.read_text()) or {}
    cfg["_path"] = str(path)
    cfg["intents"] = cfg.get("intents") or []
    cfg["intent_by_id"] = {i["id"]: i for i in cfg["intents"]}
    if path is None or tenant in TENANT_CONFIG_FILES:
        _CONFIG_CACHE[tenant] = cfg
    elif path.name.endswith("_image.yaml"):
        slug = path.stem.replace("_image", "")
        _CONFIG_CACHE[slug] = cfg
    return cfg


def _default_config() -> dict[str, Any]:
    return load_image_config("gauntlet")


# Backward-compatible module exports (Gauntlet reference tenant).
_DEFAULT = _default_config()
INTENT_CATALOG: list[dict[str, Any]] = _DEFAULT["intents"]
INTENT_BY_ID: dict[str, dict[str, Any]] = _DEFAULT["intent_by_id"]
OBJECTION_METAPHORS: dict[str, str] = _DEFAULT.get("objection_metaphors") or {}
AD_METAPHORS: dict[str, str] = _DEFAULT.get("ad_metaphors") or {}
OBJECTION_CTA_PAIR: dict[str, str] = (_DEFAULT.get("action_map") or {}).get("objection_pairs") or {}
GAUNTLET_GOLD: str = (_DEFAULT.get("brand") or {}).get("accent_color", "#c9a227")


def _top_objections(ctx: dict) -> list[str]:
    return list(ctx.get("top_objections") or [])


def _ad_id(ctx: dict) -> str | None:
    return ctx.get("ad_variant_id")


def _format_template(s: str, ctx: dict, config: dict) -> str:
    ad_id = _ad_id(ctx) or ""
    objections = _top_objections(ctx)
    top1 = objections[0] if objections else ""
    brand = config.get("brand") or {}
    return s.format(
        ad_variant_id=ad_id,
        ad_variant_suffix=ad_id.replace("x-", "") if ad_id else "",
        top_objection=top1,
        audience_route=ctx.get("audience_route", "neutral"),
        accent_color=brand.get("accent_color", "#c9a227"),
        environment=(config.get("industry_env") or {}).get(
            ctx.get("industry") or "general",
            (config.get("industry_env") or {}).get("general", "professional workspace"),
        ),
    )


def _expand_signals(signals: list[str], ctx: dict) -> list[str]:
    ad_id = _ad_id(ctx) or ""
    objections = _top_objections(ctx)
    top1 = objections[0] if objections else ""
    out: list[str] = []
    for sig in signals:
        out.append(sig.format(
            ad_variant_suffix=ad_id.replace("x-", "") if ad_id else "",
            top_objection=top1,
        ))
    return out


def _pick(intent_id: str, rank: int, why: str, signals: list[str],
          disposition: str = "allude") -> ImageIntentPick:
    return {
        "intent_id": intent_id,
        "rank": rank,
        "why": why,
        "signals_used": signals,
        "disposition": disposition,
    }


def _match_when(when: dict, ctx: dict) -> bool:
    """Match a rule's when-clause against image context."""
    if not when:
        return True
    ad_id = _ad_id(ctx)
    objections = _top_objections(ctx)
    top1 = objections[0] if objections else None

    for key, expected in when.items():
        if key == "ad_variant_id":
            if expected == "$present":
                if not ad_id:
                    return False
            elif ad_id != expected:
                return False
        elif key == "top_objection":
            if expected == "$present":
                if not top1:
                    return False
            elif top1 != expected:
                return False
        elif key == "audience_route":
            if ctx.get("audience_route", "neutral") != expected:
                return False
        elif key == "channel":
            if ctx.get("channel") != expected:
                return False
        else:
            if ctx.get(key) != expected:
                return False
    return True


def _is_loss_objection(top1: str | None, config: dict) -> bool:
    if not top1:
        return False
    metaphors = config.get("objection_metaphors") or {}
    meta = metaphors.get(top1, "")
    loss_ids = (config.get("selection") or {}).get("loss_avoidance_objections") or []
    return "loss" in meta.lower() or top1 in loss_ids


def _resolve_rank(rank: int | str, picks: list[ImageIntentPick]) -> int:
    if rank == "$next":
        return len(picks) + 1
    return int(rank)


def _rule_label(kind: str, idx: int, when: dict) -> str:
    when_bits = ", ".join(f"{k}={v}" for k, v in (when or {}).items())
    return f"{kind}[{idx}]" + (f" when {{{when_bits}}}" if when_bits else " (default)")


def select_image_intent(ctx: dict, config: dict | None = None) -> ImageIntentSelection:
    """Deterministic intent selection from visitor context + tenant YAML rules."""
    config = config or _default_config()
    selection_cfg = config.get("selection") or {}
    objections = _top_objections(ctx)
    top1 = objections[0] if objections else None

    picks: list[ImageIntentPick] = []
    rule_fired = "fallback_rules (default peer_proof)"

    for idx, rule in enumerate(selection_cfg.get("primary_rules") or []):
        if _match_when(rule.get("when") or {}, ctx):
            rule_fired = _rule_label("primary_rules", idx, rule.get("when") or {})
            for p in rule.get("picks") or []:
                why = _format_template(p.get("why", ""), ctx, config)
                signals = _expand_signals(list(p.get("signals_used") or []), ctx)
                picks.append(_pick(p["intent_id"], p["rank"], why, signals))
            break

    if not picks:
        fallback_rules = selection_cfg.get("fallback_rules") or []
        default_rules = [r for r in fallback_rules if not (r.get("when") or {})]
        additive_rules = [r for r in fallback_rules if (r.get("when") or {})]

        def _apply_rule(rule: dict, idx: int, *, kind: str) -> None:
            nonlocal rule_fired
            before = len(picks)
            for p in rule.get("picks") or []:
                if "when_objection_loss" in p:
                    if not top1 or top1 not in (config.get("objection_metaphors") or {}):
                        continue
                    is_loss = _is_loss_objection(top1, config)
                    if p["when_objection_loss"] != is_loss:
                        continue
                rank = _resolve_rank(p.get("rank", len(picks) + 1), picks)
                why = _format_template(p.get("why", ""), ctx, config)
                signals = _expand_signals(list(p.get("signals_used") or []), ctx)
                picks.append(_pick(p["intent_id"], rank, why, signals))
            if len(picks) > before:
                rule_fired = _rule_label(kind, idx, rule.get("when") or {})

        for idx, rule in enumerate(additive_rules):
            if not _match_when(rule.get("when") or {}, ctx):
                continue
            _apply_rule(rule, idx, kind="fallback_rules")

        if not picks:
            for idx, rule in enumerate(default_rules):
                _apply_rule(rule, idx, kind="fallback_rules")

    seen: dict[str, ImageIntentPick] = {}
    for p in picks:
        if p["intent_id"] not in seen or p["rank"] < seen[p["intent_id"]]["rank"]:
            seen[p["intent_id"]] = p
    ordered = sorted(seen.values(), key=lambda x: x["rank"])
    for i, p in enumerate(ordered):
        p["rank"] = i + 1

    if not ordered:
        ordered = [_pick("peer_proof", 1, "fallback default", ["default"])]
        rule_fired = "fallback_rules (hard default peer_proof)"

    primary = ordered[0]
    secondary = ordered[1] if len(ordered) > 1 else None
    return {"primary": primary, "secondary": secondary, "intents": ordered,
            "rule_fired": rule_fired}


def _resolve_drives_action(ctx: dict, top_objection: str | None,
                           config: dict) -> str:
    action_map = config.get("action_map") or {}
    pairs = action_map.get("objection_pairs") or {}
    if top_objection and top_objection in pairs:
        return pairs[top_objection]
    cta = (ctx.get("cta_primary") or "").lower()
    for keyword, action in (action_map.get("cta_keywords") or {}).items():
        if keyword in cta:
            return action
    route = ctx.get("audience_route", "neutral")
    route_defaults = action_map.get("route_defaults") or {}
    if route in route_defaults:
        return route_defaults[route]
    return action_map.get("default", "program_overview")


def build_structured_prompt(ctx: dict, selection: ImageIntentSelection,
                            config: dict | None = None) -> StructuredPrompt:
    """Assemble StructuredPrompt from intent templates + ctx (guardrails applied separately)."""
    config = config or _default_config()
    intent_by_id = config["intent_by_id"]
    brand = config.get("brand") or {}
    accent = brand.get("accent_color", "#c9a227")

    primary_id = selection["primary"]["intent_id"]
    intent = intent_by_id[primary_id]
    secondary_id = selection["secondary"]["intent_id"] if selection.get("secondary") else None

    ad_id = _ad_id(ctx) or ""
    objections = _top_objections(ctx)
    top1 = objections[0] if objections else None
    industry_key = ctx.get("industry") or "general"
    industry_env = config.get("industry_env") or {}
    environment = industry_env.get(industry_key, industry_env.get("general", "professional workspace"))
    objection_metaphors = config.get("objection_metaphors") or {}
    ad_metaphors = config.get("ad_metaphors") or {}
    objection_metaphor = objection_metaphors.get(
        top1 or "", "stalled initiative beside active deployment")
    ad_metaphor = ad_metaphors.get(ad_id, "product proof environment — abstract continuity")

    fmt = {
        "environment": environment,
        "objection_metaphor": objection_metaphor,
        "ad_metaphor": ad_metaphor,
        "accent_color": accent,
    }

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

    composition = intent["composition_template"].format(**fmt)
    visual_metaphor = intent["visual_metaphor"].format(**fmt)

    prompt_defaults = config.get("prompt_defaults") or {}
    must_include = [
        item.format(**fmt) for item in (prompt_defaults.get("must_include") or [])
    ]
    must_include.append(f"conversion goal: {intent.get('conversion_goal', intent.get('goal', ''))}")
    if secondary_id:
        sec = intent_by_id[secondary_id]
        must_include.append(f"secondary visual cue: {sec['visual_metaphor']}")

    must_avoid = list(prompt_defaults.get("must_avoid") or [])
    must_avoid.extend(brand.get("must_avoid_additions") or [])

    drives_action = _resolve_drives_action(ctx, top1, config)

    return {
        "intent_id": primary_id,
        "secondary_intent_id": secondary_id,
        "conversion_goal": intent.get("conversion_goal", intent.get("goal", "")),
        "sales_technique": intent["sales_technique"],
        "personalization_layers": layers,
        "composition": composition,
        "visual_metaphor": visual_metaphor,
        "mood": intent["mood"],
        "accent_color": accent,
        "must_include": must_include,
        "must_avoid": must_avoid,
        "drives_action": drives_action,
        "pairs_with_objection": top1,
        "guardrails_applied": [],
        "guardrails_blocked": [],
        "selection": selection,
        "full_prompt": "",
        "tenant": config.get("tenant", "unknown"),
    }


def apply_guardrails(structured: StructuredPrompt, ctx: dict,
                     config: dict | None = None) -> StructuredPrompt:
    """Strip hold-tier facts; enforce must_avoid; log what was blocked."""
    config = config or _default_config()
    out = copy.copy(structured)
    blocked: list[str] = list(out.get("guardrails_blocked") or [])
    applied: list[str] = list(out.get("guardrails_applied") or [])

    hold = ctx.get("_hold") or {}
    layers = list(out.get("personalization_layers") or [])
    tier = ctx.get("tier", 0)
    tier_gates = (config.get("guardrails") or {}).get("tier_gates") or {}

    industry_gate = tier_gates.get("industry", 2)
    if tier < industry_gate:
        before = len(layers)
        layers = [l for l in layers if l["layer"] != "industry"]
        if len(layers) < before:
            blocked.append(f"industry_layer_stripped:tier<{industry_gate}")
            applied.append(f"tier_gate:industry_hold_below_tier_{industry_gate}")

    region_gate = tier_gates.get("region_mood", 1)
    if tier < region_gate:
        before = len(layers)
        layers = [l for l in layers if l["layer"] != "region_mood"]
        if len(layers) < before:
            blocked.append(f"region_layer_stripped:tier<{region_gate}")
            applied.append(f"tier_gate:region_hold_below_tier_{region_gate}")

    out["personalization_layers"] = layers

    text_parts = [
        out.get("composition", ""),
        out.get("visual_metaphor", ""),
        " ".join(l["value"] for l in layers),
    ]
    for key, label in (
        ("company", "company_name"),
        ("city", "exact_city"),
        ("visitor_name", "visitor_name"),
        ("income_band", "income"),
    ):
        val = hold.get(key)
        if val and str(val).strip() not in ("—", "", None):
            text_parts.append(str(val))
            blocked.append(f"hold_source_present:{label}")
    blob = " ".join(text_parts)

    for pat, label in HOLD_STRIP_PATTERNS:
        if pat.search(blob):
            blocked.append(f"pattern_blocked:{label}")
            applied.append(f"strip_pattern:{label}")

    must_avoid = list(dict.fromkeys(
        (out.get("must_avoid") or []) + GLOBAL_MUST_AVOID
    ))
    out["must_avoid"] = must_avoid
    applied.extend(["must_avoid_enforced", "no_text_in_image", "no_pii", "no_logos", "no_faces"])

    out["guardrails_blocked"] = list(dict.fromkeys(blocked))
    out["guardrails_applied"] = list(dict.fromkeys(applied))
    out["full_prompt"] = assemble_full_prompt(out, config)
    return out


def assemble_full_prompt(structured: StructuredPrompt,
                         config: dict | None = None) -> str:
    """Flatten StructuredPrompt into API-ready text."""
    config = config or _default_config()
    product = config.get("product_context", "marketing site")
    parts = [
        f"Cinematic wide hero backdrop for a {product}.",
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


def intent_catalog_for_config(config: dict | None = None) -> list[dict]:
    """Full intent taxonomy for /dev panel."""
    config = config or _default_config()
    return config.get("intents") or []
