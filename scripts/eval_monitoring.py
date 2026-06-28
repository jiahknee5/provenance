"""Manual, cost-capped stakeholder eval monitoring for PM CI.

Run locally:

    python -m scripts.eval_monitoring

The default deterministic mode performs no external model calls. LLM-backed
smoke/calibration runs are intended to be started manually from GitLab with an
OpenRouter key and tight call caps.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "evals" / "stakeholder-sample-evals.json"

MODE_CAPS = {
    "deterministic": {"sample_limit": 10, "llm_max_calls": 0},
    "smoke": {"sample_limit": 6, "llm_max_calls": 18},
    "calibration": {"sample_limit": 12, "llm_max_calls": 48},
    "deep": {"sample_limit": 30, "llm_max_calls": 120},
}


@dataclass(frozen=True)
class EvalConfig:
    mode: str
    sample_limit: int
    llm_enabled: bool
    llm_max_calls: int
    openrouter_model: str
    openrouter_api_key: str
    openrouter_base_url: str
    output_dir: Path
    ci_fail_on_eval: bool
    langfuse_export: bool
    langfuse_base_url: str
    langfuse_public_key: str
    langfuse_secret_key: str
    trace_id: str
    environment: str


def _bool_env(value: str | None, fallback: bool = False) -> bool:
    if value is None:
        return fallback
    return value.lower() in {"1", "true", "yes", "on"}


def _int_env(value: str | None, fallback: int) -> int:
    try:
        parsed = int(value or "")
    except ValueError:
        return fallback
    return parsed if parsed >= 0 else fallback


def _clamp(value: int, floor: int, ceiling: int) -> int:
    return max(floor, min(value, ceiling))


def parse_eval_config(env: dict[str, str] | None = None) -> EvalConfig:
    env = env or os.environ
    requested_mode = (env.get("EVAL_MODE") or "deterministic").lower()
    mode = requested_mode if requested_mode in MODE_CAPS else "deterministic"
    caps = MODE_CAPS[mode]
    requested_llm = _bool_env(env.get("EVAL_LLM_ENABLED"))
    llm_enabled = mode != "deterministic" and requested_llm

    return EvalConfig(
        mode=mode,
        sample_limit=_clamp(_int_env(env.get("EVAL_SAMPLE_LIMIT"), caps["sample_limit"]), 1, caps["sample_limit"]),
        llm_enabled=llm_enabled,
        llm_max_calls=(
            _clamp(_int_env(env.get("EVAL_LLM_MAX_CALLS"), caps["llm_max_calls"]), 0, caps["llm_max_calls"])
            if llm_enabled
            else 0
        ),
        openrouter_model=env.get("OPENROUTER_MODEL") or "google/gemini-2.5-flash-lite",
        openrouter_api_key=env.get("OPENROUTER_API_KEY") or "",
        openrouter_base_url=env.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1/chat/completions",
        output_dir=Path(env.get("EVAL_OUTPUT_DIR") or "eval-results"),
        ci_fail_on_eval=_bool_env(env.get("CI_FAIL_ON_EVAL")),
        langfuse_export=_bool_env(env.get("LANGFUSE_EXPORT")),
        langfuse_base_url=(env.get("LANGFUSE_BASE_URL") or "https://us.cloud.langfuse.com").rstrip("/"),
        langfuse_public_key=env.get("LANGFUSE_PUBLIC_KEY") or "",
        langfuse_secret_key=env.get("LANGFUSE_SECRET_KEY") or "",
        trace_id=env.get("EVAL_TRACE_ID") or f"pm-ci-eval-{env.get('CI_PIPELINE_ID') or int(time.time() * 1000)}",
        environment=env.get("LANGFUSE_TRACING_ENVIRONMENT") or env.get("CI_COMMIT_REF_NAME") or "ci-manual",
    )


def select_eval_cases(cases: list[dict[str, Any]], config: EvalConfig) -> list[dict[str, Any]]:
    deterministic = [case for case in cases if case.get("runner") == "deterministic"]
    if config.mode == "deterministic" or not config.llm_enabled:
        return deterministic[: config.sample_limit]

    llm_cases = [case for case in cases if case.get("runner") == "giskard_oss_llm"]
    return [*deterministic, *llm_cases][: config.sample_limit]


def _contains_forbidden(value: str, forbidden: list[str]) -> bool:
    normalized = value.lower()
    return any(str(item).lower() in normalized for item in forbidden)


def _deterministic_check(case: dict[str, Any]) -> dict[str, Any]:
    case_id = case.get("id")
    inputs = case.get("input") or {}

    if case_id == "pm_golden_summary":
        summary = inputs.get("summary") or {}
        passed = int(summary.get("passed") or 0)
        total = int(summary.get("total") or 0)
        ok = total > 0 and passed == total
        return {
            "pass": ok,
            "score": 1 if ok else 0,
            "rationale": f"Golden eval summary {passed}/{total}.",
        }

    if case_id == "gate_blocks_unsupported_claim":
        verdict = str(inputs.get("verdict") or "").lower()
        ok = verdict in {"blocked", "vetoed"} and inputs.get("selected") is False
        return {
            "pass": ok,
            "score": 1 if ok else 0,
            "rationale": "Unsupported claim is blocked and absent from selection." if ok else "Unsupported claim was selectable.",
        }

    if case_id == "winner_gate_cleared":
        arm = inputs.get("selectedArm") or {}
        ok = arm.get("selectable") is True and arm.get("state") != "gate_vetoed"
        return {
            "pass": ok,
            "score": 1 if ok else 0,
            "rationale": "Selected arm is Gate-cleared." if ok else "Selected arm is not Gate-cleared.",
        }

    if case_id == "private_signal_redaction":
        ok = not _contains_forbidden(str(inputs.get("artifact") or ""), list(inputs.get("forbidden") or []))
        return {
            "pass": ok,
            "score": 1 if ok else 0,
            "rationale": "Artifact is summarized and redacted." if ok else "Artifact exposes private signal text.",
        }

    return {"pass": False, "score": 0, "rationale": f"No deterministic evaluator registered for {case_id}."}


def _safe_json(value: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", value, flags=re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_judge(value: str | dict[str, Any]) -> dict[str, Any]:
    parsed = _safe_json(value) if isinstance(value, str) else value
    if not isinstance(parsed, dict) or not isinstance(parsed.get("pass"), bool):
        return {"skipped": True, "skipReason": "judge_unparseable_response"}

    score = parsed.get("score")
    score_value = min(1.0, max(0.0, float(score))) if isinstance(score, (int, float)) else 1.0
    return {
        "pass": parsed["pass"],
        "score": score_value,
        "rationale": str(parsed.get("rationale") or "No rationale returned.")[:240],
    }


def _judge_prompt(case: dict[str, Any]) -> str:
    return "\n".join(
        [
            "You are a CI evaluator for an apt campaign assurance app.",
            'Return only compact JSON: {"pass": boolean, "score": number between 0 and 1, "rationale": string}.',
            "Judge only the supplied synthetic fixture. Do not infer facts beyond it.",
            f"Eval id: {case.get('id')}",
            f"Score: {case.get('scoreName')}",
            f"Lane: {case.get('lane')}",
            f"Description: {case.get('description')}",
            f"Fixture: {json.dumps(case.get('input') or {}, sort_keys=True)}",
        ]
    )


def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int = 30) -> tuple[int, dict[str, Any], dict[str, str]]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body or "{}"), dict(response.headers.items())
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        try:
            parsed = json.loads(body or "{}")
        except json.JSONDecodeError:
            parsed = {}
        return error.code, parsed, dict(error.headers.items())


def judge_with_openrouter(
    case: dict[str, Any],
    config: EvalConfig,
    http_post: Callable[[str, dict[str, str], dict[str, Any], int], tuple[int, dict[str, Any], dict[str, str]]] = _post_json,
) -> dict[str, Any]:
    if not config.openrouter_api_key:
        return {"skipped": True, "skipReason": "missing_openrouter_key"}

    status, payload, _headers = http_post(
        config.openrouter_base_url,
        {
            "Authorization": f"Bearer {config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://apt.af5.org",
            "X-OpenRouter-Title": "apt PM manual eval monitoring",
        },
        {
            "model": config.openrouter_model,
            "messages": [{"role": "user", "content": _judge_prompt(case)}],
            "temperature": 0,
            "max_tokens": 220,
            "response_format": {"type": "json_object"},
        },
        30,
    )

    if status < 200 or status >= 300:
        return {
            "skipped": True,
            "skipReason": "openrouter_rate_limited" if status == 429 else f"openrouter_http_{status}",
        }

    content = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content")) or "{}"
    result = _normalize_judge(content)
    if "skipped" not in result:
        result["usage"] = payload.get("usage")
    return result


def _result_for(case: dict[str, Any], outcome: dict[str, Any], runner: str) -> dict[str, Any]:
    passed = outcome.get("pass") is True
    return {
        "id": case.get("id"),
        "lane": case.get("lane"),
        "scoreName": case.get("scoreName"),
        "runner": runner,
        "status": "pass" if passed else "fail",
        "scoreValue": outcome.get("score", 0),
        "comment": "Eval passed." if passed else "Eval failed.",
        "rationale": outcome.get("rationale"),
        "usage": outcome.get("usage"),
    }


def _skipped_result(case: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "id": case.get("id"),
        "lane": case.get("lane"),
        "scoreName": case.get("scoreName"),
        "runner": case.get("runner"),
        "status": "skipped",
        "scoreValue": 0,
        "skipReason": reason,
    }


def run_eval_suite(
    cases: list[dict[str, Any]],
    config: EvalConfig,
    judge: Callable[[dict[str, Any], EvalConfig], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    selected = select_eval_cases(cases, config)
    judge_fn = judge or judge_with_openrouter
    results: list[dict[str, Any]] = []
    llm_calls_attempted = 0
    llm_calls_skipped = 0

    for case in selected:
        if case.get("runner") == "deterministic":
            results.append(_result_for(case, _deterministic_check(case), "deterministic"))
            continue

        if not config.llm_enabled:
            llm_calls_skipped += 1
            results.append(_skipped_result(case, "llm_disabled"))
            continue

        if llm_calls_attempted >= config.llm_max_calls:
            llm_calls_skipped += 1
            results.append(_skipped_result(case, "llm_budget_exhausted"))
            continue

        llm_calls_attempted += 1
        outcome = judge_fn(case, config)
        if outcome.get("skipped"):
            llm_calls_skipped += 1
            results.append(_skipped_result(case, outcome.get("skipReason") or "llm_skipped"))
            continue
        results.append(_result_for(case, outcome, "giskard_oss_llm"))

    executed = [entry for entry in results if entry["status"] != "skipped"]
    token_usage = {"promptTokens": 0, "completionTokens": 0, "totalTokens": 0}
    for entry in results:
        usage = entry.get("usage") or {}
        token_usage["promptTokens"] += int(usage.get("prompt_tokens") or 0)
        token_usage["completionTokens"] += int(usage.get("completion_tokens") or 0)
        token_usage["totalTokens"] += int(usage.get("total_tokens") or 0)

    return {
        "run": {
            "mode": config.mode,
            "traceId": config.trace_id,
            "llmEnabled": config.llm_enabled,
            "llmMaxCalls": config.llm_max_calls,
            "openRouterModel": config.openrouter_model,
            "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "summary": {
            "total": len(executed),
            "passed": len([entry for entry in executed if entry["status"] == "pass"]),
            "failed": len([entry for entry in executed if entry["status"] == "fail"]),
            "skipped": len(results) - len(executed),
            "llmCallsAttempted": llm_calls_attempted,
            "llmCallsSkipped": llm_calls_skipped,
            "tokenUsage": token_usage,
        },
        "results": results,
    }


def build_langfuse_scores(result: dict[str, Any], trace_id: str | None = None, environment: str = "ci-manual") -> list[dict[str, Any]]:
    resolved_trace_id = trace_id or result["run"]["traceId"]
    scores = []
    for entry in result["results"]:
        if entry["status"] == "skipped":
            continue
        scores.append(
            {
                "id": f"{resolved_trace_id}-{entry['id']}",
                "traceId": resolved_trace_id,
                "name": entry["scoreName"],
                "value": entry["scoreValue"],
                "dataType": "NUMERIC",
                "environment": environment,
                "comment": f"{entry['status']}; runner={entry['runner']}; lane={entry['lane']}",
            }
        )
    return scores


def export_langfuse_scores(result: dict[str, Any], config: EvalConfig) -> dict[str, Any]:
    if not config.langfuse_export:
        return {"exported": False, "reason": "disabled"}
    if not config.langfuse_public_key or not config.langfuse_secret_key:
        return {"exported": False, "reason": "missing_credentials"}

    auth = base64.b64encode(f"{config.langfuse_public_key}:{config.langfuse_secret_key}".encode("utf-8")).decode("ascii")
    endpoint = f"{config.langfuse_base_url}/api/public/scores"
    for score in build_langfuse_scores(result, trace_id=config.trace_id, environment=config.environment):
        status, payload, _headers = _post_json(
            endpoint,
            {"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
            score,
            30,
        )
        if status < 200 or status >= 300:
            return {"exported": False, "reason": f"langfuse_http_{status}", "response": payload}
    return {"exported": True, "scoreCount": len(build_langfuse_scores(result, trace_id=config.trace_id, environment=config.environment))}


def load_cases(path: Path = DEFAULT_CASES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text())


def write_artifacts(result: dict[str, Any], config: EvalConfig, langfuse: dict[str, Any]) -> None:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {**result["run"], **result["summary"], "langfuse": langfuse}
    (config.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (config.output_dir / "results.json").write_text(json.dumps(result["results"], indent=2) + "\n")
    (config.output_dir / "langfuse-scores.json").write_text(
        json.dumps(build_langfuse_scores(result, trace_id=config.trace_id, environment=config.environment), indent=2) + "\n"
    )


def main(env: dict[str, str] | None = None) -> dict[str, Any]:
    env = env or os.environ
    config = parse_eval_config(env)
    cases = load_cases(Path(env.get("EVAL_CASES_PATH") or DEFAULT_CASES_PATH))
    result = run_eval_suite(cases, config)
    langfuse = export_langfuse_scores(result, config)
    write_artifacts(result, config, langfuse)
    print(json.dumps({**result["summary"], "mode": config.mode, "langfuse": langfuse}, indent=2))
    if config.ci_fail_on_eval and result["summary"]["failed"] > 0:
        sys.exit(1)
    return result


if __name__ == "__main__":
    main()
