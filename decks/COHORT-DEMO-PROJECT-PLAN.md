# Cohort Demo — Detailed Project Plan

**Project:** Provenance live personalized-website demo for Gauntlet cohort (Jun 29 showcase)  
**Status:** Planning · v1  
**Related:** [Meeting notes](./MEETING-NOTES-SEGMENTATION-AND-DEMO.md) · [Showcase demo](./SHOWCASE-DEMO.html) · [Competitive view](./FULL-FUNNEL-VIEW.html)

---

## Executive summary

**Goal:** During the Jun 29 presentation, every cohort member logs into a website that feels * unnervingly personalized to them* — then compares with neighbors, sees planted “borderline illegal” examples, and understands why this **cannot ship at scale without Provenance**.

**Two personalization tracks (both built):**

| Track | Data | Copy | Purpose |
|-------|------|------|---------|
| **A — Edgy / synthetic** | Gauntlet real fields + **fabricated** psychographic/social signals | Maximum emotional leverage; planted violations | Shock + “this is what unconstrained AI + data wants to say” |
| **B — Realistic / platform-native** | Gauntlet real fields + **simulated but accurate** Meta/Google/LinkedIn-style segments | Creepy-but-believable; no fabricated health claims | “This is what Meta/Google *actually* know — and still don’t verify” |

**Third beat — Provenance path:** Same recipient, same data inputs → Gate → claim ledger → safe website variant only.

**Technical thesis:** Big tech already wins on personalization volume and bandit optimization. We win on **provable generation** and **constrained self-optimization** — the demo makes that gap visceral in 10 minutes.

---

## Part 0 — Competitor analysis & differentiation (introduction)

### 0.1 What big tech already solves

Personalization and auto-optimization are **commoditized**. We do not compete on “AI writes copy” or “A/B at scale.”

| Vendor | Capability | Personalization mechanism | What they optimize | Verification |
|--------|------------|---------------------------|-------------------|--------------|
| **Meta (Advantage+)** | Auto creative, audience, placement, bidding | Lookalikes, interest graphs, on-platform behavior | CTR, ROAS, engagement | Human review suggested; no claim-level grounding |
| **Google (PMax / AI Max)** | Cross-property campaigns, Gemini assets | Search intent, in-market segments, Customer Match | Clicks, conversions | No atomic claim → source binding |
| **Salesforce (Agentforce / Einstein)** | Journey agents, predictive scoring, content gen | CRM + engagement history | Pipeline, revenue | Content trust = human queue |
| **Adobe (Journey Optimizer + Sensei)** | Real-time CDP, orchestration, Firefly | Unified profile, event streams | Engagement, LTV | Brand/compliance workflows, not entailment |
| **Netflix / Lyft / Yahoo** | Contextual bandits at scale | Per-user context → action | Watch time, rides, clicks | N/A — no factual claims |
| **HubSpot / Iterable / Braze** | Email/website personalization | CRM fields, events, segments | Open/click/convert | Merge tags ≠ verified claims |

**Pattern:** Generate → target → optimize → orchestrate. All optimize **engagement**. None guarantee **truth** or **permissibility** at the claim level.

### 0.2 The three holes (our wedge)

1. **No claim verification** — Generated copy can hallucinate; vendors say “review it.” No mandatory citation chain.
2. **No optimizer guardrail** — Bandits learn that exaggeration wins; structurally Goodhart-prone.
3. **Wrong trust surface** — Walled-garden B2C ads ≠ regulated, named-prospect outbound where being wrong is a fine or lawsuit.

### 0.3 Our two differentiators (what we build)

| # | Differentiator | Mechanism | vs. big tech |
|---|----------------|-----------|--------------|
| **1** | **Provable generation** | Atomic claim decomposition → evidence retrieval → NLI entailment + calibrated ensemble → compliance rules → cited or killed | They generate fast; we generate **with proof** |
| **2** | **Constrained self-optimization** | Same contextual bandit as Netflix — but action space = **verified+cleared variants only** | They optimize engagement; we **bound optimization to truth** |

