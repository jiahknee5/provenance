"""The Provenance node graph — the single source the Observatory's topology, the node
graph with tooling, and the architecture diagram are all generated from.

Each node declares: the lane it belongs to (the 6 role-lanes the event ledger writes),
the real TOOLS it calls, a one-line INPUT/DECISION/OUTPUT contract, the headline property
it backs (P1-P5, if any), and a layout cell (col, row) for the diagram. Edges are the
data-flow between nodes. Nothing here is invented — every tool maps to code in pipeline/.
"""
from __future__ import annotations

# lane -> display + colour (matches the dashboard legend)
LANES = {
    "library":   {"label": "Claims Library", "color": "#6b7cff"},
    "gate":      {"label": "The Gate",        "color": "#0e7c86"},
    "optimizer": {"label": "Optimizer",       "color": "#8a5cf6"},
    "drift":     {"label": "Drift Monitor",   "color": "#d98a16"},
    "website":   {"label": "Website channel", "color": "#2bb673"},
    "assurance": {"label": "Assurance Lab",   "color": "#d23b3b"},
    "enrichment": {"label": "Enrichment",     "color": "#e0764a"},
}

# the pipeline phases, in run order (the dashboard ribbon). P1-P8 are the campaign demo;
# T2-T4 are the per-recipient enrichment touchpoint demo that runs after it.
PHASES = [
    "P1 · Library", "P2 · Gate", "P3 · Campaign 1", "P4 · Twin",
    "P5 · Drift", "P6 · Campaign 2", "P7 · Website", "P8 · Assurance",
    "T2 · Enrich", "T3 · Personalize", "T4 · Fact audit",
]

