# One-Week Plan — Gauntlet Day Demo + Deck Suite

**Sprint:** 7 days · **Audience:** Gauntlet cohort on Gauntlet day  
**North star — the demo:** On Gauntlet day we put a **QR on the slide**. Everyone scans it and opens a website built for *them* — name, night school, signup path, signals that feel uncannily specific. For a moment it’s magic (“How did it know that?”). Then we push it: exaggerated stats, implied guarantees, creepy personal details, borderline-illegal copy on **planted sandbox profiles**. People compare with neighbors — “Why does yours say that?” — and the room asks: *why can’t we ship this to 200 people tomorrow?*

**The reveal:** Same person, same data, through **Provenance** — governed site, Gate ledger (green/amber/red), then the full stack live (Assurance, Optimizer, Drift). The deck tells the funnel; **the live moment is the gut punch and the fix.** Week 2 hardens this into a repeatable pipeline for Jun 29.

**Related:** [Cohort demo project plan](./COHORT-DEMO-PROJECT-PLAN.md) · [Meeting notes](./MEETING-NOTES-SEGMENTATION-AND-DEMO.md) · [Gauntlet pilot deck](./GAUNTLET-PILOT-DECK.html) · [Full funnel view](./FULL-FUNNEL-VIEW.html)

---

## Executive summary

| # | Deliverable | MVP bar | Stretch |
|---|-------------|---------|---------|
| **1** | **Edgy demo site** — creepy / false / borderline-illegal claims | Magic-link per cohort member; 3 planted shock profiles; pre-cached copy | Live LLM gen on stage |
| **2** | **Governed demo site** — personalized, real claims only | Same URLs, Track B data + Gate-cleared copy + ledger inspect | Side-by-side compare mode |
| **3** | **Deck: Marketing landscape** | Big tech + Clay / Insider / etc. | Printed leave-behind |
| **4** | **Deck: Provenance enables this** | Full component stack + live beats | Assurance + Optimizer + Drift demos in show |
| **5** | **Deck: Full funnel + touchpoints** | 5-stage funnel + where each pillar sits | Animated journey |
| **6** | **Deck: How it works** | Gate pipeline diagram + data model | Live API demo |
| **7** | **Deck: Examples** | 1 email + 1 ad + 1 web per track | Full gallery |
| **8** | **Deck: Gauntlet walkthrough** | End-to-end attribution story (simulated pixels) | Real Meta CAPI mock |

**Recommendation:** Treat **one web app with two routes** (`/ungoverned` vs `/provenance`) rather than two separate codebases. Treat **decks 3–8 as one presenter hub** with sections (reuse [FULL-FUNNEL-VIEW.html](./FULL-FUNNEL-VIEW.html) + new slides) — not six independent Keynote files.

---

## Pushback (read this first)

### What we should NOT promise in 7 days

| Ask | Pushback | Recommended alternative |
|-----|----------|------------------------|
| **Capture cohort data from phones on first load** | No stable cross-device ID on first HTTP request; GDPR/consent; WiFi latency in room | **Pre-provision profiles** from Tom’s export; magic link / QR encodes `recipient_id`; optional **self-declare** form (“confirm your night school session”) for 30-sec live moment |
| **Live agent enrichment at page load** | Agent + scrape + LLM on every page view = flaky on stage | **Batch enrichment 48h before** (Python job); show “enriched at” timestamp; facilitator toggles “what the agent found” from cache |
| **Real Meta/Google pixel firing + cross-site attribution** | Needs ad accounts, domains, consent banners, delayed attribution | **Simulated pixel payload** in UI (“Meta CAPI event received”) + **pre-built attribution graph** in walkthrough deck |
| **Actually illegal copy sent to real emails** | Legal/reputational risk | **Sandbox only** — edgy site never sends email; planted profiles labeled; facilitator script |
| **Six full slide decks from scratch** | ~60–80 slides = not build + rehearse in 7 days | **One deck, ~25–35 slides**, sections 3–8; fork existing HTML deck pattern |
| **Tier 4 social scraping at scale** | Hard, ToS-sensitive, Meta Helix dependency uncertain | **Tier 1–2 real** (Gauntlet forms) + **Tier 3–4 simulated** with “representative data” badge |
| **Full Optimizer + Drift live in room** | RL depth is Week 2 hardening | **Week 1:** static/sim leaderboard + one rule-change re-Gate demo (&lt;60s); not full RL training |

### What we SHOULD ship

