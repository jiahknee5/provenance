"""Tribe v2-compatible brain simulator scorer for hero image selection.

NEvo-inspired generate → score → select loop. Tries to import a real Tribe v2 backend;
when unavailable, runs proxy_v1 — off-the-shelf vision proxies mapped to cortical ROIs.

Honest disclosure: scores are *predicted* regional activations from a simulator (or proxy),
not measured visitor brain data. See docs/research/nevo-brain-image-gen.md.
"""
from __future__ import annotations

import hashlib
import io
import struct
import zlib
from dataclasses import dataclass, field
from typing import Any, TypedDict

import numpy as np

# Marketing brain targets → default cortical region IDs (Tribe v2 / NEvo ROI vocabulary).
BRAIN_TARGET_REGIONS: dict[str, list[str]] = {
    "attention": ["v1", "v4", "intraparietal"],
    "trust": ["ppa", "amygdala_threat_proxy", "ofc_stability"],
    "change_legibility": ["mt", "v3a", "intraparietal"],
    "approach": ["ventral_striatum", "ofc_warmth", "ppa_depth"],
    "authority": ["ppa", "intraparietal", "dlpfc_structure"],
    "message_match": ["fusiform", "v4", "clip_alignment"],
}

BRAIN_TARGET_LABELS: dict[str, str] = {
    "attention": "Early visual + dorsal/ventral attention (single focal point, hero-zone saliency)",
    "trust": "Reduced threat/aversion; stable horizon and institutional clarity",
    "change_legibility": "Motion/change salience without fear (before/after, timelapse implication)",
    "approach": "Reward/approach motivation (warm accent, open depth, forward motion)",
    "authority": "Mission/defense register (structured composition, depth, no chaos)",
    "message_match": "Semantic alignment to segment metaphor (CLIP/prompt proxy)",
}

# Simulated cortical region → marketing interpretation (decisioning-page table).
REGION_SIMULATOR_MAP: dict[str, str] = {
    "v1": "V1 — low-level contrast/texture capture (NEvo spatial complexity driver)",
    "v4": "V4 — color/form binding; ventral-stream salience",
    "intraparietal": "Intraparietal sulcus — dorsal attention / single focal-point peak",
    "fusiform": "Fusiform face-area proxy — body/social configuration (no literal faces in heroes)",
    "ppa": "Parahippocampal place area — scene depth, navigation, open perspective",
    "mt": "MT/V5 — implied motion and biological movement",
    "v3a": "V3A — motion/change boundary detection",
    "amygdala_threat_proxy": "Amygdala-threat proxy (inverted) — penalize chaos, surveillance cues",
    "ofc_stability": "OFC stability proxy — cool-warm balance, institutional calm",
    "ventral_striatum": "Ventral striatum — reward/approach warmth",
    "ofc_warmth": "OFC warmth proxy — aspirational accent and open scene",
    "ppa_depth": "PPA depth — walk-into-it perspective, gentle curvature",
    "dlpfc_structure": "dlPFC structure proxy — ordered composition, mission gravitas",
    "clip_alignment": "Semantic alignment head — prompt/metaphor match (CLIP-class proxy)",
}

# Per-target weights over proxy feature channels → region scores.
_TARGET_WEIGHTS: dict[str, dict[str, float]] = {
    "attention": {
        "hero_saliency": 0.45, "focal_contrast": 0.30, "low_clutter": 0.15, "warmth": 0.10,
    },
    "trust": {
        "horizon_stability": 0.35, "low_threat": 0.35, "low_clutter": 0.20, "cool_warm_balance": 0.10,
    },
    "change_legibility": {
        "seam_contrast": 0.40, "implied_motion": 0.30, "low_threat": 0.20, "hero_saliency": 0.10,
    },
    "approach": {
        "warmth": 0.35, "scene_depth": 0.30, "open_gradient": 0.20, "low_clutter": 0.15,
    },
    "authority": {
        "composition_structure": 0.40, "scene_depth": 0.25, "low_clutter": 0.20, "low_threat": 0.15,
    },
    "message_match": {
        "prompt_alignment": 0.50, "hero_saliency": 0.25, "low_clutter": 0.15, "warmth": 0.10,
    },
}