NODES = [
    {
        "id": "library", "lane": "library", "label": "Claims Library", "col": 0, "row": 1,
        "tools": ["4 approved source docs", "claim→evidence graph (span-bound)",
                  "content-hash source versioning"],
        "input": "4 approved sources (SOURCES) + 10 claim specs (CLAIMS)",
        "decision": "bind each claim to a verbatim source span + its source_version",
        "output": "10 atomic ClaimNodes in a versioned library",
        "code": "pipeline/library/library.py", "property": None,
    },
    {
        "id": "decompose", "lane": "gate", "label": "Decompose", "col": 1, "row": 0,
        "tools": ["sentence splitter", "token-coverage matcher", "superlative detector"],
        "input": "a rendered message (slot-filled copy)",
        "decision": "which sentences are checkable claims (match a library claim OR assert an absolute)",
        "output": "list of (sentence, matched ClaimNode | none)",
        "code": "pipeline/gate/decompose.py", "property": None,
    },
    {
        "id": "retrieve", "lane": "gate", "label": "Retrieve", "col": 2, "row": 0,
        "tools": ["BM25Okapi (rank_bm25)", "live-text reindex on library version change"],
        "input": "a claim sentence",
        "decision": "rank the live source sentences; pick top-k evidence",
        "output": "best evidence sentence + score (re-indexed after a source change)",
        "code": "pipeline/gate/retrieve.py", "property": "P3",
    },
    {
        "id": "rules", "lane": "gate", "label": "Compliance rules", "col": 3, "row": 0,
        "tools": ["rules engine (rules/helix_tenant.yaml)", "holds · blocks · disclaimers",
                  "rules_version hash"],
        "input": "claim text + claim node (tags, claim_id)",
        "decision": "veto step — holds/blocks/disclaimers raise green→amber→red; never relax",
        "output": "RuleOutcome (verdict, flags, reasons); RED short-circuits the cascade",
        "code": "pipeline/gate/rules.py", "property": "P2",
    },
    {
        "id": "nli", "lane": "gate", "label": "NLI entailment", "col": 2, "row": 1,
        "tools": ["Lexical number-aware NLI (default, deterministic)",
                  "DeBERTa-v3-large-MNLI (rich profile)"],
        "input": "claim + retrieved evidence",
        "decision": "is the claim entailed? number-aware (a drifted number → contradiction)",
        "output": "entail_prob (raw, uncalibrated) + label + reason",
        "code": "pipeline/gate/nli.py", "property": "P5",
    },
    {
        "id": "ensemble", "lane": "gate", "label": "Diverse ensemble", "col": 3, "row": 1,
        "tools": ["coverage judge (number-blind)", "numeric judge", "superlative judge",
                  "Ollama Qwen + Nemotron (rich)", "Claude (rich, if key)", "LLM cache"],
        "input": "claim + evidence (+ escalate flag if NLI uncertain)",
        "decision": "diverse votes; numeric & superlative are VETO lenses, coverage/NLI support",
        "output": "per-judge votes + mean agreement",
        "code": "pipeline/gate/ensemble.py", "property": "P5",
    },
    {
        "id": "calibrate", "lane": "gate", "label": "Calibrate", "col": 4, "row": 1,
        "tools": ["isotonic PAV calibrator (no sklearn)"],
        "input": "entail_raw = min(mean(support), min(vetoes))",
        "decision": "map raw score → calibrated P(sayable)",
        "output": "calibrated confidence",
        "code": "pipeline/gate/calibrate.py", "property": "P5",
    },
    {
        "id": "ledger", "lane": "gate", "label": "Claim ledger", "col": 5, "row": 1,
        "tools": ["verdict cache (claim_id, source_version, rules_version)",
                  "most-severe combine"],
        "input": "entail verdict + rule verdict",
        "decision": "final = most-severe(entail, rule); GREEN ≥0.60, AMBER ≥0.30, else RED",
        "output": "ClaimVerdict (green/amber/red) cached once per unique claim",
        "code": "pipeline/gate/gate.py", "property": "P2,P4",
    },
    {
        "id": "pool", "lane": "optimizer", "label": "Action pool", "col": 6, "row": 0,
        "tools": ["ActionPool (Gate-cleared arms only)", "pause/unblock on drift"],
        "input": "Gate verdicts over the candidate variants",
        "decision": "admit a variant only if it has no RED claim — the truth boundary",
        "output": "per-segment set of pullable arms (a blocked lie is never added)",
        "code": "pipeline/common/store.py", "property": "P1",
    },
    {
        "id": "bandit", "lane": "optimizer", "label": "Thompson bandit", "col": 7, "row": 0,
        "tools": ["per-segment Thompson sampling (Beta posteriors)",
                  "PosteriorStore warm-start (decayed prior)"],
        "input": "recipient segment + the active pool",
        "decision": "sample each arm's Beta posterior; pull the best — only pool arms exist",
        "output": "selected arm + updated posterior",
        "code": "pipeline/optimizer/bandit.py", "property": "P1",
    },
    {
        "id": "oracle", "lane": "optimizer", "label": "CTA oracle", "col": 8, "row": 0,
        "tools": ["synthetic CTA oracle", "stable-hash latent CTR (not Python hash())"],
        "input": "segment + selected arm",
        "decision": "draw click / no-click / unsubscribe at the arm's latent CTR",
        "output": "reward signal; lie has the HIGHEST latent CTR",
        "code": "pipeline/optimizer/oracle.py", "property": "P1",
    },
    {
        "id": "twin", "lane": "optimizer", "label": "Unconstrained twin", "col": 7, "row": 1,
        "tools": ["identical bandit, pool WITH the lie"],
        "input": "same recipients, same oracle — only the truth boundary differs",
        "decision": "free to pull the lie",
        "output": "converges to the lie (the proof: constrained run cannot)",
        "code": "pipeline/optimizer/campaign.py", "property": "P1",
    },
    {
        "id": "drift", "lane": "drift", "label": "Drift Monitor", "col": 6, "row": 2,
        "tools": ["claim→source dependency graph", "legal-hold flip / source-change trigger",
                  "surgical re-Gate (cache-miss only)", "pool mutation"],
        "input": "a legal-hold flip or a source edit",
        "decision": "re-verify ONLY the affected claims; pause variants that went red",
        "output": "before→after verdicts, recomputed ids, paused/unblocked variants",
        "code": "pipeline/drift/monitor.py", "property": "P2,P3",
    },
    {
        "id": "website", "lane": "website", "label": "Website channel", "col": 9, "row": 1,
        "tools": ["magic-link token (no PII in URL)", "same Gate", "A/B verified winner",
                  "CTA tracking"],
        "input": "a recipient token + the learned per-segment winner",
        "decision": "render only Gate-passed claims; same claim_id → same verdict as email",
        "output": "personalized page from the verified variant",
        "code": "app/site.py", "property": "P4",
    },
    {
        "id": "assurance", "lane": "assurance", "label": "Assurance Lab", "col": 9, "row": 2,
        "tools": ["adversarial trap generator (4 mutations)", "the real Gate",
                  "single-judge baseline (number-blind)", "ECE / reliability"],
        "input": "verified claims mutated into labeled traps",
        "decision": "Gate vs single judge at fixed false-reject, sliced per channel",
        "output": "catch-rate, false-reject, ECE — Gate > baseline on material traps",
        "code": "pipeline/assurance/harness.py", "property": "P5",
    },
    # --- enrichment lane (data-provenance) — touchpoint T2 + the fact half of T3/T5 ---
    {
        "id": "enrich_connectors", "lane": "enrichment", "label": "Connectors", "col": 0, "row": 3,
        "tools": ["email-domain parse (real, no network)", "news RSS (live, cached)",
                  "firmographics (simulated)", "account intent (simulated)"],
        "input": "a recipient (form submission)",
        "decision": "fan out to the allowed sources; fetch raw facts",
        "output": "raw facts tagged with their source id",
        "code": "pipeline/enrichment/connectors.py", "property": None,
    },
    {
        "id": "enrich_gate", "lane": "enrichment", "label": "Enrichment Gate", "col": 1, "row": 3,
        "tools": ["enrichment-source policy (helix_tenant.yaml)", "consent check",
                  "freshness TTL", "PHI/PII key block"],
        "input": "a raw fact + the recipient",
        "decision": "usable / disclaimer / blocked (allow-list + consent + freshness + PHI)",
        "output": "a verdicted ProfileFact carrying its lawful-basis receipt",
        "code": "pipeline/enrichment/gate.py", "property": "E1",
    },
    {
        "id": "enrich_synth", "lane": "enrichment", "label": "Synthesizer", "col": 2, "row": 3,
        "tools": ["fact merge", "signal derivation (intent / tier / news)"],
        "input": "the verdicted facts",
        "decision": "merge usable facts; derive the selection signals",
        "output": "a Profile + signals (lead_with, account_tier, recent_news)",
        "code": "pipeline/enrichment/engine.py", "property": None,
    },
    {
        "id": "profile_db", "lane": "enrichment", "label": "Profile DB", "col": 3, "row": 3,
        "tools": ["profiles.sqlite (profiles + fact receipts)"],
        "input": "a synthesized Profile",
        "decision": "persist the profile + every fact receipt",
        "output": "queryable profile + receipts (readable in observability)",
        "code": "pipeline/enrichment/store.py", "property": None,
    },
    {
        "id": "personalize", "lane": "enrichment", "label": "Personalize", "col": 8, "row": 3,
        "tools": ["gated fact inliner", "basis receipts in the ledger"],
        "input": "a Profile + the verified-claim body",
        "decision": "inline ONLY usable facts; withhold every blocked fact",
        "output": "personalized copy + a per-fact basis receipt",
        "code": "pipeline/enrichment/engine.py", "property": "P4",
    },
    {
        "id": "fact_audit", "lane": "assurance", "label": "Fact audit", "col": 9, "row": 3,
        "tools": ["fact-trap harness (4 mutations)", "the Enrichment Gate"],
        "input": "facts mutated into un-shippable traps",
        "decision": "does the gate block disallowed / stale / PHI / non-consent?",
        "output": "fact-gate catch-rate / false-block",
        "code": "pipeline/enrichment/audit.py", "property": "E1",
    },
]

