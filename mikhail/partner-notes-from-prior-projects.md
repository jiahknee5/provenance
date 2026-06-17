# Partner Notes from Prior Projects

Last updated: 2026-06-17

These are reusable findings from adjacent work that seem directly useful for Provenance.

## Product Patterns

### Alcohol Label

Useful pattern: one repo can hold product UI, evidence/audit records, and review workflows without prematurely splitting services.

What to reuse:

- Evidence-first records: every machine recommendation should point to the source facts that produced it.
- Machine recommendation plus human review: the system can draft, rank, and flag, but humans decide at the high-risk boundary.
- Audit trail as product surface: do not bury provenance in logs; make it inspectable in the UI.
- Review states: `draft`, `needs_review`, `approved`, `rejected`, `stale`, and `superseded` are more useful than a single boolean.
- Deployment shape for later: GitHub Actions manual deploy, Docker Compose, Dokploy/Traefik on VPS, app env in `/opt/<app>/.env`, no public host ports except Traefik.
- Repo hygiene for deploys: exclude `.codex` and local agent state from deploy artifacts.

How it maps to Provenance:

- Candidate profile enrichment should produce evidence-backed claims, not just a merged profile blob.
- Trend vectors should be treated as machine recommendations that require citation and review.
- Gate/Assurance outputs should be visible to the operator, not only used internally.

### Mpsort

Useful principle: "resolve as early as possible, but not earlier."

What to reuse:

- Order decision layers by cost and certainty.
- Use cheap deterministic checks before expensive model calls.
- Resolve identity and consent before enrichment.
- Resolve obvious exclusions before scoring.
- Let humans decide when the evidence is ambiguous, high-impact, or policy-sensitive.

How it maps to Provenance:

1. Start with Tom export and participant self-intake.
2. Confirm handles/URLs and consent.
3. Run low-risk public-source collection.
4. Generate evidence-backed claims.
5. Build trend vectors only from accepted claims.
6. Route uncertain or high-impact claims to human review.
7. Let Gate/Assurance decide what can be used in personalization or recommendations.

## Architecture Ideas

Architecture patterns worth borrowing are split into a separate partner-review document:

- [architecture-ideas-from-prior-projects.md](./architecture-ideas-from-prior-projects.md)

## Candidate Research Implications

- A candidate profile is not a dossier; it is a set of reviewable claims plus derived, cited trends.
- Clay can speed up enrichment, but Provenance must still own the claim ledger and review policy.
- Trend vectors should summarize behavior over time: topic momentum, artifact velocity, depth trajectory, collaboration pattern, communication style, and evidence diversity.
- Anything sensitive, protected, private, or hard to correct should stay out of the vector.
- The UI should make correction natural: "This source is mine / not mine", "This claim is wrong", "Do not use this signal", and "Add supporting evidence."

## Partner Takeaway

The strongest version of Provenance is not "we enrich candidates better." It is:

> We turn messy public and first-party signals into cited, reviewable claims; then we let governed systems personalize and recommend only inside those claims.
