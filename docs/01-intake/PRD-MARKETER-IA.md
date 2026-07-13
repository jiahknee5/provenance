# PRD — apt Marketer IA & Workflow (W9)

> **Status:** DERIVED (extends `PRD-derived.md` + `PRD-SECTION-DESIGNER.md`; follows the `BUILD-AUTONOMY.md` decision protocol, numbered `Rn`).
> **Authority:** `CONSTITUTION.md` > this PRD > decks.
> **Companion contract:** `../04-workflow/IA-MAP.md` — the route/stage/link table this PRD authorizes. Tests derive from the map (`tests/test_ia_map.py`); the map's exception ledger is the only sanctioned way to deviate.
> **Acceptance:** the suite passes (incl. map-derived nav + crawler tests) AND a marketer can complete journey J1 end-to-end following only primary CTAs.

## 1. Operator requirement (2026-07-12, verbatim intent)

The product must be **customer-ready / marketer-ready**: professional,
consistent, all links checked, easy to understand, easy to navigate. There
must be **pre-defined workflows each piece follows** — anything off-workflow
needs a very clear, documented reason. The marketer's journey to support
explicitly: **add a new website → identify what/where text & image
personalization is needed → add each into the flow → see the decisioning
around each → customize each → deploy**. Prior session (W8) established: one
menu only, collapsed-by-default, chronological zones, HubSpot/X-Ads register.

**PRD-fact:** the journey above and the "workflow + documented exception"
rule are operator requirements. **Interpretation** (accepted 2026-07-12 "go
ahead"): the corrections in R40 below.

## 2. Locked decisions

- **R40 — Stages × Journeys model.** Navigation is place-based stages
  S0 Home → S1 Connect → S2 Channels → S3 Personalize → S4 Preview →
  S5 Launch → S6 Measure (loop S6→S3). The operator's six-step flow is
  **journey J1**, a guided checklist that steps across stages; each PRODUCT
  page's primary CTA advances the active journey. Corrections applied to the
  operator's draft flow (flagged as interpretation, accepted): scope+add
  merged into one step (same surface); Channels stage added (decisioning
  needs a subject; the "search → landing page" complaint is a missing
  channel-setup page); "see decisioning" is inline in S3 cards + per-visit in
  S4, not a standalone stage; Measure added after deploy (the pillar stack
  lives post-launch).
- **R41 — Launch semantics: simulated apply.** The designer's "nothing saves
  live" staging contract stands. S5 Launch reviews staged changes +
  guardrails and performs a **clearly-labeled simulated apply** (demo
  affordance). A real apply (writing `rules/<tenant>_sections.yaml`) is a
  future decision, not silently introduced. Staged changes persist to
  localStorage (per-tenant key) so Launch can read them; the sd-* DOM
  contract is unchanged.
- **R42 — Channel setup pages are ONE data-driven template.** Per channel ×
  tenant, rendered from `rules/demo_scenarios.yaml` + the channel clusters in
  `demo_nav.py`. No hand-written per-tenant channel pages (that is how the
  consoles diverged pre-W8). Sidebar channel items land HERE (PRODUCT), never
  on galleries or landing pages; galleries demote to `Preview →` drills.
- **R43 — `/apt/demo` becomes the workspace Home (S0)**: status + J1
  checklist + preview jump-ins. The "demo tour" framing retires; the entry
  cards remain as clearly-marked PREVIEW affordances.
- **R44 — Three-plane link contract** (PRODUCT / PREVIEW / LIVE) per
  IA-MAP §1+§6, enforced by map-derived tests and a PRODUCT-plane crawler
  wired into the deploy gate. Cross-plane links carry explicit markers
  (`Preview →`, `Open ↗ — your website`).
- **R45 — Marketer vocabulary boundary.** PRODUCT pages speak marketer
  (campaign, channel, audience, landing page, results). Engineering terms
  (YAML, registry, cache key, deterministic) appear only behind the
  Developer/audit fold or on PRODUCT-dev exception surfaces (IA-MAP E1).

## 3. Out of scope (this wave)

Real registry writes on Launch (see R41) · LinkedIn ads platform (roadmap) ·
engineer-console restyle (IA-MAP E1 keeps rails) · replica redesigns (they
must keep looking like the real brands — R36/R38).
