"""Design prompt database — reference lookup for image prompts (and future copy slots).

rules/design_prompts.yaml is the human-editable SSOT for marketer console staging,
demo nav cross-links, and warm-cache documentation. Runtime image generation still
reads rules/*_image.yaml via image_gen / image_intents; this module does not
replace that path in v1.

CONSTITUTION Art IV: resolve_example() delegates to the same deterministic
image_intents + image_gen assembly as production — no ad-hoc LLM strings.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II

DB_PATH = Path(__file__).resolve().parents[2] / "rules" / "design_prompts.yaml"

_cache: dict[str, Any] | None = None


def load_db(*, reload: bool = False) -> dict[str, Any]:
    """Load rules/design_prompts.yaml (cached)."""
    global _cache
    if _cache is not None and not reload:
        return _cache
    raw = yaml.safe_load(DB_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"invalid design_prompts database: {DB_PATH}")
    _cache = raw
    return raw


def _entries(db: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = db or load_db()
    return list(data.get("entries") or [])


def get_entry(entry_id: str, *, db: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Return one entry by id, or None."""
    for entry in _entries(db):
        if entry.get("id") == entry_id:
            return dict(entry)
    return None


def list_entries(
    *,
    tenant: str | None = None,
    surface: str | None = None,
    channel: str | None = None,
    kind: str | None = None,
    db: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Filter catalog entries — all filters are optional AND conditions."""
    out: list[dict[str, Any]] = []
    for entry in _entries(db):
        if tenant is not None and entry.get("tenant") != tenant:
            continue
        if surface is not None and entry.get("surface") != surface:
            continue
        if channel is not None and entry.get("channel") not in (channel, "any"):
            continue
        if kind is not None and entry.get("kind", "image") != kind:
            continue
        out.append(dict(entry))
    return out


def entry_ids(**filters: Any) -> list[str]:
    """Convenience: list entry ids matching list_entries filters."""
    return [e["id"] for e in list_entries(**filters)]


def placeholders(*, db: dict[str, Any] | None = None) -> dict[str, str]:
    """Placeholder variables documented in the database meta section."""
    data = db or load_db()
    return dict((data.get("meta") or {}).get("placeholders") or {})


def _catalog_selection(intent_id: str, config: dict) -> II.ImageIntentSelection:
    if intent_id not in config.get("intent_by_id", {}):
        raise KeyError(f"unknown intent {intent_id!r} for tenant {config.get('tenant')}")
    pick = {
        "intent_id": intent_id,
        "rank": 1,
        "why": "design_prompts catalog reference",
        "signals_used": ["catalog"],
        "disposition": "allude",
    }
    return {
        "primary": dict(pick),
        "secondary": None,
        "intents": [dict(pick)],
        "rule_fired": "design_prompts.catalog",
    }


def _build_page_ctx(entry: dict[str, Any], overrides: dict[str, Any] | None) -> dict[str, Any]:
    """Build image ctx from example_page_params when present."""
    from pipeline.personalization import gauntlet_site as GS
    from pipeline.personalization import planet_site as PS

    page_params = dict(entry.get("example_page_params") or {})
    email = page_params.pop("email", None)
    if overrides:
        page_params.update({k: v for k, v in overrides.items() if k != "email"})
        if "email" in overrides:
            email = overrides["email"]

    class _Req:
        client = None

        def __init__(self, params: dict):
            self.query_params = params
            self.headers = {}

    tenant = entry.get("tenant", "gauntlet")
    if tenant == "planet":
        page = PS.build_page(_Req(page_params), email=email)
    else:
        page = GS.build_page(_Req(page_params), email=email)
    ctx = IG.build_image_ctx(page)
    return ctx


def _merge_image_ctx(entry: dict[str, Any], overrides: dict[str, Any] | None) -> dict[str, Any]:
    if entry.get("example_page_params") is not None:
        return _build_page_ctx(entry, overrides)
    ctx = dict(entry.get("example_image_ctx") or {})
    if overrides:
        ctx.update(overrides)
    return ctx


def _resolve_prompt_string(
    entry: dict[str, Any],
    ctx: dict[str, Any],
) -> str:
    tenant = entry.get("tenant", "gauntlet")
    surface_id = entry.get("surface", IG.DEFAULT_SURFACE_ID)
    config = II.load_image_config(tenant)

    if entry.get("catalog_intent"):
        selection = _catalog_selection(entry["intent"], config)
    else:
        selection = II.select_image_intent(ctx, config)

    structured = II.build_structured_prompt(ctx, selection, config)
    structured = II.apply_guardrails(structured, ctx, config)

    if surface_id != IG.DEFAULT_SURFACE_ID:
        structured = IG._apply_surface(structured, surface_id, config)
        prompt = II.assemble_full_prompt(structured, config)
        prompt = IG._finalize_surface_prompt(prompt, surface_id, config)
    else:
        prompt = II.assemble_full_prompt(structured, config)

    IG._assert_prompt_safe(prompt)
    return prompt


def resolve_example(
    entry_id: str,
    context_dict: dict[str, Any] | None = None,
    *,
    db: dict[str, Any] | None = None,
) -> str:
    """Resolve a fully assembled prompt for a catalog entry.

    Merges optional context_dict into example_page_params / example_image_ctx,
    then runs the same image_intents assembly path as image_gen (deterministic).
    """
    entry = get_entry(entry_id, db=db)
    if entry is None:
        raise KeyError(f"unknown design prompt entry: {entry_id}")
    if entry.get("kind") == "copy_slot":
        raise ValueError(f"entry {entry_id} is a copy slot reference — no image prompt")

    ctx = _merge_image_ctx(entry, context_dict)
    return _resolve_prompt_string(entry, ctx)


def intent_index(*, tenant: str, surface: str | None = None) -> list[str]:
    """Intent ids indexed under tenants.*.surfaces in the database."""
    data = load_db()
    tenants = data.get("tenants") or {}
    block = tenants.get(tenant) or {}
    surfaces = block.get("surfaces") or {}
    if surface:
        spec = surfaces.get(surface) or {}
        return list(spec.get("intents") or [])
    out: list[str] = []
    for spec in surfaces.values():
        for iid in spec.get("intents") or []:
            if iid not in out:
                out.append(iid)
    return out