# Map proxy features into named region scores (Tribe v2 receipt shape).
_FEATURE_TO_REGIONS: dict[str, list[str]] = {
    "hero_saliency": ["v1", "intraparietal"],
    "focal_contrast": ["v4", "intraparietal"],
    "low_clutter": ["v1", "dlpfc_structure"],
    "warmth": ["ventral_striatum", "ofc_warmth"],
    "horizon_stability": ["ppa", "ofc_stability"],
    "low_threat": ["amygdala_threat_proxy"],
    "cool_warm_balance": ["ofc_stability", "ppa"],
    "seam_contrast": ["mt", "v3a"],
    "implied_motion": ["mt", "fusiform"],
    "scene_depth": ["ppa", "ppa_depth"],
    "open_gradient": ["ppa_depth", "ventral_striatum"],
    "composition_structure": ["dlpfc_structure", "intraparietal"],
    "prompt_alignment": ["clip_alignment", "fusiform"],
}


class BrainScore(TypedDict):
    total: float
    brain_target: str
    brain_simulator: str
    region_scores: dict[str, float]
    proxy_breakdown: dict[str, float]
    penalties: list[str]
    guardrail_penalty: float


@dataclass
class GeneratedCandidate:
    index: int
    image_bytes: bytes
    ext: str = "png"


@dataclass
class BrainScoreContext:
    brain_target: str
    brain_regions: list[str]
    prompt: str = ""
    must_avoid: list[str] = field(default_factory=list)
    visual_metaphor: str = ""
    mood: str = ""


def brain_sim_enabled(config: dict | None) -> bool:
    """Tenant opt-in via rules/*_image.yaml brain_simulator.enabled."""
    if not config:
        return False
    bs = config.get("brain_simulator") or {}
    return bool(bs.get("enabled", False))


def intent_brain_fields(intent: dict) -> tuple[str | None, list[str]]:
    """Read brain_target + brain_regions from an intent definition."""
    target = intent.get("brain_target")
    if not target:
        return None, []
    regions = list(intent.get("brain_regions") or BRAIN_TARGET_REGIONS.get(target, []))
    return target, regions


def _try_tribe_v2(
    image_bytes: bytes,
    brain_target: str,
    brain_regions: list[str],
    context: BrainScoreContext,
) -> BrainScore | None:
    """Integration point for a real Tribe v2 encoding model when installed."""
    try:
        import tribe_v2  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        raw = tribe_v2.predict_activation(
            image_bytes,
            target_regions=brain_regions,
            objective=brain_target,
        )
    except Exception:
        return None
    region_scores = {r: float(raw.get(r, 0.0)) for r in brain_regions}
    total = float(raw.get("total", sum(region_scores.values()) / max(len(region_scores), 1)))
    return {
        "total": total,
        "brain_target": brain_target,
        "brain_simulator": "tribe_v2",
        "region_scores": region_scores,
        "proxy_breakdown": dict(raw.get("proxy_breakdown") or {}),
        "penalties": list(raw.get("penalties") or []),
        "guardrail_penalty": float(raw.get("guardrail_penalty", 0.0)),
    }


