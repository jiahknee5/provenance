# Week 2 — Codify + Reach Goals

**Follows:** [One-week Gauntlet plan](./ONE-WEEK-GAUNTLET-PLAN.md) (Week 1 = ship **full Provenance stack** + Gauntlet day demo)  
**Theme:** Turn the Week 1 demo into **durable product artifacts** — then pull **UX reach** goals off the backlog (compare, attribution v2, live email/ad gen).

**North star:** After Week 2, a new engineer can run the cohort demo from docs + scripts, and the capstone spine is **specified, tested, and hardened** — not tribal knowledge in a one-off HTML hack.

**Policy:** Optimizer, Drift, Assurance, Gate, and Claims Library **first ship in Week 1**. Week 2 extends and codifies them; it does not substitute for D7 delivery.

---

## Executive summary

| Track | Purpose | Outcome |
|-------|---------|---------|
| **A — Codify** | Document, structure, test, and refactor what Week 1 built | Repo layout, schemas, runbooks, consolidated deck, Gate batch as repeatable pipeline |
| **B — Reach** | Ship **UX reach** deferred from Week 1 polish | Compare mode, segmentation live, attribution v2, live email/ad templates — **not** first Provenance component delivery |

**Rule:** Codify **before** adding reach features that touch the same code paths — otherwise Week 2 becomes another scramble.

---

## Week 1 → Week 2 handoff

At end of Gauntlet day, capture within 24 hours:

| Artifact | Codify into |
|----------|-------------|
| `demo/cohort-web/` | Documented app + env setup + deploy script |
| `demo/data/recipients.jsonl` | JSON Schema + import/export CLI |
| `demo/rules/gauntlet_tenant.yaml` | Tenant spec doc + validation |
| Batch page generation scripts | `demo/scripts/` with README |
| Gate batch + ledger JSON | Gate pipeline module + contract |
| `GAUNTLET-DAY-DECK.html` | Merged into permanent deck hub; dead slides removed |
| Facilitator runbook (if ad hoc) | `docs/GAUNTLET-DAY-RUNBOOK.md` |
| QA screenshots | `.qa/gauntlet-day/` + known issues list |
| Post-demo notes | `docs/WEEK-1-RETRO.md` (what broke, what landed) |

**Gate:** No reach work starts until handoff checklist is ≥80% done (Day 1–2 of Week 2).

---

## Track A — Codify (Days 1–4)

### A1. Repository & tenant model

| Task | Deliverable |
|------|-------------|
| Freeze **Recipient Profile Graph** schema | `demo/schemas/recipient-profile.schema.json` |
| Freeze **claim ledger** schema | `demo/schemas/claim-ledger.schema.json` |
| Tenant config pattern | `demo/tenants/gauntlet/` (rules, sources, claims library) |
| Document multi-tenant swap | `docs/TENANT-MODEL.md` — marketing vs Gauntlet vs future |

### A2. Provenance pipeline (repeatable, not one-off)

| Component | Codify as |
|-----------|-----------|
| **Claims Library** | Versioned sources + approved facts; loader + tests |
| **The Gate** | `gate/` or `demo/pipeline/gate.py`: decompose → retrieve → rules → ledger |
| **Batch generation** | `generate_pages.py --track ungoverned\|provenance --cohort all` |
| **Channel adapter: website** | Document interface: `render(recipient, track, ledger?) → html` |
| **Assurance Lab** | Trap set format + CI eval on Gate changes (W1 delivered ≥20 traps + metrics) |
| **Optimizer** | Spec hardening + emotional A/B variants (W1 delivered leaderboard) |
| **Drift Monitor** | Batch re-Gate all cohort + dependency graph (W1 delivered single-profile demo) |

**Target:** Re-run full cohort batch in one command after changing one rule in YAML.

### A3. Demo app hardening

| Task | Deliverable |
|------|-------------|
| README: local dev, staging deploy, magic links | `demo/cohort-web/README.md` |
| Error states (unknown token, opt-out) | UI + tests |
| “Simulated data” badges on T3/T4 fields | Consistent component |
| Offline / fallback mode | Static export or USB bundle doc |
| Mobile QA checklist | `docs/QA-COHORT-WEB.md` |

### A4. Deck & narrative consolidation

| Task | Deliverable |
|------|-------------|
| Merge Week 1 deck sections into **`docs/PROVENANCE-DECK-HUB.html`** | Single presenter file with nav |
| Align with existing pages | Link FULL-FUNNEL, GAUNTLET-PILOT, SHOWCASE beats |
| Update competitive slides from Week 1 research | Clay, Insider, big tech — sourced bullets |
| Capstone alignment pass | Week 2 deck sections map to PROJECT-PLANNING-DOCUMENT §4 |

