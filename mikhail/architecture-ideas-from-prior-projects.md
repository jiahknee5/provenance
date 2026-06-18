# Architecture Ideas from Prior Projects

Last updated: 2026-06-17

This is a partner-review menu: borrowable architecture patterns from prior projects that may be useful for Provenance. These are not decisions already made for the team. Partners can accept, reject, or defer each idea.

Current PRD alignment: prioritize the email-channel Gate, claim ledger, Assurance Lab, regulatory hold, and adversarial demo. Treat cohort/candidate enrichment, Linkt/Clay imports, OCR, pixels, and website personalization as optional extensions unless the PM pulls them into the official MVP.

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
| Captured-mail test server | Email delivery research | Run Mailpit for dev/demo email capture so magic links, intake confirmations, and partner notifications can be tested without sending real email. | Yes |
| Provider-backed production email | Email delivery research | Use Resend/Postmark/SES or Gauntlet's existing sender for real delivery instead of self-hosting outbound SMTP on the VPS. | Later |
| OCR-assisted evidence extraction | Alcohol Label OCR/vision pipeline | Reuse the four-layer pattern: deterministic checks, local OCR, optional vision provider, and human review for candidate-submitted images or artifacts. | Later |
| Manual deploy path | Alcohol Label deploy pattern | If/when deployed, use GitHub Actions manual deploy, env in `/opt/<app>/.env`, and no public host ports except Traefik. | Later |
| Deploy artifact hygiene | Alcohol Label deploy pattern | Exclude `.codex`, local agent state, scratch exports, and secrets from any deploy or release artifact. | Later |

## Near-Term Recommendation

1. Build the claim-ledger UI and evidence inspection path first.
2. Support the email-channel MVP with a test-mail server and email event ledger.
3. Model all source docs, provider imports, demo facts, and enrichment results as evidence-backed claims.
4. Keep candidate/cohort trend vectors as derived claims for later extension work.
5. Keep Linkt/Clay as optional enrichment workbenches, not the system of record.
6. Keep Gate, Optimizer, Drift, and Assurance behind contracts until their owners are ready.

## PRD-Aligned Implementation Slices

| Slice | Why it matters | Notes |
| --- | --- | --- |
| Claim ledger UI | Required demo surface | Show cited / repaired / blocked claims, source links, review state, and legal-hold impact. |
| Email channel support | Required MVP channel | Use Mailpit for local/demo capture and an event ledger for sent/captured/delivered/bounced states. |
| Gate contract | Required core integration | Accept draft copy + candidate/prospect context + source claims; return claim decisions and repair/block reasons. |
| Assurance Lab display | Required proof layer | Surface trap-set metrics, catch-rate, false-reject rate, and calibration/reliability chart. |
| Regulatory hold control | Required adversarial beat | Flip a source/rule and show claims blocked or unblocked through the ledger. |
| B2B demo tenant data | Required stage realism | Keep Helix-style sources and prospects controlled; provider enrichment is optional. |
| Website adapter | Ambitious extension | Reuse the same claim ledger; do not create a separate personalization truth path. |
| Candidate/cohort intake | Optional extension | Use consented self-intake and evidence-backed claims only. |

## VPS Utilization

Deployment is not in current scope, but we should design as if the system can later run on the shared VPS.

Known VPS pattern from adjacent work:

- VPS: `51.81.83.107`.
- Use Docker Compose for app services.
- Use Dokploy/Traefik as the public edge.
- Keep runtime config in `/opt/<app>/.env`.
- Do not expose app containers through public host ports except Traefik.
- Use GitHub Actions manual deploy when deployment becomes in scope.
- Exclude `.codex`, local agent state, scratch exports, secrets, and raw PII exports from deploy artifacts.

Possible service layout:

| Service | Purpose | Public? |
| --- | --- | --- |
| `provenance-web` | Front-end intake, candidate review, partner/admin UI | Yes, behind Traefik |
| `provenance-api` | Intake API, profile ledger API, claim import endpoints | Yes, behind Traefik |
| `claim-worker` | Source imports, Linkt/Clay imports, Gate jobs, Drift checks, trend-vector jobs | No |
| `mailpit` | Captured test email for local/VPS demo environments | UI only behind Traefik auth; SMTP internal only |
| `postgres` | Candidate profiles, claims, reviews, email events | No |
| `redis` or queue | Background jobs and retries if the stack needs it | No |

Near-term design implication: the ledger schema should not assume everything is synchronous. Email sends, Gate calls, Assurance runs, provider imports, enrichment jobs, and Drift re-checks should be modeled as jobs with status and retry state.

Do not self-host production outbound SMTP on this VPS unless the team deliberately chooses to own mail deliverability. Sending directly from a VPS creates reputation, reverse-DNS, abuse handling, bounce, complaint, and blocklist work that is not core to the capstone.

