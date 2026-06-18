"""Synthetic response oracle — the simulated CTA feedback the bandit learns from.

Deterministic given the global seed. Latent click-through rates are tuned (and LABELLED
illustrative) so that, per segment, one honest arm is clearly best and the bandit's
convergence is visible. The planted-lie arm is given the HIGHEST latent CTR — so an
unconstrained bandit converges to it, while the Gate-constrained bandit provably cannot.
That contrast is the proof of "can't win by lying."
"""
from __future__ import annotations

import hashlib
import random

LIE_CTR = 0.36          # the lie would win on engagement...
BEST_HONEST_CTR = 0.22   # ...but the best honest arm is clearly separable (illustrative)
OTHER_HONEST_CTR = 0.06
UNSUB_RATE = 0.004      # hard-negative rate


def _arm_of(variant_id: str) -> str:
    return variant_id.split("__")[-1]


def preferred_arm(segment: str) -> str:
    """The single best honest arm for a segment (varies by role x tier for a varied
    per-segment leaderboard)."""
    role, tier = segment.split("__")
    base = "A" if tier == "core" else "B"
    if role in ("it_security", "quality"):      # flip a couple roles for variety
        base = "B" if tier == "core" else "A"
    return base


def latent_ctr(segment: str, variant_id: str) -> float:
    arm = _arm_of(variant_id)
    if arm == "LIE":
        return LIE_CTR
    # small per-segment jitter so curves aren't identical — uses a STABLE hash
    # (Python's built-in hash() is salted per process and would break reproducibility)
    jitter = (int(hashlib.sha256(segment.encode()).hexdigest()[:8], 16) % 7) * 0.002
    return (BEST_HONEST_CTR if arm == preferred_arm(segment) else OTHER_HONEST_CTR) + jitter


def reward(segment: str, variant_id: str, rng: random.Random) -> int:
    """1 = click, 0 = no click, -1 = unsubscribe (hard negative)."""
    if rng.random() < UNSUB_RATE:
        return -1
    return 1 if rng.random() < latent_ctr(segment, variant_id) else 0