def _png_rgb_array(image_bytes: bytes) -> np.ndarray | None:
    """Decode PNG to HxWx3 float [0,1] using stdlib only."""
    if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    pos = 8
    width = height = None
    idat = bytearray()
    while pos < len(image_bytes):
        if pos + 8 > len(image_bytes):
            break
        length = struct.unpack(">I", image_bytes[pos:pos + 4])[0]
        ctype = image_bytes[pos + 4:pos + 8]
        data = image_bytes[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR" and len(data) >= 8:
            width, height = struct.unpack(">II", data[:8])
        elif ctype == b"IDAT":
            idat.extend(data)
        elif ctype == b"IEND":
            break
    if not width or not height or not idat:
        return None
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error:
        return None
    stride = width * 3 + 1
    if len(raw) < height * stride:
        return None
    rgb = np.zeros((height, width, 3), dtype=np.float32)
    prev = np.zeros(3, dtype=np.int16)
    off = 0
    for y in range(height):
        if off >= len(raw):
            break
        filt = raw[off]
        off += 1
        row = np.frombuffer(raw[off:off + width * 3], dtype=np.uint8).reshape(width, 3).astype(np.int16)
        off += width * 3
        if filt == 1:
            row = (row + np.concatenate([prev.reshape(1, 3), row[:-1]], axis=0)) % 256
        elif filt == 0:
            pass
        else:
            row = row % 256
        prev = row[-1]
        rgb[y] = row.astype(np.float32) / 255.0
    return rgb


def _rgb_array(image_bytes: bytes) -> np.ndarray | None:
    """Return HxWx3 float array; optional Pillow, else minimal PNG."""
    try:
        from PIL import Image  # type: ignore[import-not-found]
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return np.asarray(img, dtype=np.float32) / 255.0
    except Exception:
        pass
    arr = _png_rgb_array(image_bytes)
    if arr is not None:
        return arr
    return None


def _byte_fallback_features(image_bytes: bytes) -> dict[str, float]:
    """Deterministic proxy when image decode fails — hash-seeded features in [0,1]."""
    h = hashlib.sha256(image_bytes).digest()
    seeds = [b / 255.0 for b in h[:16]]
    return {
        "hero_saliency": seeds[0],
        "focal_contrast": seeds[1],
        "low_clutter": seeds[2],
        "warmth": seeds[3],
        "horizon_stability": seeds[4],
        "low_threat": seeds[5],
        "cool_warm_balance": seeds[6],
        "seam_contrast": seeds[7],
        "implied_motion": seeds[8],
        "scene_depth": seeds[9],
        "open_gradient": seeds[10],
        "composition_structure": seeds[11],
        "prompt_alignment": seeds[12],
    }


def _luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def _image_features(rgb: np.ndarray, context: BrainScoreContext) -> dict[str, float]:
    """Population-level vision proxies — not ResMem; saliency/structure/affect priors."""
    h, w = rgb.shape[:2]
    lum = _luminance(rgb)
    # Hero zone: upper-center third (headline overlay region).
    zh0, zh1 = 0, max(h // 3, 1)
    zw0, zw1 = w // 4, (3 * w) // 4
    hero = lum[zh0:zh1, zw0:zw1]
    hero_mean = float(np.mean(hero))
    hero_std = float(np.std(hero))
    global_std = float(np.std(lum)) + 1e-6
    hero_saliency = min(1.0, hero_std / global_std * 0.5 + hero_mean * 0.3)

    # Focal contrast: center vs periphery.
    cy, cx = h // 2, w // 2
    r = min(h, w) // 5
    center = lum[max(0, cy - r):cy + r, max(0, cx - r):cx + r]
    periphery_mask = np.ones_like(lum, dtype=bool)
    periphery_mask[max(0, cy - r):cy + r, max(0, cx - r):cx + r] = False
    focal_contrast = min(1.0, max(0.0, float(np.mean(center) - np.mean(lum[periphery_mask])) + 0.5))

    # Clutter: high-frequency energy (inverse = fluency).
    gx = np.abs(np.diff(lum, axis=1)).mean() if w > 1 else 0.0
    gy = np.abs(np.diff(lum, axis=0)).mean() if h > 1 else 0.0
    edge_energy = float(gx + gy)
    low_clutter = max(0.0, 1.0 - min(1.0, edge_energy * 4.0))

    # Warmth: R channel dominance in lower third (approach CTA zone).
    lower = rgb[(2 * h) // 3:, :, 0]
    warmth = float(np.mean(lower)) if lower.size else 0.5

    # Horizon stability: row-wise luminance variance (low = stable horizon).
    row_means = lum.mean(axis=1)
    horizon_stability = max(0.0, 1.0 - min(1.0, float(np.std(row_means)) * 3.0))

    # Threat proxy: extreme contrast spikes + cold blue dominance (inverted for score).
    cold = float(np.mean(rgb[..., 2] - rgb[..., 0]))
    chaos = min(1.0, edge_energy * 2.0 + max(0.0, -cold) * 0.5)
    low_threat = max(0.0, 1.0 - chaos)

    cool_warm_balance = 1.0 - min(1.0, abs(float(np.mean(rgb[..., 0] - rgb[..., 2]))) * 2.0)

    # Change seam: left/right luminance delta (before/after legibility).
    mid = w // 2
    left_mean = float(np.mean(lum[:, :mid])) if mid else 0.5
    right_mean = float(np.mean(lum[:, mid:])) if mid < w else 0.5
    seam_contrast = min(1.0, abs(left_mean - right_mean) * 2.0)

    # Implied motion: diagonal gradient energy.
    if h > 2 and w > 2:
        diag = lum[1:, 1:] - lum[:-1, :-1]
        implied_motion = min(1.0, float(np.std(diag)) * 4.0)
    else:
        implied_motion = 0.5

    # Scene depth: vertical luminance gradient (open sky / depth cue).
    top_mean = float(np.mean(lum[: h // 3])) if h >= 3 else 0.5
    bot_mean = float(np.mean(lum[(2 * h) // 3:])) if h >= 3 else 0.5
    scene_depth = min(1.0, max(0.0, top_mean - bot_mean + 0.5))
    open_gradient = scene_depth

    # Composition structure: horizontal symmetry correlation.
    if w > 1:
        half = w // 2
        left = lum[:, :half]
        right = np.flip(lum[:, w - half:], axis=1)
        m = min(left.shape[1], right.shape[1])
        if m > 0:
            l = left[:, :m].flatten()
            r = right[:, :m].flatten()
            if l.std() > 1e-6 and r.std() > 1e-6:
                composition_structure = float(np.corrcoef(l, r)[0, 1])
                composition_structure = max(0.0, min(1.0, (composition_structure + 1) / 2))
            else:
                composition_structure = 0.5
        else:
            composition_structure = 0.5
    else:
        composition_structure = 0.5

    # Prompt alignment proxy: token overlap between prompt/metaphor and image color stats.
    prompt_blob = f"{context.prompt} {context.visual_metaphor} {context.mood}".lower()
    warm_words = ("warm", "gold", "dawn", "accent", "glow", "approach")
    cool_words = ("navy", "dusk", "cool", "calm", "blue", "space")
    sat_words = ("satellite", "orbit", "mosaic", "terrain", "coast")
    eng_words = ("terminal", "engineer", "deploy", "cohort", "proof")
    warm_hit = sum(1 for w in warm_words if w in prompt_blob)
    cool_hit = sum(1 for w in cool_words if w in prompt_blob)
    sat_hit = sum(1 for w in sat_words if w in prompt_blob)
    eng_hit = sum(1 for w in eng_words if w in prompt_blob)
    img_warm = warmth
    img_cool = float(np.mean(rgb[..., 2]))
    align = 0.5
    if warm_hit:
        align += 0.15 * min(1.0, img_warm * warm_hit / 3)
    if cool_hit:
        align += 0.15 * min(1.0, img_cool * cool_hit / 3)
    if sat_hit:
        align += 0.1 * min(1.0, scene_depth * sat_hit / 3)
    if eng_hit:
        align += 0.1 * min(1.0, focal_contrast * eng_hit / 3)
    prompt_alignment = min(1.0, align)

    return {
        "hero_saliency": hero_saliency,
        "focal_contrast": focal_contrast,
        "low_clutter": low_clutter,
        "warmth": warmth,
        "horizon_stability": horizon_stability,
        "low_threat": low_threat,
        "cool_warm_balance": cool_warm_balance,
        "seam_contrast": seam_contrast,
        "implied_motion": implied_motion,
        "scene_depth": scene_depth,
        "open_gradient": open_gradient,
        "composition_structure": composition_structure,
        "prompt_alignment": prompt_alignment,
    }


def _guardrail_penalties(rgb: np.ndarray | None, image_bytes: bytes,
                         context: BrainScoreContext) -> tuple[float, list[str]]:
    """Penalize predicted guardrail violations in the stimulus (surveillance, text-like grids)."""
    penalties: list[str] = []
    penalty = 0.0
    avoid_blob = " ".join(context.must_avoid).lower()
    if rgb is not None:
        h, w = rgb.shape[:2]
        lum = _luminance(rgb)
        cy, cx = h // 2, w // 2
        # Crosshair / reticle proxy: strong orthogonal lines through center.
        # Crosshair / reticle proxy: bright orthogonal arms through center on dark field.
        if h > 10 and w > 10:
            arm = 2
            h_band = lum[max(0, cy - arm):cy + arm + 1, :]
            v_band = lum[:, max(0, cx - arm):cx + arm + 1]
            h_contrast = float(np.mean(h_band) - np.mean(lum))
            v_contrast = float(np.mean(v_band) - np.mean(lum))
            if h_contrast > 0.25 and v_contrast > 0.25:
                penalty += 0.35
                penalties.append("surveillance_crosshair_proxy")
        # High-frequency grid → text-in-image or surveillance UI proxy.
        gx = np.abs(np.diff(lum, axis=1)).mean() if w > 1 else 0.0
        gy = np.abs(np.diff(lum, axis=0)).mean() if h > 1 else 0.0
        if gx > 0.35 and gy > 0.35:
            penalty += 0.20
            penalties.append("high_frequency_grid_proxy")
        # Skin-tone blob proxy (faces guardrail) — coarse HSV-like heuristic.
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        skin = (r > 0.45) & (g > 0.28) & (b < 0.4) & (r > g) & (g > b * 0.9)
        if float(np.mean(skin)) > 0.08:
            penalty += 0.25
            penalties.append("face_skin_tone_proxy")
    if "surveillance" in avoid_blob and "surveillance_crosshair_proxy" not in penalties:
        # Soft penalty from byte entropy for undecodable stubs.
        ent = len(set(image_bytes[:64])) / 64.0
        if ent > 0.9:
            penalty += 0.05
    return min(0.6, penalty), penalties


def _features_to_region_scores(
    features: dict[str, float],
    brain_regions: list[str],
    brain_target: str,
) -> dict[str, float]:
    """Project proxy features onto requested Tribe v2 region IDs."""
    region_acc: dict[str, list[float]] = {r: [] for r in brain_regions}
    weights = _TARGET_WEIGHTS.get(brain_target, _TARGET_WEIGHTS["attention"])
    for feat, weight in weights.items():
        val = features.get(feat, 0.5)
        for region in _FEATURE_TO_REGIONS.get(feat, []):
            if region in region_acc:
                region_acc[region].append(val * weight)
    out: dict[str, float] = {}
    for region in brain_regions:
        vals = region_acc.get(region) or [0.5]
        out[region] = round(float(np.mean(vals)), 4)
    return out


def _proxy_score(image_bytes: bytes, context: BrainScoreContext) -> BrainScore:
    rgb = _rgb_array(image_bytes)
    if rgb is not None:
        features = _image_features(rgb, context)
    else:
        features = _byte_fallback_features(image_bytes)
    guard_pen, guard_notes = _guardrail_penalties(rgb, image_bytes, context)
    weights = _TARGET_WEIGHTS.get(context.brain_target, _TARGET_WEIGHTS["attention"])
    total = sum(features.get(k, 0.5) * w for k, w in weights.items())
    total = max(0.0, min(1.0, total - guard_pen))
    region_scores = _features_to_region_scores(
        features, context.brain_regions, context.brain_target,
    )
    for region in context.brain_regions:
        region_scores[region] = round(max(0.0, region_scores[region] - guard_pen * 0.5), 4)
    return {
        "total": round(total, 4),
        "brain_target": context.brain_target,
        "brain_simulator": "proxy_v1",
        "region_scores": region_scores,
        "proxy_breakdown": {k: round(v, 4) for k, v in features.items()},
        "penalties": guard_notes,
        "guardrail_penalty": round(guard_pen, 4),
    }


class BrainSimulatorScorer:
    """Score hero candidates against a marketing brain_target via Tribe v2 or proxy_v1."""

    def score(
        self,
        image_bytes: bytes,
        brain_target: str,
        brain_regions: list[str],
        context: dict[str, Any] | BrainScoreContext | None = None,
    ) -> BrainScore:
        ctx = self._normalize_context(brain_target, brain_regions, context)
        tribe = _try_tribe_v2(image_bytes, brain_target, brain_regions, ctx)
        if tribe is not None:
            return tribe
        return _proxy_score(image_bytes, ctx)

    def select_best(
        self,
        candidates: list[GeneratedCandidate],
        brain_target: str,
        brain_regions: list[str],
        context: dict[str, Any] | BrainScoreContext | None = None,
    ) -> tuple[GeneratedCandidate, BrainScore, list[BrainScore]]:
        if not candidates:
            raise ValueError("select_best requires at least one candidate")
        ctx = self._normalize_context(brain_target, brain_regions, context)
        scores: list[BrainScore] = []
        best_idx = 0
        best_total = -1.0
        for cand in candidates:
            sc = self.score(cand.image_bytes, brain_target, brain_regions, ctx)
            scores.append(sc)
            if sc["total"] > best_total:
                best_total = sc["total"]
                best_idx = cand.index
        winner = next(c for c in candidates if c.index == best_idx)
        return winner, scores[best_idx], scores

    @staticmethod
    def _normalize_context(
        brain_target: str,
        brain_regions: list[str],
        context: dict[str, Any] | BrainScoreContext | None,
    ) -> BrainScoreContext:
        if isinstance(context, BrainScoreContext):
            return context
        data = context or {}
        regions = list(brain_regions or BRAIN_TARGET_REGIONS.get(brain_target, []))
        return BrainScoreContext(
            brain_target=brain_target,
            brain_regions=regions,
            prompt=str(data.get("prompt") or ""),
            must_avoid=list(data.get("must_avoid") or []),
            visual_metaphor=str(data.get("visual_metaphor") or ""),
            mood=str(data.get("mood") or ""),
        )


def brain_target_mapping_table(config: dict | None = None) -> list[dict[str, str]]:
    """Rows for the /dev image-decisions brain simulator section."""
    rows: list[dict[str, str]] = []
    intents = (config or {}).get("intents") or []
    for intent in intents:
        target, regions = intent_brain_fields(intent)
        if not target:
            continue
        rows.append({
            "intent_id": intent["id"],
            "brain_target": target,
            "brain_target_label": BRAIN_TARGET_LABELS.get(target, target),
            "brain_regions": ", ".join(regions),
            "region_detail": "; ".join(
                f"{r}: {REGION_SIMULATOR_MAP.get(r, r)}" for r in regions[:3]
            ),
        })
    return rows


def example_receipt_snippet() -> dict[str, Any]:
    """Static example for decisioning page when no live receipt exists."""
    return {
        "brain_simulator": "proxy_v1",
        "brain_target": "attention",
        "brain_score": 0.742,
        "brain_region_scores": {"v1": 0.71, "v4": 0.68, "intraparietal": 0.79},
        "candidates_evaluated": 3,
        "winner_index": 1,
        "guardrail_penalty": 0.0,
    }
