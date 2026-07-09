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
from datetime import datetime, timezone
from typing import Any
import httpx

from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import scene as SC

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
    r"\bde-anonymized\b|\babandoned\b|\bstep \d of \d\b)",
    re.I,
)

_PII_WORDS = (
    "gmail.com", "yahoo.com", "welcome back", "your team at", "we see your",
    "income band", "magic token", "hubspot", "vector", "clay",
)


def _api_key() -> str:
    return (os.environ.get("IMAGE_GEN_API_KEY") or os.environ.get("NANO_BANANA_API_KEY") or "").strip()


def _api_url() -> str:
    return (os.environ.get("IMAGE_GEN_API_URL") or DEFAULT_API_URL).strip()


def _model() -> str:
    return (os.environ.get("IMAGE_GEN_MODEL") or DEFAULT_MODEL).strip()


def build_image_ctx(page: dict) -> dict:
    """Deterministic image context from a build_page() result — no PII fields."""
    prioritized = (page.get("objections") or {}).get("prioritized") or []
    top = prioritized[0]["objection_id"] if prioritized else None
    ad = page.get("ad_variant")
    det = page.get("det") or {}
    return {
        "channel": page["entry"]["channel"],
        "ad_variant_id": ad["id"] if ad else None,
        "audience": page.get("audience", "neutral"),
        "audience_route": page.get("audience_route", "neutral"),
        "industry": det.get("industry") or "general",
        "region": det.get("region"),
        "top_objection": top,
    }


def build_image_prompt(ctx: dict) -> str:
    """Deterministic text-to-image prompt — industry/peer framing only, no PII."""
    lines = [
        "Cinematic wide hero backdrop for an AI engineering talent program marketing site.",
        "Dark moody atmosphere, warm gold accent lighting, abstract technology textures.",
        "No text, no logos, no readable faces, no company names, no maps.",
    ]
    if ctx.get("ad_variant_id"):
        av = next((v for v in GS.AD_VARIANTS if v["id"] == ctx["ad_variant_id"]), None)
        if av:
            lines.append(
                f"Visual mood aligned with {av['x_targeting_type']} ad targeting — "
                f"{av['audience_fit_label']} audience, abstract only.")
    route = ctx.get("audience_route", "neutral")
    route_mood = {
        "b2b_hire": "Corporate engineering hiring — team capability under production pressure.",
        "b2b_upskill": "Enterprise team upskilling — collaborative learning energy.",
        "individual": "Individual engineer career leap — focused determination.",
        "neutral": "Balanced B2B and individual engineering audience.",
    }
    lines.append(route_mood.get(route, route_mood["neutral"]))
    ind_key = ctx.get("industry") or "general"
    if ind_key != "general":
        label = SC.BY_KEY.get(ind_key, {}).get("label", ind_key)
        lines.append(f"Subtle {label.lower()} sector atmosphere — environmental cues only.")
    if ctx.get("region"):
        lines.append(f"Regional tone suggesting {ctx['region']} — no landmarks or addresses.")
    if ctx.get("top_objection"):
        obj = GS.OBJECTION_BY_ID.get(ctx["top_objection"])
        if obj:
            lines.append(
                f"Mood subtly addresses the concern: {obj['text']} — abstract, not literal.")
    prompt = " ".join(lines)
    _assert_prompt_safe(prompt)
    return prompt


def _assert_prompt_safe(prompt: str) -> None:
    low = prompt.lower()
    if _FORBIDDEN_PROMPT.search(prompt):
        raise ValueError("prompt contains forbidden hold/PII patterns")
    for w in _PII_WORDS:
        if w in low:
            raise ValueError(f"prompt contains forbidden token: {w}")


def image_cache_key(prompt: str, model: str | None = None) -> str:
    m = model or _model()
    return hashlib.sha256(f"{m}\x00{prompt}".encode()).hexdigest()[:32]


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


def _local_path(cache_key: str, ext: str = "png") -> pathlib.Path:
    return IMAGE_DIR / f"{cache_key}.{ext}"


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


def _save_image(cache_key: str, data: bytes, ext: str = "png") -> pathlib.Path:
    _ensure_dirs()
    path = _local_path(cache_key, ext)
    path.write_bytes(data)
    return path


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _gradient_receipt(*, prompt: str, cache_key: str, model: str, fallback_chain: list[str]) -> dict:
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
    }


