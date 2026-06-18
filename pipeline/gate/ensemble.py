"""Diverse judge ensemble — selective prediction over multiple lenses.

The point of the ensemble (vs. one LLM-judge) is that different lenses fail differently,
so their agreement is a better calibrated signal than any single judge. The deterministic
lenses:
  * CoverageJudge   — semantic token support (number-BLIND; this is also the single-judge
                      baseline the Assurance Lab beats: a number-drifted claim looks fine).
  * NumericJudge    — every asserted number must be supported.
  * SuperlativeJudge — unsupported absolutes ("#1", "guaranteed") are not entailed.

Rich profile adds cross-family Ollama judges (Qwen + Nemotron) and, if a key is present,
Claude — genuine model-family diversity, all cached.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pipeline.common import config, textutil
from pipeline.common.cache import LLMCache


@dataclass
class EnsembleResult:
    mean_p: float
    votes: dict[str, float] = field(default_factory=dict)


# --- deterministic lenses ---------------------------------------------------
def coverage_judge(claim: str, evidence: str) -> float:
    """Number-blind similarity. The gameable single-judge baseline."""
    return round(textutil.coverage(claim, evidence), 4)


def numeric_judge(claim: str, evidence: str) -> float:
    if not textutil.extract_numbers(claim):
        return 0.85  # no numeric assertion to check
    return 0.95 if textutil.numbers_supported(claim, evidence) else 0.05


def superlative_judge(claim: str, evidence: str) -> float:
    unsupported = textutil.superlatives(claim) - textutil.superlatives(evidence)
    return 0.10 if unsupported else 0.90


class JudgeEnsemble:
    def __init__(self, cache: Optional[LLMCache] = None):
        self.cache = cache

    def judge(self, claim: str, evidence: str, escalate: bool = False) -> EnsembleResult:
        votes: dict[str, float] = {
            "coverage": coverage_judge(claim, evidence),
            "numeric": numeric_judge(claim, evidence),
            "superlative": superlative_judge(claim, evidence),
        }
        # cheap-first cascade: only spend LLM judges on uncertain claims (router-referee)
        if config.use_rich() and escalate:
            from pipeline.gate import llm
            for model in config.OLLAMA_JUDGE_MODELS:
                model = model.strip()
                if not model:
                    continue
                try:
                    votes[f"ollama:{model}"] = llm.ollama_judge(model, claim, evidence, self.cache)["p"]
                except Exception:
                    pass  # a down judge drops out; the deterministic lenses still vote
            if config.claude_available():
                try:
                    votes[f"claude"] = llm.claude_judge(claim, evidence, self.cache)["p"]
                except Exception:
                    pass
        mean_p = round(sum(votes.values()) / len(votes), 4)
        return EnsembleResult(mean_p=mean_p, votes=votes)


def single_judge_baseline(claim: str, evidence: str) -> float:
    """The Assurance Lab's baseline: one number-blind similarity judge."""
    return coverage_judge(claim, evidence)
