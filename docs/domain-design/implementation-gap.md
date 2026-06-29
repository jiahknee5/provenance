# Implementation gap

> **Proposed (north-star):** [`proposed/`](proposed/)  
> **Implemented (as-built):** [`implemented/`](implemented/)  
> **Last reviewed:** 2026-06-29 (campaign emotional reaction loop wired for deterministic demo replay)

This document lists what the proposed architecture describes but the runtime has not yet fully implemented. Maturity labels match [`implemented/runtime-mapping.md`](implemented/runtime-mapping.md).

## Summary

| Area | Status | Headline gap |
|---|---|---|
| Event envelope + streams | **Partial** | Shape implemented; catalog emitters now cover claim ingestion, asset approval/publish, enrichment, and emotional signals |
| Core aggregates (Profile, Asset, Review, DecisionTrace) | **Implemented** | Schema v2 cutover complete |
| Claim / Evidence | **Partial** | `claim_extracted` / `claim_superseded` emitted at library ingest + source rebind; `ClaimStatus` still ≠ proposed lifecycle |
| Policy / Optimizer / BanditPolicy | **Partial** | YAML rules + code-level Thompson; no persisted aggregates |
| Identity | **Partial** | Resolver + events exist; no durable candidate store |
| Segmentation | **Partial** | `segment_evaluated` / `segment_assignment_updated` emitted; still implicit strings, no `SegmentDefinition` / `SegmentAssignment` aggregates |
| Emotional safety | **Partial** | Rule-based capstone loop is wired in `run_campaign` (signal → cohort → policy → reroute/block → dispatch); no live ML / dwell-scroll ingestion |
| Asset lifecycle | **Partial** | Full emit chain through `asset_publish_requested`; automated gate approval (no human review workflow) |
| Review | **Implemented** | Queue + API; advisory AMBER contract preserved |
| Observe vs domain | **By design** | Both coexist; observe is debug-only (R12) |

## Aggregates

### Implemented or near-complete

- **Profile** — unified aggregate with `active_claim_refs`, `segment_refs`, copy-safe/routing refs; `ProfileStore` is SOT delegate for customer + enrichment paths.
- **Asset** — lifecycle enum, emotional vector, claim bindings; `from_variant` bridge from demo `Variant`.
- **Review** — full queue lifecycle with `check_dispatch`; non-advisory rejection blocks dispatch.
- **DecisionTrace** — SQLite-backed store; wired at Gate, campaign, override.

### Partial — behavior exists, canonical shape incomplete

| Proposed aggregate | What exists | Gap |
|---|---|---|
| `Claim` | `ClaimNode`, `ClaimVerdict`, verdict cache | `claim_extracted` at library ingest; `claim_superseded` on source rebind; `ClaimStatus` ≠ proposed lifecycle |
| `Evidence` | `SourceDoc`, spans, `RawFact`, `ProfileFact` | No standalone `evidence_id` aggregate or immutable evidence stream per artifact |
| `Gate` | `pipeline/gate/gate.py` + domain adapter | Gate is not a persisted aggregate; `gate_id`, `verification_mode` not stored |
| `Policy` | `RulesEngine`, `EnrichmentGate`, surface policy | YAML rules, not versioned `Policy` aggregate with scope/expression/severity |
| `Optimizer` | `ThompsonBandit`, `run_campaign`, `LiveOptimizer` | No persisted `optimizer_id`, objective, context features, strategy ref |
| `BanditPolicy` | `ThompsonBandit` + `PosteriorStore` | Strategy is code + artifacts, not a `BanditPolicy` object |
| `IdentityCandidate` | `IdentityCandidate` model + `IdentityResolver` | Candidates not stored; resolution is deterministic per funnel call, not a durable workflow |
| `SegmentDefinition` | `ROLE_ANGLES`, cohort `segments.py` | No ruleset version aggregate |
| `SegmentAssignment` | Recipient `segment`, customer `Stage`, cohort tiers | No assignment id, confidence, validity window, or membership events |
| `EmotionalSignal` | Rule-based keyword inference in `emotional.py`; campaign replay derives text signals from recipient urgency/use-case | No ML/NLP pipeline or live dwell/scroll ingestion |
| `EmotionalVectorTag` | `Variant.emotional_vector` string | No tag aggregate with allowed/blocked cohorts |

## Event catalog gaps

Events defined in [`proposed/provenance_event_catalog/Event-Catalog.csv`](proposed/provenance_event_catalog/Event-Catalog.csv) **without** a current adapter emitter:

### Ingestion / enrichment

