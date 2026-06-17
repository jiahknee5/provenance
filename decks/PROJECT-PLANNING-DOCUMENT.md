Gauntlet Capstone · Deliverable 01 · Project Planning Document

# Provenance

Provable ultra-personalization — outreach that can't say anything it can't prove, and optimizes itself inside the truth.

Plan due Wed Jun 17 · 11:59 PM  ·  Showcase Mon Jun 29 (10-min live)  ·  Team of 3–4  ·  Page 5 of 5

[1 · Marketing promise](BUSINESS-VISION.html) [2 · Before → After → Value](BEFORE-AFTER-VALUE.html) [3 · Solution deep dive](SOLUTION-DEEP-DIVE.html) [4 · Why it's hard](WHY-TECHNICALLY-CHALLENGING.html) 5 · Capstone submission

1

## The problem — and why it's technically hard

Ultra-personalization (a unique, on-target message for every prospect) is the new standard — but it **breaks human review**. You cannot legally read 100,000 unique messages, so in any claims-heavy domain (pharma, fintech, insurance, food/ag) you're forced to choose: ship one *generic-but-reviewed* message, or send *personal-but-unverified* claims and risk an FTC action or lawsuit. The bottleneck isn't generation — it's **verification at scale**.

That is hard for reasons no current tool solves: deciding "is this claim entailed by its source?" with **calibrated confidence and no ground truth at inference**; the default verifier (LLM-as-judge) fails >50% of bias tests and is gameable; an optimizer told to maximize replies **learns to exaggerate** (reward-hacking); and a verified claim goes stale the moment its source changes. "Verification is the new bottleneck" (Karpathy) — and we attack it end-to-end. *(Business case on [page 1](BUSINESS-VISION.html); solution detail on [page 3](SOLUTION-DEEP-DIVE.html); hardness + research on [page 4](WHY-TECHNICALLY-CHALLENGING.html).)*

2

## Project direction

**A — Combine ML with LLM.** A trained **verifier ensemble** (NLI + diverse LLM judges, calibrated) and a **constrained contextual-bandit** policy do what the LLM can't — know what's true and decide what to send — while the LLM does generation. The coupling is load-bearing: delete the ML and you have generic AI slop.

- Also exercises **C (one problem, many ways)**: we benchmark verification methods head-to-head (single-judge vs. NLI vs. ensemble vs. self-consistency vs. hidden-state probe).

- Carries a **B-flavored thesis**: the marketing org runs through one verified pipeline — humans author the rules and approve sends, they don't write copy.

3

## Technical approach — AI as the primitive

The product is a **system of record for claims**: every claim has a tracked life, and AI is the primitive at each stage. Delete the models and there's no product — only a logger.

```
 Claims Library ─► Draft ─► The Gate (verify + clear) ─► The Optimizer ─► Send ─► Drift Monitor
 claim–evidence    grounded    decompose → NLI+ensemble    contextual bandit         audit      source-diff →
 graph + sources    gen          (calibrated) → rules;        over *verified* variants    trail      re-verify
                                 router-referee cascade        (can't reward-hack)
   └──────────── Assurance Lab — adversarial traps + reliability profiling audit The Gate ──────────┘
```

- **The Gate (the core):** atomic-claim decomposition → retrieval evidence-binding → NLI entailment + a calibrated diverse-judge ensemble → compliance rules; cheap-first **router-and-referee cascade**; optional hidden-state probe. *Cited or killed.*

- **The Optimizer:** a contextual bandit over a **constrained action space** = verified+cleared variants; reward = reply/convert, unsubscribe = hard negative; hierarchical priors for cold-start; off-policy eval. **Pruning to verified outputs is a structural fix for reward-hacking.**

- **Drift Monitor & Assurance Lab:** a claim-dependency graph re-verifies on source change; synthetic adversarial traps + reliability profiling (catch-rate, false-reject, ECE, severity) prove the verifier works.

4

## Scope — two weeks

Anchored on a **bundled demo tenant** (fictional regulated B2B — e.g. enterprise SaaS / health-tech) with realistic prospects, source docs, and an MLR hold, so verification has checkable ground truth. Standalone capstone — not tied to any single customer product.

Minimum shippable — must hit

- **The Gate end-to-end** on one channel (email): decompose → bind → NLI + small ensemble → rules → the live **claim ledger** (cited / repaired / blocked).

- **The Assurance Lab MVP**: a synthetic-trap set + the headline metric — catch-rate vs. false-reject + a calibration (reliability) diagram.

- The regulatory gate (block the legal-hold claim on demand) + the adversarial "try to make it lie" demo.

- Funnel program expressed **as data**, so a second tenant is config, not a rebuild.

Ambitious — scored on ambition

- **The truth-bounded Optimizer** on an LLM-persona simulator — show conversion climbing and that it **can't win by lying.**

- **Hidden-state probe** added to the Gate; verifier **bake-off** (judge vs. NLI vs. ensemble) on catch-rate per dollar.

- **Drift Monitor** live (flip the legal hold → claims auto-unblock; change a permit → sends auto-pause).

- Second-tenant transfer; **website channel adapter** (personalized landing page via same Gate); optional live voice.

5

## Why it's compelling — the recruit hook

- **It's the hottest problem in AI, made tangible:** "we built the AI that can't lie in your outbound — and it optimizes itself inside the truth." Sits on the verification/reliability frontier judges are watching.

- **One genuinely novel bet:** *constrained optimization as a structural fix for reward-hacking* — a fresh answer to the problem the whole field is stuck on, not just an application.

- **A bundled demo tenant, not a blank repo** — realistic prospects, sources, and an MLR hold to enforce on day one.

- **It demos like a magic trick** — a claim ledger lighting up green/amber/red, a "try to make it lie" moment, and a learning curve that proves the optimizer can't cheat.

6

## Hard parts / risks — the bet and where it breaks

**The bet:** a calibrated ensemble verifier catches false/unsayable claims at high recall without killing good copy, cheaply enough to run on every message — and a bandit bounded to verified outputs lifts conversion without ever learning to lie.

| Risk | Where it breaks · mitigation |
| --- | --- |
| Verifier reliability (top) | A single LLM-judge is gameable and biased. **Mitigation:** NLI + diverse ensemble + calibration (ECE); prove it in the Assurance Lab, never a bare yes/no. |
| Transfer / calibration | Calibration may decay off the ground-truth domain. **Mitigation:** make the transfer test a first-class deliverable; recalibrate on a small target sample; report honestly. |
| Sparse reward / cold-start | Replies are rare/slow; new segments have no data. **Mitigation:** persona simulator + cheap proxies + hierarchical bandit + off-policy eval. |
| Claim decomposition | A missed claim is unverified. **Mitigation:** measure decomposition coverage; puffery as its own class. |

7

## Who owns what — team of 3–4

Owner 1 — The Gate

verifier ML core

Claim decomposition, evidence-binding, NLI + ensemble, calibration, the router-referee cascade.

Owner 2 — Optimizer + Assurance

RL + eval core

Contextual bandit, off-policy eval, the simulator; adversarial-trap generation + reliability profiling.

Owner 3 — Library + Drift + data

data / infra

Claim–evidence graph, source registry, the live spine, the drift dependency-graph re-verification.

Owner 4 — Generation + demo

systems / product

Per-prospect generation, channel adapters, the claim-ledger UI, and the showcase.

For a team of 3, Owner 4 folds into Owner 1/3 and the demo is shared.

8

## The 10-minute showcase (Jun 29)

**Interactive demo artifact:** [SHOWCASE-DEMO.html](SHOWCASE-DEMO.html) — presenter mode with ←/→ beats, live claim ledger, "try to make it lie," legal-hold flip, Assurance Lab, and Optimizer chart. **This is what we show on stage.**

0:00 · 1 min

**Reframe.** "Ultra-personalization breaks review on every channel — email, web, ads. We automate it. The AI can't say what it can't prove."

1:00 · 3 min

**The Gate + claim ledger (MVP core).** Demo tenant **Helix Analytics** → prospect Maya Chen / Northwind Health → Generate & verify → toggle **Email | Website** (same claims, same ledger) → green/amber/red → click source → **Try to make it lie** → flip **MLR hold** on "47% TCO." *Maps to: Gate · ledger · regulatory gate · adversarial demo · website adapter (showcase).*

4:00 · 3 min

**Assurance Lab (MVP deliverable).** Catch-rate **98.7%** vs LLM-judge **71%** vs NLI-only **84%** on adversarial traps; false-reject **2.1%**; calibration diagram (ECE ±3%). Proof, not a promise. *Maps to: Assurance Lab MVP + verifier bake-off.*

7:00 · 2 min

**Truth-bounded Optimizer (ambitious).** Simulator: reply rate climbs per feedyard segment; leaderboard shows "$/head ROI" winning; **"Guaranteed 50% savings"** grayed out — structurally blocked, can't win by lying. *Maps to: constrained bandit + anti-reward-hacking story.*

9:00 · 1 min

**The ask.** Four owner surfaces (Gate · Optimizer+Assurance · Library+Drift · Generation+Demo). Team of 3–4. Live spine from day one.

**MVP ↔ demo alignment:** Every minimum-shippable bullet from §4 appears on stage — Gate on email, live claim ledger, Assurance Lab headline metrics, regulatory hold + sabotage moment. Optimizer beat covers the ambitious tier; if sim isn't ready, show the blocked-variant leaderboard as the structural "can't lie" proof.

**Companion detail:** [★ showcase demo (Jun 29)](SHOWCASE-DEMO.html) · [page 1 — marketing promise](BUSINESS-VISION.html) · [beyond marketing — other applications](BEYOND-MARKETING.html) · [page 2 — before → after → value](BEFORE-AFTER-VALUE.html) · [page 3 — solution deep dive](SOLUTION-DEEP-DIVE.html) · [page 4 — why each is technically hard](WHY-TECHNICALLY-CHALLENGING.html) · [hub](index.html).

Gauntlet Capstone · Provenance · Project Planning Document · Jun 2026. Illustrative figures are labeled as such; sources on page 2.
