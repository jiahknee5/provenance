"""Planet hero motion — multi-frame timelapse loops (NEvo-inspired, marketing-honest).

Generates 3–5 keyframe stills via the existing image API, assembles an animated WebP loop,
and caches under the same two-tier semantic keys as still heroes. Page load never blocks on
generation — pregen + async fetch only. Framing: simulated change-over-time timelapse, not
visitor neuro-stimulation."""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

from pipeline.personalization import image_gen as IG
from pipeline.personalization import image_intents as II
from pipeline.personalization.brain_simulator import (
    BrainSimulatorScorer,
    brain_sim_enabled,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
MOTION_SUBDIR = "motion"
FRAME_SUBDIR = "motion_frames"

# Temporal directives per assembly metaphor (appended to the base hero prompt).
_FRAME_DIRECTIVES: dict[str, list[str]] = {
    "change_wipe": [
        "Frame t0 — pristine before state, true-color satellite, no visible change.",
        "Frame t1 — faint analytic seam at one edge, subtle change hint only.",
        "Frame t2 — clear before/after seam, half the view shows analytic-blue delta.",
        "Frame t3 — after state dominant, change fully legible at region scale.",
    ],
    "pan_left": [
        "Frame t0 — centered wide satellite view, single focal landform.",
        "Frame t1 — subtle leftward orbital pan, same lighting and scale.",
        "Frame t2 — continued left pan across adjacent terrain mosaic.",
        "Frame t3 — broader regional mosaic, daily coverage implied.",
    ],
    "seasonal_shift": [
        "Frame t0 — early-season true-color fields, cool muted greens.",
        "Frame t1 — mid-season warming, crop canopy filling in.",
        "Frame t2 — peak season emerald tones across the quilt.",
        "Frame t3 — late-season amber shift along field edges.",
    ],
    "crop_growth": [
        "Frame t0 — bare soil grid between planting rows.",
        "Frame t1 — faint green emergence in center-pivot arcs.",
        "Frame t2 — full canopy quilt with NDVI-style health gradient.",
        "Frame t3 — harvest-ready amber sweep across the belt.",
    ],
    "storm_footprint": [
        "Frame t0 — calm coastal township, intact true-color.",
        "Frame t1 — distant storm shadow approaching offshore.",
        "Frame t2 — regional post-storm analytic tint spreading inland.",
        "Frame t3 — damage-grade overlay at region scale — not property scale.",
    ],
    "filmstrip_scroll": [
        "Frame t0 — newest crisp tile forward, history stacked behind.",
        "Frame t1 — filmstrip advances one day, soft stack recedes.",
        "Frame t2 — mid-stack depth visible, archive advantage implied.",
        "Frame t3 — deep history stack, newest tile still hero focal.",
    ],
    "orbit_pass": [
        "Frame t0 — ground track arc beginning at horizon rim.",
        "Frame t1 — pass midpoint, faint scan-line across mosaic.",
        "Frame t2 — track advancing, analytic grid softly lit.",
        "Frame t3 — pass completing, constellation rhythm implied.",
    ],
}

_DEFAULT_METAPHOR_BY_INTENT: dict[str, str] = {
    "change_proof": "change_wipe",
    "regional_truth": "pan_left",
    "archive_advantage": "filmstrip_scroll",
    "aspiration_research": "seasonal_shift",
    "message_match": "pan_left",
    "mission_authority": "orbit_pass",
    "retarget_warm": "orbit_pass",
}

# Ad-variant overrides (segment-specific motion story).
_AD_MOTION_METAPHORS: dict[str, str] = {
    "x-agriculture": "crop_growth",
    "x-insurance": "storm_footprint",
    "x-forestry": "seasonal_shift",
    "x-government": "change_wipe",
}


def _tenant_config(tenant: str | None) -> dict:
    return IG.load_image_config(tenant or IG.DEFAULT_IMAGE_TENANT)


def motion_settings(config: dict | None = None, *, tenant: str | None = None) -> dict:
    cfg = config or _tenant_config(tenant)
    base = {
        "enabled": False,
        "frames": 4,
        "duration_ms": 3000,
        "loop": True,
        "assembly": "animated_webp",
        "framing": (
            "Simulated change-over-time timelapse — multi-frame loop for demo storytelling, "
            "not measured visitor brain stimulation."
        ),
    }
    base.update(cfg.get("motion") or {})
    return base


def motion_enabled(config: dict | None = None, *, tenant: str | None = None) -> bool:
    return bool(motion_settings(config, tenant=tenant).get("enabled"))


def motion_metaphor(ctx: dict, intent_id: str, config: dict) -> str:
    """Resolve assembly metaphor: ad override → intent YAML → defaults."""
    ad = ctx.get("ad_variant_id")
    if ad and ad in _AD_MOTION_METAPHORS:
        return _AD_MOTION_METAPHORS[ad]
    for intent in config.get("intents") or []:
        if intent.get("id") == intent_id and intent.get("motion_metaphor"):
            return intent["motion_metaphor"]
    return _DEFAULT_METAPHOR_BY_INTENT.get(intent_id, "pan_left")


def motion_segment_cache_key(ctx: dict, intent_id: str, *, tenant: str | None = None) -> str:
    t = tenant or IG.DEFAULT_IMAGE_TENANT
    ad = ctx.get("ad_variant_id")
    if ad:
        return f"{t}:motion:base:{ad}"
    route = ctx.get("audience_route", "neutral")
    return f"{t}:motion:base:{intent_id}:{route}"


def motion_delta_cache_key(ctx: dict, *, tenant: str | None = None) -> str | None:
    t = tenant or IG.DEFAULT_IMAGE_TENANT
    config = _tenant_config(tenant)
    signals = II._tier2_signals_present(ctx, config)
    if not signals:
        return None
    payload = ":".join(sorted(signals))
    h = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"{t}:motion:delta:{h}"


def motion_disk_key(semantic_key: str, model: str | None = None) -> str:
    m = model or IG._model()
    return hashlib.sha256(f"motion\x00{m}\x00{semantic_key}".encode()).hexdigest()[:32]


def _motion_dir() -> pathlib.Path:
    return IG.IMAGE_DIR / MOTION_SUBDIR


def _frame_dir(disk_key: str) -> pathlib.Path:
    return IG.IMAGE_DIR / FRAME_SUBDIR / disk_key


def _public_motion_url(disk_key: str) -> str:
    return f"/static/generated/{MOTION_SUBDIR}/{disk_key}.webp"


def _public_frame_url(disk_key: str, index: int, ext: str) -> str:
    return f"/static/generated/{FRAME_SUBDIR}/{disk_key}/frame_{index}.{ext}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _manifest_key(disk_key: str) -> str:
    return f"motion:{disk_key}"


def _load_motion_cached(disk_key: str) -> dict | None:
    manifest = IG._read_manifest()
    entry = manifest.get(_manifest_key(disk_key))
    if not entry:
        return None
    path = _motion_dir() / f"{disk_key}.webp"
    if path.exists():
        out = dict(entry)
        out["url"] = _public_motion_url(disk_key)
        out.setdefault("cache_key", disk_key)
        return out
    return None


def _frame_directives(metaphor: str, n: int) -> list[str]:
    seq = _FRAME_DIRECTIVES.get(metaphor) or _FRAME_DIRECTIVES["pan_left"]
    if len(seq) >= n:
        return seq[:n]
    out = list(seq)
    while len(out) < n:
        out.append(seq[-1])
    return out


def build_frame_prompts(
    base_prompt: str,
    *,
    metaphor: str,
    n_frames: int,
    framing: str,
) -> list[str]:
    directives = _frame_directives(metaphor, n_frames)
    return [
        f"{base_prompt} Temporal progression ({metaphor}): {directive} "
        f"Keep region/landscape scale only. {framing}"
        for directive in directives
    ]


def _resize_frame(data: bytes, target: tuple[int, int] | None = None):
    from PIL import Image
    img = Image.open(io.BytesIO(data))
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    elif img.mode == "RGBA":
        img = img.convert("RGB")
    if target and img.size != target:
        img = img.resize(target, Image.Resampling.LANCZOS)
    return img


def assemble_animated_webp(
    frames: list[tuple[bytes, str]],
    *,
    duration_ms: int,
    loop: bool,
) -> bytes:
    from PIL import Image
    if not frames:
        raise ValueError("no frames to assemble")
    images: list[Image.Image] = []
    target = None
    for data, _ext in frames:
        im = _resize_frame(data, target)
        if target is None:
            target = im.size
        elif im.size != target:
            im = im.resize(target, Image.Resampling.LANCZOS)
        images.append(im)
    per_frame = max(80, duration_ms // len(images))
    out = io.BytesIO()
    images[0].save(
        out,
        format="WEBP",
        save_all=True,
        append_images=images[1:],
        duration=per_frame,
        loop=0 if loop else 1,
        quality=82,
        method=4,
    )
    return out.getvalue()


def _save_motion(
    disk_key: str,
    webp_bytes: bytes,
    receipt: dict,
    frame_rows: list[dict],
) -> dict:
    _motion_dir().mkdir(parents=True, exist_ok=True)
    path = _motion_dir() / f"{disk_key}.webp"
    path.write_bytes(webp_bytes)
    receipt = {
        **receipt,
        "url": _public_motion_url(disk_key),
        "cache_key": disk_key,
        "ext": "webp",
        "motion_type": "animated_webp",
        "frames": frame_rows,
        "generated_at": _now_iso(),
    }
    manifest = IG._read_manifest()
    stored = {k: v for k, v in receipt.items() if k != "url"}
    manifest[_manifest_key(disk_key)] = stored
    IG._write_manifest(manifest)
    return receipt


def _persist_frames(disk_key: str, frames: list[tuple[bytes, str]]) -> list[dict]:
    fdir = _frame_dir(disk_key)
    fdir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for i, (data, ext) in enumerate(frames):
        rel = f"{FRAME_SUBDIR}/{disk_key}/frame_{i}.{ext}"
        path = IG.IMAGE_DIR / rel
        path.write_bytes(data)
        rows.append({
            "index": i,
            "label": f"t{i}",
            "ext": ext,
            "image_path": rel,
            "image_url": _public_frame_url(disk_key, i, ext),
        })
    return rows


def _score_motion_frames(
    frames: list[tuple[bytes, str]],
    structured: dict,
    *,
    tenant: str | None,
) -> dict | None:
    config = _tenant_config(tenant)
    if not brain_sim_enabled(config):
        return None
    target = structured.get("brain_target") or "change_legibility"
    regions = list(structured.get("brain_regions") or [])
    scorer = BrainSimulatorScorer()
    scores: list[float] = []
    for i, (data, _ext) in enumerate(frames):
        score = scorer.score(
            data, target, regions,
            {"prompt": structured.get("full_prompt", ""), "frame_index": i},
        )
        scores.append(float(score.get("total", 0)))
    return {
        "brain_target": target,
        "brain_simulator": "proxy_v1",
        "frame_scores": scores,
        "change_legibility_mean": round(sum(scores) / len(scores), 4) if scores else None,
    }


def _resolve_motion_keys(ctx: dict, *, tenant: str | None) -> dict:
    config = _tenant_config(tenant)
    resolved = IG._resolve_prompts(ctx, tenant=tenant)
    intent_id = resolved["display_structured"]["intent_id"]
    sem_base = motion_segment_cache_key(ctx, intent_id, tenant=tenant)
    sem_delta = motion_delta_cache_key(ctx, tenant=tenant)
    delta_signals = II._tier2_signals_present(ctx, config)
    tier = "base+delta" if sem_delta else "base_only"
    sem_key = sem_delta if tier == "base+delta" else sem_base
    model = resolved["model"]
    disk_key = motion_disk_key(sem_key, model)
    metaphor = motion_metaphor(ctx, intent_id, config)
    settings = motion_settings(config)
    return {
        **resolved,
        "intent_id": intent_id,
        "sem_base_key": sem_base,
        "sem_delta_key": sem_delta,
        "sem_key": sem_key,
        "disk_key": disk_key,
        "tier": tier,
        "delta_signals": delta_signals,
        "metaphor": metaphor,
        "settings": settings,
        "gen_prompt": resolved["gen_prompt"],
        "structured": resolved["display_structured"],
    }


def get_hero_motion(
    ctx: dict,
    *,
    generate: bool = False,
    tenant: str | None = None,
    still_receipt: dict | None = None,
) -> dict:
    """Resolve motion receipt — cache-only unless generate=True."""
    config = _tenant_config(tenant)
    if not motion_enabled(config):
        return {"status": "disabled", "url": None, "motion_type": None, "receipt": {}}

    keys = _resolve_motion_keys(ctx, tenant=tenant)
    disk_key = keys["disk_key"]
    settings = keys["settings"]
    cached = _load_motion_cached(disk_key)
    if cached:
        return {
            "status": "ready",
            "url": cached["url"],
            "motion_type": cached.get("motion_type", "animated_webp"),
            "receipt": cached,
        }

    base_receipt = {
        "source": "pending",
        "motion_metaphor": keys["metaphor"],
        "assembly": settings.get("assembly", "animated_webp"),
        "duration_ms": settings.get("duration_ms", 3000),
        "loop": settings.get("loop", True),
        "framing": settings.get("framing"),
        "tier": keys["tier"],
        "base_cache_key": keys["sem_base_key"],
        "delta_cache_key": keys["sem_delta_key"],
        "delta_signals": keys["delta_signals"],
        "intent_id": keys["intent_id"],
        "cache_key": disk_key,
        "frame_prompts": [],
    }

    if not IG._api_key():
        return {"status": "unavailable", "url": None, "motion_type": None, "receipt": base_receipt}

    if not generate:
        return {
            "status": "pending",
            "url": None,
            "motion_type": "animated_webp",
            "receipt": {**base_receipt, "source": "pending"},
        }

    n_frames = int(settings.get("frames") or 4)
    prompts = build_frame_prompts(
        keys["gen_prompt"],
        metaphor=keys["metaphor"],
        n_frames=n_frames,
        framing=settings.get("framing", ""),
    )
    base_receipt["frame_prompts"] = prompts

    frames: list[tuple[bytes, str]] = []
    still_key = (still_receipt or {}).get("cache_key")
    still_ext = (still_receipt or {}).get("ext", "png")
    if still_key and keys["tier"] == "base_only":
        still_path = IG._local_path(still_key, still_ext)
        if still_path.exists():
            frames.append((still_path.read_bytes(), still_ext))

    start_idx = len(frames)
    for prompt in prompts[start_idx:]:
        result = IG._call_image_api(prompt)
        if not result:
            break
        frames.append((IG._candidate_bytes(result), result.get("ext", "png")))

    if len(frames) < 2:
        return {
            "status": "failed",
            "url": None,
            "motion_type": None,
            "receipt": {**base_receipt, "source": "api_failed"},
        }

    frame_rows = _persist_frames(disk_key, frames)
    brain_fields = _score_motion_frames(frames, keys["structured"], tenant=tenant) or {}
    webp = assemble_animated_webp(
        frames,
        duration_ms=int(settings.get("duration_ms") or 3000),
        loop=bool(settings.get("loop", True)),
    )
    receipt = _save_motion(
        disk_key,
        webp,
        {
            **base_receipt,
            "source": "generated",
            "license": "AI-generated timelapse loop (synthetic demo — disclosed on /dev)",
            "vendor": IG.GEMINI_VENDOR,
            "model": keys["model"],
            **brain_fields,
        },
        frame_rows,
    )
    return {
        "status": "ready",
        "url": receipt["url"],
        "motion_type": "animated_webp",
        "receipt": receipt,
    }


def _offline_frames_from_still(still_bytes: bytes, metaphor: str, n: int) -> list[tuple[bytes, str]]:
    """Build timelapse frames from one cached still — subtle transforms, no API."""
    from PIL import Image, ImageEnhance
    base = Image.open(io.BytesIO(still_bytes)).convert("RGB")
    w, h = base.size
    out: list[tuple[bytes, str]] = []
    shifts = {
        "change_wipe": [(1.0, 1.0), (0.95, 1.05), (0.9, 1.12), (0.85, 1.2)],
        "pan_left": [(1.0, 1.0), (1.02, 1.0), (1.04, 1.0), (1.06, 1.0)],
        "seasonal_shift": [(0.92, 1.08), (0.96, 1.04), (1.0, 1.0), (1.04, 0.96)],
        "crop_growth": [(0.88, 1.1), (0.94, 1.06), (1.0, 1.0), (1.02, 0.98)],
        "storm_footprint": [(1.0, 1.0), (0.96, 1.08), (0.9, 1.15), (0.86, 1.22)],
        "filmstrip_scroll": [(1.0, 1.0), (0.98, 1.02), (0.96, 1.04), (0.94, 1.06)],
        "orbit_pass": [(1.0, 1.0), (1.01, 1.02), (1.02, 1.04), (1.03, 1.06)],
    }
    curve = shifts.get(metaphor, shifts["pan_left"])
    for i in range(n):
        bright, contrast = curve[min(i, len(curve) - 1)]
        frame = base.copy()
        if metaphor == "pan_left" and i:
            crop = int(w * 0.02 * i)
            frame = frame.crop((crop, 0, w, h)).resize((w, h), Image.Resampling.LANCZOS)
        frame = ImageEnhance.Brightness(frame).enhance(bright)
        frame = ImageEnhance.Contrast(frame).enhance(contrast)
        buf = io.BytesIO()
        frame.save(buf, format="PNG")
        out.append((buf.getvalue(), "png"))
    return out


def build_motion_offline_from_still(
    ctx: dict,
    *,
    tenant: str | None = None,
    still_receipt: dict | None = None,
) -> dict:
    """Assemble a motion loop from an existing cached still — no image API."""
    config = _tenant_config(tenant)
    if not motion_enabled(config):
        return {"status": "disabled", "url": None, "receipt": {}}
    keys = _resolve_motion_keys(ctx, tenant=tenant)
    disk_key = keys["disk_key"]
    cached = _load_motion_cached(disk_key)
    if cached:
        return {"status": "ready", "url": cached["url"], "motion_type": "animated_webp", "receipt": cached}
    still_key = (still_receipt or {}).get("cache_key")
    still_ext = (still_receipt or {}).get("ext", "png")
    if not still_key:
        return {"status": "failed", "url": None, "receipt": {}}
    still_path = IG._local_path(still_key, still_ext)
    if not still_path.exists():
        return {"status": "failed", "url": None, "receipt": {}}
    settings = keys["settings"]
    n_frames = int(settings.get("frames") or 4)
    frames = _offline_frames_from_still(
        still_path.read_bytes(), keys["metaphor"], n_frames,
    )
    frame_rows = _persist_frames(disk_key, frames)
    webp = assemble_animated_webp(
        frames,
        duration_ms=int(settings.get("duration_ms") or 3000),
        loop=bool(settings.get("loop", True)),
    )
    receipt = _save_motion(
        disk_key,
        webp,
        {
            "source": "generated",
            "motion_metaphor": keys["metaphor"],
            "assembly": settings.get("assembly", "animated_webp"),
            "duration_ms": settings.get("duration_ms", 3000),
            "loop": settings.get("loop", True),
            "framing": settings.get("framing"),
            "tier": keys["tier"],
            "base_cache_key": keys["sem_base_key"],
            "delta_cache_key": keys["sem_delta_key"],
            "delta_signals": keys["delta_signals"],
            "intent_id": keys["intent_id"],
            "license": "Synthetic timelapse from cached still (offline pregen — disclosed on /dev)",
            "vendor": "motion_gen_offline",
            "model": keys["model"],
            "offline_from_still": still_key,
        },
        frame_rows,
    )
    return {"status": "ready", "url": receipt["url"], "motion_type": "animated_webp", "receipt": receipt}


def resolve_hero_motion(page: dict, *, generate: bool = False, tenant: str | None = None,
                        still_receipt: dict | None = None) -> dict:
    ctx = IG.build_image_ctx(page)
    return get_hero_motion(ctx, generate=generate, tenant=tenant, still_receipt=still_receipt)


def hero_motion_trace(receipt: dict) -> tuple[list[str], str, str]:
    sigs = [
        f"source={receipt.get('source', 'pending')}",
        f"motion_metaphor={receipt.get('motion_metaphor', '—')}",
        f"assembly={receipt.get('assembly', 'animated_webp')}",
    ]
    if receipt.get("cache_key"):
        sigs.append(f"cache_key={receipt['cache_key'][:12]}…")
    if receipt.get("tier"):
        sigs.append(f"tier={receipt['tier']}")
    if receipt.get("base_cache_key"):
        sigs.append(f"base_key={receipt['base_cache_key'][:28]}")
    frames = receipt.get("frames") or []
    if frames:
        sigs.append(f"frames={len(frames)}")
    if receipt.get("change_legibility_mean") is not None:
        sigs.append(f"change_legibility={receipt['change_legibility_mean']}")
    src = receipt.get("source", "pending")
    metaphor = receipt.get("motion_metaphor", "—")
    if src == "generated":
        out = f"timelapse loop · {metaphor} · {len(frames)} frames"
        why = (receipt.get("framing") or "Multi-frame change-over-time loop for Planet storytelling.")
    elif src == "pending":
        out = f"pending async · {metaphor}"
        why = "Cache miss — page ships still/gradient; client may trigger motion generation."
    else:
        out = f"no motion · {src}"
        why = "Motion unavailable — hero still or gradient only."
    return sigs, out, why


def hero_motion_dev_panel(motion: dict) -> dict:
    receipt = motion.get("receipt") or {}
    frames = receipt.get("frames") or []
    return {
        "status": motion.get("status", "disabled"),
        "motion_type": motion.get("motion_type"),
        "url": motion.get("url"),
        "motion_metaphor": receipt.get("motion_metaphor"),
        "assembly": receipt.get("assembly", "animated_webp"),
        "duration_ms": receipt.get("duration_ms"),
        "loop": receipt.get("loop", True),
        "framing": receipt.get("framing"),
        "tier": {
            "mode": receipt.get("tier"),
            "base_cache_key": receipt.get("base_cache_key"),
            "delta_cache_key": receipt.get("delta_cache_key"),
            "delta_signals": receipt.get("delta_signals") or [],
        },
        "frame_prompts": receipt.get("frame_prompts") or [],
        "frames": frames,
        "preview": {
            "url": motion.get("url"),
            "has_motion": bool(motion.get("url")),
            "frame_count": len(frames),
        },
        "brain": {
            "change_legibility_mean": receipt.get("change_legibility_mean"),
            "frame_scores": receipt.get("frame_scores") or [],
            "brain_target": receipt.get("brain_target"),
        },
        "receipt": {
            "source": receipt.get("source"),
            "cache_key": receipt.get("cache_key"),
            "generated_at": receipt.get("generated_at"),
            "license": receipt.get("license"),
        },
    }


def hero_motion_ledger_rows(receipt: dict) -> list[dict]:
    if not receipt or receipt.get("source") in (None, "pending", "disabled"):
        return []
    rows = [{
        "label": "Hero motion",
        "value": receipt.get("motion_metaphor") or receipt.get("assembly", "animated_webp"),
        "source": receipt.get("source", "—"),
        "vendor": "motion_gen",
        "policy": "say",
    }]
    if receipt.get("cache_key"):
        rows.append({
            "label": "Motion cache key",
            "value": receipt["cache_key"],
            "source": "hash(semantic motion key + model)",
            "vendor": "data/demo/image_cache/motion/",
            "policy": "observed",
        })
    if receipt.get("framing"):
        rows.append({
            "label": "Motion framing",
            "value": receipt["framing"][:200],
            "source": "tenant YAML",
            "vendor": "planet_image.yaml",
            "policy": "say",
        })
    if receipt.get("change_legibility_mean") is not None:
        rows.append({
            "label": "Motion change legibility (mean)",
            "value": str(receipt["change_legibility_mean"]),
            "source": receipt.get("brain_simulator", "proxy_v1"),
            "vendor": "brain_simulator",
            "policy": "observed",
        })
    return rows