### A5. Documentation for capstone graders

| Doc | Content |
|-----|---------|
| `docs/ARCHITECTURE.md` | System diagram, component boundaries, data flow |
| `docs/WORKFLOW-DEMO.md` | Ad → pixel → form → email → night school → web → Gate |
| `docs/GATE-SPEC.md` | Pipeline stages, rule DSL, ledger statuses |
| Update `COHORT-DEMO-PROJECT-PLAN.md` | “Built vs planned” diff after Week 1 |

---

## Track B — Reach goals (Days 3–7)

Prioritized backlog from Week 1 plan + meetings. **P0 = Week 2 UX reach; P1 = harden Provenance; P2 = Jun 29 stretch.**

> **Note:** R3 Assurance, R9 Drift, and R10 Optimizer were **Week 1 must-ship** (see PR-03–05). Week 2 items below are **extensions only**.

### P0 — UX reach (Week 2 core)

| # | Reach goal | Why now | Deliverable |
|---|------------|---------|-------------|
| R1 | **Compare mode** (`/compare`) | Highest demo impact post–Gauntlet day | Side-by-side two tokens; diff highlights |
| R2 | **Segmentation live in RPG** | Meetings: adoption curve, Maslow, emotional trigger | `segmentation.*` populated by rules; reflected in copy variants |
| R4 | **Attribution debugger v2** | Week 1 simulated → structured | Pixel event log UI: Meta + GA4 + UTM + night school + email events on timeline |
| R5 | **Email + ad channel (live generation)** | Deck §7 as live artifacts | HTML email + IG ad mock generated from same RPG + Gate in app |
| R6 | **Self-declare on load** (optional enrich) | Compromise on “phone capture” | “Confirm session / role” → merges into profile for live moment |

### P1 — Provenance hardening + polish (Week 2 if bandwidth)

| # | Reach goal | Deliverable |
|---|------------|-------------|
| R3 | **Assurance Lab hardening** | Expand trap set; CI eval on every Gate change (W1: ≥20 traps + panel) |
| R7 | **A/B emotional triggers** | 3 hero variants per segment; deeper Optimizer sim |
| R8 | **Drew email corpus** indexed | Few-shot tone in generation prompts; cited in Claims Library |
| R9 | **Drift batch re-Gate** | Re-Gate full cohort on rule change (W1: single-profile demo) |
| R10 | **Optimizer depth** | Richer simulator; SHOWCASE integration polish (W1: leaderboard + grayed lie) |
| R11 | **Enrichment agent batch v2** | Documented agent job (not live): company lookup, public profile summary |
| R12 | **Gauntlet walkthrough deck polish** | W1–W10 animated or click-through in deck hub |

### P2 — Reach (post–Week 2 / Jun 29)

| # | Reach goal | Notes |
|---|------------|-------|
| R13 | Real Meta/Google sandbox pixels | Needs ad account + consent |
| R14 | Tier 4 social scraping | ToS + Meta Helix spike |
| R15 | Live agent enrich on page load | Only after batch pipeline stable |
| R16 | Email send (Iterable/Braze adapter) | Real SMTP/API |
| R17 | Gauntlet Prime/Catalyst routing tenant | Second vertical per GAUNTLET-PILOT-DECK |
| R18 | Alpha-gal / health planted profile suite | Compliance rule pack |
| R19 | Second tenant (Helix marketing) | Transfer demo for Jun 29 |
| R20 | Live Gate on stage (one claim) | High risk; pre-scoped only |

---

## Week 2 schedule (7 days)

### Day 1 — Retro + handoff + schemas

- Write `WEEK-1-RETRO.md` from Gauntlet day notes  
- Complete handoff checklist  
- Publish RPG + ledger JSON Schema  
- Tag `week-1-demo` git branch or release note  

**Exit:** Schemas validate existing `recipients.jsonl`.

---

### Day 2 — Pipeline codify

- Extract Gate batch into repeatable module  
- Tenant folder layout `demo/tenants/gauntlet/`  
- One-command regen: `./demo/scripts/regen_all.sh`  
- `GATE-SPEC.md` + `TENANT-MODEL.md` drafts  

**Exit:** Change one rule → regen → diff ledger for 3 test users.

---

### Day 3 — Reach P0 starts

- **R4** Attribution debugger v2 (timeline UI)  
- **R2** Segmentation rules in enricher  
- **R1** Compare route (pair tokens)  

**Exit:** Compare mode works for 2 real cohort tokens.

