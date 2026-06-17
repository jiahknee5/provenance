# Provenance — Team Onboarding

Everything a new teammate needs to go from clone → first contribution. Pairs with [`README.md`](./README.md) (ownership) and the [architecture diagrams](../architecture/).

---

## 1. The one-paragraph mental model

Provenance is a **system of record for claims**. A draft message is decomposed into atomic claims; each claim is bound to an approved source and verified by a calibrated ensemble (**The Gate**); only cleared variants are sent, and a bandit (**The Optimizer**) learns the best one *inside the truth boundary*; a **Drift Monitor** re-verifies when sources change; an **Assurance Lab** continuously proves the Gate works. Delete the models and there's no product — only a logger.

Start with [`architecture/diagrams/00-system-overview.md`](../architecture/diagrams/00-system-overview.md), then your owned module's diagram.

## 2. Proposed repository layout

The capstone code lives **under `provenance/`** alongside these docs (this is the team's home; the parent `lyso/` repo is the live data spine).

```
provenance/
  decks/             # all pitch / planning / proposal artifacts (presentation)
  architecture/      # the 10 module diagrams (mermaid + HTML viewer)  ← you are near here
  team/              # this onboarding + ownership model
  app/               # NEW: Next.js cohort-demo web app          (Owner C)
  pipeline/          # NEW: python — gate/, optimizer/, drift/, assurance/  (A + B)
    gate/            #   decompose · retrieve · nli · ensemble · rules · cascade   (Owner A)
    optimizer/       #   bandit · reward · ope · simulator                          (Owner B)
    drift/           #   cdc · dependency-graph · reverify · controller             (Owner B)
    assurance/       #   trap-generator · harness · metrics                         (Owner A)
    library/         #   claim extraction · evidence binding · graph store          (Owner C)
  data/
    demo/            # recipients.jsonl · pages/ · ledger/ · planted/
  rules/             # gauntlet_tenant.yaml
  sources/           # claims_library/ — approved stats, Drew corpus refs
```
*(Layout mirrors [`COHORT-DEMO-PROJECT-PLAN §3.4`](../decks/COHORT-DEMO-PROJECT-PLAN.md). Create folders as work starts — don't scaffold empty trees.)*

## 3. Local setup

```bash
# from repo root
cd ~/projects/lyso
python3 -m venv .venv && source .venv/bin/activate     # pipeline work
pip install -r provenance/pipeline/requirements.txt    # (create as deps land)
# web app
cd provenance/app && npm install && npm run dev         # Owner C
```

Secrets (LLM keys, etc.) go in a local `.env` — **never commit**. NLI runs local (DeBERTa-v3-MNLI) or via API; pick per latency/cost.

## 4. The integration contract (freeze Day 1)

Everyone codes against the **claim-ledger record** so modules integrate without waiting on each other:

```json
{
  "recipient_id": "uuid",
  "track": "provenance",
  "html": "…rendered copy…",
  "claims": [
    {"claim_id": "c1", "text": "…", "span": [120,168],
     "verdict": "green|amber|red", "source_id": "s7",
     "confidence": 0.94, "rule_flags": []}
  ],
  "generated_at": "…"
}
```

Owner A ships a **Gate stub** returning this shape on Day 1 so Owner C (UI) and Owner B (optimizer arms) are never blocked on the real pipeline.

## 5. Build phases

Two-week scope, anchored on the live ag/biotech spine (real prospects, real sources, a real legal hold = genuine ground truth). Full detail in [`COHORT-DEMO-PROJECT-PLAN §5`](../decks/COHORT-DEMO-PROJECT-PLAN.md) and [`ONE-WEEK-GAUNTLET-PLAN`](../decks/ONE-WEEK-GAUNTLET-PLAN.md).

| Phase | Dates | Headline | Lead |
|-------|-------|----------|------|
| 0 · Foundation | Jun 16–18 | tenant data + RPG schema + planted profiles + ledger contract | C (+A) |
| 1 · Data pipeline | Jun 18–22 | recipients.jsonl, enrichment, Claims Library populated | C |
| 2 · Generation | Jun 22–25 | grounded per-prospect drafts (governed + ungoverned) | C |
| 3 · Gate + ledger ★ | Jun 22–27 | decompose → retrieve → NLI → rules → ledger | **A** |
| — · Assurance + Drift + Optimizer | Jun 24–27 | traps + metrics; rule-change re-Gate; bandit sim | A + B |
| 4 · Web app | Jun 24–28 | magic link, personalized page, compare, inspect UI | C |
| 5 · Rehearsal | Jun 28 | 10-min timed run + offline fallback | all |
| 6 · Showcase | Jun 29 | live | all |

## 6. First-week tasks (parallel, unblocked)

**Owner A (Verify):** freeze the ledger schema + ship the Gate stub; stand up decomposition + retrieval over a tiny Claims Library; first NLI pass on the 3 planted profiles.
**Owner B (Decision):** build the LLM-persona simulator + reward signal; bandit over 3–5 dummy verified arms; sketch the dependency-graph data model for Drift.
**Owner C (Platform):** Tom data → `recipients.jsonl`; RPG schema + 5 example profiles; web shell with magic-link route rendering from a cached ledger JSON.

## 7. Definition of done (MVP must-ship)

From [`PROVENANCE-CAPSTONE.md`](../decks/PROVENANCE-CAPSTONE.md) "Minimum shippable":

- [ ] The Gate end-to-end on email: decompose → bind → NLI + small ensemble → rules → live claim ledger (cited / repaired / blocked).
- [ ] Assurance Lab MVP: ≥20 synthetic traps + catch-rate vs false-reject + a calibration diagram.
- [ ] The regulatory gate (block the legal-hold claim on demand) + the "try to make it lie" demo.
- [ ] Funnel program expressed **as data** so a second tenant is config, not a rebuild.

**Ambitious (scored on ambition):** truth-bounded Optimizer on the simulator (conversion climbs, can't win by lying) · hidden-state probe + verifier bake-off · live Drift Monitor · second-tenant transfer.

## 8. The one line that scores

> *Constrained optimization as a structural fix for reward-hacking* — the bandit can't converge to a higher-reward falsehood because falsehoods never enter the reward loop. Lead the technical pitch with it.
