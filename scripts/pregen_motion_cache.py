#!/usr/bin/env python3
"""Pre-generate Planet hero motion loops into data/demo/image_cache/motion/.

Uses the same demo_cache_states() as still heroes. Respects API limits — on 429,
finishes the current asset and stops (top ad variants are listed first in the state list).

Usage:
  PYTHONPATH=. python -m scripts.pregen_motion_cache --tenant planet
  PYTHONPATH=. python -m scripts.pregen_motion_cache --tenant planet --dry-run
  railway run python -m scripts.pregen_motion_cache --tenant planet
"""
from __future__ import annotations

import argparse
import sys

from pipeline.personalization import image_gen as IG
from pipeline.personalization import motion_gen as MG
from pipeline.personalization import planet_site as PS
from pipeline.personalization.planet_image_decisions import demo_cache_states as _planet_states

_TENANTS = {
    "planet": (_planet_states, PS.build_page, PS.IMAGE_TENANT),
}

# Warm these ad variants first if we hit rate limits.
_PRIORITY_ADS = (
    "x-agriculture", "x-defense", "x-insurance", "x-forestry", "x-energy", "x-government",
)


class _Req:
    client = None

    def __init__(self, params=None, headers=None):
        self.query_params = params or {}
        self.headers = headers or {}
        self.cookies = {}


def _is_priority(label: str, params: dict) -> bool:
    campaign = (params or {}).get("utm_campaign", "")
    for ad in _PRIORITY_ADS:
        if ad in campaign:
            return True
    return "ad" in label.lower() and "v0" in label


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-generate hero motion loops for demo states")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-regen", action="store_true")
    parser.add_argument("--tenant", default="planet", choices=sorted(_TENANTS))
    parser.add_argument("--max", type=int, default=0, help="Stop after N generations (0 = all)")
    parser.add_argument("--offline-from-stills", action="store_true",
                        help="Build motion from cached stills (no API) — for deploy pregen")
    args = parser.parse_args(argv)

    states_fn, build_page, tenant = _TENANTS[args.tenant]
    states = states_fn()
    # Priority ad variants first for 429 partial runs.
    states = sorted(states, key=lambda e: (0 if _is_priority(e[0], e[1]) else 1, e[0]))

    if not MG.motion_enabled(tenant=tenant):
        print(f"[{args.tenant}] motion.enabled is false — nothing to do.")
        return 0

    print(f"[{args.tenant}] motion states to warm: {len(states)}")

    if not args.dry_run and not args.offline_from_stills and not IG._api_key():
        print("ERROR: IMAGE_GEN_API_KEY not set.", file=sys.stderr)
        return 1

    ok = cached = failed = stopped = 0
    seen: set[str] = set()
    for entry in states:
        label = entry[0]
        params = entry[1]
        email = entry[2] if len(entry) > 2 else None
        page = build_page(_Req(dict(params)), email=email)
        ctx = IG.build_image_ctx(page)
        keys = MG._resolve_motion_keys(ctx, tenant=tenant)
        disk_key = keys["disk_key"]
        dup = disk_key in seen
        seen.add(disk_key)

        if MG._load_motion_cached(disk_key) and not args.force_regen:
            print(f"  CACHED {label}" + ("  [dup]" if dup else ""))
            cached += 1
            continue

        if args.dry_run:
            print(f"  MISS   {label} disk={disk_key[:12]}… metaphor={keys['metaphor']}"
                  + ("  [dup]" if dup else ""))
            continue

        # Ensure still hero exists for frame-0 reuse when base_only.
        still = IG.resolve_hero_image(page, generate=not args.offline_from_stills, tenant=tenant)
        if args.offline_from_stills:
            motion = MG.build_motion_offline_from_still(
                ctx, tenant=tenant, still_receipt=still.get("receipt"),
            )
        else:
            motion = MG.get_hero_motion(
                ctx, generate=True, tenant=tenant, still_receipt=still.get("receipt"),
            )
        src = (motion.get("receipt") or {}).get("source")
        if src == "generated":
            print(f"  OK     {label} → {motion.get('url')}")
            ok += 1
            if args.max and ok >= args.max:
                stopped = 1
                break
        else:
            print(f"  FAIL   {label} → {src}", file=sys.stderr)
            failed += 1
            if src == "api_failed":
                stopped = 1
                break

    print(f"[{args.tenant}] distinct motion keys: {len(seen)}")
    print(f"Done: {ok} generated, {cached} cached, {failed} failed"
          + (", stopped early (rate limit / --max)" if stopped else ""))
    return 1 if failed and not ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
