"""Fact-audit — the Assurance Lab, applied to enrichment.

Just as the claim Assurance Lab mutates verified claims into traps and checks the Gate
catches them, this mutates facts into the four ways a personal fact can be un-shippable and
checks the Enrichment Gate blocks them:
  * disallowed_source — a source no human allow-listed (e.g. scraped LinkedIn / a bought list)
  * stale             — past its source TTL
  * phi_key           — a PHI/PII key that may never be inlined
  * non_consent       — the recipient never consented
Plus a clean, consented, fresh fact (label 0) for the false-block rate. Catch-rate here is
the structural proof that ungated personal data cannot reach a message.
"""
from __future__ import annotations

from dataclasses import dataclass

from pipeline.common import observe
from pipeline.enrichment.gate import EnrichmentGate
from pipeline.enrichment.schemas import FactVerdict, RawFact


@dataclass
class FactTrap:
    trap_id: str
    fact: RawFact
    mutation: str
    label: int        # 1 = should be blocked, 0 = clean (should be inlinable)
    consent: bool = True


def generate() -> list[FactTrap]:
    return [
        FactTrap("clean", RawFact(key="recent_news", value="opened a new facility",
                                  source="company_news_rss"), "clean", 0),
        FactTrap("disallowed", RawFact(key="seniority", value="VP",
                                       source="scraped_linkedin"), "disallowed_source", 1),
        FactTrap("stale", RawFact(key="recent_news", value="old headline",
                                  source="company_news_rss", age_seconds=10_000_000),
                 "stale", 1),
        FactTrap("phi", RawFact(key="diagnosis", value="redacted",
                                source="firmographic_sim"), "phi_key", 1),
        FactTrap("nonconsent", RawFact(key="intent_topic", value="ROI",
                                       source="intent_sim"), "non_consent", 1, consent=False),
    ]


def run_fact_audit(gate: EnrichmentGate, recipient) -> dict:
    import copy
    traps = generate()
    items = []
    for t in traps:
        r = recipient
        if not t.consent:
            r = copy.copy(recipient)
            try:
                r.consent = False
            except Exception:
                r = recipient.model_copy(update={"consent": False})
        pf = gate.evaluate(t.fact, r)
        blocked = pf.verdict == FactVerdict.BLOCKED
        items.append({"trap_id": t.trap_id, "mutation": t.mutation, "label": t.label,
                      "verdict": pf.verdict.value, "blocked": blocked,
                      "caught": blocked if t.label == 1 else (not blocked),
                      "reasons": pf.reasons})
    bad = [it for it in items if it["label"] == 1]
    clean = [it for it in items if it["label"] == 0]
    catch_rate = round(sum(it["blocked"] for it in bad) / len(bad), 4) if bad else 0.0
    false_block = round(sum(it["blocked"] for it in clean) / len(clean), 4) if clean else 0.0
    result = {"n_traps": len(bad), "n_clean": len(clean),
              "catch_rate": catch_rate, "false_block": false_block, "items": items}
    observe.emit("assurance", "DECISION", node="fact_audit",
                 tool="enrichment fact-trap harness",
                 detail=f"fact-gate caught {catch_rate*100:.0f}% of un-shippable facts at "
                        f"{false_block*100:.0f}% false-block",
                 decision={"catch_rate": catch_rate, "false_block": false_block},
                 output={"by_trap": {it["trap_id"]: it["verdict"] for it in items}})
    return result
