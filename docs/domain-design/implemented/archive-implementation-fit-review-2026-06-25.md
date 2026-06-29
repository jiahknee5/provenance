# Current Implementation vs Domain Design Review (archived)

> **Superseded by:** [`../implementation-gap.md`](../implementation-gap.md) and [`runtime-mapping.md`](runtime-mapping.md). Kept for historical context only.

Review date: 2026-06-25 (updated after domain bridge implementation)

Canonical design source: `docs/domain-design/proposed/`

Implementation source: current Python/FastAPI demo in `pipeline/`, `app/`, `scripts/`, and `tests/`

Runtime traceability: [`runtime-mapping.md`](runtime-mapping.md)

## Post-implementation maturity (domain bridge)

| Area | Prior fit | Current maturity | Notes |
|---|---|---|---|
| Event envelope | Gap | partial | `pipeline/domain/envelope.py` + `emit.py` |
| Event catalog | Gap | partial | Context-aware adapters at Gate, drift, campaign, funnel |
| Stream types | Gap | partial | `pipeline/domain/streams.py` JSONL per aggregate |
| IdentityCandidate | Gap | partial | `pipeline/domain/identity.py` + funnel wiring |
| Review | Gap | partial | Advisory for AMBER; `app/reviews.py` API + queue UI |
| DecisionTrace | partial | partial | `pipeline/domain/decision_trace.py` + agent intent |
| Emotional safety | Gap | partial | `pipeline/domain/emotional.py`; `Variant.emotional_vector` |
| Profile | partial | partial | `pipeline/domain/profile.py` facade |

## Executive Verdict

The current implementation is a strong working demo of the core Provenance promise: generated outreach cannot ship unsupported claims, the optimizer can only choose Gate-cleared variants, drift re-verifies affected claims, and personal facts are gated before copy use.

It is not yet a full implementation of the canonical domain design. The canonical model in `docs/domain-design/` describes a richer event-sourced domain with typed event envelopes, stream ownership, identity candidates, review lifecycle, decision traces, emotional signal cohorts, and emotional mismatch rerouting. The current code implements many of those behaviors through simpler demo contracts: claim-evidence schemas, verdict ledgers, action pools, observability events, customer records, and enrichment fact receipts.

Fit labels used below:

| Label | Meaning |
|---|---|
| Strong fit | The current implementation directly enforces the domain intent. |
| Partial fit | The implementation covers the behavior, but with simpler or differently named contracts. |
| Gap | The canonical domain concept is not implemented as a first-class runtime construct. |
| Different by design | The implementation intentionally uses a demo/runtime contract instead of the canonical shape. |

## Implementation Anchors

| Area | Current anchors |
|---|---|
| Core schemas | `pipeline/common/schemas.py` |
| Claim/evidence library | `pipeline/library/library.py` |
| Gate and rules | `pipeline/gate/gate.py`, `pipeline/gate/rules.py` |
| Optimizer and bandit | `pipeline/optimizer/bandit.py`, `pipeline/optimizer/campaign.py`, `pipeline/optimizer/live.py` |
| Drift | `pipeline/drift/monitor.py` |
| Enrichment safety | `pipeline/enrichment/schemas.py`, `pipeline/enrichment/gate.py`, `pipeline/enrichment/engine.py` |
| Customer journey and identity stitching | `pipeline/customer/schemas.py`, `pipeline/customer/funnel.py`, `pipeline/customer/store.py` |
| Runtime observability | `pipeline/common/observe.py`, `pipeline/common/topology.py` |
| App surfaces | `app/site.py`, `app/optimizer.py`, `app/observatory.py`, `app/assurance.py` |

## Traceability Matrix