1. **Visceral dual-track website** — same person, two experiences, one Provenance reveal.  
2. **Credible attribution story** — even if simulated, the *diagram* of ad → pixel → form → email → night school → page is correct.  
3. **Full Provenance stack live** — Claims Library + Gate + Optimizer + Drift + Assurance + web adapter; not slide-only for any pillar.

---

## Provenance components — all Week 1 (must ship)

Every deliverable maps to the capstone spine. **No component is deferred to Week 2 for first delivery.**

```
Claims Library → Draft → The Gate → Optimizer → Send/Render → Drift Monitor
                              ↳ Assurance Lab (audit The Gate)
```

| Component | Demo / show | Decks | Week-1 must |
|-----------|-------------|-------|-------------|
| **Claims Library** | Gauntlet tenant YAML feeds Gate | Deck 4, 6 | ≥10 approved facts + rules; source_id on GREEN |
| **The Gate** | Track B ledger inspect; batch pipeline | Deck 4, 6, 8 | Decompose → bind → rules → ledger |
| **Optimizer** | Live panel: variant leaderboard; illegal arm grayed | Deck 5, 6, SHOWCASE | “Can’t win by lying” beat on D7 |
| **Drift Monitor** | Rule change in YAML → re-Gate → stale badge | Deck 6 | Live demo &lt;60s on one profile |
| **Assurance Lab** | Catch-rate + false-reject panel (≥20 traps) | Deck 4, 6 | Metrics visible on governed site or SHOWCASE |
| **Channel adapters** | Web (both tracks); email/ad in deck §7 | Deck 7, 8 | Gate-aware examples Track A vs B |

---

## Deliverable detail

### 1) Edgy demo website (`Track A — Ungoverned`)

**URL pattern:** `demo.gauntlet.provenance.app/u/{token}` or `/ungoverned/{token}`

**Content goals:**
- Hyper-personalized hero using **real** Gauntlet fields (name, night school, signup source)
- **Tier 3–4 simulated** signals (social follows, “opened Drew email in 90 sec”, Meta interest categories)
- **Violation types to show:**
  - **False claims** — unverified stats (“top 3% of cohort”, “guaranteed capstone placement”)
  - **Creepy** — overly specific inference (“congrats on twins Jimmy & Jessica” on planted profile only)
  - **Borderline illegal** — implied income guarantee, health-adjacent (alpha-gal / Tylenol-style), FTC-style deception
- **No email send** — render only; watermark: “SIMULATED · SANDBOX DEMO”

**3 planted profiles (always available via facilitator menu):**
- **Edge-A:** Job/income guarantee  
- **Edge-B:** Health + personal detail  
- **Edge-C:** Competitor / superlative falsehood  

**Data:** Tom export + synthetic enrichment per [COHORT-DEMO-PROJECT-PLAN.md](./COHORT-DEMO-PROJECT-PLAN.md).

---

### 2) Governed demo website (`Track B — Provenance`)

**URL pattern:** same token → `/provenance/{token}` or toggle on page

**Content goals:**
- Same underlying **Recipient Profile Graph** as Track A
- Copy from **Gate batch** — every sentence cited or removed
- **Inspect mode:** claim ledger, click source, MLR-style rule blocks
- Claims **real** = entailed by Claims Library or marked “opinion/CTA” with disclaimer
- Less creepy — no fabricated family/health; platform segments OK if labeled “inferred segment”

**Side-by-side (stretch):** `/compare?a={token}&b={neighbor}` for “why is yours different?”

---

### 3) Deck section — Marketing landscape

**File:** extend [FULL-FUNNEL-VIEW.html](./FULL-FUNNEL-VIEW.html) or new `MARKETING-LANDSCAPE-DECK.html`

**Slides (~8):**

| Slide | Content |
|-------|---------|
| L1 | Thesis: personalization is **solved**; verification is **not** |
| L2 | **Big tech:** Meta Advantage+, Google PMax, Salesforce Agentforce, Adobe Journey Optimizer |
| L3 | What they optimize (engagement) vs what they don’t (claim-level truth) |
| L4 | **Personalization / GTM AI:** Clay (enrichment + outbound), **Insider** (journey + 1:1 web/email), Iterable, Braze, 6sense |
| L5 | **Discover / “personalization AI”** category — AI-native copy + segment orchestration (position as: generate fast, review manually) |
| L6 | Competitive matrix: verify claims? constrain optimizer? owned-channel B2B? |
| L7 | Three holes (from funnel doc) |
| L8 | “We don’t rebuild Meta — we add the trust layer” |

**Research task (Day 1):** 30-min pass on Clay, Insider, latest “personalization AI” vendors — one bullet each, no deep teardown.

---

### 4) Deck section — Provenance enables this

**Slides (~6):**

