Provenance · Recruit · 1-pager

# Join the Project

We're building the AI that writes personalized sales emails — but **can't say anything it can't prove.**

**One line:** "We built the outbound AI that can't lie — and it optimizes itself inside the truth."

## The problem (plain English)

Companies want to reach people with touchpoints tailored to each one — email, landing pages, ads — *"For your 847-bed system, cut reporting cycle 40%."*

AI can write those messages today. The hard part isn't writing — it's **checking**. If even one email says something wrong, the company can get fined, sued, or lose trust. In pharma, fintech, insurance, and food/ag, **every specific statement is a legal claim.**

Legal teams can't read 100,000 unique emails before they go out. So companies are stuck:

Option A

One safe, generic email to everyone → **boring, low response rates**

Option B

Personalized AI emails → **fast, but risky** if anything is wrong

**Provenance removes that tradeoff.**

## What it is

General ledger

keeps track of money

CRM

keeps track of customers

Provenance

keeps track of **claims**

A **claim** is any specific fact in a message: *"saves $10/head,"* *"egg-allergen-free,"* *"your operation has 4,000 head."* Provenance tracks each claim from the moment it's written to the moment it goes stale — with proof attached.

## What it does

Every outbound message goes through a pipeline before it sends:

1

Draft

AI writes a personalized message, pulling from approved sources (product specs, pricing sheets, public records about the prospect).

2

Verify

The message is split into individual claims. Each is checked against its source: *Does the document actually say this?*

3

Clear

Even true claims can be blocked (legal hold, wrong jurisdiction). Legal sets rules once; every message is checked automatically.

4

Optimize

The system A/B tests which **verified** message works best — and **can't cheat by exaggerating**, because only cleared claims compete.

5

Send

Approved message goes out with a full audit trail: what was said, what source backed it, who cleared it.

6

Monitor

When a source changes, affected claims are re-checked. Stale claims get paused before they send.

7

Prove

The system tests itself with adversarial traps and reports real numbers: catch rate, false-reject rate, calibration.

**The shift:** Legal stops reviewing every email. They approve the **rules and claims library once.** Every generated message is checked instantly, at any volume.

## Why it's interesting

**It's the hottest unsolved problem in AI, made tangible.** AI can generate text at scale. Verification at scale is the bottleneck — and nobody has solved it well.

**Our novel bet:** constrained optimization as a fix for reward-hacking. An optimizer told to maximize replies will learn to exaggerate. We structurally prevent that — false claims never enter the reward loop.

**It demos like a magic trick:** claims light up green/amber/red; you try to make it lie and it blocks you; flip a legal hold and a true claim turns red.

**Live data from day one** — real prospects, real sources, real legal holds — not a toy demo.

## The technology

| Piece | What it is | Why it's hard |
| --- | --- | --- |
| **Claims Library** | Extract atomic claims from docs; bind each to an exact source span | Splitting fluent prose into checkable facts is unsolved |
| **The Gate** | NLI entailment + calibrated judge ensemble + compliance rules | Calibrated verification with no ground truth; LLM-as-judge is gameable |
| **The Optimizer** | Contextual bandit over *verified-only* message variants | Sparse feedback + reward-hacking; our constraint is the structural fix |
| **Drift Monitor** | Claim-dependency graph; re-verify when sources change | Truth is temporal — staleness is an open problem |
| **Assurance Lab** | Adversarial trap generation + reliability profiling | Proving the checker works, not just promising it |

**Stack:** LLM for generation + trained ML for verification and optimization. Delete the ML and you have generic AI slop. Delete the LLM and you have a logger.

**Live domain:** Ag/biotech B2B outreach — but the architecture works for pharma, fintech, insurance, any claims-heavy outbound.

## Who we're looking for (team of 3–4)

Verifier ML

Owner 1

The Gate — claim decomposition, NLI + ensemble, calibration

RL + Eval

Owner 2

The Optimizer + Assurance Lab — bandits, adversarial traps, reliability metrics

Data / Infra

Owner 3

Claims Library + Drift Monitor — claim-evidence graph, source registry, live spine

Systems / Product

Owner 4

Generation + demo — per-prospect drafts, claim-ledger UI, showcase

"We built the marketing AI that can't lie — email, web, and every channel — and it optimizes itself inside the truth."

Gauntlet capstone · 2-week build · Showcase Mon Jun 29 · Plan due Wed Jun 17

Provenance · recruit 1-pager · Jun 2026 · [document hub](index.html) · [full capstone](PROVENANCE-CAPSTONE.html) · [solution detail](PROVENANCE-SOLUTION.html)
