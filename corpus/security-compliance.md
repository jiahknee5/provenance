# Security & Compliance

_Synthetic, illustrative. The facts a message may state about how student data is handled._

## Data handling
- Student data (applications, project code, session recordings) is encrypted in transit (TLS 1.2+)
  and at rest (AES-256). _(infra)_
- Hosted on SOC 2 Type II infrastructure (the cloud provider's attestation, not ours). _(infra)_
- Session recordings are retained 12 months, then deleted. _(retention)_
- Students can request export or deletion of their data at any time. _(rights)_

## Consent
- Live sessions are recorded only after an explicit recording-consent banner is accepted. _(consent)_
- Voice Q&A capture is opt-in per session. _(consent)_

## What you may and may NOT say (cite this file)
- You MAY say: "data is encrypted in transit and at rest," "recordings are deleted after 12 months,"
  "you can request deletion anytime."
- You may NOT say: "SOC 2 certified" (the certification is the cloud provider's, not the Academy's —
  state it precisely or not at all).
- You may NOT say: "HIPAA-compliant" or "FERPA-certified" — no such attestation exists in this corpus.
  These belong on the Cannot-say deny-list.

## Sub-processors
- Cloud hosting, email delivery, video conferencing, and payment processing are handled by named
  third-party sub-processors listed in the DPA. Point to the DPA; don't name them from memory.
