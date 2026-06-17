Provenance Capstone ProjectAppendix A · Before→AfterAppendix B · Why it's hard

Gauntlet Capstone · Deliverable 01 · Project Planning Document

# Provenance

Provable ultra-personalization — outreach that can't say anything it can't prove, and optimizes itself inside the truth.

Plan due Wed Jun 17 · 11:59 PM  ·  Showcase Mon Jun 29 (10-min live)  ·  Team of 3–4  ·  Appendices: A — before/after · B — why it's hard

1

## The problem — and why it's technically hard

Ultra-personalization (a unique, on-target message for every prospect) is the new standard — but it **breaks human review**. You cannot legally read 100,000 unique messages, so in any claims-heavy domain (pharma, fintech, insurance, food/ag) you're forced to choose: ship one *generic-but-reviewed* message, or send *personal-but-unverified* claims and risk an FTC action or lawsuit. The bottleneck isn't generation — it's **verification at scale**.

That is hard for reasons no current tool solves: deciding "is this claim entailed by its source?" with **calibrated confidence and no ground truth at inference**; the default verifier (LLM-as-judge) fails >50% of bias tests and is gameable; an optimizer told to maximize replies **learns to exaggerate** (reward-hacking); and a verified claim goes stale the moment its source changes. "Verification is the new bottleneck" (Karpathy) — and we attack it end-to-end. *(Full per-capability hardness + research in Appendix B.)*

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

Anchored on a live data spine (a real ag/biotech B2B pipeline with real prospects, real sources, and a real legal hold) so verification has genuine, checkable ground truth.

Minimum shippable — must hit

- **The Gate end-to-end** on one channel (email): decompose → bind → NLI + small ensemble → rules → the live **claim ledger** (cited / repaired / blocked).

- **The Assurance Lab MVP**: a synthetic-trap set + the headline metric — catch-rate vs. false-reject + a calibration (reliability) diagram.

- The regulatory gate (block the legal-hold claim on demand) + the adversarial "try to make it lie" demo.

- Funnel program expressed **as data**, so a second tenant is config, not a rebuild.

Ambitious — scored on ambition

- **The truth-bounded Optimizer** on an LLM-persona simulator — show conversion climbing and that it **can't win by lying.**

- **Hidden-state probe** added to the Gate; verifier **bake-off** (judge vs. NLI vs. ensemble) on catch-rate per dollar.

- **Drift Monitor** live (flip the legal hold → claims auto-unblock; change a permit → sends auto-pause).

- Second-tenant transfer; optional multi-channel / live voice.

5

## Why it's compelling — the recruit hook

- **It's the hottest problem in AI, made tangible:** "we built the AI that can't lie in your outbound — and it optimizes itself inside the truth." Sits on the verification/reliability frontier judges are watching.

- **One genuinely novel bet:** *constrained optimization as a structural fix for reward-hacking* — a fresh answer to the problem the whole field is stuck on, not just an application.

- **A live spine, not a blank repo** — real data, real sources, a real legal hold to enforce on day one.

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

0:00 · 1 min

The reframe — "ultra-personalization breaks review; we automate it. The AI can't say what it can't prove."

1:00 · 3 min

The claim ledger, live — generate a per-prospect message; claims light up **green/amber/red**; click a green one for its source; **try to make it lie** → blocked; flip the legal hold → a true claim turns red.

4:00 · 3 min

The Assurance Lab — catch-rate vs. false-reject vs. a single LLM-judge baseline; the reliability/calibration diagram. Proof, not a promise.

7:00 · 2 min

The truth-bounded Optimizer on the simulator — conversion climbs per segment, and the "win by lying" path is structurally closed.

9:00 · 1 min

The ask — four surfaces, come build the outbound AI that can't lie.

Appendix A

## Before → Solution → After → Value

Per capability: what happens without it, exactly what the solution is (deep tech + ⚡ breakthrough), what happens with it, and the value added.

↑ back to the capstone project

**Running scenario:** a regulated business (fintech, pharma, supplements, insurance, or our live ag/biotech domain) runs an outbound campaign to ~10,000–100,000 prospects, where every message makes specific factual claims and a wrong one is a fine, not a typo.

✕ Before — without it

🛠 The solution

✓ After — with it

＄ Value added

The campaign overall the big picture

BeforeWeeks to launch through legal review; you ship **one generic compliant email**; constant fear of a bad claim; no audit trail if challenged.

The solutionThe **Provenance engine**: a claim *system of record* wrapping a closed loop — a calibrated **learned verifier** gates a **constrained optimizer**, with continuous re-grounding.⚡ **Breakthrough:** couples grounded generation + calibrated verification + constrained RL in one loop — it optimizes for conversion *inside* a hard truth boundary.