### 0.4 Positioning for the demo audience

> “Meta would personalize this page beautifully. Google would bid on your intent. Salesforce would score you as a lead. **None of them would stop the page from guaranteeing you a job.** Provenance would.”

**Reference deck:** [FULL-FUNNEL-VIEW.html](./FULL-FUNNEL-VIEW.html)

---

## Part 1 — Demo vision & narrative

### 1.1 Experience overview (10 min live + 5 min cohort interaction)

```
[0:00] Competitor frame — "They already do personalization"
[1:00] QR / magic link — cohort logs in
[2:00] Track A or B website renders — "How did it know that?"
[3:00] Compare mode — pairs/table groups, side-by-side
[4:00] Planted edgy profiles — facilitator walks through violations
[5:00] Scale discussion — "200 of these by Friday?"
[6:00] Provenance reveal — Gate + ledger on same profile
[7:00] Assurance Lab metrics — catch-rate / false-reject (Week 1 must)
[8:00] Optimizer — bounded variants; grayed illegal arm (Week 1 must)
[8:30] Drift — rule change → re-Gate → stale badge (Week 1 must)
[9:00] Ask — four owner surfaces, join the build
```

### 1.2 Dual-track personalization (detail)

#### Track A — Edgy / synthetic (“uncanny + unsafe”)

**Intent:** Show the *maximum* of what unconstrained personalization + LLM copy wants to do when fed rich (including fabricated) context.

**Data we use (mix real + made up):**

| Layer | Real (Gauntlet) | Synthetic (labeled in admin) |
|-------|-----------------|------------------------------|
| Identity | Name, email, photo if available | — |
| Cohort | Night school attendance, signup source | “Top 3% engagement in cohort” |
| Career | Role from signup | Inferred salary band, “likely job search” |
| Psychographic | — | Maslow layer, adoption-curve stage, primary emotional trigger |
| Social (fabricated) | — | “Follows @karpathy, @sama”; “Engaged with posts about AI safety”; “Member of 2 AI discords” |
| Behavioral (fabricated) | — | “Visited Gauntlet pricing page 4×”; “Abandoned capstone form”; “Opened Drew email within 90 sec” |
| Health/life (fabricated — for edge cases only) | — | Planted profiles only: allergy, family status, financial stress |

**Copy characteristics:**
- Second-person specificity: “You left night school early on June 3…”
- Implied guarantees: outcomes, income, placement
- Urgency from fabricated behavioral signals
- 2–3 **planted recipients** with borderline-illegal copy (pre-authored, not live-generated at showtime)

#### Track B — Realistic / platform-native (“this is what CDPs actually have”)

**Intent:** Show personalization that mirrors **real Meta/Google/LinkedIn data classes** — creepy but legally and technically plausible — without fabricated medical/financial facts.

**Simulated platform signals (schema-accurate, not live API for capstone):**

| Platform | Signal types we simulate | Example fields |
|----------|-------------------------|----------------|
| **Meta (Custom Audiences)** | Interest categories, demographics, page engagement | `interests: ["Artificial intelligence", "Online education"]`, `age_bracket`, `region` |
| **Google (Analytics / Ads)** | In-market segments, affinity, search themes | `in_market: ["Business technology"]`, `search_themes: ["AI bootcamp", "LLM engineering"]` |
| **LinkedIn (Matched Audiences)** | Job title, seniority, industry, company size | `title: "Software Engineer"`, `seniority: "Senior"`, `industry: "Technology"` |
| **Gauntlet first-party** | Email opens, night school attendance, signup metadata | `night_school_sessions: 2`, `signup_source: "referral"` |

**Copy characteristics:**
- “Based on your interest in AI education…” (Meta-style)
- “People in your segment often…” (Google in-market style)
- Role/industry personalization (LinkedIn-style)
- **No** fabricated health claims or guaranteed outcomes — but still **unverified** stat claims (“90% of builders like you…”) that fail Gate

#### Track C — Provenance (governed)

