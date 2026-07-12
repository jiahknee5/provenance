"""Playbook — the in-shell "how it's made" guide (marketer language, real config).

GET /apt/playbook renders four chapters inside the apt console shell:

  1. How images are made  — the default methodology as a numbered flow, with the
                            tenant's REAL visual-intent catalog rendered from
                            rules/<tenant>_image.yaml (never invented prose).
  2. How copy is made     — the deterministic slot-fill default (provable by
                            construction, $0), the 5 persuasion strategies imported
                            from persuasion.STRATEGIES, and the opt-in generative
                            lane (prompt → candidates → the real Gate → cleared pool).
  3. Animated images      — Planet's shipped hero-motion loops as the preview of the
                            methodology, plus a clearly-badged future-release roadmap.
  4. AEO                  — Agent Engine Optimization: a roadmap / point-of-view
                            chapter. Nothing in it is built; every line is a thesis.

Everything factual is read from the same files the engine reads — the tenant image
YAML, the section registry paths, persuasion.STRATEGIES, prebuild caps, the realtime
ceiling — so the playbook cannot drift from the product. Honesty is inviolable
(CONSTITUTION Art I + the PRD non-goal): the stimulation model is always labeled
predicted / simulated proxy modeling, never measured brain data.
"""
from __future__ import annotations

from typing import Any

from starlette.requests import Request

from pipeline.observability import api_costs as AC
from pipeline.personalization import demo_nav as NAV
from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II
from pipeline.personalization import persuasion as PS
from pipeline.personalization import prebuild as PB
from pipeline.personalization.brain_simulator import intent_brain_fields


def _intent_cards(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """The tenant's REAL intent catalog, shaped for the chapter-1 cards."""
    cards: list[dict[str, Any]] = []
    for it in cfg.get("intents") or []:
        target, regions = intent_brain_fields(it)
        cards.append({
            "id": it["id"],
            "brain_target": target or "—",
            "brain_regions": regions,
            "conversion_goal": it.get("conversion_goal", ""),
            "sales_technique": it.get("sales_technique", ""),
            "visual_metaphor": it.get("visual_metaphor", ""),
            "mood": it.get("mood", ""),
            "design_principles": list(it.get("design_principles") or []),
            "color_rules": it.get("color_rules", ""),
            "composition": (it.get("composition_template") or "").strip(),
        })
    return cards


def _must_avoid(cfg: dict[str, Any]) -> list[str]:
    """The tenant's merged must-avoid list: prompt defaults + brand additions."""
    out = list(((cfg.get("prompt_defaults") or {}).get("must_avoid")) or [])
    for extra in ((cfg.get("brand") or {}).get("must_avoid_additions")) or []:
        if extra not in out:
            out.append(extra)
    return out


def build_playbook_view(request: Request) -> dict[str, Any]:
    """View model for /apt/playbook — tenant-aware via ?site= like /costs."""
    site = request.query_params.get("site", "").strip().lower()
    if site not in NAV.TENANTS:
        site = NAV.TENANTS[0]
    shell = NAV.console_shell_ctx(site, "consoles", active_sub="playbook")

    cfg = II.load_image_config(site)
    brand = cfg.get("brand") or {}
    tier_gates = ((cfg.get("guardrails") or {}).get("tier_gates")) or {}
    per_gen = AC.estimate_cost(service="gemini_image", model=IG.DEFAULT_MODEL,
                               images_generated=1)

    # Chapter 2 — the real strategy catalog (imported, never copied by hand).
    strategies = [
        {"key": k, "label": k.replace("_", " "), "principle": v["principle"],
         "headline": v["headline"], "cta": v["cta"], "lead": v.get("lead")}
        for k, v in PS.STRATEGIES.items()
    ]

    # Chapter 3 — Planet's shipped motion config is the real preview of the method.
    planet_motion = dict(II.load_image_config("planet").get("motion") or {})
    site_motion_enabled = bool((cfg.get("motion") or {}).get("enabled"))

    return {
        **shell,
        "site": site,
        "site_name": shell["active"]["name"],
        "intents": _intent_cards(cfg),
        "accent_color": brand.get("accent_color", ""),
        "brand_name": brand.get("name", shell["active"]["name"]),
        "must_avoid": _must_avoid(cfg),
        "tier_gates": tier_gates,
        "brain_sim_enabled": bool((cfg.get("brain_simulator") or {}).get("enabled")),
        "strategies": strategies,
        "planet_motion": planet_motion,
        "site_motion_enabled": site_motion_enabled,
        "caps": {
            "states_per_target": PB.CAP_STATES_PER_TARGET,
            "images_per_tenant": PB.CAP_IMAGES_PER_TENANT,
            "images_global": PB.CAP_IMAGES_GLOBAL,
            "ceiling_usd": IG.realtime_ceiling_usd(),
            "per_gen_usd": per_gen,
        },
        "files": {
            "sections": f"rules/{site}_sections.yaml",
            "image": f"rules/{site}_image.yaml",
            "prebuild": f"rules/{site}_prebuild.yaml",
        },
        "designer_href": next(it["href"] for grp in shell["nav_tree"]
                              for it in grp["items"] if it["id"] == "designer"),
    }