def _gallery_receipt(ctx: dict, *, prompt: str, cache_key: str, model: str,
                     fallback_chain: list[str]) -> dict:
    ind = ctx.get("industry") or "general"
    img = SC.image_for(ind)
    if ind == "general" or img.get("id") == "neutral-wash":
        return _gradient_receipt(prompt=prompt, cache_key=cache_key, model=model,
                                 fallback_chain=fallback_chain + ["gradient"])
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


def _generate_and_cache(ctx: dict, prompt: str, cache_key: str, model: str) -> dict:
    chain = ["cache"]
    api_result = _call_image_api(prompt)
    if api_result:
        if "b64" in api_result:
            raw = base64.b64decode(api_result["b64"])
        else:
            raw = api_result["raw"]
        ext = api_result.get("ext", "png")
        _save_image(cache_key, raw, ext)
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
        }
        manifest = _read_manifest()
        manifest[cache_key] = {k: v for k, v in receipt.items() if k != "url"}
        manifest[cache_key]["ext"] = ext
        _write_manifest(manifest)
        return receipt
    chain.append("api_failed")
    return _gallery_receipt(ctx, prompt=prompt, cache_key=cache_key, model=model,
                            fallback_chain=chain + ["gallery"])


def get_hero_image(ctx: dict, *, generate: bool = False) -> dict:
    """Resolve hero image receipt. generate=True may call the image API (server-side only)."""
    prompt = build_image_prompt(ctx)
    model = _model()
    cache_key = image_cache_key(prompt, model)

    cached = _load_cached(cache_key)
    if cached:
        return dict(cached)

    if not _api_key():
        return _gallery_receipt(ctx, prompt=prompt, cache_key=cache_key, model=model,
                                fallback_chain=["cache_miss", "no_api_key", "gallery"])

    if not generate:
        return {
            "url": None,
            "source": "pending",
            "prompt": prompt,
            "model": model,
            "vendor": VENDOR,
            "cache_key": cache_key,
            "generated_at": None,
            "license": None,
            "fallback_chain": ["cache_miss", "api_key_set", "await_async"],
        }

    return _generate_and_cache(ctx, prompt, cache_key, model)


def resolve_hero_image(page: dict, *, generate: bool = False) -> dict:
    """Page-facing wrapper → {status, fallback, url?, receipt}."""
    ctx = build_image_ctx(page)
    receipt = get_hero_image(ctx, generate=generate)
    source = receipt.get("source", "gradient")
    url = receipt.get("url")
    if source == "pending":
        return {"status": "pending", "fallback": "gradient", "url": None, "receipt": receipt}
    if url:
        return {"status": "ready", "fallback": "gradient", "url": url, "receipt": receipt}
    return {"status": "ready", "fallback": "gradient", "url": None, "receipt": receipt}


def hero_image_trace(receipt: dict) -> tuple[list[str], str, str]:
    """Signals, output, why for the decision trace."""
    sigs = [
        f"source={receipt.get('source', 'gradient')}",
        f"cache_key={receipt.get('cache_key', '—')[:12]}…",
        f"model={receipt.get('model', '—')}",
    ]
    if receipt.get("gallery_id"):
        sigs.append(f"gallery_id={receipt['gallery_id']}")
    chain = receipt.get("fallback_chain") or []
    if chain:
        sigs.append("chain=" + " → ".join(chain))
    src = receipt.get("source", "gradient")
    if src == "generated":
        out = f"generated · {receipt.get('vendor', VENDOR)}"
        why = ("disk cache miss → API generated → cached for reproducibility; "
               "prompt uses industry/route framing only (no PII)")
    elif src == "gallery":
        out = f"gallery · {receipt.get('gallery_id', 'curated')}"
        why = "no cached/generated asset — curated CC library (scene.image_for), license disclosed"
    elif src == "pending":
        out = "pending async generation"
        why = "API key present but cache empty — page ships gradient; client fetch triggers gen"
    else:
        out = "CSS gradient (instant fallback)"
        why = "no image asset resolved — hero gradient matches gauntletai.com default"
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
