# Runtime mapping (implemented ↔ proposed)

> **North-star target:** [`../proposed/`](../proposed/)  
> **Gap analysis:** [`../implementation-gap.md`](../implementation-gap.md)  
> This document maps proposed entities to code with explicit maturity labels.

## Maturity labels

| Label | Meaning |
|---|---|
| `implemented` | First-class runtime construct matching the canonical shape |
| `partial` | Behavior exists under a different name or split across modules |
| `planned` | Canonical model documented; bridge module owns the rollout |
| `out_of_scope` | Intentionally simplified for the demo (see scope boundaries) |

## Scope boundaries (demo by design)

Per [`docs/05-build/DECISIONS.md`](../../05-build/DECISIONS.md):

- **Contextual bandit**, not RL — Thompson sampling, no sequential credit assignment (R1).
- **Seeded replay**, not live inference — deterministic trace for Observatory (R5).
- **Single Assurance harness** — results sliced per channel, not separate Gates (R3).
- **Observe lanes** — operator debug graph (`pipeline/common/observe.py`, R12); canonical domain streams are the **authoritative event source** (`pipeline/domain/`, projector-backed read models).
- **AMBER is sendable** — uncertain claims ship with disclaimer; review is **advisory** for AMBER, not a dispatch block (see Phase 3 contract).

## Aggregate mapping

| Canonical entity | Maturity | As-built module(s) | Field / behavior notes |
|---|---|---|---|
| `Claim` | partial | `ClaimNode`, `ClaimVerdict` in `pipeline/common/schemas.py` | `text`≈`claim_value`; `status` uses `ClaimStatus` not canonical lifecycle; no `supersedes_claim_id` events yet |
| `Evidence` | partial | `SourceDoc`, spans, `RawFact`, `ProfileFact` | No standalone `evidence_id` + immutable event linkage |
| `Gate` | partial | `pipeline/gate/gate.py` | Verdict cascade implemented; domain events via `pipeline/domain/adapters/gate.py` |
| `Policy` | partial | `RulesEngine`, `EnrichmentGate`, `surface` policy | YAML rules, not `Policy` aggregate |
| `Optimizer` | partial | `ThompsonBandit`, `PosteriorStore`, `run_campaign`, `LiveOptimizer` | Metadata implicit in code/artifacts |
| `BanditPolicy` | partial | `ThompsonBandit` | Code-level strategy, not persisted object |
| `Profile` | implemented | `pipeline/domain/models/profile.py`, `pipeline/domain/stores/profile_store.py` | Namespaced aggregate; `CustomerStore` / enrichment `ProfileStore` delegate here |
| `IdentityCandidate` | partial | `pipeline/domain/identity.py` + funnel stitching | Resolver emits catalog identity events |
| `Asset` | implemented | `pipeline/domain/models/asset.py`, `pipeline/domain/stores/asset_store.py` | Lifecycle enum; `Variant` alias; `ActionPool` uses `asset_id` |
| `Review` | implemented | `pipeline/domain/stores/review_store.py` | Advisory for AMBER; non-advisory blocks dispatch via `check_dispatch` |
| `DecisionTrace` | implemented | `pipeline/domain/stores/decision_trace_store.py` | SQLite-backed; wired at Gate/campaign/review override |
| `SegmentDefinition` | partial | `ROLE_ANGLES`, cohort `segments.py` | No ruleset version aggregate |
| `SegmentAssignment` | partial | Recipient `segment`, customer `Stage`, cohort tiers | Implicit membership |
| `Event` envelope | partial | `pipeline/domain/envelope.py`, `emit.py` | Canonical shape; parallel to observe |
| `EmotionalSignal` | partial | `pipeline/domain/emotional.py` | Rule-based stub, no ML |
| `EmotionalVectorTag` | partial | `Variant.emotional_vector` | Populated in `pipeline/generation/variants.py` |

## Event catalog mapping (behavior → canonical name)

