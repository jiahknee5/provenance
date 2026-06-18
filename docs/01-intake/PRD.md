# PRD (locked) — Provenance End-to-End Demo

> Immutable from build start. New requirements land as numbered, dated amendments here +
> a row in `docs/05-build/DECISIONS.md`; the raw intent is never silently edited.

## Problem
Ultra-personalization breaks human review — you can't legally read 100k unique messages,
so in claims-heavy domains you must pick generic-but-reviewed or personal-but-unverified.
The bottleneck is **verification at scale**. Provenance is a *system of record for claims*:
outreach that can't say what it can't prove, optimizing itself **inside** the truth boundary.

## What this build delivers
A runnable, deterministic demo of all five Provenance modules across **two channels**
(email + website) for the demo tenant **Helix Analytics** (regulated health-tech):

1. A real, working **web form** → 1000 seeded synthetic submissions across 8 micro-segments.
2. **Claims Library** — 4 approved sources → 10 atomic claims bound to source spans, a
   versioned claim–evidence graph + dependency edges, versioned compliance rules.
3. **The Gate** (steps 1+2 of Provenance) — decompose → retrieve → NLI → calibrated diverse
   ensemble → compliance rules → claim ledger (green/amber/red). Idempotent, claim-level cached.
4. **The Optimizer** — a contextual bandit over verified arms only, learning A/B per segment
   from a simulated CTA oracle; a planted lie is structurally unreachable.
5. **Drift Monitor** — legal-hold flip / source change → surgical re-verify → pool mutation.
6. **Campaign 2** — warm-started from campaign 1 on the post-drift truth boundary.
7. **Ultra-personalized website** — magic-link retrieval at launch, A/B-winning verified
   variant, same Gate, CTA tracking, renders only Gate-passed claims.
8. **Assurance Lab** — one harness, sliced per channel, vs a single-judge baseline.
9. **Inspector UI** — ledger lights, regret contrast, blocked-lie panel, drift log, assurance.

## The 5 headline properties (must be provably true — and are, in `tests/`)
- **P1** A Gate-blocked lie can never be selected (constrained: 0 selections; the
  unconstrained twin converges to it). `tests/test_optimizer.py`
- **P2** The Gate blocks the legal-hold claim the instant the hold flips, attributable to
  `rules_version` alone. `tests/test_gate.py`
- **P3** A drift event re-verifies exactly the affected claims — no under/over-invalidation.
  `tests/test_gate.py`, `tests/test_drift.py`
- **P4** The website renders only Gate-passed claims; same claim_id → same verdict on both
  channels. `tests/test_website.py`
- **P5** Assurance catch-rate > single-judge baseline at fixed false-reject.
  `tests/test_assurance.py`

## Decisions baked in (see DECISIONS.md)
Contextual bandit (not "RL"); "can't win by lying" proven by the unconstrained twin; one
Assurance harness sliced per channel; the LLM judge is one calibrated ensemble member, not
the verifier; "live" = deterministic seeded replay; 100% synthetic data.

## Non-functional
Deterministic given the global seed (guarded across processes); offline by default (no API
key, Ollama optional for the rich profile); Gate cached at claim level; no secrets committed.

## Out of scope
Real email sending; real PII; production auth; multi-tenant beyond tenant=config; live
on-stage model inference; hidden-state probe.

## Amendments
> Appended after lock; raw intent above is never silently edited (see header).

**A1 — Observatory (2026-06-18).** Adds a watchable, per-node observability surface over
the runtime pipeline: an append-only event ledger (one JSONL per role lane, monotonic
`seq`), an interactive node graph annotated with each node's tooling, an architecture
diagram, and per-node INPUT→DECISION→OUTPUT evals tied to P1–P5. Served at `/observatory`;
produced by `python -m scripts.trace` (deterministic seeded replay, byte-identical).
Instrumentation lives inside the nodes but is a no-op unless a recorder is attached, so the
25 tests and the determinism guarantee are unchanged. See DECISIONS.md R12. Non-functional
guarantees (offline, $0, seed-locked, no secrets) are unchanged; pytest stays the
authoritative gate for P1–P5.

**A2 — Data enrichment + touchpoint automation (2026-06-18, BUILT).**
Enrich the form submission from other sources, synthesize a profile DB, personalize the
email + return-visit website, catalog all paid/free enrichment sources, make the profile DB
readable in observability. Operator chose **Fork 1-B** (facts may appear in copy — but only
Enrichment-Gate-`usable` facts with an on-file basis, audited by the Assurance Lab) and
**Fork 2-B** (one real free connector — live news RSS, opt-in + cached + $0 + no PII to
third parties). Built as the `enrichment` lane: connectors → Enrichment Gate → synthesize →
profile DB → personalize, with a new acceptance property **E1** (an un-receipted fact can
never be inlined; `tests/test_enrichment.py`). The locked "no real PII / 100% synthetic"
stance is preserved in the default synthetic mode; live mode reads only public data
(company name) — see `docs/04-workflow/ENRICHMENT-TOUCHPOINTS.md`,
`docs/audits/enrichment-privacy.md`, DECISIONS R13–R15. Non-functional guarantees unchanged
(default offline, $0, byte-identical); pytest stays authoritative.
