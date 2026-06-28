# Manual Eval Monitoring

Updated June 28, 2026.

This repo has a manual, non-blocking GitLab job named `eval_monitoring`.

The default mode is deterministic and uses zero external model calls:

```text
EVAL_MODE=deterministic
EVAL_LLM_ENABLED=false
LANGFUSE_EXPORT=false
CI_FAIL_ON_EVAL=false
```

First OpenRouter-backed smoke probe:

```text
EVAL_MODE=smoke
EVAL_LLM_ENABLED=true
EVAL_LLM_MAX_CALLS=18
EVAL_SAMPLE_LIMIT=6
OPENROUTER_MODEL=google/gemini-2.5-flash-lite
LANGFUSE_EXPORT=true
CI_FAIL_ON_EVAL=false
```

Required GitLab variables:

```text
OPENROUTER_API_KEY
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
```

Artifacts:

- `eval-results/summary.json`
- `eval-results/results.json`
- `eval-results/langfuse-scores.json`

Langfuse export sends score names, numeric values, lane IDs, runner type, and CI trace ID only.
It does not send raw enrichment data, private profile text, passwords, source URLs, or full generated copy.

Keep LLM-backed runs manual until several smoke runs show stable results, acceptable cost, and low false positives.
