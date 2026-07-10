"""Async hero image generation for the Gauntlet replica — provable, cached, non-blocking.

PRD-derived tension: docs/01-intake/PRD-derived.md says *curate imagery, don't generate
per-visitor*. We generate only when an API key upgrades the demo, with a full receipt
(prompt, model, vendor, cache_key, generated_at) and a deterministic disk cache (Art IV).
Gallery (scene.image_for) and CSS gradient remain the offline fallbacks (Art III).

Page load never waits on the image API: build_page() checks cache only; a client fetch
to /api/gauntlet/hero-image triggers generation and caches for future visitors."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import re
import shutil
from datetime import datetime, timezone
from typing import Any
import httpx

from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import image_intents as II
from pipeline.personalization import scene as SC
from pipeline.personalization.brain_simulator import (
    BrainSimulatorScorer,
    GeneratedCandidate,
    brain_sim_enabled,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "data" / "demo" / "image_cache"
IMAGE_DIR = CACHE_DIR / "images"
MANIFEST = CACHE_DIR / "manifest.json"

DEFAULT_MODEL = "gemini-2.5-flash-image"
DEFAULT_API_URL = "https://api.openai.com/v1/images/generations"
DEFAULT_GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash-image:generateContent"
)
VENDOR = "nano-banana-compatible"
GEMINI_VENDOR = "google-gemini"

# Patterns that must never appear in prompts (hold / PII surface policy).
_FORBIDDEN_PROMPT = re.compile(
    r"(@|\b\d{3}-\d{2}-\d{4}\b|\$\d|\bincome\b|\bmodeled\b|"
    r"\bde-anonymized\b|\babandoned\b|\bstep \d of \d\b|"
    r"\bwelcome back\b|\byour team at\b|\bwe see your\b)",
    re.I,
)

_PII_WORDS = (
    "gmail.com", "yahoo.com", "welcome back", "your team at", "we see your",
    "income band", "magic token", "hubspot", "vector", "clay",
    "gender", "male", "female", "non-binary",
)

DEFAULT_IMAGE_TENANT = "gauntlet"
DEFAULT_SURFACE_ID = "hero"

_SURFACE_DEFAULTS: dict[str, dict] = {
    "hero": {
        "label": "Hero background",
        "placement": "Full-width hero section backdrop",
        "prompt_opener": "Cinematic wide hero backdrop for a {product}.",
    },
    "og": {
        "label": "Open Graph / social preview",
        "placement": "Link share unfurl (Twitter, LinkedIn, Slack)",
        "prompt_opener": (
            "Open Graph social preview card (1200×630) for a {product} — "
            "shareable link thumbnail."
        ),
        "must_include": [
            "1200x630 social card aspect ratio with safe center crop margins",
            "bold single focal subject readable at thumbnail size",
            "dark moody atmosphere with warm gold accent ({accent_color})",
            "single clear focal point — processing fluency",
        ],
        "composition_suffix": (
            "Framed as a social share thumbnail with centered focal subject and "
            "generous safe margins for platform crop — no text overlay."
        ),
    },
}


def load_image_config(tenant: str = DEFAULT_IMAGE_TENANT) -> dict:
    """Load tenant image config — defaults to Gauntlet for /gauntlet routes."""
    return II.load_image_config(tenant)


def _tenant_config(tenant: str | None = None) -> dict:
    return load_image_config(tenant or DEFAULT_IMAGE_TENANT)


def surface_spec(surface_id: str, *, tenant: str | None = None) -> dict:
    """Marketer-facing surface metadata + prompt overrides from tenant config."""
    config = _tenant_config(tenant)
    yaml_surfaces = (config.get("surfaces") or {})
    base = dict(_SURFACE_DEFAULTS.get(surface_id, _SURFACE_DEFAULTS["hero"]))
    base.update(yaml_surfaces.get(surface_id) or {})
    base["id"] = surface_id
    return base


def list_surface_ids(*, tenant: str | None = None) -> list[str]:
    """Ordered surface ids for a tenant — hero first, then config extras."""
    config = _tenant_config(tenant)
    yaml_ids = list((config.get("surfaces") or {}).keys())
    out = [DEFAULT_SURFACE_ID]
    for sid in yaml_ids:
        if sid not in out:
            out.append(sid)
    return out


def _surface_opener(surface_id: str, config: dict) -> str:
    spec = surface_spec(surface_id, tenant=config.get("tenant"))
    product = config.get("product_context", "marketing site")
    accent = (config.get("brand") or {}).get("accent_color", "#c9a227")
    tmpl = spec.get("prompt_opener", _SURFACE_DEFAULTS["hero"]["prompt_opener"])
    return tmpl.format(product=product, accent_color=accent)


def _rewrite_prompt_opener(prompt: str, opener: str) -> str:
    """Replace the first sentence of an assembled prompt with the surface opener."""
    dot = prompt.find(". ")
    if dot == -1:
        return opener + " " + prompt
    return opener + prompt[dot:]


def _apply_surface(structured: II.StructuredPrompt, surface_id: str,
                   config: dict) -> II.StructuredPrompt:
    """Apply per-surface must_include / composition overrides before assembly."""
    if surface_id == DEFAULT_SURFACE_ID:
        return structured
    spec = surface_spec(surface_id, tenant=config.get("tenant"))
    out = dict(structured)
    accent = out.get("accent_color") or (config.get("brand") or {}).get("accent_color", "#c9a227")
    if spec.get("must_include"):
        tail = [m for m in (out.get("must_include") or [])
                if m.startswith("conversion goal") or m.startswith("secondary visual")]
        out["must_include"] = [
            item.format(accent_color=accent) for item in spec["must_include"]
        ] + tail
    suffix = spec.get("composition_suffix")
    if suffix:
        out["composition"] = (out.get("composition") or "").rstrip() + " " + suffix.strip()
    out["surface_id"] = surface_id
    return out


def _finalize_surface_prompt(prompt: str, surface_id: str, config: dict) -> str:
    if surface_id == DEFAULT_SURFACE_ID:
        return prompt
    return _rewrite_prompt_opener(prompt, _surface_opener(surface_id, config))


def _api_key() -> str:
    return (os.environ.get("IMAGE_GEN_API_KEY") or os.environ.get("NANO_BANANA_API_KEY") or "").strip()


def _api_url() -> str:
    return (os.environ.get("IMAGE_GEN_API_URL") or DEFAULT_API_URL).strip()


def _model() -> str:
    return (os.environ.get("IMAGE_GEN_MODEL") or DEFAULT_MODEL).strip()


def build_image_ctx(page: dict) -> dict:
    """Deterministic image context from a build_page() result — no PII fields."""
    prioritized = (page.get("objections") or {}).get("prioritized") or []
    top_objections = [p["objection_id"] for p in prioritized[:3]]
    top = top_objections[0] if top_objections else None
    ad = page.get("ad_variant")
    det = page.get("det") or {}
    ident = page.get("identity")
    hero = (page.get("sections") or {}).get("hero") or {}
    archetype_id = None
    if ident and ident.get("kind") == "cohort" and ident.get("archetype"):
        archetype_id = ident["archetype"].get("id")
    return {
        "channel": page["entry"]["channel"],
        "ad_variant_id": ad["id"] if ad else None,
        "ad_variant": ad,
        "audience": page.get("audience", "neutral"),
        "audience_route": page.get("audience_route", "neutral"),
        "industry": det.get("industry") or "general",
        "region": det.get("region"),
        "tier": page.get("tier", 0),
        "top_objection": top,
        "top_objections": top_objections,
        "cta_primary": hero.get("cta_primary"),
        "compare_emphasis": (page.get("sections") or {}).get("compare", {}).get("emphasis"),
        "archetype_id": archetype_id,
        # hold-tier source fields — used only for guardrail stripping, never emitted
        "_hold": {
            "company": det.get("company"),
            "city": det.get("city"),
            "visitor_name": (ident.get("first") if ident else None),
            "income_band": (
                ident["view"]["deep"].get("income_band")
                if ident and ident.get("kind") == "cohort"
                and ident.get("view", {}).get("deep") else None
            ),
        },
    }


def select_image_intent(ctx: dict, *, tenant: str | None = None) -> II.ImageIntentSelection:
    """Delegate to image_intents — exposed for tests and provenance."""
    config = _tenant_config(tenant)
    return II.select_image_intent(ctx, config)


def build_image_prompt(ctx: dict, *, tenant: str | None = None) -> II.StructuredPrompt:
    """Structured, action-driven prompt with provenance fields (full single-tier view)."""
    config = _tenant_config(tenant)
    selection = II.select_image_intent(ctx, config)
    structured = II.build_structured_prompt(ctx, selection, config)
    out = II.apply_guardrails(structured, ctx, config)
    _assert_prompt_safe(out["full_prompt"])
    return out


def build_base_prompt(ctx: dict, *, tenant: str | None = None) -> tuple[str, II.StructuredPrompt, II.ImageIntentSelection]:
    """Tier-1 segment-only prompt — cacheable per ad variant or intent+route."""
    config = _tenant_config(tenant)
    seg = II.segment_ctx(ctx)
    selection = II.select_image_intent(seg, config)
    structured = II.build_base_structured_prompt(seg, selection, config)
    guarded = II.apply_guardrails(structured, seg, config)
    prompt = II.assemble_base_prompt(guarded, config)
    guarded["full_prompt"] = prompt
    _assert_prompt_safe(prompt)
    return prompt, guarded, selection


def build_personalization_delta(ctx: dict, base_structured: II.StructuredPrompt,
                                *, tenant: str | None = None) -> tuple[str, list[II.PersonalizationLayer]] | None:
    """Tier-2 delta prompt — None when no signals beyond segment."""
    config = _tenant_config(tenant)
    if not II.has_personalization_delta(ctx, config):
        return None
    delta_layers = II.build_delta_layers(ctx, config)
    if not delta_layers:
        return None
    # Apply hold/guardrail scan on delta text
    blob = " ".join(l["value"] for l in delta_layers)
    hold = ctx.get("_hold") or {}
    for pat, label in II.HOLD_STRIP_PATTERNS:
        if pat.search(blob):
            delta_layers = [l for l in delta_layers if pat.search(l["value"]) is None]
    if hold.get("visitor_name") or hold.get("company"):
        delta_layers = [l for l in delta_layers if l["layer"] != "archetype"]
    if not delta_layers:
        return None
    prompt = II.assemble_delta_prompt(base_structured, delta_layers, config)
    _assert_prompt_safe(prompt)
    return prompt, delta_layers


def prompt_text(structured: II.StructuredPrompt | dict) -> str:
    """API-ready prompt string from a StructuredPrompt."""
    if isinstance(structured, dict) and structured.get("full_prompt"):
        return structured["full_prompt"]
    return II.assemble_full_prompt(structured)


def _assert_prompt_safe(prompt: str) -> None:
    # Scan only the descriptive body — must_avoid instructions are meta-guardrails.
    body = prompt.split("Must avoid:")[0]
    low = body.lower()
    if _FORBIDDEN_PROMPT.search(body):
        raise ValueError("prompt contains forbidden hold/PII patterns")
    for w in _PII_WORDS:
        if w in low:
            raise ValueError(f"prompt contains forbidden token: {w}")
    for pat, label in II.HOLD_STRIP_PATTERNS:
        if label in ("income", "age", "gender", "zip_code") and pat.search(body):
            raise ValueError(f"prompt contains hold-tier pattern: {label}")


def image_cache_key(prompt: str, model: str | None = None, *,
                    surface_id: str = DEFAULT_SURFACE_ID) -> str:
    m = model or _model()
    surf = "" if surface_id == DEFAULT_SURFACE_ID else f"{surface_id}\x00"
    return hashlib.sha256(f"{m}\x00{surf}{prompt}".encode()).hexdigest()[:32]


def segment_cache_key(ctx: dict, intent_id: str, *, tenant: str | None = None,
                      surface_id: str = DEFAULT_SURFACE_ID) -> str:
    """Semantic tier-1 key — no PII, no objection/industry/region/archetype."""
    t = tenant or DEFAULT_IMAGE_TENANT
    surf = "" if surface_id == DEFAULT_SURFACE_ID else f"{surface_id}:"
    ad = ctx.get("ad_variant_id")
    if ad:
        return f"{t}:base:{surf}{ad}"
    route = ctx.get("audience_route", "neutral")
    return f"{t}:base:{surf}{intent_id}:{route}"


def delta_cache_key(ctx: dict, *, tenant: str | None = None) -> str | None:
    """Semantic tier-2 key hash — None when segment-only visitor."""
    config = _tenant_config(tenant)
    signals = II._tier2_signals_present(ctx, config)
    if not signals:
        return None
    t = tenant or DEFAULT_IMAGE_TENANT
    payload = ":".join(sorted(signals))
    h = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"{t}:delta:{h}"


def _estimate_tokens_saved(full_len: int, used_len: int, *, cache_hit: bool) -> int:
    if cache_hit:
        return max(full_len, 0)
    return max(full_len - used_len, 0)


def _tier_receipt_fields(*, tier: str, base_cache_key: str, delta_cache_key: str | None,
                         delta_signals: list[str], base_prompt: str, delta_prompt: str | None,
                         full_prompt_len: int, used_prompt_len: int, cache_hit: bool) -> dict:
    return {
        "tier": tier,
        "base_cache_key": base_cache_key,
        "delta_cache_key": delta_cache_key,
        "delta_signals": delta_signals,
        "base_prompt": base_prompt,
        "delta_prompt": delta_prompt,
        "tokens_saved_estimate": _estimate_tokens_saved(full_prompt_len, used_prompt_len,
                                                        cache_hit=cache_hit),
    }


def _ensure_dirs() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _read_manifest() -> dict:
    if not MANIFEST.exists():
        return {}
    try:
        return json.loads(MANIFEST.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _write_manifest(data: dict) -> None:
    _ensure_dirs()
    MANIFEST.write_text(json.dumps(data, indent=2, sort_keys=True))


def _public_url(cache_key: str, ext: str = "png") -> str:
    return f"/static/generated/{cache_key}.{ext}"


def _public_generated_path(relative_path: str) -> str:
    """URL for any file under data/demo/image_cache/images/ (incl. candidates/)."""
    return f"/static/generated/{relative_path.lstrip('/')}"


def mount_generated_url(url: str | None, static_prefix: str = "/static") -> str | None:
    """Rewrite /static/generated/… for tenant-mounted static prefixes."""
    if not url or not url.startswith("/static/generated/"):
        return url
    if static_prefix == "/static":
        return url
    return static_prefix + url[len("/static"):]


def _local_path(cache_key: str, ext: str = "png") -> pathlib.Path:
    return IMAGE_DIR / f"{cache_key}.{ext}"


def _candidate_rel_path(cache_key: str, index: int, ext: str) -> str:
    return f"candidates/{cache_key}/candidate_{index}.{ext}"


def _load_cached(cache_key: str) -> dict | None:
    manifest = _read_manifest()
    entry = manifest.get(cache_key)
    if not entry:
        return None
    ext = entry.get("ext", "png")
    if _local_path(cache_key, ext).exists():
        entry = dict(entry)
        entry["url"] = _public_url(cache_key, ext)
        entry.setdefault("cache_key", cache_key)
        return entry
    return None


def invalidate_cached(cache_key: str) -> None:
    """Drop a disk-cache entry so the next generate=True call regenerates it."""
    manifest = _read_manifest()
    entry = manifest.pop(cache_key, None)
    if entry:
        _write_manifest(manifest)
    for ext in ("jpg", "png", "webp"):
        path = _local_path(cache_key, ext)
        if path.exists():
            path.unlink()
    cand_dir = IMAGE_DIR / "candidates" / cache_key
    if cand_dir.exists():
        shutil.rmtree(cand_dir, ignore_errors=True)


def _save_image(cache_key: str, data: bytes, ext: str = "png") -> pathlib.Path:
    _ensure_dirs()
    path = _local_path(cache_key, ext)
    path.write_bytes(data)
    return path


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _best_of_n(*, tenant: str | None = None, generate: bool = False) -> int:
    """Candidates per API call when brain scoring is active. Default n=3 async, n=1 pregen."""
    env = (os.environ.get("BRAIN_SIM_BEST_OF_N") or "").strip()
    if env.isdigit():
        return max(1, min(int(env), 8))
    config = _tenant_config(tenant)
    if not brain_sim_enabled(config):
        return 1
    return 3 if generate else 1


def _brain_score_context(structured: II.StructuredPrompt, prompt: str) -> dict:
    return {
        "prompt": prompt,
        "must_avoid": structured.get("must_avoid") or [],
        "visual_metaphor": structured.get("visual_metaphor") or "",
        "mood": structured.get("mood") or "",
    }


def _brain_receipt_fields(
    score: dict | None,
    *,
    candidates_evaluated: int,
    winner_index: int,
    structured: II.StructuredPrompt,
) -> dict[str, Any]:
    if not score:
        return {}
    return {
        "brain_simulator": score.get("brain_simulator"),
        "brain_target": score.get("brain_target") or structured.get("brain_target"),
        "brain_score": score.get("total"),
        "brain_region_scores": score.get("region_scores"),
        "brain_proxy_breakdown": score.get("proxy_breakdown"),
        "brain_penalties": score.get("penalties"),
        "brain_guardrail_penalty": score.get("guardrail_penalty"),
        "candidates_evaluated": candidates_evaluated,
        "winner_index": winner_index,
    }


def _generate_candidates(prompt: str, n: int) -> list[dict]:
    """Call image API up to n times; tolerate partial failures."""
    out: list[dict] = []
    for _ in range(n):
        result = _call_image_api(prompt)
        if result:
            out.append(result)
    return out


def _candidate_bytes(api_result: dict) -> bytes:
    if "b64" in api_result:
        return base64.b64decode(api_result["b64"])
    return api_result["raw"]


def _select_scored_candidate(
    api_results: list[dict],
    structured: II.StructuredPrompt,
    prompt: str,
    *,
    tenant: str | None = None,
) -> tuple[dict, dict | None, int, int, list[dict]]:
    """Pick best candidate when brain scoring enabled; else first success."""
    if not api_results:
        raise ValueError("no api results")
    config = _tenant_config(tenant)
    if not brain_sim_enabled(config) or not structured.get("brain_target"):
        return api_results[0], None, len(api_results), 0, []
    scorer = BrainSimulatorScorer()
    target = structured["brain_target"]
    regions = list(structured.get("brain_regions") or [])
    candidates = [
        GeneratedCandidate(index=i, image_bytes=_candidate_bytes(r), ext=r.get("ext", "png"))
        for i, r in enumerate(api_results)
    ]
    winner, best_score, all_scores = scorer.select_best(
        candidates, target, regions, _brain_score_context(structured, prompt),
    )
    return api_results[winner.index], best_score, len(api_results), winner.index, all_scores


def _persist_candidate_provenance(
    cache_key: str,
    prompt: str,
    api_results: list[dict],
    all_scores: list[dict],
    winner_index: int,
) -> list[dict]:
    """Save loser images + build manifest candidates[] for best-of-N provenance."""
    if not all_scores or len(api_results) < 2:
        return []
    out: list[dict] = []
    for i, (api_result, score) in enumerate(zip(api_results, all_scores)):
        ext = api_result.get("ext", "png")
        selected = i == winner_index
        if selected:
            image_path = f"{cache_key}.{ext}"
        else:
            rel = _candidate_rel_path(cache_key, i, ext)
            path = IMAGE_DIR / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(_candidate_bytes(api_result))
            image_path = rel
        out.append({
            "index": i,
            "prompt": prompt,
            "brain_score": score.get("total"),
            "brain_region_scores": score.get("region_scores"),
            "brain_proxy_breakdown": score.get("proxy_breakdown"),
            "brain_penalties": score.get("penalties"),
            "brain_guardrail_penalty": score.get("guardrail_penalty"),
            "selected": selected,
            "image_path": image_path,
            "ext": ext,
        })
    return out


def candidate_gallery_from_receipt(receipt: dict, *, static_prefix: str = "/static") -> dict:
    """View model for decided vs rejected candidate galleries on /image-decisions."""
    raw = receipt.get("candidates") or []
    winner_score = receipt.get("brain_score")
    enriched: list[dict] = []
    for c in raw:
        path = c.get("image_path") or ""
        url = mount_generated_url(_public_generated_path(path), static_prefix) if path else None
        delta = None
        if (
            winner_score is not None
            and c.get("brain_score") is not None
            and not c.get("selected")
        ):
            delta = round(float(c["brain_score"]) - float(winner_score), 4)
        enriched.append({
            **c,
            "image_url": url,
            "delta_vs_winner": delta,
            "badge": "selected" if c.get("selected") else "rejected",
        })
    enriched.sort(key=lambda row: row.get("index", 0))
    winner = next((c for c in enriched if c.get("selected")), None)
    losers = [c for c in enriched if not c.get("selected")]
    return {
        "has_candidates": len(enriched) >= 2,
        "candidates_evaluated": receipt.get("candidates_evaluated"),
        "winner_index": receipt.get("winner_index"),
        "brain_target": receipt.get("brain_target"),
        "brain_simulator": receipt.get("brain_simulator"),
        "winner_score": winner_score,
        "prompt": receipt.get("prompt"),
        "cache_key": receipt.get("cache_key"),
        "winner": winner,
        "losers": losers,
        "candidates": enriched,
    }


def _receipt_extras(structured: II.StructuredPrompt, tier_fields: dict | None = None,
                    brain_fields: dict | None = None) -> dict[str, Any]:
    """Provenance fields stored alongside generation receipt."""
    out = {
        "intent_id": structured.get("intent_id"),
        "secondary_intent_id": structured.get("secondary_intent_id"),
        "conversion_goal": structured.get("conversion_goal"),
        "sales_technique": structured.get("sales_technique"),
        "brain_target": structured.get("brain_target"),
        "brain_regions": structured.get("brain_regions"),
        "personalization_layers": structured.get("personalization_layers"),
        "composition": structured.get("composition"),
        "visual_metaphor": structured.get("visual_metaphor"),
        "mood": structured.get("mood"),
        "accent_color": structured.get("accent_color"),
        "must_include": structured.get("must_include"),
        "must_avoid": structured.get("must_avoid"),
        "drives_action": structured.get("drives_action"),
        "pairs_with_objection": structured.get("pairs_with_objection"),
        "guardrails_applied": structured.get("guardrails_applied"),
        "guardrails_blocked": structured.get("guardrails_blocked"),
        "intent_selection": structured.get("selection"),
    }
    if tier_fields:
        out.update(tier_fields)
    if brain_fields:
        out.update(brain_fields)
    return out


def _gradient_receipt(*, structured: II.StructuredPrompt, prompt: str, cache_key: str,
                      model: str, fallback_chain: list[str],
                      tier_fields: dict | None = None) -> dict:
    return {
        "url": None,
        "source": "gradient",
        "prompt": prompt,
        "model": model,
        "vendor": VENDOR,
        "cache_key": cache_key,
        "generated_at": None,
        "license": "CSS gradient fallback (instant, no network)",
        "fallback_chain": fallback_chain,
        **_receipt_extras(structured, tier_fields),
    }


def _gallery_receipt(ctx: dict, *, structured: II.StructuredPrompt, prompt: str,
                     cache_key: str, model: str, fallback_chain: list[str],
                     tier_fields: dict | None = None) -> dict:
    ind = ctx.get("industry") or "general"
    img = SC.image_for(ind)
    if ind == "general" or img.get("id") == "neutral-wash":
        return _gradient_receipt(structured=structured, prompt=prompt, cache_key=cache_key,
                                 model=model, fallback_chain=fallback_chain + ["gradient"],
                                 tier_fields=tier_fields)
    return {
        "url": img["url"],
        "source": "gallery",
        "prompt": prompt,
        "model": model,
        "vendor": "Openverse curated library",
        "cache_key": cache_key,
        "generated_at": None,
        "license": f"{img.get('license', 'CC')} · {img.get('creator', 'unknown')}",
        "gallery_id": img.get("id"),
        "fallback_chain": fallback_chain,
        **_receipt_extras(structured, tier_fields),
    }


def _is_gemini_api(url: str) -> bool:
    return "generativelanguage.googleapis.com" in url


def _resolve_api_url() -> tuple[str, bool]:
    url = _api_url()
    key = _api_key()
    if _is_gemini_api(url):
        return url, True
    if url == DEFAULT_API_URL and key.startswith("AQ."):
        return DEFAULT_GEMINI_API_URL, True
    return url, False


def _call_gemini_image_api(prompt: str, *, url: str, key: str) -> dict | None:
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }).encode()
    headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
    try:
        r = httpx.post(url, content=body, headers=headers, timeout=120.0)
        if r.status_code != 200:
            return None
        data = r.json()
    except (httpx.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    for part in (((data or {}).get("candidates") or [{}])[0].get("content") or {}).get("parts") or []:
        inline = part.get("inlineData") or part.get("inline_data")
        if not inline:
            continue
        b64 = inline.get("data")
        if not b64:
            continue
        mime = (inline.get("mimeType") or inline.get("mime_type") or "").lower()
        ext = "jpg" if "jpeg" in mime or mime == "image/jpg" else "png"
        return {"b64": b64, "ext": ext, "vendor": GEMINI_VENDOR}
    return None


def _call_openai_image_api(prompt: str, *, url: str, key: str, model: str) -> dict | None:
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": "1792x1024",
        "response_format": "b64_json",
    }).encode()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        r = httpx.post(url, content=body, headers=headers, timeout=60.0)
        if r.status_code != 200:
            return None
        data = r.json()
    except (httpx.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    items = (data or {}).get("data") or []
    if not items:
        return None
    item = items[0]
    if item.get("b64_json"):
        return {"b64": item["b64_json"], "ext": "png", "vendor": VENDOR}
    if item.get("url"):
        try:
            img_r = httpx.get(item["url"], timeout=30.0)
            if img_r.status_code == 200:
                ext = "png" if "png" in (img_r.headers.get("content-type") or "") else "jpg"
                return {"raw": img_r.content, "ext": ext, "vendor": VENDOR}
        except httpx.HTTPError:
            return None
    return None


def _call_image_api(prompt: str) -> dict | None:
    """OpenAI-compatible or Google Gemini generateContent. None on missing key or failure."""
    key = _api_key()
    if not key:
        return None
    url, use_gemini = _resolve_api_url()
    if use_gemini:
        return _call_gemini_image_api(prompt, url=url, key=key)
    return _call_openai_image_api(prompt, url=url, key=key, model=_model())


def _generate_and_cache(ctx: dict, structured: II.StructuredPrompt, prompt: str,
                        cache_key: str, model: str,
                        tier_fields: dict | None = None, *,
                        tenant: str | None = None,
                        generate: bool = True) -> dict:
    chain = ["cache"]
    n = _best_of_n(tenant=tenant, generate=generate)
    api_results = _generate_candidates(prompt, n)
    if api_results:
        api_result, brain_score, evaluated, winner_index, all_scores = _select_scored_candidate(
            api_results, structured, prompt, tenant=tenant,
        )
        raw = _candidate_bytes(api_result)
        ext = api_result.get("ext", "png")
        _save_image(cache_key, raw, ext)
        brain_fields = _brain_receipt_fields(
            brain_score,
            candidates_evaluated=evaluated,
            winner_index=winner_index,
            structured=structured,
        )
        candidate_rows = _persist_candidate_provenance(
            cache_key, prompt, api_results, all_scores, winner_index,
        )
        if brain_sim_enabled(_tenant_config(tenant)) and n > 1:
            chain.append(f"best_of_{n}")
        receipt = {
            "url": _public_url(cache_key, ext),
            "source": "generated",
            "prompt": prompt,
            "model": model,
            "vendor": api_result.get("vendor", VENDOR),
            "cache_key": cache_key,
            "generated_at": _now_iso(),
            "license": "AI-generated (synthetic demo — disclosed on /dev)",
            "fallback_chain": chain + ["api"],
            **_receipt_extras(structured, tier_fields, brain_fields),
        }
        if candidate_rows:
            receipt["candidates"] = candidate_rows
        manifest = _read_manifest()
        manifest[cache_key] = {k: v for k, v in receipt.items() if k != "url"}
        manifest[cache_key]["ext"] = ext
        _write_manifest(manifest)
        return receipt
    chain.append("api_failed")
    return _gallery_receipt(ctx, structured=structured, prompt=prompt, cache_key=cache_key,
                            model=model, fallback_chain=chain + ["gallery"],
                            tier_fields=tier_fields)


def _resolve_prompts(ctx: dict, *, tenant: str | None = None,
                     surface_id: str = DEFAULT_SURFACE_ID) -> dict:
    """Build tier-1 base + optional tier-2 delta/combined prompts."""
    config = _tenant_config(tenant)
    t = tenant or DEFAULT_IMAGE_TENANT

    base_prompt, base_structured, seg_selection = build_base_prompt(ctx, tenant=tenant)
    full_structured = build_image_prompt(ctx, tenant=tenant)
    base_structured = _apply_surface(base_structured, surface_id, config)
    full_structured = _apply_surface(full_structured, surface_id, config)
    base_prompt = _finalize_surface_prompt(
        II.assemble_base_prompt(base_structured, config), surface_id, config)
    full_prompt = _finalize_surface_prompt(
        II.assemble_full_prompt(full_structured, config), surface_id, config)
    full_len = len(full_prompt)

    sem_base_key = segment_cache_key(ctx, base_structured["intent_id"],
                                     tenant=t, surface_id=surface_id)
    sem_delta_key = delta_cache_key(ctx, tenant=t)
    delta_signals = II._tier2_signals_present(ctx, config)

    delta_result = build_personalization_delta(ctx, base_structured, tenant=tenant)
    if delta_result:
        delta_prompt, delta_layers = delta_result
        combined_prompt = II.assemble_combined_prompt(base_structured, delta_layers, config)
        tier = "base+delta"
        gen_prompt = _finalize_surface_prompt(combined_prompt, surface_id, config)
        used_len = len(delta_prompt)
    else:
        delta_prompt = None
        delta_layers = []
        combined_prompt = None
        tier = "base_only"
        gen_prompt = base_prompt
        used_len = len(base_prompt)

    model = _model()
    base_disk_key = image_cache_key(base_prompt, model, surface_id=surface_id)
    gen_disk_key = image_cache_key(gen_prompt, model, surface_id=surface_id)

    tier_fields = _tier_receipt_fields(
        tier=tier,
        base_cache_key=sem_base_key,
        delta_cache_key=sem_delta_key,
        delta_signals=delta_signals,
        base_prompt=base_prompt,
        delta_prompt=delta_prompt,
        full_prompt_len=full_len,
        used_prompt_len=used_len,
        cache_hit=False,
    )

    # Merge full structured for receipt (visitor-facing provenance)
    display_structured = full_structured
    display_structured["selection"] = seg_selection if tier == "base_only" else full_structured.get("selection")

    return {
        "base_prompt": base_prompt,
        "delta_prompt": delta_prompt,
        "gen_prompt": gen_prompt,
        "full_prompt": full_prompt,
        "base_structured": base_structured,
        "display_structured": display_structured,
        "base_disk_key": base_disk_key,
        "gen_disk_key": gen_disk_key,
        "sem_base_key": sem_base_key,
        "sem_delta_key": sem_delta_key,
        "tier": tier,
        "tier_fields": tier_fields,
        "model": model,
        "delta_layers": delta_layers,
        "surface_id": surface_id,
    }


def get_surface_image(ctx: dict, *, surface_id: str = DEFAULT_SURFACE_ID,
                      generate: bool = False,
                      tenant: str | None = None) -> dict:
    """Resolve an image surface receipt using two-tier base + delta cache strategy."""
    resolved = _resolve_prompts(ctx, tenant=tenant, surface_id=surface_id)
    base_structured = resolved["display_structured"]
    gen_prompt = resolved["gen_prompt"]
    base_prompt = resolved["base_prompt"]
    base_disk_key = resolved["base_disk_key"]
    gen_disk_key = resolved["gen_disk_key"]
    tier = resolved["tier"]
    tier_fields = resolved["tier_fields"]
    model = resolved["model"]

    # a. Check full (personalized) cache key
    cached = _load_cached(gen_disk_key)
    if cached:
        tier_fields["tokens_saved_estimate"] = _estimate_tokens_saved(
            len(resolved["full_prompt"]), 0, cache_hit=True)
        return {**cached, **tier_fields}

    # b. Segment-only visitor — check base cache
    if tier == "base_only":
        cached_base = _load_cached(base_disk_key)
        if cached_base:
            tier_fields["tokens_saved_estimate"] = _estimate_tokens_saved(
                len(resolved["full_prompt"]), 0, cache_hit=True)
            return {**cached_base, **tier_fields}

    # c. base+delta miss but base exists — still need combined generation
    if tier == "base+delta":
        cached_base = _load_cached(base_disk_key)
        if cached_base and not generate:
            # Pending personalized variant; base is warm
            tier_fields["base_warm"] = True

    if not _api_key():
        return _gallery_receipt(ctx, structured=base_structured, prompt=gen_prompt,
                                cache_key=gen_disk_key, model=model,
                                fallback_chain=["cache_miss", "no_api_key", "gallery"],
                                tier_fields=tier_fields)

    if not generate:
        return {
            "url": None,
            "source": "pending",
            "prompt": gen_prompt,
            "model": model,
            "vendor": VENDOR,
            "cache_key": gen_disk_key,
            "generated_at": None,
            "license": None,
            "fallback_chain": ["cache_miss", "api_key_set", "await_async"],
            **_receipt_extras(base_structured, tier_fields),
        }

    # d. Generate base first if miss (when delta needed, base still cached separately)
    if tier == "base+delta" and not _load_cached(base_disk_key):
        _generate_and_cache(ctx, resolved["base_structured"], base_prompt,
                            base_disk_key, model,
                            _tier_receipt_fields(
                                tier="base",
                                base_cache_key=resolved["sem_base_key"],
                                delta_cache_key=None,
                                delta_signals=[],
                                base_prompt=base_prompt,
                                delta_prompt=None,
                                full_prompt_len=len(resolved["full_prompt"]),
                                used_prompt_len=len(base_prompt),
                                cache_hit=False,
                            ),
                            tenant=tenant, generate=generate)

    # e. Generate final image (base_only or base+delta combined prompt)
    return _generate_and_cache(ctx, base_structured, gen_prompt, gen_disk_key, model,
                               tier_fields, tenant=tenant, generate=generate)


def get_hero_image(ctx: dict, *, generate: bool = False,
                   tenant: str | None = None) -> dict:
    """Resolve hero image receipt — alias for the default hero surface."""
    return get_surface_image(ctx, surface_id=DEFAULT_SURFACE_ID,
                             generate=generate, tenant=tenant)


def resolve_surface_image(page: dict, *, surface_id: str = DEFAULT_SURFACE_ID,
                          generate: bool = False,
                          tenant: str | None = None) -> dict:
    """Page-facing wrapper → {status, fallback, url?, receipt, dev, surface_id}."""
    ctx = build_image_ctx(page)
    receipt = get_surface_image(ctx, surface_id=surface_id,
                                generate=generate, tenant=tenant)
    source = receipt.get("source", "gradient")
    url = receipt.get("url")
    if source == "pending":
        out = {"status": "pending", "fallback": "gradient", "url": None, "receipt": receipt}
    elif url:
        out = {"status": "ready", "fallback": "gradient", "url": url, "receipt": receipt}
    else:
        out = {"status": "ready", "fallback": "gradient", "url": None, "receipt": receipt}
    out["surface_id"] = surface_id
    out["dev"] = image_surface_dev_panel(out, surface_id=surface_id, tenant=tenant)
    return out


def resolve_hero_image(page: dict, *, generate: bool = False,
                       tenant: str | None = None) -> dict:
    """Page-facing wrapper for the hero surface — backward-compatible alias."""
    return resolve_surface_image(page, surface_id=DEFAULT_SURFACE_ID,
                                 generate=generate, tenant=tenant)


_GUARD_LABELS = {
    "industry_layer_stripped": "Industry layer stripped (tier gate)",
    "region_layer_stripped": "Region mood stripped (tier gate)",
    "hold_source_present": "Hold-tier source present — not emitted",
    "pattern_blocked": "Hold pattern blocked in prompt body",
}


def _guardrail_label(entry: str) -> str:
    if ":" in entry:
        kind, detail = entry.split(":", 1)
        base = _GUARD_LABELS.get(kind, kind.replace("_", " "))
        return f"{base} ({detail})"
    return entry.replace("_", " ")


def image_surface_dev_panel(image: dict, *, surface_id: str = DEFAULT_SURFACE_ID,
                            tenant: str | None = None) -> dict:
    """Structured decision chain for /dev panel — full data + decisioning per surface."""
    spec = surface_spec(surface_id, tenant=tenant)
    receipt = image.get("receipt") or {}
    sel = receipt.get("intent_selection") or {}
    primary = sel.get("primary") or {}
    secondary = sel.get("secondary")
    intents = sel.get("intents") or []
    rule = sel.get("rule_fired") or "select_image_intent()"

    intent_rows = []
    for pick in intents:
        intent_rows.append({
            "intent_id": pick["intent_id"],
            "rank": pick["rank"],
            "why": pick.get("why", ""),
            "signals": pick.get("signals_used") or [],
            "disposition": pick.get("disposition", "allude"),
            "primary": pick["intent_id"] == primary.get("intent_id"),
        })

    layers = receipt.get("personalization_layers") or []
    applied = receipt.get("guardrails_applied") or []
    blocked = receipt.get("guardrails_blocked") or []
    chain = receipt.get("fallback_chain") or []
    url = image.get("url") or receipt.get("url")
    src = receipt.get("source", "gradient")

    brain_target = receipt.get("brain_target")
    brain_target_label = receipt.get("brain_target_label")
    if brain_target and not brain_target_label:
        from pipeline.personalization.brain_simulator import BRAIN_TARGET_LABELS
        brain_target_label = BRAIN_TARGET_LABELS.get(brain_target, brain_target)

    tier = receipt.get("tier", "base_only")
    delta_signals = receipt.get("delta_signals") or []
    tier_label = {
        "base": "Segment base (pre-cached)",
        "base_only": "Segment base only — no delta signals",
        "base+delta": "Personalization delta applied",
    }.get(tier, tier)

    return {
        "surface_id": surface_id,
        "surface_label": spec["label"],
        "surface_placement": spec.get("placement", ""),
        "intent_selection": {
            "rule_fired": rule,
            "primary_id": primary.get("intent_id"),
            "secondary_id": (secondary or {}).get("intent_id"),
            "intents": intent_rows,
        },
        "conversion": {
            "goal": receipt.get("conversion_goal"),
            "sales_technique": receipt.get("sales_technique"),
            "drives_action": receipt.get("drives_action"),
            "pairs_with_objection": receipt.get("pairs_with_objection"),
        },
        "layers": layers,
        "tier": {
            "mode": tier,
            "label": tier_label,
            "base_cache_key": receipt.get("base_cache_key"),
            "delta_cache_key": receipt.get("delta_cache_key"),
            "delta_signals": delta_signals,
            "tokens_saved_estimate": receipt.get("tokens_saved_estimate"),
            "base_prompt": receipt.get("base_prompt"),
            "delta_prompt": receipt.get("delta_prompt"),
            "base_warm": receipt.get("base_warm", False),
        },
        "prompt": {
            "visual_metaphor": receipt.get("visual_metaphor"),
            "composition": receipt.get("composition"),
            "mood": receipt.get("mood"),
            "accent_color": receipt.get("accent_color"),
            "must_include": receipt.get("must_include") or [],
            "must_avoid": receipt.get("must_avoid") or [],
            "full_prompt": receipt.get("prompt"),
        },
        "guardrails": {
            "applied": [{"code": g, "label": _guardrail_label(g)} for g in applied],
            "blocked": [{"code": g, "label": _guardrail_label(g)} for g in blocked],
        },
        "receipt": {
            "source": src,
            "vendor": receipt.get("vendor"),
            "model": receipt.get("model"),
            "cache_key": receipt.get("cache_key"),
            "generated_at": receipt.get("generated_at"),
            "license": receipt.get("license"),
            "url": url,
            "gallery_id": receipt.get("gallery_id"),
        },
        "fallback_chain": chain,
        "status": image.get("status", "ready"),
        "fallback": image.get("fallback", "gradient"),
        "preview": {
            "url": url,
            "has_image": bool(url),
            "gradient_note": "CSS gradient shows when no generated/cached URL resolves",
        },
        "brain": {
            "enabled": brain_target is not None or receipt.get("brain_score") is not None,
            "brain_target": brain_target,
            "brain_target_label": brain_target_label,
            "brain_regions": receipt.get("brain_regions") or [],
            "brain_simulator": receipt.get("brain_simulator"),
            "brain_score": receipt.get("brain_score"),
            "brain_region_scores": receipt.get("brain_region_scores") or {},
            "candidates_evaluated": receipt.get("candidates_evaluated"),
            "winner_index": receipt.get("winner_index"),
            "brain_guardrail_penalty": receipt.get("brain_guardrail_penalty"),
        },
    }


def hero_image_dev_panel(hero_image: dict) -> dict:
    """Backward-compatible alias — hero surface dev panel."""
    sid = hero_image.get("surface_id") or DEFAULT_SURFACE_ID
    return image_surface_dev_panel(hero_image, surface_id=sid)


def hero_image_trace(receipt: dict) -> tuple[list[str], str, str]:
    """Signals, output, why for the decision trace."""
    sigs = [
        f"source={receipt.get('source', 'gradient')}",
        f"cache_key={receipt.get('cache_key', '—')[:12]}…",
        f"model={receipt.get('model', '—')}",
    ]
    if receipt.get("intent_id"):
        sigs.append(f"intent={receipt['intent_id']}")
        if receipt.get("secondary_intent_id"):
            sigs.append(f"secondary={receipt['secondary_intent_id']}")
    if receipt.get("tier"):
        sigs.append(f"tier={receipt['tier']}")
    if receipt.get("base_cache_key"):
        sigs.append(f"base_key={receipt['base_cache_key'][:24]}")
    sel = receipt.get("intent_selection") or {}
    if sel.get("rule_fired"):
        sigs.append(f"rule={sel['rule_fired'][:72]}")
    if receipt.get("drives_action"):
        sigs.append(f"drives_action={receipt['drives_action']}")
    primary = sel.get("primary") or {}
    if primary.get("why"):
        sigs.append(f"why={primary['why'][:80]}")
    blocked = receipt.get("guardrails_blocked") or []
    if blocked:
        sigs.append(f"guardrails_blocked={len(blocked)}")
        sigs.append(f"stripped={', '.join(blocked[:3])}")
    if receipt.get("brain_target"):
        sigs.append(f"brain_target={receipt['brain_target']}")
    if receipt.get("brain_score") is not None:
        sigs.append(f"brain_score={receipt['brain_score']}")
        sigs.append(f"brain_simulator={receipt.get('brain_simulator', 'proxy_v1')}")
    if receipt.get("candidates_evaluated"):
        sigs.append(f"candidates_evaluated={receipt['candidates_evaluated']}")
    if receipt.get("gallery_id"):
        sigs.append(f"gallery_id={receipt['gallery_id']}")
    chain = receipt.get("fallback_chain") or []
    if chain:
        sigs.append("chain=" + " → ".join(chain))
    src = receipt.get("source", "gradient")
    intent = receipt.get("intent_id", "—")
    goal = receipt.get("conversion_goal", "—")
    guard_summary = ""
    if blocked:
        guard_summary = f"; guardrails stripped {len(blocked)} item(s): {blocked[0]}"
    if src == "generated":
        out = f"generated · {receipt.get('vendor', VENDOR)} · intent={intent}"
        why = (f"disk cache miss → API generated → cached; intent {intent} ({goal}) "
               f"drives hero CTA; prompt uses structured layers only (no PII){guard_summary}")
        if receipt.get("brain_score") is not None:
            why += (f"; brain_sim {receipt.get('brain_simulator', 'proxy_v1')} scored "
                    f"{receipt.get('candidates_evaluated', 1)} candidate(s) — "
                    f"winner brain_score={receipt['brain_score']}")
    elif src == "gallery":
        out = f"gallery · {receipt.get('gallery_id', 'curated')} · intent={intent}"
        why = f"no cached/generated asset — curated CC library; intent selection still logged{guard_summary}"
    elif src == "pending":
        out = f"pending async · intent={intent}"
        why = f"API key present but cache empty — page ships gradient; client fetch triggers gen{guard_summary}"
    else:
        out = f"CSS gradient · intent={intent}"
        why = f"no image asset resolved — hero gradient; intent selection logged for provenance{guard_summary}"
    return sigs, out, why


def hero_image_ledger_rows(receipt: dict) -> list[dict]:
    """Extra signal-ledger rows for /dev."""
    rows = [{
        "label": "Hero image source",
        "value": receipt.get("source", "gradient"),
        "source": "observed",
        "vendor": receipt.get("vendor") or "—",
        "policy": "say",
    }]
    if receipt.get("intent_id"):
        rows.append({
            "label": "Image intent",
            "value": receipt["intent_id"],
            "source": "select_image_intent()",
            "vendor": "image_intents",
            "policy": "say",
        })
    if receipt.get("conversion_goal"):
        rows.append({
            "label": "Conversion goal",
            "value": receipt["conversion_goal"],
            "source": "intent template",
            "vendor": receipt.get("intent_id", "—"),
            "policy": "say",
        })
    if receipt.get("drives_action"):
        rows.append({
            "label": "Drives action",
            "value": receipt["drives_action"],
            "source": "CTA linkage",
            "vendor": "build_structured_prompt()",
            "policy": "say",
        })
    if receipt.get("prompt"):
        rows.append({
            "label": "Image prompt",
            "value": receipt["prompt"][:240] + ("…" if len(receipt["prompt"]) > 240 else ""),
            "source": "deterministic",
            "vendor": "build_image_prompt()",
            "policy": "say",
        })
    if receipt.get("model"):
        rows.append({
            "label": "Image model",
            "value": receipt["model"],
            "source": "config",
            "vendor": receipt.get("vendor") or VENDOR,
            "policy": "observed",
        })
    if receipt.get("cache_key"):
        rows.append({
            "label": "Image cache key",
            "value": receipt["cache_key"],
            "source": "hash(prompt + model)",
            "vendor": "data/demo/image_cache/",
            "policy": "observed",
        })
    if receipt.get("tier"):
        rows.append({
            "label": "Image tier",
            "value": receipt["tier"],
            "source": "two-tier cache",
            "vendor": "image_gen.resolve",
            "policy": "observed",
        })
    if receipt.get("base_cache_key"):
        rows.append({
            "label": "Segment base key",
            "value": receipt["base_cache_key"],
            "source": "segment identity",
            "vendor": "image_gen.resolve",
            "policy": "observed",
        })
    if receipt.get("delta_cache_key"):
        rows.append({
            "label": "Personalization delta key",
            "value": receipt["delta_cache_key"],
            "source": "objection/industry/region/archetype",
            "vendor": "image_gen.resolve",
            "policy": "observed",
        })
    if receipt.get("tokens_saved_estimate") is not None:
        rows.append({
            "label": "Tokens saved (est.)",
            "value": str(receipt["tokens_saved_estimate"]),
            "source": "full vs base/delta prompt",
            "vendor": "image_gen.resolve",
            "policy": "observed",
        })
    if receipt.get("brain_score") is not None:
        rows.append({
            "label": "Brain simulator score",
            "value": str(receipt["brain_score"]),
            "source": receipt.get("brain_simulator", "proxy_v1"),
            "vendor": "brain_simulator",
            "policy": "observed",
        })
    if receipt.get("brain_target"):
        rows.append({
            "label": "Brain target",
            "value": receipt["brain_target"],
            "source": "intent YAML",
            "vendor": "brain_simulator",
            "policy": "say",
        })
    if receipt.get("candidates_evaluated"):
        rows.append({
            "label": "Candidates evaluated",
            "value": str(receipt["candidates_evaluated"]),
            "source": "best-of-N",
            "vendor": "image_gen",
            "policy": "observed",
        })
    if receipt.get("license"):
        rows.append({
            "label": "Image license",
            "value": receipt["license"],
            "source": receipt.get("source", "gradient"),
            "vendor": receipt.get("vendor") or "—",
            "policy": "say",
        })
    chain = receipt.get("fallback_chain")
    if chain:
        rows.append({
            "label": "Image fallback chain",
            "value": " → ".join(chain),
            "source": "observed",
            "vendor": "image_gen.resolve",
            "policy": "observed",
        })
    return rows


def intent_catalog_for_dev(tenant: str | None = None) -> list[dict]:
    """Full intent taxonomy for /dev panel."""
    return II.intent_catalog_for_config(_tenant_config(tenant))
