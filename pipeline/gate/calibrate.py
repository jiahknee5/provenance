"""Isotonic calibration via pool-adjacent-violators (PAV) — no sklearn dependency.

Turns a raw entailment/agreement score into a calibrated probability: "when we say 0.9,
we're right ~90% of the time." The Assurance Lab fits this on a labeled mix of verified
claims + adversarial traps, then reports ECE / a reliability diagram. Unfit, it is the
identity (so the Gate works before any calibration data exists).
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field


@dataclass
class IsotonicCalibrator:
    xs: list[float] = field(default_factory=list)   # sorted score thresholds
    ys: list[float] = field(default_factory=list)   # calibrated probabilities
    fitted: bool = False

    def fit(self, scores: list[float], labels: list[int]) -> "IsotonicCalibrator":
        if not scores:
            return self
        pairs = sorted(zip(scores, labels), key=lambda p: p[0])
        # PAV: blocks of (sum_label, count, x_right)
        blocks: list[list[float]] = []
        for x, y in pairs:
            blocks.append([float(y), 1.0, x])
            while len(blocks) >= 2 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
                s2, c2, _ = blocks.pop()
                blocks[-1][0] += s2
                blocks[-1][1] += c2
                blocks[-1][2] = x
        self.xs, self.ys = [], []
        for s, c, xr in blocks:
            self.xs.append(xr)
            self.ys.append(s / c)
        self.fitted = True
        return self

    def predict(self, score: float) -> float:
        if not self.fitted or not self.xs:
            return max(0.0, min(1.0, score))
        i = bisect_right(self.xs, score)
        if i == 0:
            return self.ys[0]
        if i >= len(self.xs):
            return self.ys[-1]
        # linear interpolate between the two surrounding calibration points
        x0, x1 = self.xs[i - 1], self.xs[i]
        y0, y1 = self.ys[i - 1], self.ys[i]
        if x1 == x0:
            return y1
        return y0 + (y1 - y0) * (score - x0) / (x1 - x0)
