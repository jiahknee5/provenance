# Demo alignment changelog

Tracks domain-design gap closures and alignment decisions on branch `vr/demo-alignment`.

## 2026-06-29 — Catalog event emitters (implementation-gap closure)

### Closed gaps

| Gap | Implementation | Files |
|---|---|---|
| `claim_extracted` | Emit per claim on library `from_seed()` / `load()` | `pipeline/domain/adapters/claim.py`, `pipeline/library/library.py` |
| `claim_superseded` | Emit on `mark_verified()` source rebind; optional `supersedes_claim_id` at ingest | same + `pipeline/common/schemas.py` |
| `enrichment_requested` / `enrichment_received` | Emit around `enrich()` connector fan-out | `pipeline/domain/adapters/enrichment.py`, `pipeline/enrichment/engine.py` |
| `asset_emotional_vector_tagged` | Emit after draft at `build_action_pool` | `pipeline/domain/adapters/asset.py`, `pipeline/generation/variants.py` |
| `asset_approved` | Automated gate clearance (not human review) | same |
| `asset_publish_requested` | Emit before dispatch in `run_campaign` | `pipeline/optimizer/campaign.py` |
| `text_sentiment_scored` | Emit for text-derived signals in emotional policy | `pipeline/domain/emotional.py` |
| `emotional_signal_detected` | Already present; now preceded by sentiment scoring | `pipeline/domain/emotional.py` |
| `emotional_segment_assignment_updated` | Emit when high-anxiety cohort detected | `pipeline/domain/emotional.py` |

### Decisions

- **Asset approval is automated** — cleared variants get `asset_approved` with `approved_by: gate_auto` in payload; human review queue remains advisory for AMBER claims only (existing contract).
- **Claim supersession is source-rebind** — demo models supersede as same `claim_id` rebound to a new `source_version`, not a separate claim aggregate revision.
- **Emotional policy not in campaign loop yet** — events emit when `EmotionalSafetyPolicy.evaluate()` is called; wiring into `run_campaign` deferred (reaction loop still partial).

### Tests

- `tests/test_domain_events.py` — claim ingest/supersede, extended asset lifecycle
- `tests/test_emotional_safety.py` — sentiment + emotional cohort events
- `tests/test_optimizer.py`, `tests/test_enrichment.py` — regression green

### Remains (see `implementation-gap.md`)

- Emotional reaction loop end-to-end in campaign
- Segmentation / Policy / Optimizer persisted aggregates
- Human asset approval workflow
- ML-based emotional inference
