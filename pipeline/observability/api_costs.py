"""Append-only ledger for estimated LLM/API call costs.

Records are persisted to data/demo/api_cost_ledger.jsonl (gitignored). Costs are
*estimates* from rules/api_pricing.yaml — not exact vendor billing.
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from pipeline.common import config

LEDGER_PATH = config.DATA_DIR / "api_cost_ledger.jsonl"
_PRICING_PATH = config.RULES_DIR / "api_pricing.yaml"
_LOCK = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_pricing() -> dict:
    if not _PRICING_PATH.exists():
        return {"services": {}}
    return yaml.safe_load(_PRICING_PATH.read_text()) or {"services": {}}


def _model_pricing(service: str, model: str) -> dict:
    svc = (_load_pricing().get("services") or {}).get(service) or {}
    models = svc.get("models") or {}
    return models.get(model) or models.get("default") or {}


def estimate_cost(
    *,
    service: str,
    model: str,
    images_generated: int = 0,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> float:
    """Return estimated USD for one call from published pricing tables."""
    rates = _model_pricing(service, model)
    cost = 0.0
    if images_generated and rates.get("per_image_usd") is not None:
        cost += float(rates["per_image_usd"]) * images_generated
    if input_tokens and rates.get("input_per_mtok_usd") is not None:
        cost += float(rates["input_per_mtok_usd"]) * input_tokens / 1_000_000
    if output_tokens and rates.get("output_per_mtok_usd") is not None:
        cost += float(rates["output_per_mtok_usd"]) * output_tokens / 1_000_000
    if not cost and rates.get("per_call_usd") is not None:
        cost = float(rates["per_call_usd"])
    return round(cost, 6)


def service_for_vendor(vendor: str, *, use_gemini: bool) -> str:
    if use_gemini or vendor == "google-gemini":
        return "gemini_image"
    if vendor == "anthropic":
        return "anthropic"
    if vendor == "ollama-local":
        return "ollama"
    return "openai_image"


def record_call(
    *,
    tenant: str,
    service: str,
    model: str,
    operation: str,
    status: str = "success",
    cache_key: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    images_generated: int = 0,
    duration_ms: int | None = None,
    request_id: str | None = None,
    estimated_cost_usd: float | None = None,
    extra: dict[str, Any] | None = None,
) -> dict:
    """Append one cost record; thread-safe. Returns the record written."""
    if estimated_cost_usd is None:
        estimated_cost_usd = estimate_cost(
            service=service,
            model=model,
            images_generated=images_generated,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    row = {
        "timestamp": _utc_now(),
        "tenant": tenant,
        "service": service,
        "model": model,
        "operation": operation,
        "cache_key": cache_key,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "images_generated": images_generated,
        "estimated_cost_usd": estimated_cost_usd if status == "success" else 0.0,
        "duration_ms": duration_ms,
        "request_id": request_id or uuid.uuid4().hex[:12],
        "status": status,
    }
    if extra:
        row.update(extra)
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row, separators=(",", ":"))
    with _LOCK:
        with LEDGER_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return row


def record_anthropic_usage(
    *,
    tenant: str,
    model: str,
    operation: str,
    response: Any,
    cache_key: str | None = None,
    duration_ms: int | None = None,
) -> dict:
    """Record estimated cost from an Anthropic messages.create response."""
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", None) if usage else None
    output_tokens = getattr(usage, "output_tokens", None) if usage else None
    return record_call(
        tenant=tenant,
        service="anthropic",
        model=model,
        operation=operation,
        cache_key=cache_key,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        images_generated=0,
        duration_ms=duration_ms,
        status="success",
    )


def record_ollama_usage(
    *,
    tenant: str,
    model: str,
    operation: str,
    duration_ms: int | None = None,
) -> dict:
    return record_call(
        tenant=tenant,
        service="ollama",
        model=model,
        operation=operation,
        status="success",
        images_generated=0,
        duration_ms=duration_ms,
        estimated_cost_usd=0.0,
    )


def read_ledger(
    *,
    limit: int = 500,
    tenant: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> list[dict]:
    """Read ledger rows newest-first, optionally filtered."""
    if not LEDGER_PATH.exists():
        return []
    rows: list[dict] = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if tenant and row.get("tenant") != tenant:
            continue
        ts = row.get("timestamp") or ""
        if since and ts < since:
            continue
        if until and ts > until:
            continue
        rows.append(row)
    rows.sort(key=lambda r: r.get("timestamp") or "", reverse=True)
    return rows[:limit]


def summarize(
    *,
    tenant: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> dict:
    """Aggregate stats for dashboard cards."""
    rows = read_ledger(limit=10_000, tenant=tenant, since=since, until=until)
    today_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = sum(float(r.get("estimated_cost_usd") or 0) for r in rows)
    today = sum(
        float(r.get("estimated_cost_usd") or 0)
        for r in rows
        if (r.get("timestamp") or "").startswith(today_prefix)
    )
    by_tenant: dict[str, float] = {}
    by_operation: dict[str, float] = {}
    by_service: dict[str, float] = {}
    errors = 0
    for r in rows:
        t = r.get("tenant") or "unknown"
        by_tenant[t] = by_tenant.get(t, 0.0) + float(r.get("estimated_cost_usd") or 0)
        op = r.get("operation") or "unknown"
        by_operation[op] = by_operation.get(op, 0.0) + float(r.get("estimated_cost_usd") or 0)
        svc = r.get("service") or "unknown"
        by_service[svc] = by_service.get(svc, 0.0) + float(r.get("estimated_cost_usd") or 0)
        if r.get("status") in ("error", "429"):
            errors += 1
    return {
        "total_cost_usd": round(total, 4),
        "today_cost_usd": round(today, 4),
        "call_count": len(rows),
        "error_count": errors,
        "by_tenant": {k: round(v, 4) for k, v in sorted(by_tenant.items())},
        "by_operation": {k: round(v, 4) for k, v in sorted(by_operation.items())},
        "by_service": {k: round(v, 4) for k, v in sorted(by_service.items())},
        "disclaimer": "Estimated from published pricing — not exact vendor billing.",
    }


def costs_for_cache_key(cache_key: str, *, tenant: str | None = None) -> dict:
    """Sum ledger rows tied to a cache key (hero generation path)."""
    if not cache_key:
        return {"estimated_cost_usd": 0.0, "calls": []}
    rows = [
        r for r in read_ledger(limit=500, tenant=tenant)
        if r.get("cache_key") == cache_key
    ]
    total = round(sum(float(r.get("estimated_cost_usd") or 0) for r in rows), 6)
    by_candidate: dict[int, float] = {}
    for r in rows:
        idx = (r.get("candidate_index")
               if r.get("candidate_index") is not None
               else (r.get("extra") or {}).get("candidate_index"))
        if idx is not None:
            by_candidate[int(idx)] = round(
                by_candidate.get(int(idx), 0.0) + float(r.get("estimated_cost_usd") or 0), 6)
    return {
        "estimated_cost_usd": total,
        "calls": rows,
        "by_candidate": by_candidate,
    }


def costs_for_session_cache_keys(cache_keys: list[str], *, tenant: str | None = None) -> float:
    keys = {k for k in cache_keys if k}
    if not keys:
        return 0.0
    total = 0.0
    for r in read_ledger(limit=2000, tenant=tenant):
        if r.get("cache_key") in keys:
            total += float(r.get("estimated_cost_usd") or 0)
    return round(total, 6)