Same recipient ID + same input profile → generation → **Gate pipeline** → only cleared claims render → ledger visible in “inspect” mode.

---

## Part 2 — Data architecture

### 2.1 Recipient Profile Graph (RPG)

Unified JSON schema per demo user. Single source of truth for both tracks.

```json
{
  "recipient_id": "uuid",
  "track_default": "realistic",
  "identity": {
    "name": "Alex Kim",
    "email": "alex@example.com",
    "photo_url": null
  },
  "gauntlet_first_party": {
    "signup_source": "night_school",
    "night_school_sessions": [{"date": "2026-06-05", "topic": "Agents"}],
    "email_engagement": {"drew_opens": 3, "last_open": "2026-06-12"},
    "capstone_interest": "trust / verification"
  },
  "platform_realistic": {
    "meta": {"interests": [], "region": "US-CA"},
    "google": {"in_market": [], "affinity": []},
    "linkedin": {"title": "", "seniority": "", "industry": ""}
  },
  "synthetic_edgy": {
    "enabled": false,
    "maslow_layer": "esteem",
    "adoption_curve": "early_adopter",
    "emotional_trigger": "ambition",
    "fabricated_social": [],
    "fabricated_behavioral": []
  },
  "segmentation": {
    "icp_fit": "high",
    "decision_timing": "evaluating"
  },
  "demo_flags": {
    "planted_edge_case": null,
    "show_compare": true,
    "facilitator_notes": ""
  }
}
```

### 2.2 Data sourcing & enrichment pipeline

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ Tom export      │────▶│ Identity resolver │────▶│ RPG (base)          │
│ (Gauntlet CSV)  │     │ email → recipient │     │ gauntlet_first_party│
└─────────────────┘     └──────────────────┘     └──────────┬──────────┘
                                                            │
┌─────────────────┐     ┌──────────────────┐               │
│ Manual seed     │────▶│ Segment inferencer│───────────────┤
│ (roles, goals)  │     │ adoption/Maslow   │               │
└─────────────────┘     └──────────────────┘               │
                                                            ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ Platform schema │────▶│ Realistic enricher│────▶│ platform_realistic  │
│ (Meta/Google/   │     │ rule-based map    │     │ track B inputs      │
│  LinkedIn tmpl) │     │ from signup fields│     └─────────────────────┘
└─────────────────┘     └──────────────────┘

┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ Creative brief  │────▶│ Synthetic enricher│────▶│ synthetic_edgy      │
│ (planted only)  │     │ human-authored    │     │ track A inputs      │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

**Phase 1 data tasks:**

| Task | Input | Output | Owner |
|------|-------|--------|-------|
| Tom cohort export | Email lists, signups, attendance | `data/demo/cohort_raw.csv` | Data |
| Identity resolution | CSV | `data/demo/recipients.jsonl` | Data |
| Realistic enrichment | Signup fields → platform schema | `platform_*` blocks populated | Data + PM |
| Synthetic profiles | 3 planted + optional opt-in edgy | `synthetic_edgy` blocks | PM + Copy |
| Consent / opt-out | Cohort comms | `demo_flags.opt_out` | PM |

**Privacy:** Synthetic/fabricated fields **never** presented as real to the recipient — facilitator script labels Track A as “what unconstrained systems *could* infer.” Track B uses only plausible platform classes. Opt-out → generic demo persona.

---

## Part 3 — Technical architecture (detailed)

### 3.1 System diagram