| Canonical concept | Fit | Current implementation | Gap or note |
|---|---|---|---|
| `Claim` | Strong fit | `ClaimNode` binds each claim to source id, source span, source version, status, numeric metadata, segment tags, and rule tags. `ClaimVerdict` captures verdict, confidence, reasons, rules version, and source version. | Field names differ from the canonical `Claim` entity, but the verification and lifecycle intent is implemented. |
| `Evidence` | Strong fit | `SourceDoc`, source spans, `bound_evidence()`, and retrieval corpus model the evidence substrate. Enrichment `RawFact` and `ProfileFact` add personal-data evidence receipts. | Evidence is not a standalone canonical `Evidence` entity with `evidence_id`, `evidence_type`, and immutable event linkage. |
| `Gate` | Strong fit | `Gate.verify_claim()` performs retrieve, rules, NLI, ensemble, calibration, verdict cache, and message ledger generation. | The Gate emits observability records, not canonical `policy_evaluated`, `claim_verified`, or `dispatch_suppressed` events. |
| `Policy` | Partial fit | `RulesEngine` enforces holds, blocks, disclaimers, and rules version. `EnrichmentGate` enforces allow-list, consent, TTL, PHI/PII blocks, and basis. Customer `surface` policy controls say/allude/hold. | Policy exists as YAML-backed rule engines, not a first-class `Policy` aggregate with `policy_id`, `scope`, `expression`, and severity. |
| `Optimizer` | Strong fit | `ActionPool`, `PosteriorStore`, `ThompsonBandit`, `run_campaign()`, and `LiveOptimizer` implement truth-bounded selection and learning. | Canonical optimizer metadata such as `optimizer_id`, objective, context features, reward metric, and strategy ref is implicit in code and persisted artifacts. |
| `BanditPolicy` | Strong fit | `ThompsonBandit` and `PosteriorStore` are the active strategy implementation. | The strategy is code-level, not a separate persisted `BanditPolicy` object. |
| Drift and freshness | Strong fit | `DriftMonitor` walks claim-to-source dependencies, re-Gates only affected claims, and pauses or unblocks variants. Rule-version changes force re-verification through the verdict cache key. | Canonical `claim_marked_stale`, `claim_reverification_requested`, and `claim_superseded` events are not emitted. |
| `Profile` | Partial fit | Enrichment `Profile` stores recipient facts and derived signals. Customer `Customer` stores identity, touchpoint timeline, facts, consent, stage, and magic token. | There is no single canonical `Profile` aggregate with `active_claim_refs`, `segment_refs`, copy-safe refs, routing-only refs, and reconciliation timestamp. |
| `IdentityCandidate` | Gap | Customer storage resolves by visitor id, email, and magic token. Personalization has identity-graph signal categories. | There is no first-class identity candidate object, match confidence, conflict status, or resolver workflow. |
| `Event` envelope | Gap | `pipeline/common/observe.py` writes deterministic JSONL observability events with a closed vocabulary such as `INPUT`, `TOOL`, `DECISION`, `OUTPUT`, `DRIFT`, and `CACHE_HIT`. | The canonical envelope fields from `Event-Envelope.csv` are not implemented: `event_id`, `event_name`, `stream_id`, `stream_type`, `stream_position`, `correlation_id`, `causation_id`, `subject_ref`, `actor`, `policy_ref`, `review_ref`, `trace_ref`, and `privacy_tier`. |
| Event catalog | Gap | Runtime behavior exists for many cataloged actions, especially claim verification, policy checks, drift, asset selection, and dispatch-like serving. | Canonical event names such as `claim_verified`, `policy_evaluated`, `asset_selection_recorded`, `decision_trace_recorded`, `review_requested`, and `emotional_mismatch_blocked` appear only in `docs/domain-design/`. |
| Stream types | Gap | Runtime ledgers are organized by observability lanes and files, not by aggregate streams. | The canonical `lead`, `asset`, `review`, `account`, and `decision_trace` streams are not implemented as ordered append-only domain streams. |
| `Asset` | Partial fit | `Variant` models channel, segment, template, arm label, claim ids, planted-lie flag, and headline. `build_action_pool()` validates variants before optimizer use. | No first-class `Asset` lifecycle with status, policy version, approval fields, publish timestamp, or emotional vector tags. |
| `Review` | Gap | The Gate can block, amber, or red claims; rules can represent legal holds. Assurance provides adversarial validation. | No human review aggregate, queue, assignment, approve/reject/escalate lifecycle, or review stream. |
| `DecisionTrace` | Partial fit | `MessageLedger`, `ClaimVerdict`, campaign traces, ledgers, observability logs, and golden eval graph logs explain decisions. | No canonical `DecisionTrace` store with claim refs, evidence refs, rule refs, asset ref, actor type, actor id, and durable explanation record. |
| Segmentation | Partial fit | Recipient `segment` values, role/company-size microsegments, personalization segments, customer stages, and derived enrichment signals drive selection. | No `SegmentDefinition` and `SegmentAssignment` aggregates with ruleset version, membership state, confidence, evaluated time, and validity window. |
| Emotional signals | Gap | Customer and personalization code includes surface policy, persuasion, and signal categories; demo scenarios include persuasion/emotional framing concepts. | No first-class `EmotionalSignal`, `EmotionalVectorTag`, emotional cohort assignment, arousal-track cap, or emotional mismatch circuit breaker. |
| Safety policy | Strong fit for factual/personal-data safety; gap for emotional safety | Claim Gate blocks unsupported or impermissible claims. Enrichment Gate blocks unreceipted, stale, PHI/PII, disallowed-source, and non-consented facts. Customer surface policy prevents creepy reuse. | The canonical emotional mismatch policy from `05-safety-policy.md` is not implemented as a dispatch circuit breaker. |