EDGES = [
    ("library", "decompose"), ("library", "retrieve"),
    ("decompose", "retrieve"), ("retrieve", "nli"), ("retrieve", "rules"),
    ("rules", "ledger"), ("nli", "ensemble"), ("ensemble", "calibrate"),
    ("calibrate", "ledger"),
    ("ledger", "pool"), ("ledger", "twin"), ("ledger", "website"), ("ledger", "assurance"),
    ("pool", "bandit"), ("bandit", "oracle"), ("oracle", "bandit"),
    ("library", "drift"), ("drift", "pool"), ("drift", "ledger"),
    ("bandit", "website"),
    # enrichment lane (data-provenance)
    ("enrich_connectors", "enrich_gate"), ("enrich_gate", "enrich_synth"),
    ("enrich_synth", "profile_db"), ("profile_db", "pool"), ("profile_db", "personalize"),
    ("bandit", "personalize"), ("personalize", "website"),
    ("drift", "enrich_gate"), ("enrich_gate", "fact_audit"),
]

# the 5 headline properties + E1 (enrichment), attached to the nodes that prove them
PROPERTIES = {
    "P1": {"claim": "A Gate-blocked lie can never be selected (the twin converges to it)",
           "test": "tests/test_optimizer.py", "nodes": ["pool", "bandit", "oracle", "twin"]},
    "P2": {"claim": "The Gate blocks the held claim the instant the hold flips (rules_version alone)",
           "test": "tests/test_gate.py", "nodes": ["rules", "ledger", "drift"]},
    "P3": {"claim": "A drift event re-verifies exactly the affected claims — no over/under-invalidation",
           "test": "tests/test_gate.py, tests/test_drift.py", "nodes": ["retrieve", "drift"]},
    "P4": {"claim": "Website renders only Gate-passed claims; same claim_id → same verdict on both channels",
           "test": "tests/test_website.py", "nodes": ["ledger", "website"]},
    "P5": {"claim": "Assurance catch-rate > single-judge baseline at fixed false-reject",
           "test": "tests/test_assurance.py", "nodes": ["nli", "ensemble", "calibrate", "assurance"]},
    "E1": {"claim": "An un-receipted personal fact (disallowed source / stale / PHI / non-consent) can never be inlined",
           "test": "tests/test_enrichment.py", "nodes": ["enrich_gate", "personalize", "fact_audit"]},
}


def topology() -> dict:
    """The full graph as a plain dict — written to topology.json for the dashboard."""
    return {"lanes": LANES, "phases": PHASES, "nodes": NODES,
            "edges": [list(e) for e in EDGES], "properties": PROPERTIES}
