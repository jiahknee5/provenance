"""Contextual bandit — per-segment Thompson sampling over the verified action pool.

The context is the recipient's micro-segment; within a segment the bandit samples each
active arm's Beta posterior and pulls the best. It can ONLY ever pull arms that are in the
pool, and the Gate decides what is in the pool — so a blocked variant is unreachable by
construction, not by a special case here.
"""
from __future__ import annotations

import random

from pipeline.common.store import ActionPool, PosteriorStore


class ThompsonBandit:
    def __init__(self, pool: ActionPool, posteriors: PosteriorStore, rng: random.Random):
        self.pool = pool
        self.post = posteriors
        self.rng = rng

    def select(self, segment: str) -> str | None:
        arms = self.pool.active(segment)
        if not arms:
            return None
        best, best_theta = None, -1.0
        for arm in arms:
            a, b = self.post.get(segment, arm)
            theta = self.rng.betavariate(a, b)
            if theta > best_theta:
                best, best_theta = arm, theta
        return best

    def update(self, segment: str, arm: str, reward: int) -> None:
        a, b = self.post.get(segment, arm)
        if reward == 1:
            a += 1
        elif reward == 0:
            b += 1
        else:                       # unsubscribe = hard negative
            b += 3
        self.post.set(segment, arm, a, b)

    def posterior_mean(self, segment: str, arm: str) -> float:
        a, b = self.post.get(segment, arm)
        return a / (a + b)
