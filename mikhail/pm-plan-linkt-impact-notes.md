# PM Plan and Linkt Impact Notes

Working note only until the PM finalizes repo organization.

Last reviewed: 2026-06-17

Inputs:

- Root PDF: `Project Planning Document — Provenance (Gauntlet Capstone).pdf`
- Linkt resource: https://www.linkt.ai/

## What The PM Plan Changes

The PDF centers the official capstone around a controlled, graded demo:

- The minimum shippable product is **The Gate end-to-end on one channel: email**.
- The live product surface is the **claim ledger**: cited, repaired, blocked.
- The Assurance Lab MVP is required: synthetic traps, catch-rate, false-reject rate, and calibration/reliability diagram.
- The regulatory/legal-hold toggle and "try to make it lie" adversarial moment are required.
- The website adapter and optimizer are ambitious/showcase additions, not the first dependency.
- The demo tenant is Helix-style regulated B2B with realistic prospects, source docs, and an MLR hold.

Short version: the current plan is not "build the best enrichment engine." It is "prove the Gate can govern generated outreach at claim level."

Implication for my research:

- Candidate/social enrichment should be treated as a **later intake/personalization extension**, not the core capstone path.
- The most immediately relevant pieces from the research are the claim-ledger contract, evidence-backed trend vectors, human review, email delivery, and VPS-ready service shape.
- Any candidate background analysis should map into the same claim ledger rather than becoming a separate scoring dossier.
- For near-term partner alignment, frame our responsibility as:
  1. front-end intake,
  2. claim/evidence review surfaces,
  3. email/test-mail support,
  4. optional website adapter,
  5. optional enrichment workbench integration.

## Research Items To Reclassify

Keep near-term:

- Claim ledger as first-class data model.
- Evidence-backed claims and review states.
- Mailpit/test email server for email-channel MVP.
- Provider-backed production email guidance.
- VPS-ready service layout.
- Browser privacy impact on first-party event tracking.

Keep as optional:

- Gauntlet cohort personalized website.
- Candidate self-intake social/source links.
- Trend-vector summaries from supplied/public evidence.
- Clay/Linkt as enrichment workbenches.
- OCR-assisted evidence extraction for candidate-submitted artifacts.

Defer or keep out of MVP:

- Broad social-media image red/green flag scoring.
- Third-party ad pixels for candidate scoring.
- Automated accept/reject/ranking based on enrichment.
- Direct VPS outbound SMTP.

## Suggested Front-End / Intake Slice

If our lane remains front end and initial data collection/intake, the most PRD-aligned slice is:

1. Claim ledger UI for the Helix-style tenant.
2. Source/evidence inspection panel.
3. Email draft preview with cited / repaired / blocked claim states.
4. Legal-hold toggle UI or operator control.
5. Mailpit-backed test email capture surface.
6. Optional provider-import review queue for Linkt/Clay outputs.
7. Optional cohort/candidate intake flow once PM confirms it belongs in the showcase.

This keeps us useful even if the PM narrows the capstone back to the official Gate/email demo.

## Linkt Fit Assessment

Linkt describes itself as AI-powered GTM intelligence for sales teams. Its docs expose:

- ICPs: define ideal customer profiles and fields to research.
- Sheets: store enriched companies/contacts.
- Tasks: run search, ingest, enrichment, and monitoring workflows.
- Signals: monitor companies for events like funding, leadership changes, hiring surges, RFPs, and topic-based events.
- CSV import: upload CSVs, create an enrichment ICP, create a sheet, configure an ingest task, execute, then review enriched entities.
- Contact discovery: discover/enrich people at target companies, including email discovery and LinkedIn matching.
- Webhooks: receive HTTPS callbacks when workflows complete.
- API key auth via `x-api-key`; keys must stay server-side.

Best uses for Provenance:

1. **Demo tenant prospect generation**
   - Linkt could help create or enrich realistic B2B prospect/company records for a Helix-style tenant.
   - This fits the PDF better than candidate-social analysis because the official story is regulated B2B outreach.

2. **Company and account signals**
   - Linkt signals can become source-backed claims like "Company announced a hiring surge" or "Company is discussing AI initiatives."
   - Those can feed the claim ledger and Gate.

3. **CSV enrichment workbench**
   - Tom/cohort export or demo prospect CSVs could be imported for enrichment, but outputs must be converted into Provenance claims with references.

4. **Webhook-driven worker flow**
   - Linkt can call a Provenance webhook when an enrichment task finishes.
   - Our worker can then import entities/signals into the claim ledger.

Less-good uses:

- Candidate personal/social background scoring.
- Sensitive candidate red/green flag analysis.
- Anything requiring external contact emails or mobile phones without explicit consent and review.
- Replacing the claim ledger. Linkt is a research/enrichment source, not our source of truth.

## Linkt vs Clay

| Tool | Better fit | Caution |
| --- | --- | --- |
| Linkt | B2B GTM/company/contact enrichment, ICPs, account signals, prospect discovery, webhooks | More sales/prospect oriented than candidate-intake oriented; contact discovery may pull sensitive or unwanted data |
| Clay | Flexible enrichment table/workbench, waterfall enrichment, manual research workflows | Still needs source URLs, consent basis, provider attribution, and human review |

Working recommendation:

- If the PM plan stays Helix/regulatory-B2B first, evaluate **Linkt for demo-tenant prospect/account enrichment**.
- If the team keeps the Gauntlet cohort candidate-intake path, evaluate **Clay first** for flexible enrichment and use Linkt only if candidate/company matching naturally becomes a GTM-style workflow.
- In both cases, imported outputs should become cited claims with `provider`, `source_url`, `observed_at`, `review_status`, and `decision_use`.

## Possible Linkt Import Contract

```json
{
  "claim_id": "uuid",
  "subject_type": "company",
  "subject_id": "helix-prospect-123",
  "source": "linkt",
  "provider_entity_id": "linkt-entity-id",
  "claim_type": "company_signal",
  "claim_text": "Northwind Health is hiring for AI operations roles.",
  "evidence_url": "https://source.example/article",
  "evidence_excerpt": "Hiring signal or source excerpt",
  "observed_at": "2026-06-17T00:00:00Z",
  "collection_method": "provider_import",
  "provider": "linkt",
  "review_status": "needs_review",
  "decision_use": "assistive_only"
}
```

## Open Partner Questions

- Is the PM keeping the official Helix-style tenant as the primary showcase path?
- Are we still responsible for Gauntlet cohort candidate intake, or is that now a secondary demo?
- Do we want Linkt research outputs for B2B prospects, candidates, or both?
- Who owns the claim ledger UI if Owner 4 folds into the Gate/Data owners?
- Should Mailpit/test email be part of the first implementation slice because email is the required MVP channel?
- Are we allowed to use real external enrichment providers for the demo, or should all demo tenant data remain synthetic/controlled?

## Sources Checked

- Linkt homepage: https://www.linkt.ai/
- Linkt docs: https://docs.linkt.ai/
- Linkt authentication: https://docs.linkt.ai/docs/getting-started/authentication
- Linkt CSV import: https://docs.linkt.ai/docs/guides/ingest/csv-import
- Linkt contact discovery: https://docs.linkt.ai/docs/guides/search/contact-discovery
- Linkt tasks: https://docs.linkt.ai/docs/core-concepts/workflows/tasks
- Linkt signals: https://docs.linkt.ai/docs/core-concepts/data-models/signals
- Linkt webhooks: https://docs.linkt.ai/docs/core-concepts/workflows/webhooks