| Slide | Content |
|-------|---------|
| P1 | System of record for **claims** (not campaigns) |
| P2 | Differentiator 1: **Provable generation** |
| P3 | Differentiator 2: **Constrained self-optimization** |
| P4 | Component stack diagram (Library → Gate → Optimizer → Drift → Assurance) |
| P5 | True ≠ allowed (compliance rules DSL) |
| P6 | Gauntlet as pilot customer (talent routing) — link [GAUNTLET-PILOT-DECK.html](./GAUNTLET-PILOT-DECK.html) |

---

### 5) Deck section — Full funnel + touchpoints

**Slides (~7):**

| Slide | Content |
|-------|---------|
| F1 | Five stages: Awareness → Consideration → Intent → Conversion → Retention |
| F2 | Big tech owns paid top; **we own verifiable owned-channel middle/bottom** |
| F3 | Touchpoint map: X/IG ads, landing page, form, email, night school, retargeting |
| F4 | Where **Claims Library** sits (source docs, CRM, program rules) |
| F5 | Where **Gate** sits (pre-send / pre-render) |
| F6 | Where **Optimizer** sits (variant selection among cleared claims) |
| F7 | Where **Drift** sits (criteria change → re-verify) |

Reuse funnel diagram from [SOLUTION-MASTER-SLIDE.html](./SOLUTION-MASTER-SLIDE.html).

---

### 6) Deck section — How it works

**Slides (~8):**

| Slide | Content |
|-------|---------|
| H1 | Recipient Profile Graph (attributes + significance labels) |
| H2 | Ingest: forms, pixels (simulated), email events, attendance |
| H3 | Generation: LLM + labeled attributes (not mail-merge templates) |
| H4 | Gate pipeline: decompose → retrieve → NLI → rules → ledger |
| H5 | Render: website channel adapter |
| H6 | Optimizer: bandit over verified arms only |
| H7 | Drift: dependency graph + re-Gate |
| H8 | Assurance Lab: catch-rate / false-reject |

---

### 7) Deck section — Examples gallery

**Slides (~6) — static mocks OK:**

| Asset | Track A (ungoverned) | Track B (governed) |
|-------|----------------------|---------------------|
| **Email** | “Hey {name}, director at {co}, Austin weather…” + false stat | Same context; claims cited; blocked line struck through |
| **Ad** | IG-style card: emotional trigger, exaggerated promise | Same card; disclaimer + sourced claim |
| **Website** | Screenshot from edgy demo | Screenshot from governed demo + ledger |

Include **tier legend:** T1 identity · T2 firmographic · T3 behavioral · T4 social (simulated).

---

### 8) Deck section — Gauntlet walkthrough (attribution story)

**Slides (~10) + live handoff to websites:**

```
[X / Instagram ad]  →  click  →  [Landing + Meta Pixel + GA4 events]
        ↓
[Form: name, role, goals, night school interest]  →  CRM row
        ↓
[Drew email drip] + [YouTube night school attendance]  →  events in profile
        ↓
[Agent enrichment batch]  →  tier 2–4 attributes (some simulated)
        ↓
[Ungoverned web]  😱   vs   [Provenance web]  ✅
```

| Slide | Content |
|-------|---------|
| W1 | “Meet Alex” — persona card |
| W2 | Ad on X/IG (mock creative) |
| W3 | Landing page + **pixel events** (PageView, Lead — simulated JSON) |
| W4 | Form fields → attribute map |
| W5 | Email touch + open event |
| W6 | Night school attendance row |
| W7 | Enrichment agent output (batch, not live) |
| W8 | **Live:** QR → edgy site |
| W9 | **Live:** toggle → governed site + ledger |
| W10 | “This is why Provenance” |

**Pixel simulation (recommended):**  
UI panel “Attribution debugger” showing fake `_fbp`, `_ga`, `utm_*`, `night_school_session_id` — educates without real ad account setup.

---

## Data model (both websites)

**Recipient Profile Graph** — one JSON row per cohort member:

```yaml
identity: { name, email_token }
gauntlet_t1: { signup_source, role, company, location, night_school_sessions[] }
email_events: { drew_opens, last_subject }
pixels_simulated: { meta_interests[], google_in_market[], utm_campaign }
enrichment_t3_t4: { simulated: true, social_signals[], behavioral[] }  # labeled
segmentation: { adoption_curve, emotional_trigger, maslow_layer }
demo_flags: { planted_edge_case?, show_creepy_t4 }
```

**Attribute significance labels** (for LLM prompts — from transcript):

> “night_school: attended Jun 5 Agents session — means warm lead, reference in hero”

---

