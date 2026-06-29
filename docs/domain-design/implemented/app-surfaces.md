# App surfaces (implemented)

> Code: `app/`. Entrypoint: `uvicorn app.main:app`.

FastAPI modules register routes on the shared `app` from `app/server.py`.

## Core funnel and outreach

| Route | Module | Purpose |
|---|---|---|
| `GET /`, `GET /lead`, `POST /submit` | `main.py` | Lead capture form → Recipient + enrichment |
| `GET /site/{token}` | `site.py` | Personalized website channel |
| `GET /personalize`, `GET /api/personalize` | `personalize.py` | Super-personalization provenance demo |
| `GET /lp`, `GET /admin/landings`, `GET /admin/landing/{pid}` | `cohort.py` | Cohort QR landing + admin gallery |
| `GET /google`, `GET /google/callback` | `google_login.py` | OAuth tier escalation demo |

## Optimizer and bandit

| Route | Module | Purpose |
|---|---|---|
| `GET /optimizer`, `GET /optimizer/bandit-dashboard` | `optimizer.py` | Bandit dashboard UI |
| `GET /api/optimizer/live`, `POST /api/optimizer/live/settle` | `optimizer.py` | Live optimizer replay API |
| `GET /api/optimizer/dashboard`, `GET /api/optimizer/lift` | `optimizer.py` | Campaign metrics |

## Governance and assurance

| Route | Module | Purpose |
|---|---|---|
| `GET /assurance` | `assurance.py` | Golden evals + Assurance dashboard |
| `GET /api/reviews`, `POST /api/reviews`, `PATCH /api/reviews/{id}` | `reviews.py` | Review queue API |
| `GET /assurance/reviews` | `reviews.py` | Review queue UI |
| `GET /policies`, `POST /policies/save` | `policies.py` | Rules corpus editor |

## Observability

| Route | Module | Purpose |
|---|---|---|
| `GET /observatory` | `observatory.py` | Operator node graph dashboard |
| `GET /api/observe/*` | `observatory.py`, `assurance.py`, `funnel.py` | Event/node/eval/funnel feeds |
| `GET /graph` | `graph.py` | Architecture graph viewer |
| `GET /funnel`, `GET /api/observe/funnel` | `funnel.py` | Customer journey view |

## Demo and workspace

| Route | Module | Purpose |
|---|---|---|
| `GET /demo`, `GET /demo/live`, `GET /api/demo/*` | `demo.py` | Interactive demo scenes |
| `GET /showcase/*` | `showcase.py` | Showcase tenant pages |
| `GET /workspace`, `GET /records/*` | `workspace.py` | Operator workspace |
| `GET /inspector` | `inspector.py` | Demo inspector |
| `GET /composer` | `composer.py` | Message composer |
| `GET /agent`, `GET /api/agent/run` | `agent.py` | Agent demo |
| `GET /sources`, `GET /archive`, `GET /help/*` | various | Supporting UI |

## Pipeline modules (no direct route)

These power the above but live under `pipeline/`:

- `pipeline/gate/` — claim verification
- `pipeline/optimizer/` — Thompson bandit campaigns
- `pipeline/drift/` — freshness monitor
- `pipeline/enrichment/` — fact synthesis + Enrichment Gate
- `pipeline/customer/` — funnel system of record
- `pipeline/personalization/` — cohort/landing tiers
- `pipeline/domain/` — event-sourced domain bridge

## PM frontend (separate repo)

The React PM app in `provenance-mn/` consumes domain event names via `src/domain/provenance.ts` but does not run the Python pipeline. It mirrors catalog vocabulary for UI prototyping; runtime truth remains in this repo.
