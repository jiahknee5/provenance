# Provenance — Derived & Locked PRD

> **Status:** LOCKED (derived from the working project per the operator's 2026-06-24 restructure directive).
> Changes follow the decision protocol in `BUILD-AUTONOMY.md` (numbered `Rn`, PRD-fact vs interpretation).
> The build runs against this doc + `docs/03-spec/SPEC.md`. Acceptance = the test suite (§7) passes AND the UI is high-fidelity + consistent across every page (§6).

## 1. Vision & wedge

**Provenance is the GTM workspace that can prove every move.** A CRM/revenue platform where every AI-driven action — a personalized message, an optimized variant, an enriched fact, a reported metric — carries its **source, its lawful basis, and its surface policy**, and is continuously audited for drift and overclaim.

The market (Attio, HubSpot, Ploy.ai) ships personalization and automation you have to *trust*. Provenance ships personalization you can *verify*. The one-line thesis, inherited from the project: **"don't ship what you can't prove."**

**Pillars** (the lens every decision passes through):
1. **Provable** — every surfaced fact/claim binds to a source + basis; nothing renders without provenance.
2. **Optimizing** — a contextual-bandit Optimizer learns the best *verified* variant per segment; it can't win by lying (the Gate bounds its action pool).
3. **Watched** — Drift re-verifies on source change; the Assurance Lab catches hallucination/overclaim with adversarial traps.
4. **Quiet** — an Attio-grade "Quiet Workspace" UI; color only in the data; a deterministic agent in place of a sprawling dashboard.

## 2. Market & positioning

| | Attio | HubSpot | Ploy.ai | **Provenance** |
|---|---|---|---|---|
| Core | Modern CRM / data model | GTM platform | GTM AI agents | **Provenance-verified GTM/CRM** |
| AI posture | personalize / enrich | automate | autonomous agents | **provable** personalization + a deterministic optimization agent |
| Moat | flexible data model | breadth | agent autonomy | **every action carries its receipt; drift + hallucination monitored** |

Customers = the same buyers as Attio/HubSpot: **RevOps, Growth/Marketing, Sales leadership** at scaling B2B companies — plus the compliance-sensitive segment (regulated industries) who can't adopt black-box GTM AI.

## 3. Locked decisions (this restructure)

| R | Decision | Type |
|---|---|---|
| **R22** | **Restructure on the engine, do not rebuild.** Keep the verified pipeline (Gate, Optimizer/bandit + oracle, Drift, Assurance, provenance ledger, personalization, enrichment). Rebuild only the product/UI layer + the agent on top. | operator |
| **R23** | **Deterministic agent, LLM-optional.** The "agent that navigates optimizations" is a deterministic command-palette + guided-flow navigator over the real optimizer/assurance/drift state — $0, offline, provable. A natural-language LLM layer is opt-in (gated by `ANTHROPIC_API_KEY`); default off. Agent-LED, not agent-ONLY — scannable record/table views remain. | operator |
| **R24** | **Design = "Quiet Workspace"** (the Attio-derived system in the design library, `insp-attio`): pure-white canvas, near-black Inter-Display headings, near-monochrome cool-grey scale, hairline borders, color only in product data (one signal-blue + soft tag tints), calm `cubic-bezier(.2,0,0,1)` motion. | operator |
| **R25** | **Icons = Phosphor** (MIT), SF-Symbols-style weight ladder + duotone. **SF Symbols itself is license-restricted to Apple platforms and cannot ship in this web app** — Phosphor delivers the same look, legally. | interpretation (operator asked for SF Symbols; license forbids web use) |
| **R26** | **Assurance is minimalist and monitors Drift.** One quiet surface: a trust score + the live drift watch (stale/retracted facts → paused variants), not a sprawling dashboard. | operator |
| **R27** | **$0 / offline / deterministic stays the default.** Network (enrichment, the live cloner, LLM agent) is opt-in and cached. The seed governs all synthetic data. | PRD-fact (inherited) |

## 4. Personas (the multi-user test cast — §7 exercises each)

| # | Persona | Role / goal | Primary surface | Acceptance moment |
|---|---|---|---|---|
| P1 | **Renata, RevOps lead** | Trust the pipeline numbers; tune optimization | Records + Agent + Assurance | Every metric drills to a sourced record; the agent explains *why* a variant won |
| P2 | **Sam, SDR / rep** | Send personalized outreach that's on-policy | Records + Composer | Can't send a message containing a `hold`/unverified fact — it's blocked with a reason |
| P3 | **Maya, Growth marketer** | Run variant experiments; watch lift | Optimizer + Agent | Sees the bandit converge to the honest winner; the creepy/ungated variant is provably never selected |
| P4 | **Liam, Workspace admin** | Configure sources, policy, members | Settings + Catalog | Sets a source's basis/TTL; Drift pauses dependent variants on expiry |
| P5 | **Dr. Chen, skeptical exec / CISO** | "Prove it won't hallucinate or leak" | Assurance (minimalist) | One screen: trap catch-rate, drift status, provenance coverage = 100% |
| P6 | **First-time visitor (anonymous)** | Evaluate the product | Marketing/demo | The live demo shows provenance-tagged personalization across scenarios |

## 5. Product surfaces (restructured)

Built on the existing routes; reorganized under the Quiet-Workspace shell (left sidebar + record-first main + ⌘K agent):

1. **Workspace shell** — left sidebar (workspace switcher, object nav, saved views), top bar (search, ⌘K agent), record-first main. (new `base.html`)
2. **Records / Pipeline** — the data grid: companies/people/deals, inline cells, soft-tint status pills, avatar stacks. (reframes `funnel`/`cohort`/`admin_landings`)
3. **Composer** — write outreach; the Gate verifies every claim inline; `say`/`allude`/`hold` enforced; can't ship the unprovable. (reframes `personalize`/`site`)
4. **Optimizer** — variant experiments per segment; the bandit's learned winner; the blocked ungated arm shown greyed. (reuses `optimizer`)
5. **Agent (⌘K + panel)** — the deterministic navigator: ask/route over optimizations, records, assurance, drift; guided flows. (new)
6. **Assurance** — minimalist: trust score + **Drift watch**. (reframes `assurance` + `drift`)
7. **Catalog / Settings** — sources, lawful basis, TTL, members, policy. (reuses `enrichment_catalog`)
8. **Demo** (public) — the live-cloner personalization showcase (already shipped). Kept as the top-of-funnel demo.

## 6. UI quality bar (the loop gates on this)

- **One token set** (`Quiet Workspace`) applied app-wide via `base.html`; no page defines its own palette/type.
- **Consistency check across every page**: same nav, same type scale, same button system, same spacing rhythm, same motion. A script asserts each page extends the shell + uses the tokens (no rogue `max-width`, no off-palette hexes).
- **High-fidelity** = matches the `insp-attio` recreation prompt (measured, not vibes): white canvas, Inter Display headings, 10px buttons, hairline borders, color only in data.
- Phosphor icons throughout (one weight for nav, duotone for emphasis).

## 7. Test suite (multi-user — full plan in SPEC §Tests)

Every persona (P1–P6) gets an end-to-end journey test plus invariant tests. The acceptance gate (`/loop` target):

- **All existing tests stay green** (the engine: 86+ currently).
- **Per-persona journeys pass** (P1 metric→record drill; P2 hold-fact send blocked; P3 bandit converges + blocked-arm never selected; P4 source-TTL → drift pause; P5 assurance trust panel renders the three numbers; P6 demo renders provenance).
- **Provenance invariant**: no surface renders a fact without a source; no `hold` fact reaches copy. (assert across surfaces)
- **UI-consistency invariant**: every navigable template extends the shell + uses the token set; no off-system colors. (assert)
- **Determinism**: byte-identical artifacts on re-run at the global seed.

## 8. Out of scope (this pass)

- Real third-party CRM sync (HubSpot/Salesforce import) — documented, not built.
- The LLM agent layer ships **inert by default** (key-gated); deterministic agent is the product.
- Multi-tenant auth / billing.
- Native/mobile apps (web only → Phosphor, not SF Symbols, per R25).

## 9. Build order (phases → `/loop` to completion)

0. ✅ Attio design language → library (`insp-attio`).
1. ◀ This doc + SPEC (locked).
2. Quiet-Workspace shell + tokens + Phosphor, applied to every surface.
3. Deterministic agent navigator (⌘K + guided flows over the engine state).
4. Minimalist Assurance + Drift.
5. Multi-user test suite + loop until green & UI-consistent.
6. *(stop condition — operator go)* deploy to the provenance service.

Stop conditions honored throughout (`BUILD-AUTONOMY.md`): deploy/push/spend, a CONSTITUTION conflict, or a P0 gap with no defensible default.
