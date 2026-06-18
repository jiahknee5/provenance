"""The Enrichment Gate — the "clear" step for personal data, mirroring the claim Gate.

A RawFact becomes a verdicted ProfileFact:
  * BLOCKED   — source not allow-listed, recipient didn't consent, fact is stale (age > TTL),
                or the key is PHI/PII-blocked. Never reaches a message.
  * DISCLAIMER— usable but inferred (account-level) — inlined with an "inferred" flag.
  * USABLE    — allow-listed + consented + fresh — may be inlined, basis on file.

The basis + ttl come from the human-owned enrichment-source policy in rules/helix_tenant.yaml
(HITL gate #2). A fact a human never authorized a source for cannot be used — by construction.
"""
from __future__ import annotations

import yaml

from pipeline.common import observe
from pipeline.common.config import RULES_DIR
from pipeline.enrichment.schemas import FactVerdict, ProfileFact, RawFact


def load_policy(path: str | None = None) -> dict:
    p = path or (RULES_DIR / "helix_tenant.yaml")
    cfg = yaml.safe_load(open(p))
    return cfg.get("enrichment", {})


class EnrichmentGate:
    def __init__(self, policy: dict | None = None):
        self.policy = policy if policy is not None else load_policy()
        self.allowed = {s["id"]: s for s in self.policy.get("allowed_sources", [])}
        self.blocked_keys = set(self.policy.get("blocked_keys", []))
        self.consent_required = bool(self.policy.get("consent_required", True))
        self.default_ttl = int(self.policy.get("default_ttl_seconds", 2592000))

    def policy_version(self) -> str:
        import hashlib
        import json
        return "ep_" + hashlib.sha256(
            json.dumps(self.policy, sort_keys=True, default=str).encode()).hexdigest()[:10]

    def evaluate(self, fact: RawFact, recipient) -> ProfileFact:
        reasons: list[str] = []
        src = self.allowed.get(fact.source)

        if src is None:
            verdict, basis, kind, ttl = FactVerdict.BLOCKED, "", "", 0
            reasons.append(f"source '{fact.source}' is not in the enrichment allow-list")
        else:
            basis = src.get("basis", "")
            kind = src.get("kind", "")
            ttl = int(src.get("ttl_seconds", self.default_ttl))
            base = FactVerdict(src.get("verdict", "usable"))
            if self.consent_required and not getattr(recipient, "consent", False):
                verdict = FactVerdict.BLOCKED
                reasons.append("recipient did not consent")
            elif fact.key in self.blocked_keys:
                verdict = FactVerdict.BLOCKED
                reasons.append(f"key '{fact.key}' is PHI/PII-blocked")
            elif fact.age_seconds > ttl:
                verdict = FactVerdict.BLOCKED
                reasons.append(f"stale: age {fact.age_seconds}s > ttl {ttl}s")
            else:
                verdict = base
                if verdict == FactVerdict.DISCLAIMER:
                    reasons.append("account-level inferred signal — flag as inferred")

        pf = ProfileFact(
            key=fact.key, value=fact.value, source=fact.source, confidence=fact.confidence,
            age_seconds=fact.age_seconds, detail=fact.detail,
            fact_id=ProfileFact.make_id(recipient.recipient_id, fact.key, fact.source),
            recipient_id=recipient.recipient_id, source_kind=kind, basis=basis,
            ttl_seconds=ttl, verdict=verdict, reasons=reasons,
        )
        observe.emit("enrichment", "DECISION", node="enrich_gate",
                     tool=f"enrichment-source policy {self.policy_version()}",
                     detail=f"{fact.key} ({fact.source}) → {verdict.value}"
                            + (f": {reasons[0]}" if reasons else ""),
                     input={"key": fact.key, "source": fact.source, "age_seconds": fact.age_seconds},
                     decision={"verdict": verdict.value, "basis": basis, "reasons": reasons},
                     claim_id=pf.fact_id)
        return pf