```
                    ┌─────────────────────────────────────────────┐
                    │           COHORT DEMO WEB APP               │
                    │  (Next.js or Vite + API routes)             │
                    └─────────────────────────────────────────────┘
                      │              │              │
          magic link  │              │              │  compare mode
          auth        ▼              ▼              ▼
               ┌──────────┐   ┌────────────┐   ┌─────────────┐
               │ Auth     │   │ Personalize│   │ Compare     │
               │ service  │   │ renderer   │   │ view        │
               └────┬─────┘   └─────┬──────┘   └─────────────┘
                    │                 │
                    │    ┌────────────┴────────────┐
                    │    │                         │
                    ▼    ▼                         ▼
               ┌─────────────┐              ┌───────────────┐
               │ RPG store   │              │ Generation    │
               │ (Postgres / │              │ service       │
               │  JSONL)     │              │ (LLM + cache) │
               └─────────────┘              └───────┬───────┘
                                                    │
                         ┌──────────────────────────┼──────────────────────────┐
                         │                          │                          │
                         ▼                          ▼                          ▼
                  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
                  │ UNGOVERNED  │           │ THE GATE    │           │ Optimizer   │
                  │ pipeline    │           │ (Provenance)│           │ (optional)  │
                  │ Track A/B   │           │ Track C     │           │             │
                  └─────────────┘           └──────┬──────┘           └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │ Claim       │
                                            │ ledger API  │
                                            └─────────────┘
```

### 3.2 Component specifications

#### 3.2.1 Auth — magic link per recipient

| Spec | Detail |
|------|--------|
| **Flow** | Email in Tom export → pre-provisioned token → QR encodes `https://demo.provenance.app/r/{token}` |
| **Fallback** | Facilitator “demo login” dropdown for planted profiles |
| **Security** | Tokens single-use optional; rate limit; no PII in URL beyond opaque token |
| **Tech** | JWT or signed opaque token; 7-day expiry; Redis optional for revoke |

#### 3.2.2 Personalization renderer (website channel adapter)

| Spec | Detail |
|------|--------|
| **Input** | `recipient_id`, `track` (`edgy` \| `realistic` \| `provenance`), `page_template` |
| **Output** | HTML landing page: hero, 3 proof blocks, CTA, “why you” section citing profile signals |
| **Templates** | 1 base template; content slots filled from generation cache |
| **Inspect mode** | Toggle shows claim ledger overlay (Track C only) |

**Technical approach:**
- Pre-generate all copy **48h before showcase** (no live LLM on stage unless redundant fallback cached)
- Store variants: `{recipient_id, track, html, claims[], generated_at}`
- Render from cache; live demo = switching tracks + ledger UI, not waiting on inference

#### 3.2.3 Generation service

| Spec | Detail |
|------|--------|
| **Ungoverned (A/B)** | LLM prompt: full RPG context + emotional trigger + Drew-email tone few-shot → raw copy |
| **Governed (C)** | Same prompt → **Gate pipeline** → repaired copy + ledger |
| **Prompt structure** | System: brand voice · User: RPG JSON + segment hints · Output: structured JSON `{hero, blocks[], cta, claims[]}` |
| **Caching** | Hash(prompt + model + track) → disk cache; version pin |

#### 3.2.4 The Gate (core technical — must be real, not faked)

Pipeline per generated asset:

```
Draft text
    │
    ▼
[1] Atomic claim decomposition (LLM or spaCy + LLM repair)
    │  → [{claim_id, text, span}]
    ▼
[2] Evidence retrieval (Claims Library + source docs)
    │  → [{claim_id, source_id, passage, score}]
    ▼
[3] Entailment check (NLI model: premise=source, hypothesis=claim)
    │  + calibrated ensemble (optional second judge)
    ▼
[4] Compliance rules engine (DSL: MLR holds, FTC, channel, jurisdiction)
    │  → permitted | blocked | needs_disclaimer
    ▼
[5] Router-referee cascade
    │  cheap checks first; escalate uncertain to ensemble
    ▼
Claim ledger: GREEN (cited) | AMBER (repaired/disclaimer) | RED (blocked)
```

| Stage | Model / tech | MVP target |
|-------|--------------|------------|
| Decomposition | GPT-4.1 mini / local Qwen | ≥95% claim recall on eval set |
| Retrieval | Hybrid BM25 + embeddings over Claims Library | top-3 contains gold source ≥90% |
| NLI | DeBERTa-v3-large-MNLI or equivalent | calibrated P(correct) |
| Rules | YAML/JSON rule DSL + regex | 100% on planted MLR holds |
| Ledger | Postgres + API | <200ms p95 for demo |

