**2-page submission**  ·  ⌘P → Save as PDF (Letter) prints exactly 2 pages

Gauntlet Capstone · Project Planning Document

# Provenance — provable ultra-personalization

Outreach that can't say anything it can't prove, and optimizes itself inside the truth.

**Direction A (ML + LLM)** · Team 3–4 · Plan due Wed Jun 17 11:59 PM · Showcase Mon Jun 29 (10-min live)

## 1 · The problem — and why it's technically hard

Ultra-personalization (a unique message per prospect) **breaks human review** — you can't legally read 100,000 unique messages — so claims-heavy businesses (pharma, fintech, insurance, ag) must choose *generic-but-reviewed* or *personal-but-unverified-and-risky*. The bottleneck is **verification at scale**, and it's genuinely hard: judging "is this claim entailed by its source?" with **calibrated confidence and no ground truth at inference**; the default verifier (LLM-as-judge) fails >50% of bias tests and is gameable; an engagement-optimizer **learns to exaggerate** (reward-hacking); and a verified claim goes stale the moment its source changes. "Verification is the new bottleneck." *(Per-capability hardness + research: page 2.)*

## 2 · Project direction — A (ML + LLM)

A calibrated **verifier ensemble** (NLI + diverse LLM judges) and a **constrained contextual-bandit** policy decide what's true and what to send; the LLM generates. Delete the ML and it's generic slop. Also runs a **C**-style verifier bake-off and carries a **B** thesis (the org runs through one verified pipeline — humans set rules, not write copy).

## 3 · Technical approach — AI as the primitive

