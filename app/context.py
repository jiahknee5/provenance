"""Shared pipeline context for the running app — one Library + Rules + Gate, with any
persisted demo state (legal-hold flips, source changes) applied at startup and the A/B
learnings (winning verified arm per segment) loaded for the website channel.

Server and scripts stay coherent through files: scripts write learnings.json / demo_state
/ the shared verdict cache; the app reads them.
"""
from __future__ import annotations

import json

from pipeline.common.config import RUNS_DIR
from pipeline.gate.gate import Gate
from pipeline.gate.rules import RulesEngine
from pipeline.library.library import ClaimsLibrary

LEARNINGS = RUNS_DIR / "learnings.json"
DEMO_STATE = RUNS_DIR / "demo_state.json"


class Ctx:
    def __init__(self):
        self.library = ClaimsLibrary.from_seed()
        self.rules = RulesEngine.load()
        self._apply_demo_state()
        self.gate = Gate(self.library, self.rules)

    def _apply_demo_state(self) -> None:
        if DEMO_STATE.exists():
            st = json.loads(DEMO_STATE.read_text())
            if st.get("hold"):
                self.rules.set_hold("mlr_hold_tco", True)
            for sc in st.get("source_changes", []):
                self.library.apply_source_change(sc["source_id"], sc["text"])

    def winner(self, segment: str) -> str:
        if LEARNINGS.exists():
            arm = json.loads(LEARNINGS.read_text()).get(segment)
            if arm:
                return arm.split("__")[-1]
        return "A"


_ctx: Ctx | None = None


def ctx() -> Ctx:
    global _ctx
    if _ctx is None:
        _ctx = Ctx()
    return _ctx


def reset_ctx() -> None:
    global _ctx
    _ctx = None
