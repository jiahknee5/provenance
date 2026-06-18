"""NLI entailment scoring — "is this claim entailed by its evidence?"

Default: a deterministic, number-aware lexical scorer. It is intentionally strict about
numbers and unsupported absolutes, because those are exactly the trap classes a
similarity-only judge is fooled by. Raw entailment here is *uncalibrated* — the
Calibrator (calibrate.py) turns it into a probability, which is why the architecture has
both stages.

Rich upgrade: microsoft/deberta-v3-large-mnli, used only when the optional deps + model
are importable. Its raw entailment prob feeds the same Calibrator.
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.common import config, textutil


@dataclass
class NLIResult:
    label: str          # "entailment" | "neutral" | "contradiction"
    entail_prob: float  # raw, uncalibrated P(entailed)
    reason: str = ""


class LexicalNLI:
    """Deterministic, number-aware entailment heuristic."""

    def score(self, claim: str, evidence: str) -> NLIResult:
        cov = textutil.coverage(claim, evidence)
        nums_ok = textutil.numbers_supported(claim, evidence)
        unsupported_sups = textutil.superlatives(claim) - textutil.superlatives(evidence)

        entail = cov
        label = "entailment" if cov >= 0.6 else "neutral"
        reason = f"coverage={cov:.2f}"

        if not nums_ok:
            entail = min(entail, 0.12)
            label = "contradiction"
            reason = "claim asserts a number not entailed by the source"
        elif unsupported_sups:
            entail = min(entail, 0.30)
            label = "neutral"
            reason = f"unsupported absolute(s): {sorted(unsupported_sups)}"
        elif cov >= 0.6:
            entail = max(entail, 0.80)

        return NLIResult(label=label, entail_prob=max(0.02, min(0.98, entail)), reason=reason)


class DebertaNLI:
    """microsoft/deberta-v3-large-mnli (optional). One-time ~1.6GB download on first use."""

    def __init__(self):
        from transformers import pipeline  # type: ignore
        self._pipe = pipeline("text-classification", model=config.DEBERTA_MODEL,
                              top_k=None, truncation=True)

    def score(self, claim: str, evidence: str) -> NLIResult:
        # MNLI premise=evidence, hypothesis=claim
        out = self._pipe({"text": evidence, "text_pair": claim})
        scores = {d["label"].lower(): d["score"] for d in out}
        p = float(scores.get("entailment", 0.0))
        label = max(scores, key=scores.get)
        return NLIResult(label=label, entail_prob=p, reason="deberta-v3-mnli")


def make_nli():
    if config.use_rich():
        try:
            return DebertaNLI()
        except Exception:
            pass  # fall back to deterministic — logged by the Gate, never silent in tests
    return LexicalNLI()
