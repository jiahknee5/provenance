# Domain bridge (implemented)

> Code: `pipeline/domain/`. Envelope spec: [`../proposed/provenance_event_catalog/Event-Envelope.csv`](../proposed/provenance_event_catalog/Event-Envelope.csv).

## Event envelope

`EventEnvelope` in `pipeline/domain/envelope.py` implements the catalog fields:

- Identity: `event_id`, `event_name`, `event_version`
- Timing: `occurred_at`, `recorded_at`
- Stream: `stream_id`, `stream_type`, `stream_position`
- Tracing: `correlation_id`, `causation_id`
- Context: `tenant_id`, `subject_ref`, `actor`, `source`, `payload`
- Optional refs: `policy_ref`, `review_ref`, `trace_ref`, `privacy_tier`, `metadata`

`StreamType` enum: `lead`, `account`, `asset`, `review`, `decision_trace`.

## Recording and emission

```text
start_domain_run(run_id) → DomainRecorder active
emit_domain(event_name, stream_id, stream_type, subject_ref, payload, ...)
end_domain_run()
```

- `DomainRecorder` (`streams.py`) assigns monotonic `stream_position` per stream and writes JSONL.
- Projectors update SQLite read models on emit (disposable projections; streams are SOT).
- When no recorder is active, `emit_domain` is a no-op (tests unchanged).

## Adapter emission points

### Gate (`adapters/gate.py`)

| Verdict | Events emitted |
|---|---|
| GREEN | `claim_verified` |
| AMBER | `policy_evaluated` (+ optional advisory `review_requested`) |
| RED unsupported | `claim_contradicted` |
| RED compliance veto | `policy_evaluated`, `dispatch_suppressed` |

AMBER is **sendable with disclaimer** — not treated as `claim_contradicted`.

### Campaign (`adapters/campaign.py`)

Per-recipient bandit draw → `asset_selection_recorded` on the `asset` stream.

### Funnel (`adapters/funnel.py`)

Touchpoint capture → `form_submitted`, `evidence_captured`, `visitor_identified`, etc. on `lead` streams.

### Drift (`adapters/drift.py`)

Source/rule change → `claim_marked_stale`, `claim_reverification_requested`.

### Identity (`identity.py`)

`IdentityResolver.resolve()` → `identity_resolution_requested`, then `identity_resolved` or `identity_conflicted`.

### Emotional (`emotional.py`)

Rule-based keyword detection (not ML). On mismatch → `emotional_mismatch_blocked`, optional `emotional_reroute_applied`.

### Decision trace (`decision_trace.py`)

Gate/campaign/override paths → `decision_trace_recorded`, operator override → `decision_overridden`.

### Review (`review.py` + `stores/review_store.py`)

Queue CRUD via `app/reviews.py` API. Lifecycle: `review_requested`, `review_approved`, `review_rejected`, `review_escalated`. `check_dispatch()` blocks non-advisory rejections only.

## Events not yet emitted at runtime

Many catalog events in [`../proposed/provenance_event_catalog/Event-Catalog.csv`](../proposed/provenance_event_catalog/Event-Catalog.csv) have no adapter yet — see [`../implementation-gap.md`](../implementation-gap.md).

## Observe vs domain

| | Domain | Observe |
|---|---|---|
| Vocabulary | Catalog snake_case | INPUT, TOOL, DECISION, OUTPUT, DRIFT… |
| Default | Active with domain run | No-op without recorder |
| Consumer | Replay, audit, projectors | Observatory UI, golden evals |

Both can fire for the same logical decision; domain is authoritative for schema v2.

## Verification commands

```bash
python -m scripts.trace
python -m scripts.replay_streams --verify
python -m scripts.check_domain_artifact_sync
pytest tests/test_domain_artifact_sync.py
```
