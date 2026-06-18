# Enrichment — privacy note & network carve-out

> Covers the live free connector (Fork 2-B, DECISIONS R15). The default demo is synthetic +
> offline + $0; this documents what changes when `PROVENANCE_ENRICH=live`.

## What the live connector does, exactly
- **Email-domain parse** — pure string parse of the domain the user gave us. **No network.**
- **Public news RSS** (`pipeline/enrichment/connectors.py › LiveNewsConnector`) — a single
  GET to Google News RSS, query = the **company name** (already user-provided). Reads a
  public feed; takes the first headline. **Nothing else leaves the machine.**

## Data minimization — what leaves the machine
| Leaves | To | Why it's acceptable |
|---|---|---|
| the company **name** | a public news search | the company is public; the name isn't the recipient's PII |
| the email **domain** | (parse only — no lookup wired) | derived from the address the user submitted |

**Never sent:** the recipient's name, email address, role, or any field beyond the company
name. No paid vendor is called. No PII is transmitted to a third party.

## Guarantees preserved
- **$0** — Google News RSS is free; no metered API.
- **Deterministic** — every live response is cached (`LLMCache`, keyed on the company), so a
  re-run replays from cache. The 25+ test suite and the default trace run in **synthetic**
  mode and never touch the network.
- **Honest failure** — no network → the connector returns nothing and the engine logs
  "connector unavailable" on the enrichment lane. It never fabricates a fact to cover a miss.
- **Opt-in** — live mode is off unless `PROVENANCE_ENRICH=live` is set explicitly.

## Lawful-basis posture (the part a human owns)
Every fact still passes the **Enrichment Gate** against the human-owned
`rules/helix_tenant.yaml › enrichment` policy: allow-listed source + recorded `basis` +
freshness TTL + consent + PHI/PII block. A live news fact is `public_record`; an
un-allow-listed source is blocked regardless of how it was fetched. **Wiring a real
connector does not bypass the policy — it feeds it.**

## Out of scope (still)
Real email *sending*, real recipient PII, paid vendor APIs, and scraping ToS-restricted
sources (LinkedIn et al. are *cataloged*, not called). Moving any of these in-scope is a
new operator decision + a new PRD amendment.
