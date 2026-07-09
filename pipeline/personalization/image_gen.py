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
from pipeline.personalization import image_intents as II
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


def load_image_config(tenant: str = DEFAULT_IMAGE_TENANT) -> dict:
    """Load tenant image config — defaults to Gauntlet for /gauntlet routes."""
    return II.load_image_config(tenant)


def _tenant_config(tenant: str | None = None) -> dict:
    return load_image_config(tenant or DEFAULT_IMAGE_TENANT)


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
    """Structured, action-driven prompt with provenance fields."""
    config = _tenant_config(tenant)
    selection = II.select_image_intent(ctx, config)
    structured = II.build_structured_prompt(ctx, selection, config)
    out = II.apply_guardrails(structured, ctx, config)
    _assert_prompt_safe(out["full_prompt"])
    return out


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


def _receipt_extras(structured: II.StructuredPrompt) -> dict[str, Any]:
    """Provenance fields stored alongside generation receipt."""
    return {
        "intent_id": structured.get("intent_id"),
        "secondary_intent_id": structured.get("secondary_intent_id"),
        "conversion_goal": structured.get("conversion_goal"),
        "sales_technique": structured.get("sales_technique"),
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


def _gradient_receipt(*, structured: II.StructuredPrompt, prompt: str, cache_key: str,
                      model: str, fallback_chain: list[str]) -> dict:
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
        **_receipt_extras(structured),
    }


def _gallery_receipt(ctx: dict, *, structured: II.StructuredPrompt, prompt: str,
                     cache_key: str, model: str, fallback_chain: list[str]) -> dict:
    ind = ctx.get("industry") or "general"
    img = SC.image_for(ind)
    if ind == "general" or img.get("id") == "neutral-wash":
        return _gradient_receipt(structured=structured, prompt=prompt, cache_key=cache_key,
                                 model=model, fallback_chain=fallback_chain + ["gradient"])
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
        **_receipt_extras(structured),
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
                        cache_key: str, model: str) -> dict:
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
            **_receipt_extras(structured),
        }
        manifest = _read_manifest()
        manifest[cache_key] = {k: v for k, v in receipt.items() if k != "url"}
        manifest[cache_key]["ext"] = ext
        _write_manifest(manifest)
        return receipt
    chain.append("api_failed")
    return _gallery_receipt(ctx, structured=structured, prompt=prompt, cache_key=cache_key,
                            model=model, fallback_chain=chain + ["gallery"])


def get_hero_image(ctx: dict, *, generate: bool = False,
                   tenant: str | None = None) -> dict:
    """Resolve hero image receipt. generate=True may call the image API (server-side only)."""
    structured = build_image_prompt(ctx, tenant=tenant)
    prompt = structured["full_prompt"]
    model = _model()
    cache_key = image_cache_key(prompt, model)

    cached = _load_cached(cache_key)
    if cached:
        return dict(cached)

    if not _api_key():
        return _gallery_receipt(ctx, structured=structured, prompt=prompt, cache_key=cache_key,
                                model=model, fallback_chain=["cache_miss", "no_api_key", "gallery"])

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
            **_receipt_extras(structured),
        }

    return _generate_and_cache(ctx, structured, prompt, cache_key, model)


def resolve_hero_image(page: dict, *, generate: bool = False,
                       tenant: str | None = None) -> dict:
    """Page-facing wrapper → {status, fallback, url?, receipt}."""
    ctx = build_image_ctx(page)
    receipt = get_hero_image(ctx, generate=generate, tenant=tenant)
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
    if receipt.get("intent_id"):
        sigs.append(f"intent={receipt['intent_id']}")
        if receipt.get("secondary_intent_id"):
            sigs.append(f"secondary={receipt['secondary_intent_id']}")
    if receipt.get("drives_action"):
        sigs.append(f"drives_action={receipt['drives_action']}")
    sel = receipt.get("intent_selection") or {}
    primary = sel.get("primary") or {}
    if primary.get("why"):
        sigs.append(f"why={primary['why'][:80]}")
    if receipt.get("gallery_id"):
        sigs.append(f"gallery_id={receipt['gallery_id']}")
    chain = receipt.get("fallback_chain") or []
    if chain:
        sigs.append("chain=" + " → ".join(chain))
    src = receipt.get("source", "gradient")
    intent = receipt.get("intent_id", "—")
    goal = receipt.get("conversion_goal", "—")
    if src == "generated":
        out = f"generated · {receipt.get('vendor', VENDOR)} · intent={intent}"
        why = (f"disk cache miss → API generated → cached; intent {intent} ({goal}) "
               "drives hero CTA; prompt uses structured layers only (no PII)")
    elif src == "gallery":
        out = f"gallery · {receipt.get('gallery_id', 'curated')} · intent={intent}"
        why = "no cached/generated asset — curated CC library; intent selection still logged"
    elif src == "pending":
        out = f"pending async · intent={intent}"
        why = "API key present but cache empty — page ships gradient; client fetch triggers gen"
    else:
        out = f"CSS gradient · intent={intent}"
        why = "no image asset resolved — hero gradient; intent selection logged for provenance"
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