- ~~`enrichment_requested`, `enrichment_received`~~ — emitted at `pipeline/enrichment/engine.py` `enrich()`

### Evidence / claims

- ~~`claim_extracted`~~ — emitted at `ClaimsLibrary.from_seed()` / `load()` via `domain/adapters/claim.py`
- ~~`claim_superseded`~~ — emitted on `mark_verified()` source rebind (+ optional `supersedes_claim_id` at ingest)

### Segmentation

- ~~`emotional_signal_detected`~~ — emitted in `EmotionalSafetyPolicy.evaluate()` (when signals provided)
- ~~`emotional_segment_assignment_updated`~~ — emitted when high-anxiety cohort detected
- Emitted: `segment_evaluated`, `segment_assignment_updated` (at recipient assignment in `scripts.pipeline`)

### Asset lifecycle

- ~~`asset_emotional_vector_tagged`~~ — emitted at `build_action_pool`
- ~~`asset_approved`~~ — automated gate clearance at `build_action_pool` (no human review queue step)
- ~~`asset_publish_requested`~~ — emitted per recipient in `run_campaign` before dispatch
- Emitted: `asset_draft_created`, `asset_validated` (at `build_action_pool`); `asset_dispatched`, `dispatch_failed` (at `run_campaign`)

## Flow gaps (vs proposed diagrams)

### [`proposed/04-sequence-diagram.md`](proposed/04-sequence-diagram.md)

| Sequence phase | Status |
|---|---|
| Visit + form + identity resolution | **Partial** — funnel + identity resolver emit core events |
| Evidence + claim lifecycle | **Partial** — verify/contradict/stale emit; extract/supersede do not |
| Emotional inference + cohorting | **Demo implemented** — campaign replay derives text signals, emits cohort events, and carries policy context through dispatch |
| Optimizer select + decision trace | **Implemented** — selection + trace recording |
| Gate + policy + review | **Partial** — Gate adapter + review queue; not all branches in sequence |
| Emotional mismatch reroute | **Demo implemented** — selected fear assets can reroute to active relief/neutral assets before publish; repeated high-arousal tracks block |
| Asset lifecycle + delivery | **Partial** — full catalog emit chain through publish; human approval workflow absent |

### [`proposed/03-reaction-loop.md`](proposed/03-reaction-loop.md)

The capstone emotional reaction cycle is now implemented end-to-end in deterministic replay:

`run_campaign` treats the bandit's selected asset as a proposal, derives a text sentiment signal from recipient urgency/use-case, evaluates `EmotionalSafetyPolicy`, emits emotional cohort + mismatch/reroute events, publishes the safe asset, and updates the bandit from the asset that actually shipped. Repeated high-arousal fear-track proposals are counted per recipient/vector and blocked at the configured cap.

Still out of scope for the demo: live ML/NLP inference, dwell/scroll ingestion, and a persisted `EmotionalSignal` aggregate.

### [`proposed/05-safety-policy.md`](proposed/05-safety-policy.md)

- **Factual + personal-data safety:** strong (Gate + Enrichment Gate + surface policy)
- **Emotional mismatch circuit breaker:** demo-complete — keyword rules, per-recipient/vector track counts, relief/neutral reroute, and block-on-cap are wired through campaign dispatch

## Intentionally out of scope (demo)

Per [`docs/05-build/DECISIONS.md`](../05-build/DECISIONS.md):

- RL / sequential credit assignment (R1) — contextual bandit only
- Live LLM inference default (R5, R6) — seeded deterministic replay
- Separate Gates per channel (R3) — one Assurance harness, sliced per channel
- Full multi-tenant production identity graph — demo resolver only

## Recommended next steps (priority order)

1. ~~**Emit remaining high-value catalog events**~~ — **done** for claim ingest/supersede, enrichment, emotional signals, asset approval/publish/tagging.
2. ~~**Wire emotional reaction loop**~~ — **done for capstone replay** in `run_campaign`; live behavioral ingestion remains out of scope.
3. **Segmentation aggregates** — only if product needs auditable membership history; today implicit segments suffice for demo.
4. **Human asset approval** — route cleared assets through review queue before `asset_approved` when compliance requires it.
5. **Policy / Optimizer persistence** — defer until multi-optimizer or policy versioning is a product need.

## Verification

When closing a gap, update:

- [`implemented/runtime-mapping.md`](implemented/runtime-mapping.md) maturity labels
- This file (remove or downgrade the gap entry)
- Proposed artifacts only if the **north-star model** itself changed (not when implementation catches up)