**Demo-specific rules (Gauntlet tenant):**
- Block guaranteed income / job placement
- Block health claims tied to personal attributes
- Block “#1 in cohort” without source
- Block competitor disparagement without substantiation
- Require disclaimer on educational outcome claims

#### 3.2.5 Compare mode

| Spec | Detail |
|------|--------|
| **UI** | Two-up or grid; select neighbor from dropdown (same table / random) |
| **Shows** | Side-by-side hero + diff highlights on claims |
| **Facilitator** | “Why is yours different?” → micro-segment + emotional trigger explanation |
| **Tech** | Client-side diff of cached HTML; highlight spans with claim IDs |

#### 3.2.6 Planted edge-case profiles

Pre-built, not generated live:

| Profile | Violation type | Track | Facilitator script |
|---------|----------------|-------|-------------------|
| **Edge-1 “Jordan”** | Implied job guarantee | A | “FTC / educational advertising” |
| **Edge-2 “Sam”** | Health-adjacent + personal detail | A | “Fabricated inference + medical adjacency” |
| **Edge-3 “Riley”** | Unverified superlative + fake urgency | B | “Platform-style — still unverified stats” |

Each has: ungoverned page, governed page, ledger JSON, violation checklist.

#### 3.2.7 Optimizer (Week 1 must)

| Spec | Detail |
|------|--------|
| **Scope** | Offline sim for showcase; not live cohort traffic |
| **Mechanism** | Contextual bandit; arms = verified variant IDs only |
| **Demo viz** | Chart: reply rate ↑; grayed “Guaranteed placement” arm never enters pool |
| **Proves** | Structural anti-reward-hacking |
| **Ship by** | D4 (panel) · rehearsed D6 · shown D7 |

#### 3.2.8 Assurance Lab (Week 1 must)

| Metric | Target (illustrative for demo) |
|--------|-------------------------------|
| Catch rate on adversarial traps | >90% ensemble vs ~70% LLM-judge-only |
| False reject | <5% |
| ECE (calibration) | ±3% |

≥20 traps; pre-compute on trap set; display in governed site sidebar or SHOWCASE beat on D7.

#### 3.2.9 Drift Monitor (Week 1 must)

| Spec | Detail |
|------|--------|
| **Demo** | Facilitator changes one rule in tenant YAML → re-Gate one profile → stale badge → updated ledger |
| **Target** | Completes in <60s on stage |
| **Ship by** | D5 script + UI · rehearsed D6 |

### 3.3 Tech stack recommendation

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Web app | **Next.js 15** (App Router) | SSR per-recipient pages, API routes, fast deploy |
| DB | **SQLite** (demo) or Postgres | Recipient cache + ledger; portable |
| Auth | Magic link tokens | No passwords in room |
| LLM | OpenAI / Anthropic API | Generation + decomposition |
| NLI | Local or API | Latency vs cost tradeoff |
| Hosting | Vercel + env secrets | QR-friendly HTTPS |
| Pre-gen batch | Python script | `scripts/demo/generate_cohort_pages.py` |

### 3.4 Repository layout (proposed)

```
lyso/
  demo/
    cohort-web/          # Next.js app
    scripts/
      import_cohort.py
      enrich_realistic.py
      enrich_synthetic.py
      generate_pages.py
      run_gate_batch.py
    data/
      cohort_raw.csv
      recipients.jsonl
      pages/             # cached HTML per recipient/track
      ledger/            # claim JSON per recipient
      planted/           # edge case profiles
    rules/
      gauntlet_tenant.yaml
    sources/
      claims_library/    # approved stats, Drew email corpus refs
```

---

## Part 4 — Segmentation & copy engine (feeds both tracks)

### 4.1 Segmentation dimensions (from meeting notes)