---

### Day 4 — Live email/ad gen + app hardening

- **R5** Email + ad templates from Gate (live gen in app)  
- **R3** Assurance CI on Gate module changes  
- Codify **A3** app README + error states  

**Exit:** Live email mock in app; Assurance CI green on trap set.

---

### Day 5 — Provenance hardening + deck merge

- **R9** Drift batch re-Gate script (extend W1 single-profile demo)  
- **R10** Optimizer sim depth (extend W1 leaderboard)  
- **A4** Merge decks into PROVENANCE-DECK-HUB  
- **R8** Drew corpus in Claims Library (if available)  

**Exit:** Single deck hub; batch drift reproducible.

---

### Day 6 — Integration + QA

- Full regen → deploy staging  
- Mobile + compare + governed + edgy regression  
- **R6** Self-declare form (optional)  
- **R7** Emotional trigger variants (if time)  
- Update capstone planning doc with Week 1–2 status  

**Exit:** QA checklist green; runbook complete.

---

### Day 7 — Buffer + Jun 29 prep

- P1 items from backlog if ahead  
- Record 5-min demo video (backup for Jun 29)  
- Prioritize Week 3 from P2 list  
- Team retro: codify quality + reach velocity  

**Exit:** Written Week 3 scope (Jun 29 showcase hardening).

---

## Codify vs reach — dependency graph

```
Week 1 demo (frozen snapshot)
        │
        ▼
  Schemas + tenant layout ──► Gate pipeline module ──► regen_all.sh
        │                           │
        │                           ├──► R3 Assurance eval
        │                           ├──► R5 email/ad adapters
        │                           └──► R9 Drift re-run
        │
        ├──► ARCHITECTURE.md / GATE-SPEC.md
        │
        └──► Compare + debugger UI (R1, R4) — needs stable RPG + pages
```

---

## Success criteria (end of Week 2)

### Codify (must)
- [ ] New teammate runs demo from README in < 30 min  
- [ ] RPG + ledger schemas validated in CI or script  
- [ ] One-command cohort regen documented and working  
- [ ] `ARCHITECTURE.md` + `GATE-SPEC.md` exist  
- [ ] Deck hub consolidated (one HTML entry point)  
- [ ] Week 1 retro captured  

### Reach (must — P0)
- [ ] Compare mode shipped  
- [ ] Segmentation fields drive visible copy difference  
- [ ] Assurance Lab: trap set + headline metrics  
- [ ] Attribution timeline (simulated pixels + first-party events)  
- [ ] Email + ad examples generated through Gate path  

### Reach (should — P1)
- [ ] Drift demo (one rule change → re-Gate)  
- [ ] Optimizer “can’t win by lying” panel  
- [ ] Drew tone in Track B generation  

---

## Risks (Week 2)

| Risk | Mitigation |
|------|------------|
| Week 1 shipped messy — codify takes whole week | Timebox codify to Days 1–2; cut P1 not P0 |
| Gate refactor breaks demo | Tag Week 1 release; regression on 10 tokens |
| Reach sprawl | P0 only unless codify exit criteria met |
| Jun 29 scope creep | Week 2 ends with written Week 3 plan, not infinite reach |

---

## Pushback (Week 2)

| Temptation | Recommendation |
|------------|----------------|
| Skip codify, jump to live scraping | **No** — you'll re-break Gauntlet day demo |
| Real pixels + CAPI in Week 2 | **P2** — sandbox account is a project, not a day |
| Second tenant before Gate stable | **P2** — transfer demo is Jun 29 stretch |
| Rewrite demo in new framework | **No** — refactor in place unless blocked |

---

## Links

| Doc | Use |
|-----|-----|
| [ONE-WEEK-GAUNTLET-PLAN.md](./ONE-WEEK-GAUNTLET-PLAN.md) | Week 1 sprint |
| [COHORT-DEMO-PROJECT-PLAN.md](./COHORT-DEMO-PROJECT-PLAN.md) | Technical depth |
| [MEETING-NOTES-SEGMENTATION-AND-DEMO.md](./MEETING-NOTES-SEGMENTATION-AND-DEMO.md) | Segmentation reach (R2, R7) |
| [SHOWCASE-DEMO.html](./SHOWCASE-DEMO.html) | Jun 29 presenter beats |
| [PROJECT-PLANNING-DOCUMENT.html](./PROJECT-PLANNING-DOCUMENT.html) | Capstone MVP vs ambitious |

---

*Week 2 starts after Gauntlet day retro. First action: `WEEK-1-RETRO.md` + schema freeze.*
