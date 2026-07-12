"""Prebuild manifest — the version-controlled list of demo states to pre-generate.

rules/gauntlet_prebuild.yaml is the single source of truth for which image
states get baked into the deploy image, per surface (hero, og, …). Three consumers
share it so they can't drift:
  · scripts/warm_hero_cache.py        — generates the images before deploy
  · /dev/image-decisions (Part 6)     — live cache inventory
  · /dev/business console             — per-state load policy + prebuild toggles

Entries are semantic (entry kind + ad variant), not raw params: UTMs resolve from
the ad catalog and the email magic token from the cohort, so the manifest can't
fall out of sync with either. Deterministic: no network, no API calls.

Backward compat: a flat ``states`` list (no ``surfaces``) is treated as hero-only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pipeline.personalization import cohort as CO
from pipeline.personalization import gauntlet_site as GS

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "rules" / "gauntlet_prebuild.yaml"

_cache: dict[str, dict] = {}


def load_prebuild_manifest(path: Path | None = None) -> dict[str, Any]:
    """Load and cache the prebuild manifest YAML."""
    p = path or MANIFEST_PATH
    key = str(p)
    if key not in _cache:
        data = yaml.safe_load(p.read_text()) or {}
        data.setdefault("states", [])
        _cache[key] = data
    return _cache[key]


def manifest_surface_ids(manifest: dict | None = None) -> list[str]:
    """Surface ids declared in the manifest — hero always first."""
    m = manifest or load_prebuild_manifest()
    if m.get("surfaces"):
        out = ["hero"]
        for sid in m["surfaces"]:
            if sid not in out:
                out.append(sid)
        return out
    return ["hero"]


def _surface_states(manifest: dict, surface_id: str) -> list[dict]:
    """Resolve the state list for a surface — flat ``states`` → hero only."""
    if manifest.get("surfaces"):
        return list(manifest["surfaces"].get(surface_id) or [])
    if surface_id == "hero":
        return list(manifest.get("states") or [])
    return []


def _entry_params(state: dict, manifest: dict) -> dict:
    kind = state.get("entry", "direct")
    if kind == "ad":
        vid = state.get("variant", "")
        v = GS.AD_BY_VARIANT_ID.get(vid)
        if v is None:
            raise ValueError(f"prebuild manifest: unknown ad variant {vid!r} in state {state.get('id')!r}")
        return {"utm_source": "x", "utm_medium": "paid",
                "utm_campaign": v["utm_campaign"], "utm_content": v["variant_id"]}
    if kind == "search":
        return {"ref": "google"}
    if kind == "email":
        return {"utm_source": "hubspot", "utm_medium": "email",
                "utm_campaign": "cohort-april",
                "e": CO.magic_token(CO.BY_ID["liam"])}
    if kind == "direct":
        return {}
    raise ValueError(f"prebuild manifest: unknown entry kind {kind!r} in state {state.get('id')!r}")


def manifest_states(manifest: dict | None = None,
                    *, surface_id: str = "hero") -> list[dict]:
    """Every manifest state for a surface, resolved: {id, label, params, email, prebuild, surface_id}."""
    m = manifest or load_prebuild_manifest()
    known_email = m.get("known_email") or "maya.chen@gauntletai.com"
    rows: list[dict] = []
    for s in _surface_states(m, surface_id):
        rows.append({
            "id": s["id"],
            "label": s.get("label") or s["id"],
            "params": _entry_params(s, m),
            "email": known_email if s.get("identity") == "known" else None,
            "prebuild": bool(s.get("prebuild", True)),
            "surface_id": surface_id,
        })
    return rows


def manifest_all_states(manifest: dict | None = None) -> list[dict]:
    """All states across every declared surface."""
    m = manifest or load_prebuild_manifest()
    out: list[dict] = []
    for sid in manifest_surface_ids(m):
        out.extend(manifest_states(m, surface_id=sid))
    return out


def prebuild_states(manifest: dict | None = None,
                    *, surface_id: str | None = None) -> list[tuple[str, dict, str | None, str]]:
    """(label, params, email, surface_id) tuples for states flagged prebuild: true —
    the exact list scripts/warm_hero_cache.py generates before a deploy."""
    m = manifest or load_prebuild_manifest()
    surface_ids = [surface_id] if surface_id else manifest_surface_ids(m)
    out: list[tuple[str, dict, str | None, str]] = []
    for sid in surface_ids:
        for r in manifest_states(m, surface_id=sid):
            if r["prebuild"]:
                label = r["label"] if sid == "hero" else f"{r['label']} · {sid}"
                out.append((label, r["params"], r["email"], sid))
    return out
