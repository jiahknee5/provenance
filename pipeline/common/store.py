"""Two first-class, mutable runtime objects: the action pool and the posterior store.

ActionPool — the set of Gate-cleared variant ids per segment, the ONLY arms the bandit
may pull. It is mutable because Drift's whole job is to mutate it (pause invalidated
variants, unblock newly-cleared ones). A blocked/unverified variant is never added — the
truth boundary is enforced at pool-construction, not by a downstream filter.

PosteriorStore — persisted bandit posteriors (Beta params per arm per segment), so
campaign #2 can warm-start from campaign #1 instead of cold.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from pipeline.common.config import RUNS_DIR


class ActionPool:
    def __init__(self, campaign: str, channel: str):
        self.campaign = campaign
        self.channel = channel
        self.segments: dict[str, list[str]] = {}   # segment -> cleared variant_ids
        self.paused: set[str] = set()               # drift-invalidated variant_ids

    def add(self, segment: str, variant_id: str) -> None:
        self.segments.setdefault(segment, [])
        if variant_id not in self.segments[segment]:
            self.segments[segment].append(variant_id)

    def pause(self, variant_ids: Iterable[str]) -> None:
        self.paused.update(variant_ids)

    def unblock(self, variant_ids: Iterable[str]) -> None:
        self.paused.difference_update(variant_ids)

    def active(self, segment: str) -> list[str]:
        """The arms the bandit may actually pull right now."""
        return [v for v in self.segments.get(segment, []) if v not in self.paused]

    def all_variant_ids(self) -> set[str]:
        return {v for vs in self.segments.values() for v in vs}

    # --- persistence ---
    def _path(self) -> Path:
        return RUNS_DIR / f"pool_{self.campaign}_{self.channel}.json"

    def save(self) -> None:
        self._path().write_text(json.dumps(
            {"campaign": self.campaign, "channel": self.channel,
             "segments": self.segments, "paused": sorted(self.paused)}, indent=2))

    @classmethod
    def load(cls, campaign: str, channel: str) -> "ActionPool":
        p = cls(campaign, channel)
        raw = json.loads((RUNS_DIR / f"pool_{campaign}_{channel}.json").read_text())
        p.segments = raw["segments"]
        p.paused = set(raw["paused"])
        return p


class PosteriorStore:
    """Beta(alpha, beta) posteriors per segment per arm, for Thompson sampling."""

    def __init__(self, campaign: str, channel: str):
        self.campaign = campaign
        self.channel = channel
        # segment -> arm -> [alpha, beta]
        self.params: dict[str, dict[str, list[float]]] = {}

    def get(self, segment: str, arm: str) -> list[float]:
        return self.params.setdefault(segment, {}).setdefault(arm, [1.0, 1.0])

    def set(self, segment: str, arm: str, alpha: float, beta: float) -> None:
        self.params.setdefault(segment, {})[arm] = [alpha, beta]

    def warm_start_from(self, other: "PosteriorStore", decay: float = 0.5) -> None:
        """Carry prior campaign's posteriors forward as a *prior* (counts decayed, so
        new evidence can still move them). Keeps Beta(1,1) baseline."""
        for seg, arms in other.params.items():
            for arm, (a, b) in arms.items():
                self.set(seg, arm, 1.0 + (a - 1.0) * decay, 1.0 + (b - 1.0) * decay)

    def _path(self) -> Path:
        return RUNS_DIR / f"posteriors_{self.campaign}_{self.channel}.json"

    def save(self) -> None:
        self._path().write_text(json.dumps(
            {"campaign": self.campaign, "channel": self.channel, "params": self.params},
            indent=2))

    @classmethod
    def load(cls, campaign: str, channel: str) -> "PosteriorStore":
        ps = cls(campaign, channel)
        ps.params = json.loads(
            (RUNS_DIR / f"posteriors_{campaign}_{channel}.json").read_text())["params"]
        return ps
