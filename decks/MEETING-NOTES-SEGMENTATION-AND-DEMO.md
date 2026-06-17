# Meeting Notes — Segmentation, ICP & Cohort Demo

**Captured:** Jun 16, 2026  
**Context:** Provenance capstone planning — how we segment, message, and demo to the Gauntlet cohort

---

## Executive summary

Two parallel threads from the meeting:

1. **Go-to-market thinking** — expand beyond basic demographic segmentation: adoption-curve stages, emotional triggers, Maslow hierarchy, decision timing, and a crisp ICP.
2. **Showcase demo concept** — live, per-person personalized website for everyone in the room; side-by-side comparison; deliberate “borderline illegal” examples to show why ungoverned personalization fails at scale → Provenance as the fix.

**Demo audience:** Gauntlet cohort (night school attendees, email lists, online signups). **Data owner to confirm:** Tom.

---

## 1. Segmentation — what else beyond the obvious?

Current thinking is not enough if we only slice by role, company, or industry. Additional segmentation lenses to explore:

| Lens | What it captures | Example use |
|------|------------------|-------------|
| **Innovation adoption curve** | Where they sit on Rogers’ diffusion curve | Message tone, proof depth, risk framing |
| **Emotional trigger profile** | Which motivators move them (fear, ambition, belonging, status) | A/B copy variants |
| **Hierarchy of needs** | Maslow layer they’re optimizing for (survival → self-actualization) | Headline angle, offer type |
| **Decision timing** | Where they are in the buy/join journey *right now* | CTA urgency vs nurture |
| **Regulatory / risk posture** | How conservative they are about claims and compliance | How edgy copy can get |
| **Channel / touchpoint history** | Night school vs email-only vs online signup | Personalization inputs |

### Innovation adoption curve (Rogers)

Map cohort members (and future customers) to:

| Stage | ~Share | Traits | Messaging implication |
|-------|--------|--------|---------------------|
| **Innovators** | ~2.5% | Tolerate broken UX; want novelty | “Be first — shape the primitive” |
| **Early adopters** | ~13.5% | Visionaries; tolerate risk for edge | “Unfair advantage before the market catches up” |
| **Early majority** | ~34% | Pragmatists; need proof from peers | Case studies, Gauntlet social proof, Drew-style examples |
| **Late majority** | ~34% | Skeptics; need standards | “This is how serious teams ship AI” |
| **Laggards** | ~16% | Risk-averse; change only when forced | Not primary ICP for capstone |

**Hypothesis for Gauntlet demo:** Night school attendees skew **early adopter / early majority** — they showed up, they’re investing time, but they still want peer proof and a credible path.

**Action:** Tag each demo recipient with an adoption-curve segment (inferred from attendance depth, signup source, engagement).

---

## 2. A/B test emotional triggers

Test copy variants that differ on **emotional lever**, not just wording:

| Trigger | Example angle for Provenance / Gauntlet |
|---------|----------------------------------------|
| **Fear / loss aversion** | “Your AI outreach is one hallucinated claim from a compliance incident.” |
| **Ambition / status** | “Ship 1:1 at blast scale before anyone else in your vertical.” |
| **Belonging** | “Built with the Gauntlet cohort — you’ve already seen the problem up close.” |
| **Curiosity / novelty** | “What if every sentence had a citation you could click?” |
| **Security / stability** | “Governed generation — the system of record for claims.” |

**Action:** For the cohort demo, pre-assign 2–3 trigger variants per person (within Gate-approved bounds) and show the Optimizer learning which lever works *per micro-segment* — with the explicit caveat that without Provenance, emotional optimization drifts into exaggeration.

Reference copy patterns: **emails from Drew** = good baseline examples of tone that already works with this audience.

---

## 3. Copy — “high-leverage transformation”

Craft messaging around **transformation**, not features:

- **Before:** Personalization OR compliance — pick one.
- **After:** Every touchpoint personalized; every claim proved.
- **Leverage point:** One rule change in the Claims Library updates 100k variants — legal sets policy once, not per asset.

