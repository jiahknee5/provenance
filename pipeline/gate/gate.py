"""The Gate — decompose -> retrieve -> NLI -> ensemble -> calibrate -> rules -> ledger.

Idempotent and pure w.r.t. (claim_id, source_version, rules_version): the verdict cache
means each unique claim is Gated once, never per user. Drift re-Gates only the claims
whose source_version changed (cache miss); everything else hits the cache. The
`compute_calls` / `verified_keys` spy is what the drift test asserts surgical
re-verification against.

Decision logic: numeric + superlative are *veto* lenses; coverage + NLI (+ any LLM
judges) are *support*. entail_raw = min(mean(support), min(vetoes)). Rules can only make a
verdict more restrictive. A blocked claim is RED — it never becomes a sendable arm.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from pipeline.common import observe
from pipeline.common.cache import LLMCache, VerdictCache
from pipeline.common.schemas import (ClaimVerdict, MessageLedger, Recipient, Variant,
                                     Verdict)
from pipeline.gate.calibrate import IsotonicCalibrator
from pipeline.gate.decompose import Decomposer
from pipeline.gate.ensemble import EnsembleResult, JudgeEnsemble
from pipeline.gate.nli import make_nli
from pipeline.gate.retrieve import Retriever
from pipeline.gate.rules import RulesEngine
from pipeline.library import seed_data
from pipeline.library.library import ClaimsLibrary

GREEN_T = 0.60
AMBER_T = 0.30


def _hash8(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Gate:
    def __init__(self, library: ClaimsLibrary, rules: RulesEngine,
                 calibrator: Optional[IsotonicCalibrator] = None,
                 verdict_cache: Optional[VerdictCache] = None,
                 llm_cache: Optional[LLMCache] = None):
        self.library = library
        self.rules = rules
        self.nli = make_nli()
        self.llm_cache = llm_cache or LLMCache()
        self.ensemble = JudgeEnsemble(self.llm_cache)
        self.calibrator = calibrator or IsotonicCalibrator()
        self.retriever = Retriever(library)
        self.decomposer = Decomposer(library)
        self.verdict_cache = verdict_cache or VerdictCache()
        # spy for the drift test (surgical re-verification)
        self.compute_calls = 0
        self.verified_keys: list[tuple[str, str, str]] = []

    # ---- core: verify one claim (cache-keyed, idempotent) ------------------
    def verify_claim(self, claim_text: str, claim=None) -> ClaimVerdict:
        rules_version = self.rules.rules_version()
        cid = claim.claim_id if claim else f"free_{_hash8(claim_text)}"
        source_id = claim.source_id if claim else "none"
        sv = self.library.source_version(source_id) if claim else "none"

        cached = self.verdict_cache.get(cid, sv, rules_version)
        if cached is not None:
            observe.emit("gate", "CACHE_HIT", node="ledger", detail=f"{cid} → {cached.verdict.value} (served from cache)",
                         decision={"verdict": cached.verdict.value, "cached": True}, claim_id=cid)
            return cached

        self.compute_calls += 1
        self.verified_keys.append((cid, sv, rules_version))
        observe.emit("gate", "INPUT", node="gate", detail=f"verify {cid}", claim_id=cid,
                     input={"claim_id": cid, "text": claim_text, "source_id": source_id,
                            "source_version": sv, "rules_version": rules_version})

        # --- evidence (live source text, so a changed source is seen) ---
        hits = self.retriever.retrieve(claim_text, k=1)
        evidence = hits[0]["text"] if hits else ""
        ev_source = hits[0]["source_id"] if hits else source_id
        observe.emit("gate", "TOOL", node="retrieve", tool="BM25Okapi (rank_bm25)", claim_id=cid,
                     detail=(f"top evidence from {ev_source} (score {hits[0]['score']:.2f})" if hits else "no evidence"),
                     input={"claim": claim_text},
                     output={"evidence": evidence, "source_id": ev_source,
                             "score": round(hits[0]["score"], 3) if hits else 0.0})

        # --- cheap-first cascade ---
        rule_out = self.rules.apply(claim_text, claim)
        observe.emit("gate", "DECISION", node="rules", tool=f"rules engine {rules_version}", claim_id=cid,
                     detail=(rule_out.verdict.value if rule_out.verdict else "no rule constrains"),
                     input={"rule_tags": claim.rule_tags if claim else []},
                     decision={"verdict": rule_out.verdict.value if rule_out.verdict else None,
                               "flags": rule_out.flags}, output={"reasons": rule_out.reasons})
        if rule_out.verdict == Verdict.RED:
            cv = ClaimVerdict(claim_id=cid, text=claim_text,
                              span=claim.span if claim else (0, 0), verdict=Verdict.RED,
                              source_id=ev_source, confidence=0.02, rule_flags=rule_out.flags,
                              nli_score=0.0, ensemble_score=0.0,
                              reasons=["blocked by compliance rule"] + rule_out.reasons,
                              source_version=sv, rules_version=rules_version)
            self.verdict_cache.put(cv)
            observe.emit("gate", "OUTPUT", node="ledger", detail=f"{cid} → RED (compliance veto, cascade short-circuit)",
                         claim_id=cid, decision={"verdict": "red", "via": "rule"},
                         output={"confidence": 0.02, "flags": rule_out.flags})
            return cv

        nli = self.nli.score(claim_text, evidence)
        observe.emit("gate", "DECISION", node="nli", tool=type(self.nli).__name__, claim_id=cid,
                     detail=nli.reason, input={"claim": claim_text, "evidence": evidence},
                     decision={"label": nli.label, "entail_prob": round(nli.entail_prob, 4)})
        escalate = AMBER_T <= nli.entail_prob <= 0.85   # only spend LLM judges if uncertain
        if escalate:
            observe.emit("gate", "ESCALATE", node="ensemble", claim_id=cid,
                         detail=f"NLI uncertain ({nli.entail_prob:.2f}) → spend LLM judges")
        ens = self.ensemble.judge(claim_text, evidence, escalate=escalate)
        observe.emit("gate", "DECISION", node="ensemble", tool="diverse judge ensemble", claim_id=cid,
                     detail=f"mean agreement {ens.mean_p} (numeric & superlative are veto lenses)",
                     input={"escalated": escalate},
                     decision={"votes": ens.votes, "mean_p": ens.mean_p})
        entail_raw = self._combine(nli.entail_prob, ens)
        confidence = self.calibrator.predict(entail_raw)

        if entail_raw >= GREEN_T:
            entail_verdict = Verdict.GREEN
        elif entail_raw >= AMBER_T:
            entail_verdict = Verdict.AMBER
        else:
            entail_verdict = Verdict.RED
        observe.emit("gate", "DECISION", node="calibrate", tool="isotonic PAV calibrator", claim_id=cid,
                     detail=f"entail_raw {entail_raw:.3f} → confidence {confidence:.3f} ({entail_verdict.value})",
                     input={"entail_raw": round(entail_raw, 4)},
                     decision={"entail_verdict": entail_verdict.value},
                     output={"confidence": round(confidence, 4)})

        final = self._most_severe(entail_verdict, rule_out.verdict)
        reasons = [nli.reason] + rule_out.reasons
        if final == Verdict.RED and entail_verdict == Verdict.RED:
            reasons.insert(0, "not entailed by any approved source")

        cv = ClaimVerdict(claim_id=cid, text=claim_text,
                          span=claim.span if claim else (0, 0), verdict=final,
                          source_id=ev_source, confidence=round(confidence, 4),
                          rule_flags=rule_out.flags, nli_score=round(nli.entail_prob, 4),
                          ensemble_score=ens.mean_p, reasons=reasons,
                          source_version=sv, rules_version=rules_version)
        self.verdict_cache.put(cv)
        observe.emit("gate", "OUTPUT", node="ledger", detail=f"{cid} → {final.value.upper()} (most-severe of entail+rule)",
                     claim_id=cid, decision={"verdict": final.value, "entail_verdict": entail_verdict.value,
                                             "rule_verdict": rule_out.verdict.value if rule_out.verdict else None},
                     output={"confidence": round(confidence, 4), "flags": rule_out.flags, "reasons": reasons})
        return cv

    @staticmethod
    def _combine(nli_p: float, ens: EnsembleResult) -> float:
        v = ens.votes
        support = [nli_p, v["coverage"]]
        support += [p for k, p in v.items() if k.startswith("ollama") or k.startswith("claude")]
        mean_support = sum(support) / len(support)
        veto = min(v["numeric"], v["superlative"])
        return max(0.0, min(1.0, min(mean_support, veto)))

    @staticmethod
    def _most_severe(a: Optional[Verdict], b: Optional[Verdict]) -> Verdict:
        order = {None: 0, Verdict.GREEN: 1, Verdict.AMBER: 2, Verdict.RED: 3}
        return a if order.get(a, 0) >= order.get(b, 0) else (b or Verdict.GREEN)

    # ---- claim-level verification of a variant (no recipient) --------------
    def verify_variant(self, variant: Variant) -> list[ClaimVerdict]:
        verdicts = [self.verify_claim(self.library.claim(cid).text, self.library.claim(cid))
                    for cid in variant.claim_ids if self.library.claim(cid)]
        if variant.planted_lie:
            verdicts.append(self.verify_claim(seed_data.PLANTED_LIE_TEXT, None))
        return verdicts

    def variant_cleared(self, variant: Variant) -> bool:
        return all(v.verdict != Verdict.RED for v in self.verify_variant(variant))

    # ---- message-level verification (per recipient, per channel) -----------
    def verify_message(self, recipient: Recipient, variant: Variant, channel: str) -> MessageLedger:
        body = variant.render(recipient, self.library.claim_text_map())
        if variant.planted_lie:
            body += f"\nHelix Analytics {seed_data.PLANTED_LIE_TEXT}."
        decomposed = self.decomposer.decompose(body)
        claims = [self.verify_claim(d.text, d.claim) for d in decomposed]
        return MessageLedger(recipient_id=recipient.recipient_id, channel=channel,
                             variant_id=variant.variant_id, segment=variant.segment,
                             html=body, claims=claims, generated_at=_now())