## 7-day schedule

Assume **Gauntlet day = end of Day 7**. Adjust dates to your actual event.

### Day 1 — Lock scope + data + deck skeleton

| Owner | Task | Out |
|-------|------|-----|
| PM | Confirm Gauntlet day date; Tom data request; consent email to cohort | `cohort_raw.csv` spec |
| PM | Cut scope doc signed (this plan + pushback) | No live scrape on stage |
| Design | Deck hub scaffold (HTML presenter, 8 sections) | `GAUNTLET-DAY-DECK.html` shell |
| Content | Competitive research: Clay, Insider, big tech bullets | Slide copy L1–L8 |
| Eng | RPG schema + import script stub | `recipients.jsonl` × 5 samples |

**Exit criteria:** Data schema frozen; deck file exists with section nav; 5 test profiles.

---

### Day 2 — Data + Claims Library + Assurance traps

| Owner | Task | Out |
|-------|------|-----|
| Data | Tom export → clean → pseudo emails if needed | Full roster |
| Data | Realistic Meta/Google/LinkedIn blocks (rule-based) | `platform_*` populated |
| Data | 3 planted edge profiles + 10 synthetic “creepy” extras | `planted/` JSON |
| Eng | Gauntlet tenant Claims Library YAML | Approved facts + rules |
| Gate | Assurance trap set draft (≥20 adversarial claims) | `traps/gauntlet.yaml` |
| Content | Attribute significance doc for top 15 fields | Prompt labels |

**Exit criteria:** Every cohort member has RPG row; Library + traps ready.

---

### Day 3 — Ungoverned site + Assurance eval (Deliverable 1)

| Owner | Task | Out |
|-------|------|-----|
| Eng | Next.js app: magic link auth, `/u/{token}` | Deployed staging |
| Eng | Batch gen Track A copy (LLM + cache) | `pages/ungoverned/` |
| Eng | Assurance eval script v0 → catch-rate / false-reject | Console or JSON |
| Eng | Landing template: hero, proof blocks, “data we used” panel | Edgy but branded |
| Content | 3 planted copy sets (false / creepy / illegal-adjacent) | Facilitator script |
| QA | Mobile check (cohort on phones) | Screenshots |

**Exit criteria:** 10 test tokens load edgy pages < 2s; trap metrics run.

---

### Day 4 — Gate + Optimizer (Deliverables 2 + Optimizer)

| Owner | Task | Out |
|-------|------|-----|
| Eng | Gate batch: decompose → rules → ledger JSON | `pages/provenance/` |
| Eng | `/provenance/{token}` + inspect overlay | Green/amber/red UI |
| Eng | Optimizer panel: leaderboard + grayed illegal variant | SHOWCASE or sidebar |
| Eng | Toggle or second URL between tracks | A ↔ B switch |
| Eng | Blocked claims visible (strikethrough on Edge profiles) | Demo clarity |
| Content | Track B copy review — no fabricated health | Legal-safe |

**Exit criteria:** Same token both tracks; Optimizer shows excluded lie; ledger clickable.

---

### Day 5 — Drift + Decks 3–6

| Owner | Task | Out |
|-------|------|-----|
| Eng | Drift: rule-change script + stale badge UI | One profile demo <60s |
| Eng | Assurance panel wired to governed site | Catch-rate visible |
| Content | Slides L + P + F + H (sections 3–6) | ~29 slides drafted |
| Design | Diagrams: funnel, pipeline, full stack | In deck HTML |
| Eng | Embed screenshots from staging sites | Placeholders OK |
| PM | Rehearse full Provenance stack talk track | Script v1 |

**Exit criteria:** Drift demo works; Assurance on screen; sections 3–6 runnable.

---

### Day 6 — Decks 7–8 + full Provenance rehearsal

| Owner | Task | Out |
|-------|------|-----|
| Content | Example gallery slides (email/ad/web Gate-aware) | Section 7 |
| Content | Walkthrough slides W1–W10 | Section 8 |
| Eng | “Attribution debugger” panel on site (simulated pixels) | UI component |
| Eng | Batch all cohort pages (both tracks) | No live LLM on day 7 |
| All | Full run: deck → QR → edgy → governed → Assurance → Optimizer → Drift | Timed 15 min |

**Exit criteria:** End-to-end rehearsal under 20 min; all Provenance components demoed.

---

### Day 7 — Gauntlet day

| Time | Activity |
|------|----------|
| T-60 | Staging smoke test; hotspot backup |
| T-30 | QR on slide; facilitator login for planted profiles |
| **Show** | Landscape → walkthrough → QR edgy → governed → **Assurance + Optimizer + Drift** → Q&A |
| Post | Capture issues; start [Week 2 codify + reach](./WEEK-2-CODIFY-AND-REACH.md) |

