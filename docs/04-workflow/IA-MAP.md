# IA-MAP — the apt marketer IA contract (W9)

> STATUS: **LOCKED v1** (operator approved 2026-07-12 — decisions recorded as
> R40–R45 in `../01-intake/PRD-MARKETER-IA.md`; D1→R40, D2→R41, D3→R42,
> D4→R43). This file is the source of truth for navigation, page archetypes,
> and link rules. `tests/test_ia_map.py` derives its assertions from the
> tables here; a route or link that drifts from this map fails the suite.
> Exceptions live in the ledger below — never silently.

## 1. Mental model — three planes

| Plane | What it is | Link affordance |
|---|---|---|
| **PRODUCT** | Pages the marketer works in (setup, design, results). The sidebar lives entirely here. | plain links |
| **PREVIEW** | Simulated visitor arrivals (entry chips, galleries, preview tool). | `Preview →` labeled actions |
| **LIVE** | The customer's own website (the replica). | `Open ↗ — your website` marked actions only; never a plain nav destination |

The bug class this kills: sidebar "Organic search" landing on a scenario
landing page (PRODUCT nav item → LIVE destination, unsignposted).

## 2. Stages (place nav) — the sidebar IS this list, in this order

| Stage | Sidebar group | The marketer's question | Primary surfaces |
|---|---|---|---|
| S0 Home | (workspace home) | "Where am I, what's next?" | `/apt/demo` reworked: status + active journey checklist |
| S1 Connect | Your website | "Is apt on my site?" | connect/verify page (today: `Add new website` stub → build) |
| S2 Channels | Channels | "Who arrives, and from where?" | **channel setup pages (NEW)** — one archetype, data-driven per channel × tenant |
| S3 Personalize | Personalization | "What changes on my pages?" | section designer (`/{t}apt/dev/business`), playbook (reference drill) |
| S4 Preview | Preview | "What will a given visitor see, and why?" | preview tool (`/apt/dev`), per-target receipts/decision panels |
| S5 Launch | Launch | "Am I safe to ship this?" | staged-diff review + guardrail check + apply (semantics: D2) |
| S6 Measure | Results | "Is it working?" | live activity (`/observatory`), spend (`/costs`), A/B + drift panels |

Iteration loop: S6 findings feed S3 (tune) — the loop is the product.

## 3. Journeys (task nav) — guided paths that step ACROSS stages

The stages are the map; journeys are the trips. A journey is a checklist
overlay: each step points at one stage page, and that page's **primary CTA
advances the journey**. This is the testable form of "every piece follows a
pre-defined workflow."

**J1 — Launch a new website** (the operator-named flow):
1. Connect the website (S1)
2. Understand arrival channels (S2)
3. Scope personalization — which sections, which text/image targets (S3: designer, `personalize` + add-target controls)
4. Customize each target — mode, policy, strategy, prompt, variants (S3: same cards; decisioning shown inline per target)
5. Preview as visitors from each channel; read the decisions + receipts (S4)
6. Review staged changes + guardrails; launch (S5)
7. Watch results; return to step 4 to tune (S6 → S3)

**J2 — Add one personalization target** (steady-state): S3 scope → S3
customize → S4 preview → S5 launch.

**J3 — Tune an underperformer**: S6 spot (A/B panel / drift pause) → S3
customize → S4 preview → S5 launch.

Golden-path test (to build): each journey is completable by following ONLY
each page's primary CTA — no dead ends, no plane jumps without signposting.

## 4. Page archetypes — every PRODUCT page declares exactly one

| Archetype | Required blocks |
|---|---|
| Stage overview | what this stage is (1 para, marketer words) · status at a glance · ONE primary action above the fold |
| Channel setup (NEW) | signals that arrive with this channel · how message-match works · which landing experience is mapped and why · guardrails on this channel · expected-vs-live example · actions: `Preview an arrival →` (PREVIEW) + `Open live example ↗` (LIVE) |
| Designer | zones: This visit → Design → Proof (W8-B) · collapsed sections · staged-diff drawer |
| Preview tool | identity toggle · entry simulation · open-live CTA (W8-A) |
| Results | one metric family per page · receipts one click away |
| Reference drill | playbook/guide content; reachable from its stage, never a stage itself |

Shell rules (all archetypes): apt sidebar is the ONLY menu · breadcrumb =
Website / Stage / Page · sections collapsed by default · marketer vocabulary
on PRODUCT pages (engineering terms only behind the Developer/audit fold).

## 5. Route table — route → plane → stage → archetype → disposition