For Gauntlet specifically, transformation frame:

> “You’re building AI products. Provenance is how you ship them without becoming the cautionary tale.”

**Action:** Draft 3 hero variants (transformation / fear / ambition) for the live website demo; Gate clears all before go-live.

---

## 4. Hierarchy of needs (Maslow) — targeting

Layer messaging to the need the recipient is most likely optimizing for:

| Level | Need | Gauntlet-relevant hook |
|-------|------|------------------------|
| **Physiological / safety** | Job security, income stability | “Don’t bet your capstone grade — or your job — on unverified AI copy.” |
| **Safety / stability** | Predictability, auditability | “Every claim traceable. Drift caught before it ships.” |
| **Belonging** | Cohort, community | “Built for builders like you — demo uses *your* Gauntlet profile.” |
| **Esteem** | Mastery, credibility | “Show judges a system that proves it’s hard — and that you solved it.” |
| **Self-actualization** | Building the future | “The trust primitive for the agentic era.” |

**Action:** Infer primary need layer from signup source + role (e.g. career-switchers → safety; founders → esteem/self-actualization).

---

## 5. Decision timing — when are they ready to act?

Separate **who they are** from **when they decide**:

| Signal | Timing inference |
|--------|------------------|
| Night school **attendance** (repeat vs one-off) | Warmer; closer to “early majority” buy-in |
| Recent **online signup** | Top-of-funnel; nurture not hard close |
| **Email engagement** with Drew’s sends | Familiar with Gauntlet voice; lower friction |
| **Capstone deadline proximity** (Jun 17 planning doc, Jun 29 showcase) | Urgency window for “join the team / follow the build” CTA |

**Action:** Add a `decision_timing` field to demo profiles: `exploring` | `evaluating` | `ready_to_commit`.

---

## 6. ICP (Ideal Customer Profile) — draft for capstone

**Primary ICP (demo + wedge):** Regulated B2B marketing / growth teams shipping AI-generated outreach at volume.

**Capstone demo ICP (narrow):** Gauntlet cohort member who:

- Attended ≥1 night school **or** is on active email list
- Building or joining an AI-heavy capstone
- Feels the tension: “I want personalization speed but I can’t verify everything”
- Adoption stage: early adopter → early majority

| Attribute | Ideal | Disqualifier |
|-----------|-------|--------------|
| **Role** | Builder, PM, growth, compliance-adjacent marketer | Pure consumer / no AI in stack |
| **Pain** | Volume × verification bottleneck | Single static landing page only |
| **Data** | Known profile (name, background, attendance) | Anonymous traffic only |
| **Risk tolerance** | Wants edgy demo *in a sandbox* | Would confuse demo violations with product |

**Action:** Finalize ICP one-pager after Tom confirms cohort data fields.

---

## 7. Open question — alpha-gal & protein positioning

**Note from meeting:** “Alpha-gal syndrome — good for the protein?”

**Capture as open research** (likely a segmentation example, not capstone scope):

- **Alpha-gal syndrome:** tick-bite–linked allergy to mammalian meat (alpha-gal epitope).
- **Segment question:** Is this audience a *target* for alternative/plant protein — or a *compliance minefield* (health claims, medical adjacency)?
- **Provenance angle:** Any protein/health marketing to this segment requires strict claim governance (efficacy, “safe for,” cross-reactivity).

**Action:** Park unless team picks a health/nutrition vertical for a second demo tenant. If pursued: treat as high-scrutiny segment; Gate + medical-legal rules mandatory.

---

## 8. Showcase demo concept — live personalized website

### The idea

During the Jun 29 presentation:

1. **Give everyone a URL** (or QR) — they log in.
2. **Each person sees a website personalized to them** — headshot/name, background, night school history, inferred segment, emotional trigger variant.
3. **Side-by-side mode** — pairs or table groups compare: “Why does yours say X and mine say Y?”
4. **2–3 planted profiles** get **edgy / borderline-illegal** copy (exaggerated claims, implied guarantees, missing disclaimers) — *on purpose*, in a controlled sandbox.
5. **Facilitated discussion:**
   - “This felt amazing — and terrifying. Why can’t we ship this tomorrow at scale?”
   - Verification bottleneck, true ≠ allowed, reward-hacking, liability.
