# Domain design documentation

Architecture docs for the Provenance demo are split into **proposed** (north-star target) and **implemented** (what the code does today), plus a gap analysis between them.

## Layout

| Path | Purpose |
|---|---|
| [`proposed/`](proposed/) | Canonical event-sourced domain model — context maps, aggregates, sequence diagrams, event catalog CSVs, and governance rules. **Target architecture**, not a guarantee of runtime completeness. |
| [`implemented/`](implemented/) | As-built description derived from `pipeline/`, `app/`, and `scripts/`. Start here to understand what actually runs. |
| [`implementation-gap.md`](implementation-gap.md) | Remaining work: proposed concepts not yet first-class in code, organized by area. |

## Where to start

- **Understanding the product thesis and target model** → [`proposed/01-context-map.md`](proposed/01-context-map.md) and [`proposed/project-architecture.md`](proposed/project-architecture.md)
- **Understanding what is built** → [`implemented/overview.md`](implemented/overview.md) and [`implemented/runtime-mapping.md`](implemented/runtime-mapping.md)
- **Planning implementation work** → [`implementation-gap.md`](implementation-gap.md)

## Code anchors

| Area | Path |
|---|---|
| Domain bridge (events, streams, stores) | `pipeline/domain/` |
| Demo schemas (Claim, Gate, Variant) | `pipeline/common/schemas.py`, `pipeline/gate/` |
| FastAPI surfaces | `app/` |
| Schema v2 cutover | `docs/05-build/DECISIONS.md` (R27) |
| Catalog sync CI | `scripts/check_domain_artifact_sync.py` |

## Governance

When changing files under `proposed/provenance_event_catalog/`, update the companion artifacts listed in [`proposed/harness-regressions.md`](proposed/harness-regressions.md) in the same change set. CI enforces this via `scripts/check_domain_artifact_sync.py`.

## Historical note

[`implemented/archive-implementation-fit-review-2026-06-25.md`](implemented/archive-implementation-fit-review-2026-06-25.md) predates the schema v2 domain bridge. Use [`implementation-gap.md`](implementation-gap.md) for current gap status.