| Dimension | Inference source | Affects |
|-----------|------------------|---------|
| Adoption curve | Attendance depth, signup recency | Proof depth, CTA boldness |
| Emotional trigger | Rule-based assignment for demo | Hero angle (fear/ambition/belonging) |
| Maslow layer | Role + signup goals | Offer framing |
| Decision timing | Engagement signals | Urgency vs nurture |
| ICP fit | Rule score | Whether to show “join team” CTA |

### 4.2 Copy generation matrix

For each recipient, pre-generate **3 variants** (cached):

1. **Ungoverned edgy** (if `synthetic_edgy.enabled`)
2. **Ungoverned realistic** (platform signals only)
3. **Provenance governed** (Gate output)

Optional: 3 emotional-trigger sub-variants within (2) for Optimizer story.

### 4.3 Drew email corpus

Use 2–3 real Drew sends as few-shot tone anchors — subject patterns, cadence, CTA style. **Not** copied verbatim; style transfer only.

---

## Part 5 — Build phases & timeline

**Showcase date:** Jun 29, 2026  
**Planning doc due:** Jun 17

### Phase 0 — Foundation (Jun 16–18)

| Deliverable | Done when |
|-------------|-----------|
| Tom data confirmed + `cohort_raw.csv` | Fields documented, PII cleared |
| RPG schema frozen | JSON schema + 5 example profiles |
| Competitor intro slide/deck section | Pull from Part 0 → presenter notes |
| Planted edge profiles written | 3 full copy sets + violation list |
| Consent / opt-out comms sent | Email to cohort |

### Phase 1 — Data pipeline (Jun 18–22)

| Deliverable | Done when |
|-------------|-----------|
| `recipients.jsonl` populated | All cohort members + planted |
| Realistic enricher | Meta/Google/LinkedIn blocks for all |
| Synthetic enricher | Planted + optional edgy cohort subset |
| Segment tags computed | adoption, Maslow, trigger, timing |

### Phase 2 — Ungoverned generation (Jun 22–25)

| Deliverable | Done when |
|-------------|-----------|
| Generation prompts v2 | Drew tone + segment matrix |
| Batch: Track A pages | Cached HTML for planted + sample |
| Batch: Track B pages | Cached HTML for **all** cohort |
| Compare mode mock | Static prototype |

### Phase 3 — Gate + ledger (Jun 22–27) ★ critical path

| Deliverable | Done when |
|-------------|-----------|
| Claims Library (Gauntlet tenant) | Approved stats, sources, MLR holds |
| Gate pipeline MVP | Decompose → retrieve → NLI → rules |
| Batch: Track C pages | Governed HTML for all cohort |
| Ledger API + inspect UI | Green/amber/red + source drawer |
| Planted profiles: governed vs ungoverned pairs | Facilitator rehearsal ready |

### Phase 4 — Web app (Jun 24–28)

| Deliverable | Done when |
|-------------|-----------|
| Magic link auth | Token per recipient |
| Personal landing page route | `/r/[token]` |
| Track switcher (facilitator) | A / B / C toggle |
| Compare view | Two-up diff |
| Mobile-safe | Phone login in room |
| Load test | 200 concurrent OK |

### Phase 5 — Rehearsal (Jun 28)

| Deliverable | Done when |
|-------------|-----------|
| Full run with team | 10 min timed |
| Fallback offline mode | USB/local if WiFi fails |
| QR printed + backup link | Slides ready |

### Phase 6 — Showcase (Jun 29)

Live execution per narrative §1.1.

---

## Part 6 — Team ownership (maps to capstone)

| Surface | Owns | Demo responsibilities |
|---------|------|----------------------|
| **Owner 1 — Gate** | Verifier ML core | NLI, ensemble, rules, ledger API, batch governed pages |
| **Owner 2 — Optimizer + Assurance + Drift** | RL + eval + drift | Trap set, metrics panel, Optimizer leaderboard, rule-change demo |
| **Owner 3 — Library + Drift** | Claims + sources | Gauntlet tenant Claims Library, source docs, Drew corpus indexing |
| **Owner 4 — Generation + demo** | Product/systems | Web app, auth, enrichment, ungoverned generation, compare UI, rehearsal |

