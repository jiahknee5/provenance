"""Shared pipeline context for the running app — one Library + Rules + Gate, with any
persisted demo state (legal-hold flips, source changes) applied at startup and the A/B
learnings (winning verified arm per segment) loaded for the website channel.

Server and scripts stay coherent through files: scripts write learnings.json / demo_state
/ the shared verdict cache; the app reads them.
"""
from __future__ import annotations

import json

from pipeline.common.config import RULES_DIR, RUNS_DIR
from pipeline.gate.gate import Gate
from pipeline.gate.rules import RulesEngine
from pipeline.library.library import ClaimsLibrary

LEARNINGS = RUNS_DIR / "learnings.json"
DEMO_STATE = RUNS_DIR / "demo_state.json"

# Each tenant gates with its OWN compliance rules (holds / blocks / disclaimers). The claims
# library is shared; the per-tenant difference is the rule set, which is the load-bearing
# compliance layer — so a hold/block in one tenant never affects another's action pool.
TENANT_RULES = {"helix": "helix_tenant.yaml", "academy": "academy_tenant.yaml"}


class Ctx:
    def __init__(self):
        self.library = ClaimsLibrary.from_seed()
        self.rules = RulesEngine.load()
        self._apply_demo_state()
        self.gate = Gate(self.library, self.rules)
        self._live: dict = {}
        self._gates: dict = {"helix": self.gate}   # helix gate already carries demo_state

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

    def gate_for(self, tenant: str = "helix") -> Gate:
        """The Gate for a tenant — its OWN compliance rules over the (shared) claims library.
        A hold/block in one tenant's rules changes only that tenant's verdicts and pool."""
        if tenant not in self._gates:
            fname = TENANT_RULES.get(tenant, "helix_tenant.yaml")
            self._gates[tenant] = Gate(self.library, RulesEngine.load(RULES_DIR / fname))
        return self._gates[tenant]

    def live_for(self, tenant: str = "helix"):
        """The online bandit fed by REAL /site traffic — gated by THIS tenant's rules, so its
        action pool reflects the tenant's own compliance state. Keyed by tenant so tenants
        learn independently. Built lazily and cached per tenant."""
        if tenant not in self._live:
            from pipeline.generation.variants import build_action_pool
            from pipeline.optimizer.live import LiveOptimizer
            pool, _ = build_action_pool(self.gate_for(tenant), "website", f"live_{tenant}")
            self._live[tenant] = LiveOptimizer(pool, channel="website", tenant=tenant)
        return self._live[tenant]

    @property
    def live(self):
        """The default (Helix) tenant's live optimizer."""
        return self.live_for("helix")


_ctx: Ctx | None = None


def ctx() -> Ctx:
    global _ctx
    if _ctx is None:
        _ctx = Ctx()
    return _ctx


def reset_ctx() -> None:
    global _ctx
    _ctx = None
