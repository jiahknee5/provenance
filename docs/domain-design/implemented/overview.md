# Implemented architecture overview

> Derived from code as of schema v2 (`SCHEMA_VERSION=2`, decision R27). Compare to north-star in [`../proposed/`](../proposed/).

## What the demo proves

The runtime implements a **truth-bounded outreach pipeline**:

1. Claims are verified against evidence before copy can ship (Gate).
2. The optimizer (Thompson bandit) selects only Gate-cleared variants.
3. Drift re-verifies affected claims when sources or rules change.
4. Personal/enrichment facts pass an Enrichment Gate before copy use.
5. Domain events are recorded to append-only JSONL streams for audit and replay.

Intentional demo simplifications (contextual bandit not RL, seeded replay not live inference, single Assurance harness) are documented in [`../../05-build/DECISIONS.md`](../../05-build/DECISIONS.md).

## Two parallel event systems

| System | Module | Purpose |
|---|---|---|
| **Domain streams** | `pipeline/domain/` | Catalog event names, full envelopes, aggregate streams — **source of truth** for schema v2 |
| **Observe lanes** | `pipeline/common/observe.py` | Operator debug graph for Observatory UI; no-op unless a recorder is attached |

Domain emission is always-on when a `DomainRecorder` is active (`start_domain_run`). Observe remains for deterministic UI traces (R12).

## First-class aggregates (schema v2)

These have models under `pipeline/domain/models/` and SQLite stores under `pipeline/domain/stores/`:

| Aggregate | Model | Store | Notes |
|---|---|---|---|
| `Profile` | `models/profile.py` | `stores/profile_store.py` | Unifies customer + enrichment; legacy `CustomerStore` delegates here |
| `Asset` | `models/asset.py` | `stores/asset_store.py` | Replaces `Variant` at runtime boundary; lifecycle enum |
| `Review` | `models/review.py` | `stores/review_store.py` | Human queue; AMBER reviews are advisory |
| `DecisionTrace` | `models/decision_trace.py` | `stores/decision_trace_store.py` | Explainability records at Gate, campaign, override |

## Partial / demo-layer constructs

Core demo schemas in `pipeline/common/schemas.py` still power Gate and optimizer:

- `ClaimNode`, `ClaimVerdict`, `SourceDoc` — claim/evidence substrate
- `Variant`, `Recipient`, `ActionPool`, `PosteriorStore` — bandit campaign
- `RulesEngine` — YAML policy, not a `Policy` aggregate

Domain adapters translate runtime behavior into catalog events without renaming core schemas.

## Domain bridge modules

| Module | Role |
|---|---|
| `envelope.py` | `EventEnvelope` matching `proposed/provenance_event_catalog/Event-Envelope.csv` |
| `streams.py` | Append-only JSONL per `StreamType` (`lead`, `asset`, `review`, `account`, `decision_trace`) |
| `emit.py` | `emit_domain`, correlation/causation, recorder lifecycle |
| `adapters/gate.py` | Gate verdicts → `claim_verified`, `policy_evaluated`, `claim_contradicted`, `dispatch_suppressed` |
| `adapters/campaign.py` | Bandit selection → `asset_selection_recorded` |
| `adapters/funnel.py` | Funnel touchpoints → `form_submitted`, `evidence_captured`, etc. |
| `adapters/drift.py` | Drift → `claim_marked_stale`, `claim_reverification_requested` |
| `identity.py` | `IdentityCandidate`, resolver → identity catalog events |
| `emotional.py` | Rule-based emotional signals + mismatch circuit breaker |
| `decision_trace.py` | `decision_trace_recorded`, `decision_overridden` |
| `review.py` | Review lifecycle events + `check_dispatch` |

## Stream layout

Streams live under `data/streams/{stream_type}/{stream_id}.jsonl`. Demo data is in `data/demo/streams/`. Replay: `python -m scripts.replay_streams --verify`.

## Related docs

- [`runtime-mapping.md`](runtime-mapping.md) — entity-by-entity maturity table
- [`domain-bridge.md`](domain-bridge.md) — event emission and adapter details
- [`app-surfaces.md`](app-surfaces.md) — FastAPI routes and UI entry points
- [`../implementation-gap.md`](../implementation-gap.md) — remaining north-star work
