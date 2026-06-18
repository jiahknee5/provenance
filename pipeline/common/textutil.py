"""Deterministic text utilities shared by the Library, the Gate, and the Assurance Lab.

The number-awareness here is load-bearing: a number-drifted claim ("47%" -> "57%") is
nearly identical lexically, so a similarity-only judge passes it. Extracting and
comparing the actual numbers is what lets the ensemble catch it — the honest reason the
Gate beats a single judge on the number-drift trap class.
"""
from __future__ import annotations

import re

_STOP = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "by", "with", "your",
    "you", "we", "our", "is", "are", "was", "were", "be", "been", "it", "its", "that",
    "this", "at", "as", "from", "over", "per", "up", "than", "their", "they", "has",
    "have", "had", "can", "will", "more", "most", "into", "across",
}

# words that assert an unsupported absolute / superlative / guarantee
SUPERLATIVE_TOKENS = {
    "guaranteed", "guarantee", "best", "#1", "number-one", "only", "always", "never",
    "unmatched", "unbeatable", "leading", "first", "top", "100%", "zero-risk", "risk-free",
    "every", "all", "none", "fastest", "cheapest", "safest", "perfect",
}

_NUM_RE = re.compile(r"(?<![\w])(\d+(?:\.\d+)?)\s*(%|percent|x|hours?|days?|months?|weeks?|minutes?|m|k|bps)?", re.I)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9#]+", text.lower())


def content_tokens(text: str) -> set[str]:
    # exclude pure-digit tokens so word-coverage is "number-blind" — the asserted numbers
    # are checked separately by numbers_supported(). This is what makes a similarity-only
    # judge look fine on a number-drifted claim while the numeric lens catches it.
    return {t for t in tokenize(text) if t not in _STOP and len(t) > 1 and not t.isdigit()}


def extract_numbers(text: str) -> list[tuple[float, str]]:
    """Return [(value, normalized_unit), ...]. Unit '' when bare."""
    out: list[tuple[float, str]] = []
    for m in _NUM_RE.finditer(text):
        val = float(m.group(1))
        unit = (m.group(2) or "").lower()
        unit = {"percent": "%"}.get(unit, unit)
        unit = re.sub(r"s$", "", unit) if unit in ("hours", "days", "months", "weeks", "minutes") else unit
        out.append((val, unit))
    return out


def superlatives(text: str) -> set[str]:
    toks = set(tokenize(text)) | {w for w in re.findall(r"#?\w+%?", text.lower())}
    return {s for s in SUPERLATIVE_TOKENS if s in toks or s in text.lower()}


def coverage(claim: str, evidence: str) -> float:
    """Fraction of the claim's content tokens that appear in the evidence."""
    c = content_tokens(claim)
    if not c:
        return 1.0
    e = content_tokens(evidence)
    return len(c & e) / len(c)


def numbers_supported(claim: str, evidence: str, tol: float = 1e-6) -> bool:
    """Every number the claim asserts must be matched (value+unit) in the evidence."""
    enums = extract_numbers(evidence)
    for cval, cunit in extract_numbers(claim):
        ok = any(abs(cval - ev) <= max(tol, 0.01 * abs(cval)) and (cunit == eu or cunit == "" or eu == "")
                 for ev, eu in enums)
        if not ok:
            return False
    return True