AfterLaunch **same day**; ship **100,000 personalized, pre-verified** messages; the funnel self-optimizes; a full audit trail accrues automatically.

Value added**Faster, bigger, and safer at once** — the old trade-off between "personalized" and "compliant" disappears.

1 · Claims Library system of record

Before"What are we allowed to say?" lives in scattered decks and a rep's memory. A rep reuses a claim you **retired six months ago** in a live email — now inaccurate, now a compliance incident.

The solution**Atomic-claim extraction** + normalization into a **claim–evidence graph**: each claim node bound to a source span via retrieval, versioned with provenance; generation and reps draw **only** from it.⚡ **Breakthrough:** a structured, queryable claim/evidence substrate instead of flat RAG chunks — structure-aware reading over messy docs, where decomposing fluent text into checkable claims is itself an open problem.

AfterOne approved, current library. The retired claim **isn't selectable**. Every rep and every AI draft pulls from the same verified, in-date set.

Value addedA single source of truth → fewer incidents and **approve-once-reuse-everywhere** (kills duplicate review). The library becomes a compounding asset.

2 · The Gate — verify + clear the bottleneck remover

BeforeLegal/MLR reads **every asset** — 2–4 weeks per campaign. Under deadline, a team ships **"clinically proven"** with no study behind it → FTC complaint, takedown, brand hit.

The solutionDecompose draft → retrieval **evidence-binding** → **NLI entailment** + a diverse-family **judge ensemble**, calibrated (isotonic; report **ECE**) → compliance-rule engine; **router-and-referee cascade** (cheap NLI first, escalate the uncertain); optional **hidden-state probe** on intermediate activations to pre-flag likely-wrong generations.⚡ **Breakthrough:** replaces the unreliable single LLM-judge (>50% bias-test failure) with calibrated-ensemble **selective prediction** — verification that holds under adversarial, reward-hacking pressure. "Verification is the bottleneck."

AfterEvery message auto-checked in **seconds**. "Clinically proven" with no source is **blocked or rewritten before send**; each surviving claim carries its citation. Legal set the rules **once**.

Value addedReview **weeks → seconds**; **~0 unsubstantiated claims** shipped; 1:1 personalization at scale becomes legally possible at all.

3 · The Optimizer — truth-bounded A/B revenue engine

BeforeOne generic email to the whole list — or a manual A/B that takes weeks to reach significance and tests one thing at a time. Conversion stays flat.

The solution**Contextual bandit** (Thompson / LinUCB) over a **constrained action space** = verified + cleared variants; reward = reply/convert, unsubscribe = hard negative; **hierarchical priors** for cold-start segments; **off-policy evaluation** (doubly-robust) on logged sends; **anytime-valid confidence sequences** for adaptive tests.⚡ **Breakthrough:** pruning the action space to verified outputs is a **structural fix for reward-hacking** — the policy *cannot* converge to a higher-reward falsehood, because falsehoods never enter the reward loop. Constrained optimization as anti-Goodhart.

AfterEach micro-segment **auto-converges to its best verified message** — "$/head ROI" wins for feedlots, "peer-hospital reference" for procurement — and only true variants ever compete.

Value added**Continuous conversion lift** per segment, with **zero added liability** — the upside of aggressive optimization without the downside.

4 · Drift Monitor keeps claims true over time

BeforeA legal hold lifts but nobody re-checks 100k live messages → a now-**allowed** claim sits unused for months (lost revenue). Or a permit changes and you keep sending a now-**false** claim (liability).

The solutionA **claim-dependency graph** (claim → source-version) + change-data-capture on sources; a source diff **propagates invalidation** along the graph and triggers **targeted re-verification** of only the affected claims, then auto-pauses / unblocks live sends.⚡ **Breakthrough:** treats truth as a *temporal* property — continuous re-grounding / state-drift detection (the under-measured "memory goes stale" problem). Incremental cache-invalidation, for truth.

AfterClaims **auto-re-verify** when a source changes: the cleared claim **unblocks everywhere instantly**; the stale one is **paused** before it sends.

Value added**Capitalize cleared claims immediately** (revenue) **+ avoid stale-claim liability** (risk) — with no manual re-audit of the corpus.

5 · Assurance Lab proof the checker works

Before"Trust us, the AI checks the claims" — but **no proof**. A risk committee or enterprise buyer stalls the deal for months waiting for evidence that never comes.

The solutionA **synthetic adversarial-trap generator** (mutates verified claims: number-drift, unsupported superlatives, false equivalence, true-but-unsayable) → a held-out adversarial set; **reliability profiling**: catch-rate at fixed false-reject, **paraphrase robustness**, calibration (**ECE** / reliability diagrams), severity-weighted error buckets.⚡ **Breakthrough:** decomposed reliability (not one pass-rate) + **adversarially testing your own verifier** — the direct answer to benchmark-gaming and "average success hides failures." A wind tunnel for the checker.

