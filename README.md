# Provenance — Capstone

**Provable ultra-personalization** — outreach that can't say anything it can't prove, and optimizes itself inside the truth.

> Gauntlet Capstone (10-week program) · Direction A (ML + LLM) · **Planning doc due Jun 17** · **10-min live showcase Jun 29, 2026** · Team of 3.

This is the self-contained home for the Provenance capstone, carved out of the LysoReach repo (which remains the **live data spine** — real ag/biotech prospects, real sources, a real legal hold = genuine ground truth for verification).

---

## Start here

| You are… | Go to |
|----------|-------|
| New to the project | [`architecture/diagrams/00-system-overview.md`](./architecture/diagrams/00-system-overview.md) — the whole system in two diagrams |
| A teammate / building | [`team/README.md`](./team/README.md) → [`team/onboarding.md`](./team/onboarding.md) |
| Designing a module | [`architecture/`](./architecture/) — architecture + data-process per module |
| Presenting / pitching | [`decks/index.html`](./decks/index.html) — the deck hub |

## The 5 modules

```
① Claims Library ─► generate ─► ② The Gate ─► ③ The Optimizer ─► send ─► ④ Drift Monitor
   claim–evidence    grounded    verify + clear   verified arms only        re-verify on
   graph             draft       (cited or killed)                          source change
        └────────────────── ⑤ Assurance Lab — adversarially proves the Gate ──────────────┘
```

See [`architecture/README.md`](./architecture/README.md) for all 10 module diagrams (+ a styled HTML viewer).

## Folder map

```
provenance/
  README.md           ← you are here
  architecture/       10 module diagrams (mermaid .md) + provenance-architecture.html viewer
  team/               team-of-3 ownership, RACI, onboarding, build phases
  decks/              all pitch / planning / proposal / demo artifacts (see index below)
```

## Deck index (`decks/`)

The deck corpus is flat (every cross-link is sibling-relative); this is the logical map. Hub: [`decks/index.html`](./decks/index.html).

**Graded submission**
- [`PROJECT-PLANNING-DOCUMENT`](./decks/PROJECT-PLANNING-DOCUMENT.html) · [`PROVENANCE-CAPSTONE`](./decks/PROVENANCE-CAPSTONE.html) (+ appendices A/B) · [`PROVENANCE-SUBMISSION-2PAGE`](./decks/PROVENANCE-SUBMISSION-2PAGE.html) · [`BEFORE-AFTER-VALUE`](./decks/BEFORE-AFTER-VALUE.html) · [`WHY-TECHNICALLY-CHALLENGING`](./decks/WHY-TECHNICALLY-CHALLENGING.html)

**Pitch & vision**
- [`AGENCY-PITCH`](./decks/AGENCY-PITCH.html) (+ [technical appendix](./decks/AGENCY-PITCH-TECHNICAL-APPENDIX.html)) · [`THE-BIG-PICTURE`](./decks/THE-BIG-PICTURE.html) · [`BUSINESS-VISION`](./decks/BUSINESS-VISION.html) · [`BEYOND-MARKETING`](./decks/BEYOND-MARKETING.html) · [`PROVENANCE-EXPLAINER-1PAGE`](./decks/PROVENANCE-EXPLAINER-1PAGE.html)

**Solution & mechanism**
- [`PROVENANCE-SOLUTION`](./decks/PROVENANCE-SOLUTION.html) · [`SOLUTION-DEEP-DIVE`](./decks/SOLUTION-DEEP-DIVE.html) · [`SOLUTION-MASTER-SLIDE`](./decks/SOLUTION-MASTER-SLIDE.html) · [`MECHANISM-TO-VALUE`](./decks/MECHANISM-TO-VALUE.html) · [`FULL-FUNNEL-VIEW`](./decks/FULL-FUNNEL-VIEW.html) · [`PROVABLE-FUNNEL-FOR-MARKETERS`](./decks/PROVABLE-FUNNEL-FOR-MARKETERS.html) · [`SELF-OPTIMIZING-SLIDES`](./decks/SELF-OPTIMIZING-SLIDES.html)

**Demo (Jun 29)**
- [`SHOWCASE-DEMO`](./decks/SHOWCASE-DEMO.html) · [`COHORT-DEMO-PROJECT-PLAN`](./decks/COHORT-DEMO-PROJECT-PLAN.md) · [`MEETING-NOTES-SEGMENTATION-AND-DEMO`](./decks/MEETING-NOTES-SEGMENTATION-AND-DEMO.md)

**Sprint planning**
- [`GAUNTLET-SPRINT-PRD`](./decks/GAUNTLET-SPRINT-PRD.html) · [`GAUNTLET-SPRINT-PLAN`](./decks/GAUNTLET-SPRINT-PLAN.html) · [`GAUNTLET-PILOT-DECK`](./decks/GAUNTLET-PILOT-DECK.html) · [`ONE-WEEK-GAUNTLET-PLAN`](./decks/ONE-WEEK-GAUNTLET-PLAN.md) · [`WEEK-2-CODIFY-AND-REACH`](./decks/WEEK-2-CODIFY-AND-REACH.md)

**Recruiting**
- [`PROVENANCE-RECRUIT-1PAGE`](./decks/PROVENANCE-RECRUIT-1PAGE.html)

**Proposal archive** *(superseded — kept for lineage)*
- [`CAPSTONE-IDEA-MENU`](./decks/CAPSTONE-IDEA-MENU.html) · [`OVERSIGHT-LAYER-PROPOSAL`](./decks/OVERSIGHT-LAYER-PROPOSAL.html) · [`QUALITY-ORACLE-PROPOSAL`](./decks/QUALITY-ORACLE-PROPOSAL.html) · [`SELF-COMPILING-FUNNEL-PROPOSAL`](./decks/SELF-COMPILING-FUNNEL-PROPOSAL.html)

---

*The LysoReach product docs (data model, sources, enrichment, deploy) remain in [`../docs/`](../docs/) — Provenance rides that live spine.*
