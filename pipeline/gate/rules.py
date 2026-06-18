"""Compliance rules engine — the "clear" step (legal) of the Gate.

Legal authors rules once; every message is then auto-checked. Rules can only make a
verdict MORE restrictive (green -> amber -> red), never less. `rules_version` is the hash
of the *active* rule set, so flipping the MLR hold changes the version, which changes the
verdict-cache key and forces a re-Gate — the legal-hold demo (T2).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Optional

import yaml

from pipeline.common.config import RULES_DIR
from pipeline.common.schemas import ClaimNode, Verdict

_SEVERITY = {None: 0, Verdict.AMBER: 1, Verdict.RED: 2}


@dataclass
class RuleOutcome:
    verdict: Optional[Verdict] = None      # None = rules don't constrain (pass through to NLI)
    flags: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


class RulesEngine:
    def __init__(self, cfg: dict):
        self.cfg = cfg

    @classmethod
    def load(cls, path: Optional[str] = None) -> "RulesEngine":
        p = path or (RULES_DIR / "helix_tenant.yaml")
        return cls(yaml.safe_load(open(p)))

    # ---- versioning: hash the ACTIVE rule set ------------------------------
    def rules_version(self) -> str:
        active = {
            "holds": [{"id": h["id"], "claim_id": h["claim_id"], "active": bool(h.get("active"))}
                      for h in self.cfg.get("holds", [])],
            "blocks": [b["id"] for b in self.cfg.get("blocks", [])],
            "disclaimers": [d["id"] for d in self.cfg.get("disclaimers", [])],
        }
        h = hashlib.sha256(json.dumps(active, sort_keys=True).encode()).hexdigest()[:12]
        return "r_" + h

    def set_hold(self, hold_id: str, active: bool) -> str:
        for h in self.cfg.get("holds", []):
            if h["id"] == hold_id:
                h["active"] = active
        return self.rules_version()

    # ---- application -------------------------------------------------------
    def apply(self, claim_text: str, claim: Optional[ClaimNode]) -> RuleOutcome:
        out = RuleOutcome()
        text = claim_text.lower()

        # holds key on claim_id (only fire for an identified library claim)
        if claim is not None:
            for h in self.cfg.get("holds", []):
                if h.get("active") and h["claim_id"] == claim.claim_id:
                    self._raise(out, Verdict(h["verdict"]), h["id"], h["reason"])

        # blocks key on claim text patterns
        for b in self.cfg.get("blocks", []):
            if re.search(b["pattern"], text):
                self._raise(out, Verdict(b["verdict"]), b["id"], b["reason"])

        # disclaimers key on the claim's rule_tags
        if claim is not None:
            for d in self.cfg.get("disclaimers", []):
                if d["rule_tag"] in claim.rule_tags:
                    self._raise(out, Verdict(d["verdict"]), d["id"], d["reason"])

        return out

    @staticmethod
    def _raise(out: RuleOutcome, verdict: Verdict, flag: str, reason: str) -> None:
        out.flags.append(flag)
        out.reasons.append(reason)
        if _SEVERITY[verdict] > _SEVERITY[out.verdict]:
            out.verdict = verdict
