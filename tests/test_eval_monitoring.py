from __future__ import annotations

import json

from scripts.eval_monitoring import (
    build_langfuse_scores,
    judge_with_openrouter,
    parse_eval_config,
    run_eval_suite,
    select_eval_cases,
)


SAMPLE_CASES = [
    {
        "id": "pm_golden_summary",
        "runner": "deterministic",
        "scoreName": "pm_golden_summary",
        "lane": "golden_evals",
        "input": {"summary": {"passed": 18, "total": 18}},
    },
    {
        "id": "gate_blocks_unsupported_claim",
        "runner": "deterministic",
        "scoreName": "gate_blocks_unsupported_claim",
        "lane": "assurance",
        "input": {"verdict": "blocked", "selected": False},
    },
    {
        "id": "winner_gate_cleared",
        "runner": "deterministic",
        "scoreName": "winner_gate_cleared",
        "lane": "optimizer",
        "input": {"selectedArm": {"state": "leader", "selectable": True}},
    },
    {
        "id": "private_signal_redaction",
        "runner": "deterministic",
        "scoreName": "private_signal_leakage",
        "lane": "enrichment",
        "input": {
            "artifact": "Imported 4 enrichment facts into summarized basis cards.",
            "forbidden": ["linkedin.com/in/", "raw_pdf_text", "password"],
        },
    },
    {
        "id": "claim_support_judge",
        "runner": "giskard_oss_llm",
        "scoreName": "claim_support",
        "lane": "copy_generation",
        "input": {
            "copy": "Northwind completed a clinical operations rollout with Helix.",
            "evidence": "Case study says Northwind completed a clinical operations rollout with Helix.",
        },
    },
    {
        "id": "surface_policy_respected",
        "runner": "giskard_oss_llm",
        "scoreName": "surface_policy_respected",
        "lane": "copy_generation",
        "input": {
            "copy": "Northwind appears to be investing in AI operations workflows.",
            "policy": "allude",
            "forbidden": "Must not state unsupported hiring claims as fact.",
        },
    },
]


def test_parse_eval_config_caps_paid_llm_runs() -> None:
    deterministic = parse_eval_config({"EVAL_MODE": "deterministic"})

    assert deterministic.mode == "deterministic"
    assert deterministic.llm_enabled is False
    assert deterministic.llm_max_calls == 0

    config = parse_eval_config(
        {
            "EVAL_MODE": "smoke",
            "EVAL_LLM_ENABLED": "true",
            "EVAL_LLM_MAX_CALLS": "999",
            "EVAL_SAMPLE_LIMIT": "999",
        }
    )

    assert config.mode == "smoke"
    assert config.llm_enabled is True
    assert config.llm_max_calls == 18
    assert config.sample_limit == 6
    assert config.openrouter_model == "google/gemini-2.5-flash-lite"


def test_select_eval_cases_keeps_deterministic_mode_zero_cost() -> None:
    selected = select_eval_cases(SAMPLE_CASES, parse_eval_config({"EVAL_MODE": "deterministic"}))

    assert [case["runner"] for case in selected] == ["deterministic"] * 4
    assert [case["id"] for case in selected] == [
        "pm_golden_summary",
        "gate_blocks_unsupported_claim",
        "winner_gate_cleared",
        "private_signal_redaction",
    ]


def test_run_eval_suite_caps_optional_judges() -> None:
    calls = []

    def judge(case, config):
        calls.append(case["id"])
        return {"pass": True, "score": 0.91, "rationale": "Synthetic fixture is supported."}

    result = run_eval_suite(
        SAMPLE_CASES,
        parse_eval_config(
            {
                "EVAL_MODE": "smoke",
                "EVAL_LLM_ENABLED": "true",
                "EVAL_LLM_MAX_CALLS": "1",
            }
        ),
        judge=judge,
    )

    assert calls == ["claim_support_judge"]
    assert result["summary"]["total"] == 5
    assert result["summary"]["passed"] == 5
    assert result["summary"]["failed"] == 0
    assert result["summary"]["skipped"] == 1
    assert result["summary"]["llmCallsAttempted"] == 1
    assert result["summary"]["llmCallsSkipped"] == 1
    skipped = [entry for entry in result["results"] if entry["status"] == "skipped"]
    assert skipped[0]["skipReason"] == "llm_budget_exhausted"


def test_langfuse_scores_are_idempotent_and_sanitized() -> None:
    result = run_eval_suite(SAMPLE_CASES, parse_eval_config({"EVAL_MODE": "deterministic"}))
    scores = build_langfuse_scores(result, trace_id="pm-ci-eval-test", environment="ci-manual")

    assert scores[0]["id"] == "pm-ci-eval-test-pm_golden_summary"
    assert scores[0]["traceId"] == "pm-ci-eval-test"
    assert scores[0]["dataType"] == "NUMERIC"
    assert json.dumps(scores).find("Northwind completed") == -1
    assert json.dumps(scores).find("linkedin.com/in/") == -1


def test_openrouter_rate_limit_is_skipped_provider_noise() -> None:
    def http_post(url, headers, payload, timeout):
        return 429, {}, {}

    response = judge_with_openrouter(
        SAMPLE_CASES[4],
        parse_eval_config(
            {
                "EVAL_MODE": "smoke",
                "EVAL_LLM_ENABLED": "true",
                "OPENROUTER_API_KEY": "test-key",
            }
        ),
        http_post=http_post,
    )

    assert response == {"skipped": True, "skipReason": "openrouter_rate_limited"}