| Runtime behavior | Canonical event | Adapter / emitter |
|---|---|---|
| Gate GREEN verdict | `claim_verified` | `domain/adapters/gate.py` |
| Gate AMBER verdict | `policy_evaluated` (+ optional advisory `review_requested`) | Same; **not** `claim_contradicted` |
| Gate RED (unsupported) | `claim_contradicted` | Same |
| Gate RED (compliance veto) | `policy_evaluated` + `dispatch_suppressed` | Same |
| Rules engine decision | `policy_evaluated` | `domain/adapters/gate.py` |
| Drift re-verify | `claim_marked_stale`, `claim_reverification_requested` | `domain/adapters/drift.py` |
| Recipient segment assignment | `segment_evaluated`, `segment_assignment_updated` | `domain/adapters/segment.py` (at `scripts.pipeline`) |
| Asset create + gate clearance | `asset_draft_created`, `asset_validated` | `domain/adapters/asset.py` (at `build_action_pool`) |
| Per-recipient bandit select | `asset_selection_recorded` | `domain/adapters/campaign.py` (inside recipient loop) |
| Per-recipient serve / no-arm | `asset_dispatched`, `dispatch_failed` | `domain/adapters/asset.py` (at `run_campaign`) |
| Segment winner summary | (observe DECISION only) | Not duplicated as domain event |
| Funnel touchpoint | `evidence_captured`, `form_submitted`, etc. | `domain/adapters/funnel.py` |
| Identity resolve | `identity_resolution_requested`, `identity_resolved`, `identity_conflicted` | `pipeline/domain/identity.py` |
| Review queue | `review_requested`, `review_approved`, `review_rejected`, `review_escalated` | `pipeline/domain/review.py` |
| Explainability | `decision_trace_recorded`, `decision_overridden` | `pipeline/domain/decision_trace.py` |
| Emotional mismatch | `emotional_mismatch_blocked`, `emotional_reroute_applied` | `pipeline/domain/emotional.py` |

## Observe vs domain streams

| Concern | Observe (`observe.emit`) | Domain (`emit_domain`) |
|---|---|---|
| Purpose | Operator node graph, UI/Observatory | Business audit, catalog replay |
| Vocabulary | INPUT, TOOL, DECISION, OUTPUT, DRIFT… | Catalog snake_case names |
| Default | No-op unless recorder | Always-on recorder + projector on emit |
| Envelope | seq, lane, node, phase | Full [`Event-Envelope.csv`](../proposed/provenance_event_catalog/Event-Envelope.csv) fields |

## Implementation anchors

| Area | Path |
|---|---|
| Domain bridge | `pipeline/domain/` |
| Core schemas | `pipeline/common/schemas.py` |
| Gate | `pipeline/gate/gate.py` |
| Optimizer | `pipeline/optimizer/campaign.py`, `live.py` |
| Drift | `pipeline/drift/monitor.py` |
| Customer / funnel | `pipeline/customer/funnel.py` |
| Review API | `app/reviews.py` |
| Governance CI | `scripts/check_domain_artifact_sync.py`, `tests/test_domain_artifact_sync.py` |

## Migration v2 cutover checklist

1. `SCHEMA_VERSION = 2` stamped in `pipeline/common/config.py`, SQLite `schema_meta`, event envelope `metadata.schema_version`, and `data/demo/manifest.json`.
2. Run `python -m scripts.migrate_v1_to_v2` to bootstrap unified `Profile` rows from v1 `customers` + enrichment `profiles` tables.
3. Run `python -m scripts.trace` then `python -m scripts.replay_streams --verify` to rebuild projections from domain streams.
4. Verify `pytest` green and `scripts/check_domain_artifact_sync.py` passes.
5. Deprecated paths: direct `customers.sqlite` writes (use `ProfileStore`); in-memory decision traces; `CanonicalProfile` facade (`pipeline/domain/profile.py` shim only).
