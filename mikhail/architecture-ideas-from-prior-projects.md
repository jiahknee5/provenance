# Architecture Ideas from Prior Projects

Last updated: 2026-06-17

This is a partner-review menu: borrowable architecture patterns from prior projects that may be useful for Provenance. These are not decisions already made for the team. Partners can accept, reject, or defer each idea.

## Borrowable Patterns

| Idea | Borrowed from | How Provenance could use it | Adopt now? |
| --- | --- | --- | --- |
| Claim ledger as a first-class data model | Alcohol Label | Store candidate facts, enrichment outputs, trend-vector dimensions, and personalization claims as cited records with timestamps and review state. | Yes |
| Machine suggestion plus human review | Alcohol Label | Let enrichment and trend-vector jobs propose claims, but route uncertain/high-impact claims through a human review queue before they affect recommendations. | Yes |
| Audit trail as product UI | Alcohol Label | Give partners/admins an inspectable view of where a candidate signal came from, what it supports, and whether Gate accepted/rejected it. | Yes |
| Review-state lifecycle | Alcohol Label | Use explicit states like `draft`, `needs_review`, `approved`, `rejected`, `stale`, and `superseded` instead of a single `valid` boolean. | Yes |
| Resolve early, but not earlier | Mpsort | Order the pipeline as identity -> consent -> source collection -> claims -> trend vector -> Gate -> human review -> personalization. | Yes |
| Cost/certainty ordered pipeline | Mpsort | Run deterministic checks and official API fetches before Clay/AI research, and run expensive/ambiguous enrichment only where it changes a decision. | Yes |
| Bounded service contracts | Provenance scope decision | Keep intake/profile UI in our scope while Gate, Optimizer, Drift, and Assurance remain service contracts with clear inputs/outputs. | Yes |
| Drift-ready source snapshots | Alcohol Label + Provenance Drift | Preserve `evidence_url`, `observed_at`, provider, extracted fields, and source freshness so claims can be rechecked later. | Yes |
| VPS-ready service shape | Alcohol Label deploy pattern | Design collectors/enrichment jobs as separable services or scheduled workers that can later run via Docker Compose behind Traefik/Dokploy. | Later |
| Manual deploy path | Alcohol Label deploy pattern | If/when deployed, use GitHub Actions manual deploy, env in `/opt/<app>/.env`, and no public host ports except Traefik. | Later |
| Deploy artifact hygiene | Alcohol Label deploy pattern | Exclude `.codex`, local agent state, scratch exports, and secrets from any deploy or release artifact. | Later |

## Near-Term Recommendation

1. Build the front-end intake and candidate profile ledger first.
2. Model all enrichment as evidence-backed claims.
3. Model trend vectors as derived claims that cite underlying evidence.
4. Keep Clay as an optional enrichment workbench, not the system of record.
5. Keep Gate, Optimizer, Drift, and Assurance behind contracts until their owners are ready.

## Why These Fit Provenance

The useful through-line from prior projects is not any particular framework or deployment script. It is the habit of making claims inspectable, reviewable, and reversible.

For the candidate-research track, that means Provenance should avoid building an opaque candidate dossier. The architecture should produce:

- Source records: where data came from and when it was observed.
- Evidence-backed claims: what the source supports.
- Derived trend-vector claims: summaries that cite lower-level claims.
- Review state: whether a human or Gate accepted the claim for use.
- Freshness state: whether Drift needs to re-check the source.

That structure keeps the front-end useful now and gives the later Gate/Optimizer/Drift/Assurance services clean contracts.