A **system of record for claims**; AI drives every stage (delete the models and there's only a logger):

```
 **Claims Library** → Draft → **The Gate** (verify+clear) → **The Optimizer** → Send → **Drift Monitor**  ·  **Assurance Lab** audits the Gate
```

- **The Gate:** decompose → evidence-bind → NLI + calibrated judge ensemble → compliance rules; router-and-referee cascade; optional hidden-state probe. *Cited or killed.*

- **The Optimizer:** contextual bandit over a **constrained action space** (verified+cleared variants); unsubscribe = hard negative; hierarchical cold-start; off-policy eval. **Pruning to verified outputs is a structural fix for reward-hacking.**

- **Drift Monitor + Assurance Lab:** claim-dependency-graph re-verification on source change; synthetic adversarial traps + reliability profiling prove the verifier.

## 4 · Scope — two weeks

Minimum shippable

- **The Gate end-to-end** on email → the live **claim ledger** (cited / repaired / blocked).

- **Assurance Lab MVP**: catch-rate vs. false-reject + a calibration diagram.

- Regulatory gate + the "try to make it lie" demo; program-as-data (2nd tenant = config).

Ambitious

- **Truth-bounded Optimizer** on an LLM-persona simulator — conversion climbs, can't win by lying.

- Hidden-state probe + verifier **bake-off** (judge vs. NLI vs. ensemble).

- Live **Drift Monitor**; second-tenant transfer.

## 5 · Why it's compelling

- The hottest AI problem made tangible — **"the outbound AI that can't lie."**

- One genuinely novel bet: **constrained optimization as a structural fix for reward-hacking.**

- A **live data spine** (real prospects, sources, and a legal hold) on day one; demos like a magic trick.

## 6 · Hard parts / risks

**Verifier reliability (top):** a single judge is gameable → NLI + ensemble + calibration, proven in the Assurance Lab.  **Transfer/calibration:** may decay off-domain → make the transfer test a deliverable; recalibrate.  **Sparse reward / cold-start:** simulator + hierarchical bandit + off-policy.  **Claim decomposition:** a missed claim is unverified → measure coverage.

## 7 · Who owns what (team of 3–4)

O1 · verifier ML core **The Gate** — decomposition, binding, NLI + ensemble, calibration, cascade.

O2 · RL + eval core **Optimizer + Assurance** — bandit, off-policy, simulator; traps + profiling.

O3 · data / infra **Library + Drift + spine** — claim–evidence graph, sources, re-verification.

O4 · systems / product **Generation + demo** — per-prospect gen, channel adapters, ledger UI. *(Team of 3 → folds into O1/O3.)*

## 8 · The 10-minute showcase (Jun 29)

**Live artifact:** [SHOWCASE-DEMO.html](SHOWCASE-DEMO.html) (presenter mode · ←/→ beats).

**1m** reframe (every channel) → **3m** Gate + ledger (**Email | Website** toggle · try-to-make-it-lie · MLR hold) → **3m** Assurance Lab → **2m** Optimizer → **1m** ask. *Standalone demo tenant; email = MVP; website = ambitious adapter.*

Provenance · Page 2 · Technical depth

# Why each capability is at the edge of AI

Ambition is the Gauntlet criterion — so here is the depth, and the current research that says each is unsolved.

Frontier weight concentrates in **The Gate (verification), The Optimizer (truth-bounded RL), and the Assurance Lab (reliability proof)** — the hottest current cluster. Each row: the deep mechanism, why it's open (with research signals), and the bet.

| Capability | Technical mechanism (deep) | Why it's at the edge (research) | The bet · where it breaks |
| --- | --- | --- | --- |
| Claims Libraryemerging | **Atomic-claim extraction** → a **claim–evidence graph**; source-span binding via retrieval; versioned provenance. | Decomposing fluent prose into checkable claims + structure-aware reading is unsolved; flat RAG loses structure; GraphRAG often loses to vanilla. S5 · S3 — DeepRead · Contextual Retrieval · EMNLP'25. | A missed claim is unverified. Measure decomposition coverage; puffery as its own class. |
| The Gatefrontier | Decompose → evidence-bind → **NLI entailment + calibrated diverse judge ensemble** → rules; **router-referee cascade**; optional hidden-state probe. | Calibrated verification with **no ground truth at inference**; LLM-judge fails >50% bias tests, is gameable, decays under shift; "verification is the bottleneck." S1 · S2 · S10 — [2604.15149](https://arxiv.org/abs/2604.15149) · [2604.16790](https://arxiv.org/html/2604.16790v1) · [2603.04445](https://arxiv.org/html/2603.04445v2) · [2605.24919](https://arxiv.org/html/2605.24919). | Load-bearing: false-neg ships lies, false-pos kills copy. NLI+ensemble+calibration; prove in the Assurance Lab. |
| The Optimizerfrontier · novel | **Contextual bandit** (Thompson/LinUCB) over a **constrained verified action space**; hierarchical cold-start; doubly-robust off-policy; anytime-valid stats. | Sparse/delayed/expensive/irreversible feedback + off-policy on tiny data + reward-hacking (engagement→exaggeration). S9 · S2 · S1 — [2602.03806](https://arxiv.org/pdf/2602.03806) · RouteLLM · [2504.16828](https://arxiv.org/pdf/2504.16828). | Sim-to-real / cold-start — but **constrained-can't-lie holds regardless.** The most defensible novelty. |
| Drift Monitorfrontier | **Claim-dependency graph** + change-data-capture on sources → propagate invalidation → **targeted re-verification**; auto-pause/unblock. | Truth as a **temporal property**; memory/state under-measured; staleness is the named open problem. S4 · S8 — Anthropic long-running agents · mem0 2026. | Dependency-graph completeness; conservative invalidation (over- vs. under-). |
| Assurance Labfrontier | **Synthetic adversarial-trap generation** + **reliability profiling** (catch-rate@fixed-FR, paraphrase robustness, ECE, severity buckets). | A single pass-rate hides failures and is gameable; you must **adversarially test your own verifier**; synthetic-verification prevents collapse. S1 · S2 · S10 — Berkeley RDI · weak supervision. | Traps may miss real failures. Diverse mutation operators + a real held-out slice. |

**⚡ The one to lead with:** **constrained optimization as a structural fix for reward-hacking** — the policy *cannot* converge to a higher-reward falsehood because falsehoods never enter the reward loop. A fresh answer to the problem the whole field is stuck on, not just an application.

**Signals:** S1 reliability is the production bottleneck · S2 benchmarks distrusted/gameable · S3 long context unsolved · S4 memory/state under-measured · S5 RAG still fails · S8 enterprise governance/audit gaps · S9 multi-model routing standard · S10 feedback/labels/synthetic-verification messy.

arXiv IDs surfaced in June-2026 research; "STATE-Bench"/"ReliabilityBench" and the S1–S10 codes come from the cohort deep-research brief (used as that framework), not independent verification. Illustrative figures labeled as such. Fittingly, we don't present an unsourced claim as sourced.