| Route | Plane | Stage | Archetype | Disposition |
|---|---|---|---|---|
| `/apt/demo` | PRODUCT | S0 | Stage overview | REWORK: workspace home + J1 checklist (D4) |
| `Add new website` (stub) | PRODUCT | S1 | Stage overview | BUILD: connect/verify page |
| sidebar channel items (today → galleries/landing URLs) | PRODUCT | S2 | Channel setup | BUILD: channel setup pages; galleries demoted to drills |
| `/{t}apt/{direct,email}-gallery`, `/{t}apt/ads`, `/{t}apt/ad` | PREVIEW | S2 drill | — | KEEP as `Preview →` drills from channel pages; REMOVE as sidebar destinations |
| `/{t}apt/dev/business` | PRODUCT | S3 | Designer | KEEP (W8 shape) |
| `/apt/playbook` | PRODUCT | S3 drill | Reference | KEEP |
| `/apt/dev` | PRODUCT | S4 | Preview tool | KEEP (W8-A) |
| staged-diff drawer (`sd-staged`) | PRODUCT | S5 | Launch review | EXTEND: guardrail summary + apply per D2 |
| `/observatory` | PRODUCT | S6 | Results | KEEP |
| `/costs` | PRODUCT | S6 | Results | KEEP |
| `/{t}apt` (+ `?ip=`, utm entries) | LIVE | — | — | KEEP; reachable only via marked ↗ actions |
| `/{t}apt/dev` (engineer console) | PRODUCT-dev | — | — | EXCEPTION E1 |
| `/{t}apt/image-decisions`, `/image-decisions` | PRODUCT-dev | S3 drill | Reference | EXCEPTION E1 (dev-fold entry) |
| `/apt/mockups*` | internal | — | — | EXCEPTION E2 (design exploration, not in nav) |
| `/showcase`, `/site/{token}*`, `/lead`, `/submit` | legacy | — | — | EXCEPTION E3 (locked property tests — see RECONCILIATION T-09) |
| `/api/*` (costs, observe, persuasion, hero-image) | API | — | — | non-nav; crawler ignores |

## 6. Link contract

Every `<a>` on a PRODUCT page is one of:
- **advance** — the page's primary CTA; moves the active journey forward
- **drill** — deeper within the same stage (galleries, playbook chapters)
- **cross-plane** — carries `Preview →` or `Open ↗ — your website` marking
- **external** — none expected on PRODUCT pages

Enforced by tests (to build, wired into the deploy gate):
1. `test_ia_map.py` — route inventory == §5 table (drift fails); sidebar
   items resolve to PRODUCT pages in stage order.
2. Crawler — from `/apt/demo`, walk every same-host link on every PRODUCT
   page: 0 broken, 0 dead redirects, every PRODUCT page ≤2 clicks from the
   sidebar, 0 orphans.
3. Golden-path — each journey completable via primary CTAs only.

## 7. Exception ledger

| # | What | Why it may break the rules | Review |
|---|---|---|---|
| E1 | Engineer consoles + image-decisions guides keep in-page rails and engineering vocabulary | Technical trace surface behind `Technical view →` / dev fold; the receipts differentiator needs an uncompressed home (R32) | keep |
| E2 | `/apt/mockups*` outside nav | design-exploration artifacts, not product | keep |
| E3 | `/showcase`, `/site/{token}*`, `/lead`, `/submit` | Art VII locked property tests pin them (RECONCILIATION T-09) | keep |

## 8. Decisions — RESOLVED (see PRD-MARKETER-IA.md)

- **D1 → R40**: stages S0–S6 approved; journeys overlay them.
- **D2 → R41**: simulated apply, clearly labeled; staging persists to
  localStorage so the Launch page can read it; real apply is a future call.
- **D3 → R42**: channel setup = one data-driven template, no per-tenant forks.
- **D4 → R43**: `/apt/demo` is the workspace Home with the J1 checklist.

## 9. Demo vs real (R46) — marker inventory

One standard chip (`.demo-chip`); tooltip states what the full implementation
does instead. No chip on a surface = it is real in this workspace.

| Surface | Marker | Real implementation |
|---|---|---|
| Every page (sidebar footer) | `demo` | customer workspace, real operator identity |
| Connect — website list | `demo data` | real domains + live install checks |
| Connect — add a website | `simulated` | verifies edge rewrite, imports sections |
| Launch — apply | `demo — apply is simulated` | writes section registry + redeploys |
| Channel pages — mapped arrivals | `demo scenarios` | live campaign integrations (X/Google/Meta/HubSpot) |
| Designer — A/B panels | `seeded (demo)` in panel title | live Thompson posteriors from real traffic |
| Consoles — CRM / lead context | `demo cohort` | real CRM sync (HubSpot, Salesforce) |
| Observatory | banner: seeded engine replay | live per-visit activity board (W11 rec) |
| REAL, unmarked | — | Gate verdicts, receipts, per-section event rows, cost ledger, realtime image generation are the live engine |