AfterAn audited dashboard — **"98.7% catch-rate, 2.1% false-reject, calibrated ±3%"** — from continuously running adversarial traps. You put a number in front of legal, the board, and procurement.

Value addedTurns trust into a **metric** → clears risk committees and **shortens enterprise sales cycles** (assurance is itself a revenue lever).

The bottom line, in four columns

**Before:** slow, generic, anxious — personalization traded for safety.  **The solution:** a claim system-of-record + a verify → optimize → monitor → assure pipeline in front of every send.  **After:** instant, 1:1, provable.  **Value added:** risk down, personalization unlocked, revenue up — the three numbers every stakeholder is paid to move.

Appendix B

## Why each capability is technically hard

Against the Gauntlet bar and current research — the technical crux, the Gauntlet fit, the S1–S10 research signals, and the bet / where it breaks.

↑ back to the capstone project

### How Gauntlet scores — and our read

The brief's six criteria: **the problem** (and why it's technically hard — *ambition is the criterion*), **project direction**, **technical approach** (AI as a primitive, not a bolt-on), **scope** (ambitious vs. minimum shippable in two weeks), **why it's compelling**, and **hard parts / risks**.

**Our direction: A — Combine ML with LLM.** A trained verifier ensemble + a constrained contextual-bandit policy do what the LLM can't (know what's true, decide what to send); the LLM does generation. It also exercises **C** (we compare verification methods head-to-head) and carries a **B**-flavored thesis (the org runs through one verified pipeline; humans set rules, not write copy).

## Capability by capability

CAPABILITY 1Claims Library — claim–evidence extractionemerging

The technical crux

Extracting **atomic, checkable claims** from fluent marketing prose (compound claims, implicature, puffery vs. fact) and binding each to the exact source span is unsolved at fidelity — and flat RAG chunking destroys the document structure you need to do it.

Gauntlet fit

Technical ambition in knowledge extraction; **AI-as-primitive** — the claim/evidence substrate is model-extracted, not hand-built. (Direction A.)

Research says it's open

Retrieval and generation interact in ways no one has closed; structure-aware reading beats flat chunks, and GraphRAG often underperforms vanilla RAG.

S5 · RAG still failsS3 · long context

DeepRead (structure-aware "locate-then-read") · Anthropic Contextual Retrieval · EMNLP 2025 "Context Length Alone Hurts… Despite Perfect Retrieval."

The bet · where it breaks

A missed or mis-split claim is an **unverified** claim. Mitigation: measure decomposition coverage explicitly; handle puffery as its own class. Breaks if implicature evades extraction.

CAPABILITY 2The Gate — calibrated ensemble verificationfrontier

The technical crux

Decide "is this claim entailed by its source?" with **calibrated confidence and no ground truth at inference**. The obvious tool — LLM-as-judge — fails >50% of bias tests and is gameable; calibration decays under distribution shift; and the generator is an adversary that wants to embellish. This is the single hottest problem in applied AI: *"verification is the bottleneck."*

Gauntlet fit

Highest technical ambition; the purest **AI-as-primitive** (delete the verifier and there is no product); Direction A, with a C-style method comparison built in.

Research says it's open

Quality/reliability is the #1 production blocker; evals lag observability; benchmarks get gamed; the default scalable verifier (LLM-judge) is unreliable.

S1 · reliability bottleneckS2 · benchmarks gamedS10 · feedback / judge messy