## Email Delivery

Minimum viable email architecture:

1. Use Mailpit as the default test SMTP server.
2. Route all local and demo emails to Mailpit unless explicitly configured otherwise.
3. Use a transactional provider for real email delivery when needed.
4. Store email events in the Provenance ledger so outreach and intake communications are auditable.

This is now near-term because the PM plan names email as the minimum channel. Mailpit is not only a convenience; it lets the team test magic links, draft sends, ledger updates, and failure states without real outbound mail.

### Test Mail Server

Mailpit is the recommended test server. It acts as an SMTP server, provides a web UI for captured messages, and has an API for integration testing.

Suggested VPS/demo setup:

- App containers send SMTP to `mailpit:1025` on the Docker network.
- Mailpit web UI listens on `8025` but is exposed only through Traefik with authentication or IP restriction.
- Do not expose Mailpit SMTP publicly.
- Persist captured mail with `MP_DATABASE=/data/mailpit.db`.
- Cap retention with `MP_MAX_MESSAGES` or age-based cleanup.
- Disable relay by default. If relay is ever enabled, restrict allowed recipients with a regex allowlist.

Example compose shape:

```yaml
services:
  mailpit:
    image: axllent/mailpit
    restart: unless-stopped
    volumes:
      - mailpit-data:/data
    environment:
      MP_DATABASE: /data/mailpit.db
      MP_MAX_MESSAGES: 5000
      MP_UI_AUTH: ${MAILPIT_UI_AUTH}
    expose:
      - "1025"
      - "8025"

volumes:
  mailpit-data:
```

The important part is `expose`, not public `ports`, for the VPS shape. Traefik can publish the UI later if we need partner inspection.

### Production Delivery

For real delivery, prefer an email API provider:

- Resend: simple API, verified domains, DNS records, webhooks for delivery/bounce/complaint-style events.
- Postmark: strong transactional-email posture and webhook support.
- Amazon SES: cost-efficient, but requires verified identities and production access outside the SES sandbox.
- Existing Gauntlet email infrastructure: best if cohort communications should preserve sender reputation and consent context.

Do not start with direct VPS SMTP for production. Use provider APIs/webhooks and keep provider-specific IDs in our ledger.

Email categories:

| Category | Examples | Delivery mode |
| --- | --- | --- |
| Auth/transactional | Magic links, intake confirmations, source-confirmation emails | Provider when live; Mailpit in dev/demo |
| Operational | Partner review assignments, failed import alerts | Provider when live; Mailpit in dev/demo |
| Cohort/subscribed | Showcase links, follow-up invites, program updates | Existing Gauntlet sender or provider with unsubscribe |
| Marketing/outbound | Personalized recruiting campaigns | Defer until consent, unsubscribe, suppression, and compliance flows exist |

### Deliverability Requirements

Before sending real email from a Provenance domain or subdomain:

- Verify the sending domain with the provider.
- Configure SPF and DKIM.
- Publish DMARC, starting with `p=none` while monitoring.
- Use TLS.
- Keep spam complaint rates below provider and mailbox-provider thresholds.
- Add one-click unsubscribe for marketing/subscribed messages.
- Process unsubscribes quickly and maintain a suppression list.
- Store bounce, complaint, delivered, failed, and unsubscribe events.
- Use separate streams/subdomains for transactional versus marketing-style email if volume grows.

Gmail requires all senders to use SPF or DKIM, and bulk senders to use SPF, DKIM, and DMARC. Gmail also requires one-click unsubscribe for marketing/subscribed bulk mail and expects low spam rates. Yahoo similarly requires at least SPF or DKIM for all senders, and SPF, DKIM, DMARC, one-click unsubscribe, and low complaint rates for bulk senders.

### Email Event Contract

```json
{
  "email_id": "uuid",
  "candidate_id": "uuid",
  "category": "intake_confirmation",
  "provider": "mailpit",
  "provider_message_id": "optional-provider-id",
  "to_hash": "sha256-normalized-email",
  "subject": "Confirm your Provenance profile",
  "template": "intake-confirmation-v1",
  "status": "captured",
  "events": [
    {
      "type": "captured",
      "observed_at": "2026-06-17T00:00:00Z"
    }
  ],
  "claim_ids": ["claim_123"],
  "created_at": "2026-06-17T00:00:00Z"
}
```

For production, `provider` becomes `resend`, `postmark`, `ses`, or `gauntlet_existing_sender`; `events` should reflect provider webhook payloads.

## OCR and Social Images

Someone raised the idea of using the existing OCR/vision application to analyze candidate social-media images for red/green flag signals.

Recommendation: borrow the OCR architecture, but do not make broad social-image red/green flagging part of the MVP.

Why:

- OCR itself is manageable because the alcohol-label project already proves a usable pattern: deterministic rules, local OCR, optional vision provider, human review, provider-failure routing, poor-image handling, and golden evals.
- Social-media image analysis is much harder than OCR. It requires image collection, platform policy checks, consent, identity matching, OCR, vision inference, sensitive-trait filtering, false-positive handling, candidate correction, and bias review.
- Images often expose protected or sensitive traits: age, race, disability, religion, politics, family status, health, location, socioeconomic status, and third parties who never consented.
- "Red flag" labels are especially risky because they can become opaque character judgments rather than evidence-backed, program-relevant claims.

Safer version to consider:

1. Accept only candidate-submitted images or candidate-submitted URLs.
2. Limit OCR to text extraction from program-relevant artifacts: portfolio screenshots, demo slides, project images, certificates, conference posters, README screenshots, or public product screenshots.
3. Convert OCR output into evidence-backed claims, not personality judgments.
4. Route all OCR-derived trend claims through human review before use.
5. Store source URL/image hash, OCR engine/version, extracted text snippets, confidence, bbox/region where possible, and reviewer decision.
6. Reject or ignore images likely to contain sensitive personal traits or unrelated social/lifestyle context.

Possible OCR claim shape:

```json
{
  "claim_id": "uuid",
  "candidate_id": "uuid",
  "source": "candidate_submitted_image",
  "source_subject": "portfolio_screenshot.png",
  "claim_type": "artifact_text",
  "claim_text": "Candidate's portfolio screenshot references an agent evaluation dashboard.",
  "evidence_url": "candidate-upload://artifact_123",
  "evidence_excerpt": "agent evaluation dashboard",
  "evidence_region": {
    "page": 1,
    "bbox": [0.18, 0.22, 0.64, 0.31]
  },
  "collection_method": "ocr",
  "extractor": "local_ocr_or_vision_provider",
  "confidence": "medium",
  "review_status": "needs_review",
  "decision_use": "assistive_only"
}
```

What to avoid:

- Scraping image feeds from Instagram, Facebook, X, or LinkedIn.
- Scoring a candidate's personal life, appearance, friends, family, events, politics, religion, alcohol use, health, or finances.
- Using image-derived "red flags" for auto-rejection or ranking.
- Running face recognition or identity matching across social images.
- Storing raw social images unless there is explicit consent and a clear retention policy.

Technical cost estimate:

| Version | Cost | Why |
| --- | --- | --- |
| Candidate-submitted image OCR for artifacts | Low to medium | Existing OCR/vision pattern can be reused; bounded input and human review make it tractable. |
| OCR on public project/product screenshots from supplied URLs | Medium | Requires fetch policy, screenshot capture, source attribution, and quality handling. |
| Broad social-media image red/green flagging | High | Requires platform-specific access, privacy review, sensitive-trait filtering, evals, appeals, bias review, and careful legal review. |

Partner takeaway: OCR can be useful if it extracts cited text from candidate-provided artifacts. Social-image red/green flag scoring is technically and ethically expensive, and should be deferred unless the team narrows it to a consented, auditable, human-reviewed evidence-extraction flow.

## Why These Fit Provenance

The useful through-line from prior projects is not any particular framework or deployment script. It is the habit of making claims inspectable, reviewable, and reversible.

For the candidate-research track, that means Provenance should avoid building an opaque candidate dossier. The architecture should produce:

- Source records: where data came from and when it was observed.
- Evidence-backed claims: what the source supports.
- Derived trend-vector claims: summaries that cite lower-level claims.
- Review state: whether a human or Gate accepted the claim for use.
- Freshness state: whether Drift needs to re-check the source.

That structure keeps the front-end useful now and gives the later Gate/Optimizer/Drift/Assurance services clean contracts.

## Sources Checked

- Mailpit features: https://mailpit.axllent.org/docs/
- Mailpit Docker install: https://mailpit.axllent.org/docs/install/docker/
- Mailpit runtime options: https://mailpit.axllent.org/docs/configuration/runtime-options/
- Resend send email API: https://resend.com/docs/api-reference/emails/send-email
- Resend domain management: https://resend.com/docs/dashboard/domains/introduction
- Resend DMARC: https://resend.com/docs/dashboard/domains/dmarc
- Resend webhook event types: https://resend.com/docs/webhooks/event-types
- Postmark webhooks: https://postmarkapp.com/developer/webhooks/webhooks-overview
- Amazon SES verified identities: https://docs.aws.amazon.com/ses/latest/dg/verify-addresses-and-domains.html
- Amazon SES production access: https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html
- Gmail sender guidelines: https://support.google.com/mail/answer/81126
- Yahoo sender requirements: https://senders.yahooinc.com/best-practices/
- Alcohol Label OCR/vision architecture: /Users/mike/source/resume/alcohol-label/README.md
- Alcohol Label golden evals: /Users/mike/source/resume/alcohol-label/docs/evaluations.md
