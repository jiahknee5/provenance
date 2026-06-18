"""Claim decomposer — pull the atomic factual claims out of a rendered message and bind
each to its library claim where one matches.

A sentence is treated as a claim if it either (a) matches an approved library claim by
token coverage (the verbatim slot-filled claims do), or (b) asserts a guarantee/superlative
(the planted lie does, and those patterns are exactly what compliance must catch).
Greetings and CTAs ("Book a 20-minute demo") match neither and are skipped.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from pipeline.common import observe, textutil
from pipeline.common.schemas import ClaimNode
from pipeline.library.library import ClaimsLibrary

MATCH_THRESHOLD = 0.7


@dataclass
class DecomposedClaim:
    text: str
    claim: Optional[ClaimNode]


def _split_sentences(message: str) -> list[str]:
    parts: list[str] = []
    for line in message.replace("\r", "").split("\n"):
        for s in re.split(r"(?<=[.!?])\s+", line):
            s = s.strip()
            if s:
                parts.append(s)
    return parts


class Decomposer:
    def __init__(self, library: ClaimsLibrary):
        self.library = library

    def _best_claim(self, sentence: str) -> tuple[Optional[ClaimNode], float]:
        best, best_cov = None, 0.0
        for c in self.library.claims_in_date():
            cov = textutil.coverage(c.text, sentence)  # how much of the claim is asserted
            if cov > best_cov:
                best, best_cov = c, cov
        return best, best_cov

    def decompose(self, message: str) -> list[DecomposedClaim]:
        out: list[DecomposedClaim] = []
        for sent in _split_sentences(message):
            claim, cov = self._best_claim(sent)
            has_absolute = bool(textutil.superlatives(sent))
            if cov >= MATCH_THRESHOLD:
                out.append(DecomposedClaim(text=sent, claim=claim))
            elif has_absolute:
                out.append(DecomposedClaim(text=sent, claim=None))  # unverified assertion (the lie)
        observe.emit("gate", "OUTPUT", node="decompose", tool="coverage matcher + superlative detector",
                     detail=f"{len(out)} checkable claim(s) extracted",
                     input={"message": message},
                     output=[{"sentence": d.text, "claim_id": d.claim.claim_id if d.claim else None}
                             for d in out])
        return out