Karpathy (Sequoia Ascent 2026) · LLM-judge bias [2604.16790](https://arxiv.org/html/2604.16790v1) · RLVR reward-hacking [2604.15149](https://arxiv.org/abs/2604.15149) · calibration-under-shift [2603.04445](https://arxiv.org/html/2603.04445v2) · hidden-state probes [2605.24919](https://arxiv.org/html/2605.24919).

The bet · where it breaks

The verifier is load-bearing: false-negatives ship lies, false-positives kill good copy. Mitigation: NLI + diverse ensemble + calibration, proven by the Assurance Lab. Breaks if calibration won't transfer off the ground-truth domain.

CAPABILITY 3The Optimizer — truth-bounded contextual banditfrontier · most novel

The technical crux

Sequential decisions under **sparse, delayed, expensive, irreversible** feedback (replies are rare, slow, and each send costs a lead); off-policy learning on tiny logged data; per-micro-segment cold-start; **and** the optimizer is intrinsically prone to reward-hacking — optimizing engagement teaches it to exaggerate.

Gauntlet fit

Deep technical ambition (RL/bandits under constraints); **AI-as-primitive** (a learned policy steers the LLM at runtime); Direction A. **The original contribution:** bounding the action space to *verified* outputs is a structural fix for reward-hacking.

Research says it's open

Learned routing/policies are becoming standard but tool/sequence choice is "the missing policy"; reward-hacking is an active, unsolved failure mode.

S9 · multi-model routingS2 · reward hackingS1 · reliability

Contextual bandits for multi-turn [2602.03806](https://arxiv.org/pdf/2602.03806) · RouteLLM · process reward models [2504.16828](https://arxiv.org/pdf/2504.16828) · RLVR reward-hacking [2604.15149](https://arxiv.org/abs/2604.15149).

The bet · where it breaks

Sparse/delayed reward + cold-start. Mitigation: persona simulator + hierarchical bandit + off-policy eval. Breaks on sim-to-real gap or negative transfer — but the **constrained-optimization-can't-lie** claim holds regardless, and is the boldest, most defensible novelty.

CAPABILITY 4Drift Monitor — temporal re-groundingfrontier

The technical crux

A verified claim is only true *until its source changes*. Detecting which of N live claims a source change invalidates — and re-verifying only those — is a state/dependency problem. Most "memory" work tests retrieval, not whether state stays **correct** over time; staleness is the named hard problem.

Gauntlet fit

Technical ambition in **state management** — explicitly where the brief's research says teams get stuck; AI-as-primitive (re-verification is model-driven). Direction A, governance-flavored (B).

Research says it's open

Memory and state are under-measured and under-governed; long-running agents need artifacts and re-grounding, not bigger windows; enterprises flag visibility/audit gaps.

S4 · memory/stateS8 · enterprise governance

Anthropic long-running agents · mem0 *State of AI Agent Memory 2026* · STATE-Bench (named in the cohort research doc — directional).

The bet · where it breaks

Dependency-graph completeness: miss a dependency and a stale claim ships. Mitigation: conservative invalidation. Breaks toward over-invalidation (too many re-checks) or under (staleness slips through).

CAPABILITY 5Assurance Lab — adversarial self-test + reliability profilingfrontier

The technical crux

Proving a verifier works requires **adversarially attacking your own checker** and reporting **decomposed reliability** — catch-rate at fixed false-reject, paraphrase robustness, calibration (ECE), severity buckets — because a single pass-rate hides failures and can be gamed.

Gauntlet fit

The research calls evaluation infrastructure the most timely capstone area; high ambition + the strongest **evaluation story**; AI-as-primitive (synthetic adversarial generation + profiling). Direction C + A.

Research says it's open

Reliability must be decomposed beyond average success; benchmarks are gamed so you must adversarially test; synthetic-data verification is what prevents collapse.

S1 · decompose reliabilityS2 · benchmark integrityS10 · synthetic verification

Berkeley RDI (broke 8 top agent benchmarks) · agent-reliability research line · "Mixture of LLMs in the loop" weak supervision.

The bet · where it breaks

Synthetic traps may not represent real failures (sim-to-real for the eval itself). Mitigation: diverse mutation operators + a real held-out slice. Breaks if a verifier passes traps but misses real lies.

## The research signals (S1–S10), decoded

From the deep-research brief — the current ecosystem signals each capability is anchored to.

S1 — **Reliability is the production bottleneck.** Quality is the top blocker; observability is universal, evals lag.

S2 — **Benchmarks are distrusted / gameable.** Top agent benchmarks exploited; RLVR reward-hacking.

S3 — **Long context isn't solved.** Degrades even with perfect retrieval.

S4 — **Memory & state under-measured/governed.** Staleness is the open problem.

S5 — **RAG still fails.** Flat chunks lose structure; GraphRAG often underperforms.

S8 — **Enterprise = fleet/governance problem.** Audit, identity, oversight gaps.

S9 — **Multi-model routing is standard.** Learned routing/cascades (RouteLLM).

S10 — **Feedback / labels / synthetic verification are messy.** Naive LLM labeling is noisy; external verification prevents collapse.

Where the ambition concentrates

The frontier weight sits in **The Gate (verification), The Optimizer (truth-bounded RL), and the Assurance Lab (reliability proof)** — the hottest current cluster. The single most original bet is **constrained optimization as a structural fix for reward-hacking**: the policy can't converge to a higher-reward falsehood because falsehoods never enter the reward loop. That's the line that scores on ambition.

Citation discipline: arXiv IDs were surfaced in June-2026 research; "STATE-Bench"/"ReliabilityBench" and the S1–S10 codes come from the cohort's deep-research brief rather than independent verification, and are used as that brief's framework. Illustrative figures (catch-rates, timeframes) are labeled as such. Fittingly, we don't present an unsourced claim as a sourced one.

Provenance · Gauntlet Capstone · Project Planning Document + Appendices A & B · Jun 2026 · [hub](index.html)
