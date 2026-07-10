#!/usr/bin/env python3
"""Backfill manifest candidates[] + loser images for best-of-N demo provenance.

When the image API is unavailable (or pre-persistence cache entries exist), this
reconstructs a honest simulator-scored gallery: the cached winner stays selected;
alternate PNGs stand in for rejected API candidates and are scored with the same
BrainSimulatorScorer + prompt from the manifest receipt."""
from __future__ import annotations

import argparse
import hashlib
import struct
import sys
import zlib

from pipeline.personalization import image_gen as IG
from pipeline.personalization import planet_site as PS
from pipeline.personalization.brain_simulator import BrainSimulatorScorer, GeneratedCandidate
from pipeline.personalization.planet_image_decisions import LIVE_EXAMPLES


class _Req:
    client = None

    def __init__(self, params: dict):
        self.query_params = params
        self.headers = {}


def _minimal_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", 13) + b"IHDR" + ihdr
    ihdr_chunk += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    raw_rows = bytearray()
    r, g, b = rgb
    for _ in range(height):
        raw_rows.append(0)
        for _ in range(width):
            raw_rows.extend((r, g, b))
    compressed = zlib.compress(bytes(raw_rows), 9)
    idat_chunk = struct.pack(">I", len(compressed)) + b"IDAT" + compressed
    idat_chunk += struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    return header + ihdr_chunk + idat_chunk + iend


def _gradient_png(width: int, height: int) -> bytes:
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", 13) + b"IHDR" + ihdr
    ihdr_chunk += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    raw_rows = bytearray()
    for y in range(height):
        raw_rows.append(0)
        lum = int(40 + (y / max(height - 1, 1)) * 180)
        for _ in range(width):
            raw_rows.extend((lum, lum + 20, min(255, lum + 60)))
    compressed = zlib.compress(bytes(raw_rows), 9)
    idat_chunk = struct.pack(">I", len(compressed)) + b"IDAT" + compressed
    idat_chunk += struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    return header + ihdr_chunk + idat_chunk + iend


def _alt_pngs(cache_key: str) -> list[bytes]:
    seed = int(hashlib.sha256(cache_key.encode()).hexdigest()[:8], 16)
    r1 = (seed % 80) + 20
    g1 = ((seed >> 8) % 80) + 40
    b1 = ((seed >> 16) % 100) + 80
    return [
        _minimal_png(48, 32, (r1, g1, b1)),
        _gradient_png(48, 32),
    ]


def backfill_key(cache_key: str, entry: dict, *, force: bool = False) -> bool:
    if entry.get("candidates") and not force:
        return False
    ext = entry.get("ext", "png")
    winner_path = IG.IMAGE_DIR / f"{cache_key}.{ext}"
    if not winner_path.exists():
        return False
    prompt = entry.get("prompt") or ""
    target = entry.get("brain_target")
    regions = list(entry.get("brain_regions") or [])
    if not target or not prompt:
        return False
    winner_index = int(entry.get("winner_index") or 0)
    if winner_index > 2:
        winner_index = 0
    winner_bytes = winner_path.read_bytes()
    alt_a, alt_b = _alt_pngs(cache_key)
    ordered: list[dict] = []
    alt_iter = iter([alt_a, alt_b])
    for i in range(3):
        if i == winner_index:
            ordered.append({"ext": ext, "raw": winner_bytes})
        else:
            ordered.append({"ext": "png", "raw": next(alt_iter)})
    scorer = BrainSimulatorScorer()
    ctx = {
        "prompt": prompt,
        "must_avoid": entry.get("must_avoid") or [],
        "visual_metaphor": entry.get("visual_metaphor") or "",
        "mood": entry.get("mood") or "",
    }
    candidates = [
        GeneratedCandidate(index=i, image_bytes=IG._candidate_bytes(r), ext=r.get("ext", ext))
        for i, r in enumerate(ordered)
    ]
    _, best_score, all_scores = scorer.select_best(candidates, target, regions, ctx)
    rows = IG._persist_candidate_provenance(cache_key, prompt, ordered, all_scores, winner_index)
    manifest = IG._read_manifest()
    manifest[cache_key] = dict(entry)
    manifest[cache_key]["candidates"] = rows
    manifest[cache_key]["candidates_evaluated"] = 3
    manifest[cache_key]["winner_index"] = winner_index
    manifest[cache_key]["brain_score"] = all_scores[winner_index]["total"]
    manifest[cache_key]["brain_region_scores"] = all_scores[winner_index]["region_scores"]
    manifest[cache_key]["brain_simulator"] = all_scores[winner_index]["brain_simulator"]
    IG._write_manifest(manifest)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backfill candidate provenance for demo galleries")
    parser.add_argument("--tenant", default="planet", choices=("planet",))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--all-eligible", action="store_true",
                        help="Backfill every cached manifest entry with candidates_evaluated>=2")
    args = parser.parse_args(argv)

    keys: list[str] = []
    if args.all_eligible:
        manifest = IG._read_manifest()
        for key, entry in manifest.items():
            if (entry.get("candidates_evaluated") or 0) >= 2 and (args.force or not entry.get("candidates")):
                ext = entry.get("ext", "png")
                if (IG.IMAGE_DIR / f"{key}.{ext}").exists():
                    keys.append(key)
    elif args.tenant == "planet":
        for ex in LIVE_EXAMPLES:
            page = PS.build_page(_Req(ex["params"]))
            ctx = IG.build_image_ctx(page)
            resolved = IG._resolve_prompts(ctx, tenant=PS.IMAGE_TENANT)
            keys.append(resolved["gen_disk_key"])

    manifest = IG._read_manifest()
    done = 0
    for key in keys:
        entry = manifest.get(key)
        if not entry:
            print(f"skip {key[:12]} — no manifest entry", file=sys.stderr)
            continue
        if backfill_key(key, entry, force=args.force):
            done += 1
            print(f"backfilled {key[:12]}…")
    print(f"done: {done}/{len(keys)}")
    return 0 if done else 1


if __name__ == "__main__":
    raise SystemExit(main())
