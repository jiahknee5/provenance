"""Model clients for the rich inference profile (optional).

Ollama (local, free) provides two cross-family judges; Claude is enabled only when a key
is present. Every call is cached by input hash via LLMCache, so the rich profile is just
as reproducible as the deterministic one once the cache is warm. The deterministic
default profile never calls these — the demo runs fully offline without them.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from pipeline.common import config
from pipeline.common.cache import LLMCache

_JUDGE_PROMPT = (
    "You are a strict claim verifier for regulated marketing copy. "
    "Decide whether the CLAIM is fully supported (entailed) by the EVIDENCE. "
    "Reply with a single JSON object: "
    '{{"label": "ENTAILED|NEUTRAL|CONTRADICTED", "p": <0..1 confidence the claim is entailed>}}.\n\n'
    "EVIDENCE:\n{evidence}\n\nCLAIM:\n{claim}\n"
)


def _parse_label(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            label = str(obj.get("label", "NEUTRAL")).upper()
            p = float(obj.get("p", 0.5))
            return {"label": label, "p": max(0.0, min(1.0, p))}
        except Exception:
            pass
    up = text.upper()
    if "CONTRADICT" in up:
        return {"label": "CONTRADICTED", "p": 0.1}
    if "ENTAIL" in up:
        return {"label": "ENTAILED", "p": 0.85}
    return {"label": "NEUTRAL", "p": 0.5}


def ollama_judge(model: str, claim: str, evidence: str, cache: Optional[LLMCache] = None) -> dict:
    own = cache is None
    cache = cache or LLMCache()
    key = LLMCache.hash_input("ollama", model, claim, evidence)

    def compute() -> dict:
        import httpx
        prompt = _JUDGE_PROMPT.format(evidence=evidence, claim=claim)
        r = httpx.post(
            f"{config.OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0}, "format": "json"},
            timeout=120,
        )
        r.raise_for_status()
        out = _parse_label(r.json().get("response", ""))
        out["model"] = model
        return out

    try:
        result = cache.get_or_compute(key, compute)
    finally:
        if own:
            cache.close()
    return result


def claude_judge(claim: str, evidence: str, cache: Optional[LLMCache] = None) -> dict:
    own = cache is None
    cache = cache or LLMCache()
    key = LLMCache.hash_input("claude", config.CLAUDE_JUDGE_MODEL, claim, evidence)

    def compute() -> dict:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.CLAUDE_JUDGE_MODEL,
            max_tokens=128,
            temperature=0,
            messages=[{"role": "user",
                       "content": _JUDGE_PROMPT.format(evidence=evidence, claim=claim)}],
        )
        out = _parse_label(msg.content[0].text)
        out["model"] = config.CLAUDE_JUDGE_MODEL
        return out

    try:
        result = cache.get_or_compute(key, compute)
    finally:
        if own:
            cache.close()
    return result