---

## Team split (suggested)

| Surface | Owns |
|---------|------|
| **Gate + Optimizer + Assurance + Drift** | Verifier / rules / batch / panels |
| **Web app + enrichment batch** | Full-stack + data import |
| **Decks + copy + examples** | PM + design |
| **Rehearsal + facilitator** | Whoever presents |

Team of 3: merge web + data; **Provenance stack (Gate through Assurance) is critical path D2–D5**.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tom data late | Medium | High | Synthetic roster; swap day 6 |
| Cohort PII backlash | Medium | High | Opt-out; simulated badge; no real emails sent |
| WiFi failure | Medium | High | Hotspot; pre-cache; facilitator local laptop |
| Gate not ready day 4 | Medium | High | Governed site shows **rules-only** ledger; honest MVP |
| Scope creep (live agents) | High | High | **Pushback table** — batch only |
| “Illegal” copy optics | Low | High | Sandbox watermark; planted only; script |
| Six decks unfinished | High | Medium | **One hub deck** with sections |
| Phone “first load capture” fails | High | Medium | Magic link = pre-identified; optional confirm form |

---

## Additional scope (from prior meetings) — reach goals

*Week 2 = codify + UX reach only — **not** first delivery of Provenance components. Full schedule: [WEEK-2-CODIFY-AND-REACH.md](./WEEK-2-CODIFY-AND-REACH.md)*

| Reach goal | Week 2 priority |
|------------|-----------------|
| Compare mode, segmentation live, attribution v2, live email/ad generation | **P0** |
| Assurance CI hardening, Drift batch re-Gate all cohort, Drew corpus | **P1** |
| Real pixels, live scrape, email send, second tenant, Prime/Catalyst routing | **P2** / Jun 29 |

---

## Success criteria (Gauntlet day)

### Must ship
- [ ] Cohort opens **edgy site** on phone — recognizes self + one “how did they know that?” moment  
- [ ] Same person opens **governed site** — claims cited or blocked; ledger visible  
- [ ] Presenter runs **landscape + Provenance + walkthrough** from one deck (≥20 slides)  
- [ ] **Attribution story** clear: ad → pixel → form → email → night school → page  
- [ ] **Full Provenance stack live** — Claims Library + Gate + Optimizer + Drift + Assurance (not slide-only)  
- [ ] **Optimizer** — illegal variant grayed; cannot top leaderboard  
- [ ] **Drift** — rule change → stale → re-Gate demo in &lt;60s  
- [ ] **Assurance** — ≥20 traps; catch-rate + false-reject visible on D7  
- [ ] Planted **false / creepy / borderline** examples facilitated safely  

### Should ship
- [ ] Example gallery (email + ad + web Gate-aware)  
- [ ] Simulated pixel debugger panel  
- [ ] Compare two cohort members *(Week 2 P0 if not)*  

### Won't ship (week 1)
- Live phone fingerprinting / passive capture  
- Real-time agent enrichment  
- Real cross-platform ad attribution  
- Email actually sent to cohort  

---

## File deliverables checklist

| Artifact | Path (proposed) |
|----------|-----------------|
| This plan | `docs/ONE-WEEK-GAUNTLET-PLAN.md` |
| Presenter hub deck | `docs/GAUNTLET-DAY-DECK.html` *(to build Day 1)* |
| Edgy + governed web | `demo/cohort-web/` |
| Recipient data | `demo/data/recipients.jsonl` |
| Claims + rules | `demo/rules/gauntlet_tenant.yaml` |
| Facilitator script | `docs/GAUNTLET-DAY-RUNBOOK.md` *(Day 6)* |
| QA screenshots | `.qa/gauntlet-day/` |

---

## Recommended narrative (15 min)

1. **Landscape (2 min)** — Meta/Google/Clay/Insider personalize; none verify claims.  
2. **Funnel (2 min)** — Every touchpoint adds attributes; pixels + forms + email + night school.  
3. **Live edgy site (3 min)** — QR; shock; planted illegal/false moment.  
4. **Provenance (3 min)** — Same data; Gate; ledger; real claims only.  
5. **How it works (2 min)** — Library → Gate → Optimizer → Drift → Assurance.  
6. **Ask (1 min)** — Join the build; capstone Jun 29 alignment.

---

*Update daily during sprint. Week 2: [codify + reach goals](./WEEK-2-CODIFY-AND-REACH.md). First action: confirm Gauntlet day date + Tom data SLA.*