6. **Reveal Provenance:** same profiles re-run through Gate → violations flagged → safe variants only → ledger + Assurance Lab.

### Why this demo works

| Beat | Audience feels | Provenance proves |
|------|----------------|-------------------|
| Personalization | “Wow, it knows me” | Channel adapter + claims library |
| Comparison | “Mine is different — unfair?” | Micro-segment + Optimizer (bounded) |
| Edgy examples | “Wait, can they say that?” | Gate + regulatory hold |
| Scale discussion | “We’d never approve 200 of these by hand” | Per-rule governance, not per-document |
| Close | “I want this primitive” | System of record for claims |

### Demo campaign: Gauntlet users

| Input | Source | Use in personalization |
|-------|--------|------------------------|
| Name, email | Email lists | Login + salutation |
| Night school signup | Attendance records | “You were in Week N session on …” |
| Online signup metadata | Gauntlet platform | Role, goals, project interest |
| Drew email corpus | Existing sends | Tone / structure templates |
| Inferred adoption stage | Heuristic from above | Copy depth + CTA |

**Planted edge cases (examples):**

- Profile A: Implied guaranteed job placement / income outcome.
- Profile B: Health-adjacent claim tied to a personal detail scraped from signup.
- Profile C: Competitor disparagement or unverified “#1 in cohort” stat.

All **pre-authored** for demo safety — not live-scraped at showtime without Gate review.

---

## 9. Available data & owners

| Dataset | Status | Owner / next step |
|---------|--------|-------------------|
| Current Gauntlet cohort fields | **TBD** | **Check with Tom** — what’s exportable, PII rules, format |
| Gauntlet email lists | Available (confirm) | Tom |
| Gauntlet online signups | Available (confirm) | Tom |
| Night school signups + **attendance** | Available (confirm) | Tom |
| Drew standard emails | Available — use as copy exemplars | Team |

**Privacy / consent for live demo:** Confirm cohort is OK being personalized on screen; offer opt-out profile or synthetic fallback.

---

## 10. Action items

| # | Action | Owner | Due |
|---|--------|-------|-----|
| 1 | Confirm cohort data export with Tom (fields, PII, attendance join) | — | ASAP |
| 2 | Build demo recipient roster + inferred segments (adoption curve, need layer, timing) | — | Pre-build |
| 3 | Draft 3 emotional-trigger hero variants + 3 “edgy” planted profiles | — | Pre-showcase |
| 4 | Scope live website demo (auth, per-user render, compare view) | — | Align w/ showcase Jun 29 |
| 5 | Pull 2–3 Drew emails as tone references | — | This week |
| 6 | Finalize ICP one-pager after data confirmed | — | Post-Tom |
| 7 | Resolve alpha-gal / protein thread — in or out of scope | — | Team decision |

---

## 11. Links to deck

| Doc | Relevance |
|-----|-----------|
| [COHORT-DEMO-PROJECT-PLAN.md](./COHORT-DEMO-PROJECT-PLAN.md) | **Full build plan** — competitor analysis, dual tracks, Gate architecture, timeline |
| [GAUNTLET-PILOT-DECK.html](./GAUNTLET-PILOT-DECK.html) | **Pilot customer deck** — Prime / Catalyst / hiring partner routing |
| [SHOWCASE-DEMO.html](./SHOWCASE-DEMO.html) | Existing presenter beats — extend with live cohort website |
| [BUSINESS-VISION.html](./BUSINESS-VISION.html) | Personalization promise + website channel |
| [BEYOND-MARKETING.html](./BEYOND-MARKETING.html) | Why Gate transfers outside marketing |
| [PROJECT-PLANNING-DOCUMENT.html](./PROJECT-PLANNING-DOCUMENT.html) | Capstone scope, Jun 29 demo section |

---

*Raw notes distilled from team sync. Update after Tom data review and demo scope lock.*
