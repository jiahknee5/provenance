# Mikhail Working Notes

Last updated: 2026-06-17

These notes are a temporary research/workbench area until the PM finalizes the project organization and PRD. Keep root-level artifacts, especially the PM PDF, untracked unless the team decides where they belong.

## Current Working Frame

The latest PM planning document makes the official capstone path:

1. Email-channel Gate MVP.
2. Live claim ledger with cited / repaired / blocked states.
3. Assurance Lab metrics and calibration proof.
4. Regulatory/legal-hold toggle.
5. "Try to make it lie" adversarial demo.
6. Website adapter, optimizer, cohort personalization, and enrichment providers as optional or ambitious extensions.

That means the research here should support the claim-ledger/Gate path first. Candidate background enrichment remains useful, but it is not the center of the current MVP unless the PM re-scopes it back in.

## Notes Index

- [pm-plan-linkt-impact-notes.md](./pm-plan-linkt-impact-notes.md) — current interpretation of the PM PDF plus Linkt fit.
- [architecture-ideas-from-prior-projects.md](./architecture-ideas-from-prior-projects.md) — borrowable architecture patterns, VPS/email/OCR notes, and near-term implementation shape.
- [social-data-sources-for-candidate-matching.md](./social-data-sources-for-candidate-matching.md) — candidate/cohort enrichment research; now framed as an extension to the claim-ledger model.
- [partner-notes-from-prior-projects.md](./partner-notes-from-prior-projects.md) — short partner-facing lessons from prior projects.

## Working Rule

Every external enrichment output should become a cited Provenance claim before it influences copy, recommendations, or scoring.

For the MVP, prioritize:

- claim and evidence schemas;
- claim-ledger UI;
- email/test-mail flow;
- Gate/Assurance integration contracts;
- realistic B2B demo tenant data.

Defer:

- automated candidate scoring;
- social-media red/green flags;
- broad third-party pixels;
- direct VPS outbound SMTP;
- production deployment decisions.
