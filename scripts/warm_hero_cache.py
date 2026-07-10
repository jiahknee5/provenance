#!/usr/bin/env python3
"""Warm the image cache for every state and surface the demo actually shows.

Railway's filesystem is ephemeral, so anything generated at runtime is lost on the
next deploy. This script generates every demo-reachable image surface locally into
data/demo/image_cache/, which ships inside the Docker image (see .dockerignore) —
fresh deploys then serve every background inline, instantly.

It drives the real build_page() → image_gen resolution path with generate=True, so
the disk cache keys match EXACTLY what production requests (no hand-built keys).

Tenants:
  gauntlet (default) — 12 X ad variants + direct/search/email entries, anon + known;
                       warms hero + Open Graph surfaces from rules/gauntlet_prebuild.yaml.
  planet             — the same segment set PLUS every base+delta the demo surfaces:
                       an objection nearly always fires and geo-IP region is the star
                       signal, so Planet ships base+delta heroes that the segment-only
                       bases never cover. Also warms the example-account IP LOCATION
                       variants (region_mood + tier-2 industry deltas).

Usage:
  railway run python -m scripts.warm_hero_cache                     # gauntlet, key from Railway env
  railway run python -m scripts.warm_hero_cache --tenant planet     # planet
  PYTHONPATH=. python -m scripts.warm_hero_cache --tenant planet --dry-run  # list states + status
"""
from __future__ import annotations

import argparse
import sys

from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_gen as IG
from pipeline.personalization import planet_site as PS
# Single source of truth for the warmed state lists — gauntlet reads the
# version-controlled manifest rules/gauntlet_prebuild.yaml (per-surface prebuild
# flag), shared with the /dev/image-decisions guide and the /dev/business
# console so they can't drift.
from pipeline.personalization.planet_image_decisions import demo_cache_states as _planet_states
from pipeline.personalization.prebuild import prebuild_states as _gauntlet_states

# Per-tenant wiring: (state list, build_page callable, image tenant slug).
_TENANTS = {
    "gauntlet": (_gauntlet_states, GS.build_page, IG.DEFAULT_IMAGE_TENANT),
    "planet": (_planet_states, PS.build_page, PS.IMAGE_TENANT),
}


class _Req:
    """Minimal request stand-in (mirrors tests) — offline client → tier 0 unless ?ip=."""
    client = None

    def __init__(self, params=None, headers=None):
        self.query_params = params or {}
        self.headers = headers or {}
        self.cookies = {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Warm image cache for all demo states and surfaces")
    parser.add_argument("--dry-run", action="store_true", help="List states without API calls")
    parser.add_argument("--force-regen", action="store_true",
                        help="Regenerate even when disk cache already has an entry")
    parser.add_argument("--tenant", default="gauntlet", choices=sorted(_TENANTS),
                        help="Which demo to warm (default: gauntlet)")
    args = parser.parse_args(argv)

    states_fn, build_page, tenant = _TENANTS[args.tenant]
    states = states_fn()
    print(f"[{args.tenant}] demo states to warm: {len(states)}")

    if not args.dry_run and not IG._api_key():
        print("ERROR: IMAGE_GEN_API_KEY not set — run via `railway run` or export a key.",
              file=sys.stderr)
        return 1

    ok = cached = failed = 0
    seen_keys: set[str] = set()
    for entry in states:
        if len(entry) == 4:
            label, params, email, surface_id = entry
        else:
            label, params, email = entry
            surface_id = IG.DEFAULT_SURFACE_ID
        page = build_page(_Req(dict(params)), email=email)
        ctx = IG.build_image_ctx(page)
        resolved = IG._resolve_prompts(ctx, tenant=tenant, surface_id=surface_id)
        key = resolved["gen_disk_key"]
        dup = key in seen_keys
        seen_keys.add(key)
        if IG._load_cached(key) and not args.force_regen:
            print(f"  CACHED {label} ({resolved['tier']}) surface={surface_id}"
                  + ("  [dup key]" if dup else ""))
            cached += 1
            continue
        if args.force_regen:
            IG.invalidate_cached(key)
            if resolved.get("base_disk_key") and resolved["base_disk_key"] != key:
                IG.invalidate_cached(resolved["base_disk_key"])
        if args.dry_run:
            print(f"  MISS   {label} ({resolved['tier']}) surface={surface_id} disk={key[:12]}…"
                  + ("  [dup key]" if dup else ""))
            continue
        img = IG.resolve_surface_image(page, surface_id=surface_id,
                                       generate=True, tenant=tenant)
        src = (img.get("receipt") or {}).get("source")
        if src == "generated":
            print(f"  OK     {label} ({resolved['tier']}) surface={surface_id} → {img.get('url')}")
            ok += 1
        else:
            print(f"  FAIL   {label} surface={surface_id} → {src}", file=sys.stderr)
            failed += 1

    print(f"[{args.tenant}] distinct disk keys: {len(seen_keys)}")
    print(f"Done: {ok} generated, {cached} already cached, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
