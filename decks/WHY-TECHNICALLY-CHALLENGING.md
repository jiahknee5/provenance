Provenance · capstone · page 4 of 5

# Why each capability is technically hard — against the Gauntlet bar and current research

Gauntlet scores on **ambition** — did you attack a genuinely unsolved problem — not polish. For each capability: the **technical crux**, the **Gauntlet fit**, the **research signals** that say it's open, and **the bet / where it breaks.**

[1 · Marketing promise](BUSINESS-VISION.html) [2 · Before → After → Value](BEFORE-AFTER-VALUE.html) [3 · Solution deep dive](SOLUTION-DEEP-DIVE.html) 4 · Why it's hard [5 · Capstone submission](PROJECT-PLANNING-DOCUMENT.html)

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

Citation discipline: arXiv IDs were surfaced in June-2026 research; "STATE-Bench"/"ReliabilityBench" and the S1–S10 codes come from the cohort's deep-research brief rather than independent verification, and are used as that brief's framework. Fittingly, we don't present an unsourced claim as a sourced one.

Provenance · capstone page 4 of 5 · Jun 2026 · [← page 3](SOLUTION-DEEP-DIVE.html) · [page 5 →](PROJECT-PLANNING-DOCUMENT.html) · [hub](index.html).