**Team of 3:** Owner 4 merges with 1/3; Gate is non-negotiable on critical path.

---

## Part 7 — Risks & mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tom data delayed | No real personalization | Synthetic cohort roster; swap when ready |
| Live LLM fails on stage | Dead air | Pre-cache all pages; live = track toggle only |
| WiFi in venue | Login fails | Offline hotspot; local fallback on laptop |
| Cohort discomfort with edgy copy | Backlash | Label Track A synthetic; opt-out; facilitator script |
| Legal concern on planted violations | Optics | Pre-authored sandbox; never sent externally |
| Gate not ready | Weak close | Show ledger on 3 planted profiles only; honest MVP scope |
| Fabricated data presented as real | Trust hit | UI badge: “Simulated signals”; script distinction A vs B |

---

## Part 8 — Success criteria

### Must ship (MVP demo)

- [ ] ≥90% of cohort gets personalized Track B page via magic link
- [ ] 3 planted edge profiles with ungoverned + governed pair
- [ ] Gate ledger visible on Track B with green/amber/red + source click
- [ ] **Full Provenance stack live:** Claims Library + Gate + Optimizer + Drift + Assurance
- [ ] Optimizer panel: illegal variant grayed; cannot top leaderboard
- [ ] Drift demo: rule change → re-Gate → stale badge in &lt;60s
- [ ] Assurance Lab: ≥20 traps; catch-rate + false-reject on D7
- [ ] Facilitator can explain competitor gap in ≤2 min (Part 0)
- [ ] “Why can't we ship Track A at scale?” lands with audience

### Ambitious

- [ ] Track A edgy pages for full cohort (or volunteer subset)
- [ ] Compare mode works for 2 recipients *(Week 2 P0 if not)*
- [ ] Live Gate on one audience suggestion (pre-scoped claim)
- [ ] Real Meta/Google OAuth enrichment (likely post-capstone)

---

## Part 9 — Differentiation recap (presenter crib sheet)

**Say this:**

1. “Meta and Google personalize better than we ever will inside their walls. Good. We’re not rebuilding Advantage+.”
2. “The gap is when *you* generate specific claims to *named people* on *your* channels — email, website, sales — where wrong = lawsuit.”
3. “Watch Track B — that’s realistic platform data. Still no one verified the stat in your hero line.”
4. “Watch Track A — that’s what happens when you add synthetic inference and remove the guardrails. You felt it.”
5. “Track C is the same person. Same data. Every sentence cited or killed. That’s Provenance.”

---

## Appendix A — Platform signal reference (realistic track)

What Meta / Google / LinkedIn actually expose to advertisers (simulated for demo):

**Meta:** Core demographics, interest categories, custom audiences from pixel events, lookalike %, page engagement.  
**Google:** Affinity, in-market, life events (limited), Customer Match (hashed email), search term themes in PMax asset reports.  
**LinkedIn:** Job title, function, seniority, company, industry, matched audiences, lead gen form fields.

We **do not** need live API integration for Jun 29 — schema-faithful simulation from Gauntlet signup fields is sufficient for Track B credibility.

---

## Appendix B — Links

| Doc | Use |
|-----|-----|
| [MEETING-NOTES-SEGMENTATION-AND-DEMO.md](./MEETING-NOTES-SEGMENTATION-AND-DEMO.md) | Source notes |
| [FULL-FUNNEL-VIEW.html](./FULL-FUNNEL-VIEW.html) | Competitor analysis deck |
| [SHOWCASE-DEMO.html](./SHOWCASE-DEMO.html) | Presenter-mode beats (Helix tenant) |
| [WHY-TECHNICALLY-CHALLENGING.html](./WHY-TECHNICALLY-CHALLENGING.html) | Gate / Optimizer hardness |
| [PROJECT-PLANNING-DOCUMENT.html](./PROJECT-PLANNING-DOCUMENT.html) | Capstone scope + owners |

---

*Update after Tom data review and Phase 0 kickoff.*