## Canonical Artifact Coverage

| Domain-design artifact | Implementation fit |
|---|---|
| `01-context-map.md` | Core claim, gate, optimizer, activation, and enrichment contexts exist. Identity resolver, review/compliance lifecycle, decision trace context, and emotional safety context are only partial or missing. |
| `02-aggregate-model.md` | The demo implements a smaller aggregate set: `SourceDoc`, `ClaimNode`, `ClaimVerdict`, `MessageLedger`, `Variant`, `Recipient`, enrichment `ProfileFact`, customer `Customer`, `ActionPool`, and `PosteriorStore`. Several canonical aggregates remain conceptual only. |
| `03-reaction-loop.md` | The optimizer loop exists for asset serving, clicks/no-clicks, reward updates, and re-selection. The emotional signal detection, emotional segment update, policy evaluation, and emotional reroute path is not implemented end to end. |
| `04-sequence-diagram.md` | Evidence/claim verification, optimizer selection, Gate validation, website dispatch, drift, and assurance are implemented. Identity resolution, canonical event recording, human review, and emotional mismatch rerouting are gaps. |
| `05-safety-policy.md` | Factual safety and personal-data safety are strong. Emotional mismatch blocking and relief/neutral rerouting are not first-class runtime behavior. |
| `06-field-purpose-and-domain-data-model.md` | The demo has equivalent or adjacent fields for claims, evidence receipts, verdicts, variants, recipients, customer facts, and optimizer state. It does not yet implement the complete canonical entity field set. |
| `provenance_event_catalog/` | The catalog is canonical documentation. Runtime code does not emit the cataloged event names or envelope shape. |
| `harness-regressions.md` | The warning about keeping canonical artifacts synchronized is relevant. If event catalog or envelope changes become runtime work, review should require coordinated updates across diagrams, field-purpose model, and catalog CSVs. |

## Recommended Path

Keep the current demo contracts stable for the showcase/runtime path. They already prove the main product thesis with focused code, deterministic tests, and inspectable artifacts.

If the project moves from demo implementation toward the canonical domain architecture, add a bridge rather than replacing the working pipeline:

1. Introduce a typed `DomainEvent` or `EventEnvelope` module that matches `Event-Envelope.csv`.
2. Add adapter emitters at existing decision points in Gate, Drift, Optimizer, Enrichment Gate, customer funnel, and website dispatch.
3. Map existing observability events to canonical event names where the behavior is already real, while preserving `pipeline/common/observe.py` for deterministic UI/debug traces.
4. Add canonical stream writers for `lead`, `asset`, `review`, `account`, and `decision_trace` only after event names and payloads are stable.
5. Implement `IdentityCandidate`, `Review`, `DecisionTrace`, and emotional mismatch/reroute only when the product flow needs them as runtime behavior, not just as diagram completeness.

## Verification Notes

This review is documentation-only. It should not change public APIs, schemas, tests, runtime behavior, or canonical design artifacts.

Before merging, verify:

| Check | Expected result |
|---|---|
| `docs/domain-design/implementation-fit-review.md` exists | New review file is present. |
| Existing root `plan.md` is untouched | No diff to `plan.md` from this change. |
| Canonical design files are untouched | No diff to `01-context-map.md`, `02-aggregate-model.md`, `03-reaction-loop.md`, `04-sequence-diagram.md`, `05-safety-policy.md`, `06-field-purpose-and-domain-data-model.md`, or `provenance_event_catalog/*`. |
| Referenced implementation anchors exist | Every path named in the anchors table exists in the repo. |
| Review covers all canonical areas | Aggregate model, event envelope/catalog, stream types, sequence, reaction loop, and safety policy are all addressed above. |

