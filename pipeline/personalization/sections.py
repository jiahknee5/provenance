"""Section registry loader — rules/<tenant>_sections.yaml (S1/R30).

The registry is the one data model both personalization lanes read: an ordered list
of page sections per tenant, each carrying 0..n text_targets (copy slots) and 0..n
image_targets (surfaces). Schema, validation rules, and this loader API are pinned by
04-spec/contracts/registry-schema.md — changes require a logged decision.

T-01 seeds the YAML DESCRIPTIVELY (Art IV): it mirrors the slot() ids hardcoded in
gauntlet_site/planet_site.build_page plus the hero/og image surfaces, and build_page
does not read it yet — page output is byte-identical before/after this module lands.

Caching mirrors demo_nav.load_scenarios: a module-level cache keyed on the file path,
populated once per process after schema validation.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

RULES_DIR = Path(__file__).resolve().parents[2] / "rules"

# --------------------------------------------------------------------------- #
# Pinned schema vocabulary (registry-schema.md) — unknown keys are rejected.
# --------------------------------------------------------------------------- #
_TOP_KEYS = {"version", "tenant", "sections"}
_SECTION_KEYS = {"id", "label", "region", "personalize", "goal", "channels",
                 "text_targets", "image_targets", "guardrails", "evals"}
_TEXT_TARGET_KEYS = {"slot_id", "label", "mode", "workflow", "strategy", "policy",
                     "source", "claims", "prompt", "gate"}
_IMAGE_TARGET_KEYS = {"surface_id", "label", "workflow", "intent_rules", "guardrails",
                      "prebuilt_states_cap"}

_TEXT_MODES = {"deterministic", "generative"}
_TEXT_WORKFLOWS = {"realtime", "prebuilt"}       # deterministic→realtime only (enforced below)
_IMAGE_WORKFLOWS = {"prebuilt", "realtime", "live"}  # live = discouraged, UI warns; loader accepts
_POLICIES = {"say", "allude", "hold"}

_cache: dict[str, dict[str, Any]] = {}


def _registry_path(tenant: str) -> Path:
    return RULES_DIR / f"{tenant}_sections.yaml"


def _err(tenant: str, msg: str) -> ValueError:
    return ValueError(f"sections registry [{tenant}]: {msg}")


def validate_registry(data: Any, *, tenant: str = "?") -> dict:
    """Validate a parsed registry mapping against the pinned contract; raise ValueError.

    Rejection rules (registry-schema.md): unknown top-level/field keys; duplicate
    id/slot_id/surface_id; generative with empty prompt or missing gate; deterministic
    with non-empty prompt; workflow prebuilt on a deterministic text target; policy
    not in {say, allude, hold}; plus mode/workflow enum enforcement implied by the schema.
    """
    if not isinstance(data, dict):
        raise _err(tenant, "top level must be a mapping")
    unknown = set(data) - _TOP_KEYS
    if unknown:
        raise _err(tenant, f"unknown top-level keys {sorted(unknown)}")
    for req in ("version", "tenant", "sections"):
        if req not in data:
            raise _err(tenant, f"missing required top-level key {req!r}")
    sections = data["sections"]
    if not isinstance(sections, list):
        raise _err(tenant, "'sections' must be a list")

    seen_sections: set[str] = set()
    seen_slots: set[str] = set()
    seen_surfaces: set[str] = set()
    for sec in sections:
        if not isinstance(sec, dict):
            raise _err(tenant, "each section must be a mapping")
        unknown = set(sec) - _SECTION_KEYS
        if unknown:
            raise _err(tenant, f"unknown section field keys {sorted(unknown)}")
        sec_id = sec.get("id")
        if not sec_id:
            raise _err(tenant, "section missing 'id'")
        if sec_id in seen_sections:
            raise _err(tenant, f"duplicate section id {sec_id!r}")
        seen_sections.add(sec_id)

        for t in sec.get("text_targets") or []:
            if not isinstance(t, dict):
                raise _err(tenant, f"section {sec_id!r}: text target must be a mapping")
            unknown = set(t) - _TEXT_TARGET_KEYS
            if unknown:
                raise _err(tenant, f"section {sec_id!r}: unknown text_target field keys {sorted(unknown)}")
            slot_id = t.get("slot_id")
            if not slot_id:
                raise _err(tenant, f"section {sec_id!r}: text target missing 'slot_id'")
            if slot_id in seen_slots:
                raise _err(tenant, f"duplicate slot_id {slot_id!r}")
            seen_slots.add(slot_id)
            mode = t.get("mode")
            if mode not in _TEXT_MODES:
                raise _err(tenant, f"slot {slot_id!r}: mode {mode!r} not in {sorted(_TEXT_MODES)}")
            workflow = t.get("workflow")
            if workflow not in _TEXT_WORKFLOWS:
                raise _err(tenant, f"slot {slot_id!r}: workflow {workflow!r} not in {sorted(_TEXT_WORKFLOWS)}")
            policy = t.get("policy")
            if policy not in _POLICIES:
                raise _err(tenant, f"slot {slot_id!r}: policy {policy!r} not in {sorted(_POLICIES)}")
            prompt = t.get("prompt") or ""
            if mode == "generative":
                if not prompt:
                    raise _err(tenant, f"slot {slot_id!r}: mode generative with empty prompt")
                if not t.get("gate"):
                    raise _err(tenant, f"slot {slot_id!r}: mode generative missing gate")
            else:
                if prompt:
                    raise _err(tenant, f"slot {slot_id!r}: mode deterministic with non-empty prompt")
                if workflow == "prebuilt":
                    raise _err(tenant, f"slot {slot_id!r}: workflow prebuilt on a deterministic "
                                       "text target (deterministic is always realtime $0)")

        for t in sec.get("image_targets") or []:
            if not isinstance(t, dict):
                raise _err(tenant, f"section {sec_id!r}: image target must be a mapping")
            unknown = set(t) - _IMAGE_TARGET_KEYS
            if unknown:
                raise _err(tenant, f"section {sec_id!r}: unknown image_target field keys {sorted(unknown)}")
            surface_id = t.get("surface_id")
            if not surface_id:
                raise _err(tenant, f"section {sec_id!r}: image target missing 'surface_id'")
            if surface_id in seen_surfaces:
                raise _err(tenant, f"duplicate surface_id {surface_id!r}")
            seen_surfaces.add(surface_id)
            workflow = t.get("workflow")
            if workflow not in _IMAGE_WORKFLOWS:
                raise _err(tenant, f"surface {surface_id!r}: workflow {workflow!r} not in {sorted(_IMAGE_WORKFLOWS)}")
    return data


def _load(tenant: str, path: Path | None = None) -> dict[str, Any]:
    """Load, validate, and cache one tenant registry (cache keyed on path, like demo_nav)."""
    p = path or _registry_path(tenant)
    key = str(p)
    cached = _cache.get(key)
    if cached is not None:
        return cached
    raw = p.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    validate_registry(data, tenant=tenant)
    if data.get("tenant") != tenant:
        raise _err(tenant, f"file declares tenant {data.get('tenant')!r}")
    data = {
        **data,
        "_path": key,
        "_registry_version": hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16],
    }
    _cache[key] = data
    return data


# --------------------------------------------------------------------------- #
# Loader API (pinned by registry-schema.md)
# --------------------------------------------------------------------------- #
def list_sections(tenant: str) -> list[dict]:
    """Ordered, validated sections for a tenant (order = page order). Cached."""
    return _load(tenant)["sections"]


def get_section(tenant: str, section_id: str) -> dict:
    """One section by id; KeyError when the id is not in the registry."""
    for sec in list_sections(tenant):
        if sec.get("id") == section_id:
            return sec
    raise KeyError(f"sections registry [{tenant}]: no section {section_id!r}")


def list_text_targets(tenant: str) -> list[dict]:
    """All text targets, flattened in page order; each carries its section_id."""
    out: list[dict] = []
    for sec in list_sections(tenant):
        for t in sec.get("text_targets") or []:
            out.append({**t, "section_id": sec["id"]})
    return out


def list_image_targets(tenant: str) -> list[dict]:
    """All image targets, flattened in page order; each carries its section_id."""
    out: list[dict] = []
    for sec in list_sections(tenant):
        for t in sec.get("image_targets") or []:
            out.append({**t, "section_id": sec["id"]})
    return out


def registry_version(tenant: str) -> str:
    """Content hash of the tenant registry file — drift attribution (rules_version)."""
    return _load(tenant)["_registry_version"]
