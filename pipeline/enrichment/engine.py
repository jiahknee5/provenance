"""The enrichment engine — fan out to connectors, gate each fact, synthesize a profile,
then personalize a message from ONLY the gated facts.

Touchpoint T2 (enrich + synthesize) and the fact half of T3/T5 (personalize) live here.
Personalization is Fork 1-B: usable/disclaimer facts MAY appear in the copy, each carrying
its basis (the receipt); blocked facts never do. The verified product claims still come from
the claim Gate — enrichment adds the personal layer on top, it does not replace verification.
"""
from __future__ import annotations

from pipeline.common import observe
from pipeline.enrichment import connectors as conn
from pipeline.enrichment.gate import EnrichmentGate
from pipeline.enrichment.schemas import FactVerdict, Profile, ProfileFact
from pipeline.enrichment.store import ProfileStore


def synthesize(recipient, facts: list[ProfileFact]) -> Profile:
    """Merge the verdicted facts into a profile + derive the signals that drive selection."""
    usable = {f.key: f for f in facts if f.inlinable}
    signals: dict = {}
    if "intent_topic" in usable:
        signals["intent_topic"] = usable["intent_topic"].value
        signals["lead_with"] = usable["intent_topic"].value
    if "in_market" in usable:
        signals["in_market"] = True
    if "size_band" in usable:
        signals["account_tier"] = usable["size_band"].value
    if "ehr_vendor" in usable:
        signals["ehr_vendor"] = usable["ehr_vendor"].value
    if "recent_news" in usable:
        signals["recent_news"] = usable["recent_news"].value
    return Profile(recipient_id=recipient.recipient_id, segment=recipient.segment,
                   facts=facts, signals=signals)


def enrich(recipient, gate: EnrichmentGate | None = None,
           store: ProfileStore | None = None, mode: str | None = None) -> Profile:
    gate = gate or EnrichmentGate()
    observe.emit("enrichment", "INPUT", node="enrich_connectors",
                 detail=f"enrich {recipient.recipient_id} ({recipient.company}, consent={recipient.consent})",
                 input={"recipient_id": recipient.recipient_id, "company": recipient.company,
                        "consent": recipient.consent, "mode": mode or conn.config.ENRICH_MODE})
    facts: list[ProfileFact] = []
    for c in conn.connectors_for(mode):
        raws = c.fetch(recipient)
        observe.emit("enrichment", "TOOL", node="enrich_connectors", tool=c.label,
                     detail=f"{c.id}: {len(raws)} fact(s)"
                            + ("" if raws else " — none (connector unavailable / no signal)"),
                     output=[{"key": r.key, "value": r.value} for r in raws], source=c.id)
        for raw in raws:
            facts.append(gate.evaluate(raw, recipient))

    profile = synthesize(recipient, facts)
    observe.emit("enrichment", "OUTPUT", node="enrich_synth", tool="synthesizer",
                 detail=f"{len(profile.usable_facts)} usable · {len(profile.blocked_facts)} blocked · "
                        f"signals: {', '.join(profile.signals) or 'none'}",
                 output={"usable": len(profile.usable_facts), "blocked": len(profile.blocked_facts),
                         "signals": profile.signals})
    if store is not None:
        store.save(profile)
    return profile


# --------------------------------------------------------------------------- #
# Personalize — inline ONLY gated facts (Fork 1-B), each with its basis receipt.
# --------------------------------------------------------------------------- #
def _fact_sentence(f: ProfileFact, recipient) -> str | None:
    inferred = " (inferred)" if f.verdict == FactVerdict.DISCLAIMER else ""
    if f.key == "recent_news":
        return f"We saw {f.value}{inferred}."
    if f.key == "intent_topic":
        return f"Since {recipient.company} is exploring {f.value}{inferred}, here's what's most relevant:"
    if f.key == "size_band":
        return f"Tailored for a {f.value}{inferred}."
    if f.key == "ehr_vendor":
        return f"Note: we integrate with {f.value}{inferred}."
    return None


def personalize(recipient, profile: Profile, claim_body: str) -> dict:
    """Wrap the verified-claim body with gated personal facts. Returns the rendered copy +
    the receipts (each inlined fact's source + basis) for the message ledger."""
    lines, receipts = [], []
    for f in profile.usable_facts:
        sent = _fact_sentence(f, recipient)
        if not sent:
            continue
        lines.append(sent)
        receipts.append({"key": f.key, "text": sent, "source": f.source,
                         "source_kind": f.source_kind, "basis": f.basis, "verdict": f.verdict.value})
    # verified claims stay intact; gated personal facts go in a clearly-labelled block whose
    # provenance is visible (sources on file) — facts-in-copy, but never un-receipted.
    block = (f"\n\n— Personalized for {recipient.company} (sources on file) —\n"
             + "\n".join(f"• {l}" for l in lines)) if lines else ""
    body = f"{claim_body}{block}"
    observe.emit("enrichment", "OUTPUT", node="personalize", tool="fact inliner (gated)",
                 detail=f"inlined {len(receipts)} gated fact(s); {len(profile.blocked_facts)} blocked fact(s) withheld",
                 decision={"inlined": [r["key"] for r in receipts],
                           "withheld": [f.key for f in profile.blocked_facts]},
                 output={"receipts": receipts})
    return {"body": body, "personalization": receipts,
            "facts_used": len(receipts), "facts_blocked": len(profile.blocked_facts)}
