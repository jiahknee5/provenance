#!/usr/bin/env python3
"""Warm the prebuilt generative-copy cache (T-05/S2) — the text lane's warm_hero_cache.

For every registry text target with ``mode: generative`` and ``workflow: prebuilt``
this script builds the full candidate set offline (deterministic seeded synthesis, plus
LLM upgrades when ANTHROPIC_API_KEY is set — every call cost-logged via api_costs and
LLM-cached), runs EVERY candidate through the real Gate via the DecisionPool, and bakes
the candidates to data/demo/copy_cache/<tenant>__<section>__<slot>.json with stable
bytes — fresh deploys then replay the pool byte-identically at $0.

The Gate stays load-bearing at runtime: the baked file holds CANDIDATES (adversarial
probes included), and every pool build re-Gates them against current rules state — a
baked candidate whose claim goes on hold is structurally unservable without a re-warm.

Fail-loud (deploy gate): a prebuilt generative target whose cleared pool is EMPTY exits
nonzero — a page slot with nothing servable is a build defect, not a runtime surprise.

Usage:
  PYTHONPATH=. python -m scripts.warm_copy_cache                    # all tenants
  PYTHONPATH=. python -m scripts.warm_copy_cache --tenant gauntlet
  PYTHONPATH=. python -m scripts.warm_copy_cache --dry-run          # list targets only
  PYTHONPATH=. python -m scripts.warm_copy_cache --force-regen      # rebuild existing
"""
from __future__ import annotations

import argparse
import sys

from pipeline.common import config
from pipeline.personalization import generative_text as GT
from pipeline.personalization import sections


def _tenants() -> list[str]:
    return sorted(p.name[:-len("_sections.yaml")]
                  for p in sections.RULES_DIR.glob("*_sections.yaml")
                  if not p.name.startswith("_"))


def _prebuilt_generative_targets(tenant: str) -> list[dict]:
    return [t for t in sections.list_text_targets(tenant)
            if t.get("mode") == "generative" and t.get("workflow") == "prebuilt"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bake Gate-cleared generative copy pools for prebuilt text targets")
    parser.add_argument("--tenant", default=None,
                        help="One tenant (default: every rules/*_sections.yaml)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List targets and cache status without building")
    parser.add_argument("--force-regen", action="store_true",
                        help="Rebuild even when the cache file already exists")
    args = parser.parse_args(argv)

    tenants = [args.tenant] if args.tenant else _tenants()
    keyed = bool(config.ANTHROPIC_API_KEY)
    print(f"copy-cache warm: tenants={tenants} "
          f"({'LLM upgrades ON — calls cost-logged' if keyed else 'offline — $0, deterministic'})")

    baked = cached = empty = total = 0
    for tenant in tenants:
        targets = _prebuilt_generative_targets(tenant)
        print(f"[{tenant}] prebuilt generative text targets: {len(targets)}")
        for t in targets:
            total += 1
            sec, slot, prompt = t["section_id"], t["slot_id"], t.get("prompt") or ""
            path = GT._cache_path(tenant, sec, slot)
            if path.exists() and not args.force_regen and \
                    GT.load_cache(tenant, sec, slot, prompt) is not None:
                print(f"  CACHED {tenant}:{sec}:{slot} -> {path.name}")
                cached += 1
                continue
            if args.dry_run:
                print(f"  MISS   {tenant}:{sec}:{slot}"
                      + ("  [stale]" if path.exists() else ""))
                continue
            # fresh synthesis (never the disk cache), then the REAL Gate via the pool
            cands = GT.build_candidates(tenant, sec, slot, use_cache=False)
            GT.write_cache(tenant, sec, slot, cands, prompt)
            pool = GT.pool_for(tenant, sec, slot)
            cleared = pool.cleared_pool(tenant, sec, slot)
            report = pool.clearance_report(tenant, sec, slot)
            blocked = [r for r in report if not r["in_pool"]]
            print(f"  BAKED  {tenant}:{sec}:{slot} -> {path.name}  "
                  f"candidates={len(cands)} cleared={len(cleared)} blocked={len(blocked)}")
            for r in blocked:
                why = (r["copy_blocks"] or r["message_vetoes"] or
                       (["claim not cleared"] if not r["claims_cleared"] else ["blocked"]))
                print(f"         BLOCKED {r['arm']}: {why[0]}")
            if not cleared:
                print(f"  ERROR  {tenant}:{sec}:{slot} cleared pool is EMPTY — "
                      "nothing servable for a prebuilt slot", file=sys.stderr)
                empty += 1
                continue
            baked += 1

    print(f"Done: {baked} baked, {cached} already cached, {empty} empty pools, "
          f"{total} targets")
    return 1 if empty else 0


if __name__ == "__main__":
    raise SystemExit(main())
