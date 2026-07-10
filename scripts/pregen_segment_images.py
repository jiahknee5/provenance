#!/usr/bin/env python3
"""Pre-generate tier-1 segment base hero images for a tenant (Gauntlet default, Planet supported).

Iterates ad variants (12) plus neutral audience-route fallbacks per tenant.
Caches under semantic segment keys — no PII, no objection/industry/region.

Usage:
  PYTHONPATH=. python -m scripts.pregen_segment_images                    # gauntlet, via API
  PYTHONPATH=. python -m scripts.pregen_segment_images --dry-run          # list keys only
  PYTHONPATH=. python -m scripts.pregen_segment_images --tenant planet    # planet tenant
"""
from __future__ import annotations

import argparse
import sys

from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II

DEFAULT_TENANT = "gauntlet"

_ROUTES_BY_TENANT = {
    "gauntlet": ("neutral", "b2b_hire", "b2b_upskill", "individual"),
    "planet": ("neutral", "enterprise", "selfserve", "research"),
}


def _audience_routes(tenant: str) -> tuple[str, ...]:
    return _ROUTES_BY_TENANT.get(tenant, ("neutral",))


def _segment_specs(tenant: str = DEFAULT_TENANT) -> list[dict]:
    """Build segment ctx specs for pre-generation."""
    cfg = IG.load_image_config(tenant)
    ad_ids = sorted((cfg.get("ad_metaphors") or {}).keys())
    specs: list[dict] = []
    seen_keys: set[str] = set()

    for ad_id in ad_ids:
        ctx = {
            "channel": "ad",
            "ad_variant_id": ad_id,
            "audience_route": "neutral",
            "audience": "neutral",
            "industry": "general",
            "region": None,
            "tier": 0,
            "top_objection": None,
            "top_objections": [],
            "_hold": {},
        }
        sel = II.select_image_intent(II.segment_ctx(ctx), cfg)
        intent_id = sel["primary"]["intent_id"]
        key = IG.segment_cache_key(ctx, intent_id, tenant=tenant)
        if key not in seen_keys:
            seen_keys.add(key)
            specs.append({"ctx": ctx, "key": key, "intent_id": intent_id, "kind": "ad"})

    for route in _audience_routes(tenant):
        ctx = {
            "channel": "direct",
            "ad_variant_id": None,
            "audience_route": route,
            "audience": route,
            "industry": "general",
            "region": None,
            "tier": 0,
            "top_objection": None,
            "top_objections": [],
            "_hold": {},
        }
        sel = II.select_image_intent(II.segment_ctx(ctx), cfg)
        intent_id = sel["primary"]["intent_id"]
        key = IG.segment_cache_key(ctx, intent_id, tenant=tenant)
        if key not in seen_keys:
            seen_keys.add(key)
            specs.append({"ctx": ctx, "key": key, "intent_id": intent_id, "kind": "route"})

    return specs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-generate segment base hero images")
    parser.add_argument("--dry-run", action="store_true", help="List segment keys without API calls")
    parser.add_argument("--tenant", default=DEFAULT_TENANT,
                        choices=sorted(II.TENANT_CONFIG_FILES),
                        help=f"Image tenant (default: {DEFAULT_TENANT})")
    args = parser.parse_args(argv)
    tenant = args.tenant

    specs = _segment_specs(tenant)
    print(f"Segment bases to pre-generate ({tenant}): {len(specs)}")

    if args.dry_run:
        for s in specs:
            prompt, _, _ = IG.build_base_prompt(s["ctx"], tenant=tenant)
            disk_key = IG.image_cache_key(prompt)
            print(f"  {s['key']}  intent={s['intent_id']}  kind={s['kind']}  disk={disk_key[:12]}…")
        return 0

    if not IG._api_key():
        print("ERROR: IMAGE_GEN_API_KEY not set — use --dry-run or export a key.", file=sys.stderr)
        return 1

    ok = skipped = failed = 0
    for s in specs:
        prompt, structured, _ = IG.build_base_prompt(s["ctx"], tenant=tenant)
        disk_key = IG.image_cache_key(prompt)
        if IG._load_cached(disk_key):
            print(f"  SKIP (cached) {s['key']}")
            skipped += 1
            continue
        receipt = IG._generate_and_cache(
            s["ctx"], structured, prompt, disk_key, IG._model(),
            IG._tier_receipt_fields(
                tier="base",
                base_cache_key=s["key"],
                delta_cache_key=None,
                delta_signals=[],
                base_prompt=prompt,
                delta_prompt=None,
                full_prompt_len=len(prompt),
                used_prompt_len=len(prompt),
                cache_hit=False,
            ),
        )
        if receipt.get("source") == "generated":
            print(f"  OK {s['key']} → {receipt.get('url')}")
            ok += 1
        else:
            print(f"  FAIL {s['key']} → {receipt.get('source')}", file=sys.stderr)
            failed += 1

    print(f"Done: {ok} generated, {skipped} cached, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
