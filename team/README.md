# Provenance — Team of 3 · Ownership & Operating Model

> **Mission:** ship the outbound AI that can't lie — provable ultra-personalization that optimizes itself inside the truth.
> **Showcase:** Mon Jun 29, 2026 · 10-min live · **Planning doc due:** Wed Jun 17.

This folder turns the 5-pillar architecture into a **3-person build plan**. The original capstone doc carries a 4-owner split ([`PROJECT-PLANNING-DOCUMENT`](../decks/PROJECT-PLANNING-DOCUMENT.md), [`COHORT-DEMO-PROJECT-PLAN §6`](../decks/COHORT-DEMO-PROJECT-PLAN.md)); for a team of 3, **Owner 4 (Generation + demo) folds into the Platform owner**, and the cross-cutting demo is shared.

---

## The 3 owners

Each owner gets one **frontier centerpiece** plus a tightly-coupled second pillar, so no one is a single point of failure on integration.

### Owner A — Verification core *(ML / NLP)*
**Owns: ② The Gate + ⑤ Assurance Lab.**
The Gate is the non-negotiable critical path; the Assurance Lab is the harness that proves it — keeping them on one owner means the verifier and its proof never drift apart.

- Claim decomposition, evidence-binding retrieval, NLI entailment, calibrated diverse-judge ensemble, isotonic calibration / ECE.
- Router-and-referee cost cascade; optional hidden-state probe.
- Compliance-rule engine (DSL: MLR holds, FTC, channel, jurisdiction).
- Claim-ledger API (green / amber / red) + batch governed pages.
- Synthetic adversarial-trap generator + reliability profiling + the headline metric.
- **Diagrams:** [`02-the-gate.md`](../architecture/diagrams/02-the-gate.md) · [`05-assurance-lab.md`](../architecture/diagrams/05-assurance-lab.md)

### Owner B — Decisioning core *(RL / data science)*
**Owns: ③ The Optimizer + ④ Drift Monitor.**
Both are sequential, stateful systems that act *after* the Gate — natural to pair.

- Contextual bandit (Thompson / LinUCB) over the verified-variant action space; hierarchical priors; doubly-robust off-policy eval; LLM-persona simulator.
- The optimizer demo viz: reply-rate ↑ with the illegal arm grayed out (structural anti-reward-hacking).
- Claim-dependency graph + source change-data-capture; targeted re-verification; auto-pause / unblock; the rule-change drift demo.
- **Diagrams:** [`03-the-optimizer.md`](../architecture/diagrams/03-the-optimizer.md) · [`04-drift-monitor.md`](../architecture/diagrams/04-drift-monitor.md)

### Owner C — Platform & product *(data / full-stack)*
**Owns: ① Claims Library + Generation + Demo/web** (absorbs original Owner 4).
The data substrate, the generation that feeds the Gate, and the surface everyone presents on.

- Claim–evidence graph, source registry, the live ag/biotech spine, the Gauntlet-tenant Claims Library + Drew corpus indexing.
- Per-prospect grounded generation + channel adapters (email / website).
- Magic-link auth, the personalized landing-page route, compare mode, track switcher, the claim-ledger inspect UI, rehearsal, deploy.
- **Diagrams:** [`01-claims-library.md`](../architecture/diagrams/01-claims-library.md)

---

## Module → owner matrix

| Module | Pillar | Owner | Critical path? |
|--------|--------|-------|:---:|
| ① Claims Library | input / substrate | **C** | feeds everything |
| ② The Gate | verification (core) | **A** | ★ non-negotiable |
| ③ The Optimizer | decisioning | **B** | ambitious tier |
| ④ Drift Monitor | temporal | **B** | demo must-have |
| ⑤ Assurance Lab | proof / eval | **A** | demo must-have |
| Generation + web demo | product | **C** | demo backbone |

## RACI — cross-cutting deliverables

| Deliverable | A (Verify) | B (Decision) | C (Platform) |
|-------------|:---:|:---:|:---:|
| Claim ledger schema + API | **R** | C | A |
| Gauntlet tenant rules YAML | **R** | C | C |
| Claims Library + sources | C | I | **R** |
| 10-min showcase script | C | C | **R** |
| Integration / end-to-end run | A | A | **R** |

*R = responsible/drives · A = approves · C = consulted · I = informed.*

---

## Critical path & parallelization

```
C: Claims Library ──► A: The Gate ──► B: Optimizer (sim)
        │                  │
        └─► C: Generation ─┘──► C: web app + ledger UI ──► rehearsal
                           └──► A: Assurance Lab ──┐
                           └──► B: Drift Monitor ──┴► showcase
```

- **Day 1 unblocked in parallel:** C scaffolds the RPG/Library + web shell; A stubs the Gate interface + ledger schema (so C/B can integrate against it); B builds the persona simulator (no live data needed).
- **The contract that unblocks everyone:** the **claim-ledger schema** (`{recipient_id, track, html, claims:[{claim_id, text, span, verdict, source_id}]}`) — freeze it Day 1 so the Gate, the UI, the Optimizer, and Drift all code against it.
- **Gate is the bottleneck** — A protects it; B and C must not block on the *full* Gate (use the stub + 3 planted profiles until the real pipeline lands).

## Cadence

- Daily 15-min standup: yesterday / today / blockers, anchored to the [build phases](./onboarding.md#build-phases).
- Twice-weekly integration: end-to-end run on the 3 planted profiles (Jordan / Sam / Riley).
- One shared `#provenance` channel; PRs reviewed by the owner of the touched module + one other.
- **Demo rehearsal Jun 28** is a hard gate — fallback offline mode required.

---

**Read next:** [`onboarding.md`](./onboarding.md) — repo layout, setup, week-by-week milestones, and first-week tasks per owner.
