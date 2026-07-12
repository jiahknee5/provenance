"""Persuasion overlay — principle → Gate-bounded copy plan (the UC3 closing layer).

The product can't change the FACTS to be more persuasive: the Gate forbids unprovable
claims, superlatives, comparatives, and named competitors. What a persuasion principle CAN
change is the FRAME — which provable claims to lead with, in what order, under what headline
and CTA. This module maps a persuasion strategy (+ the visitor's signals) to a copy plan
that surfaces ONLY Gate-cleared claims: any claim the Gate blocks (e.g. one under a legal
hold) is dropped, so the truth boundary holds for the closing copy exactly as it does for
the website variants.

Every strategy's headline + CTA is itself run through the copy Gate (`creative.verify_copy`),
so the overlay can never ship a superlative, a comparative, a named competitor, an invented
number, or an AI-tell. Principle changes the frame; the Gate still disposes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from pipeline.common.schemas import Recipient
from pipeline.personalization import creative as CR

# Approved, role-fitting claims (the same claim set the website variants use). Order = the
# role's strongest provable proof first. The overlay only ever reorders/selects these — it
# never invents a claim.
ROLE_PROOF: dict[str, list[str]] = {
    "clinops": ["c_los", "c_speed", "c_deployed", "c_hipaa"],
    "cfo": ["c_tco", "c_price", "c_nofee", "c_deployed"],
    "it_security": ["c_soc2", "c_hipaa", "c_encrypt", "c_ehr"],
    "quality": ["c_los", "c_deployed", "c_hipaa", "c_speed"],
}
_DEFAULT_PROOF = ["c_deployed", "c_hipaa", "c_soc2"]

# Each strategy: the persuasion principle, a Gate-clean headline + CTA (no superlative /
# comparative / number / company recite / AI-tell), and an optional claim to LEAD with.
STRATEGIES: dict[str, dict] = {
    "authority": {
        "principle": "Authority — lead with source-backed proof for a technical buyer.",
        "headline": "Source-backed results your team can verify.",
        "cta": "See the proof", "lead": None},
    "social_proof": {
        "principle": "Social proof — lead with peer adoption / deployment breadth.",
        "headline": "Built for systems that demand evidence.",
        "cta": "See where it runs", "lead": "c_deployed"},
    "loss_aversion": {
        "principle": "Loss aversion — frame the cost of the status quo (a loss is felt ~2x a gain).",
        "headline": "Every claim you can’t prove is a risk you can’t see.",
        "cta": "Close the gap", "lead": None},
    "consistency": {
        "principle": "Commitment & consistency — resume the open loop from the prior visit.",
        "headline": "Pick up your evaluation where you left off.",
        "cta": "Resume", "lead": None},
    "reciprocity": {
        "principle": "Reciprocity — give a tailored, sourced assessment before the ask.",
        "headline": "A tailored, sourced assessment, yours to keep.",
        "cta": "See your assessment", "lead": None},
}


@dataclass
class CopyPlan:
    strategy: str
    principle: str
    headline: str
    cta: str
    claims: list[dict]          # [{claim_id, text, verdict, source}] — Gate-cleared, with receipts
    dropped: list[str]          # claim_ids the Gate blocked (e.g. legal hold) — proof of the boundary
    headline_ok: bool           # did the headline + CTA clear the copy Gate?
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


def list_strategies() -> list[dict]:
    return [{"key": k, "principle": v["principle"]} for k, v in STRATEGIES.items()]


def select_strategy(recipient: Recipient, signals: Optional[dict] = None) -> str:
    """Deterministic principle selection from the visitor's behavior / role / size."""
    sig = signals or {}
    if sig.get("abandoned") or sig.get("returning"):
        return "consistency"                      # resume the open loop
    if recipient.role == "it_security":
        return "authority"                        # technical buyer trusts evidence
    if (recipient.urgency or "").lower() == "high":
        return "loss_aversion"                    # urgency → cost-of-inaction frame
    if recipient.company_size == "idn":
        return "social_proof"                     # large org → peer adoption lands
    return "authority"


def build_plan(gate, library, recipient: Recipient, strategy: Optional[str] = None,
               signals: Optional[dict] = None) -> CopyPlan:
    """Build a Gate-bounded copy plan for a known visitor. Only non-red claims survive; the
    headline + CTA are themselves Gate-checked. `dropped` is the visible truth boundary."""
    strat = strategy if strategy in STRATEGIES else select_strategy(recipient, signals)
    spec = STRATEGIES[strat]

    candidates = list(ROLE_PROOF.get(recipient.role, _DEFAULT_PROOF))
    lead = spec.get("lead")
    if lead and lead in candidates:
        candidates.remove(lead)
        candidates.insert(0, lead)

    kept: list[dict] = []
    dropped: list[str] = []
    for cid in candidates:
        try:
            node = library.claim(cid)
        except (KeyError, AttributeError):
            continue                              # unknown claim id — skip, never invent
        cv = gate.verify_claim(node.text, node)
        if cv.verdict.value == "red":
            dropped.append(cid)                   # blocked by the Gate (e.g. legal hold) — dropped
            continue
        kept.append({"claim_id": cid, "text": node.text, "verdict": cv.verdict.value,
                     "source": library.source(node.source_id).title})

    facts = " ".join(c["text"] for c in kept)     # numbers in copy must trace to a kept claim
    checks = CR.verify_copy([spec["headline"], spec["cta"]], facts,
                            recipient.company, policy="allude")
    headline_ok = all(c["ok"] for c in checks)

    rationale = (f"{strat}: surfaced {len(kept)} provable claim(s) "
                 f"led by {kept[0]['claim_id'] if kept else '—'}; "
                 f"dropped {dropped or 'none'} (blocked by the Gate).")
    return CopyPlan(strategy=strat, principle=spec["principle"], headline=spec["headline"],
                    cta=spec["cta"], claims=kept, dropped=dropped,
                    headline_ok=headline_ok, rationale=rationale)
