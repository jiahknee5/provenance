Provenance · capstone · page 3 of 5

# The solutions, unpacked

Each capability in three layers: **what a business person needs to understand**, **how it actually works technically**, and **what we're building that's genuinely new** — and why. Start with [page 1](BUSINESS-VISION.html) for the marketing promise, [page 2](BEFORE-AFTER-VALUE.html) for the before/after columns.

[1 · Marketing promise](BUSINESS-VISION.html) [2 · Before → After → Value](BEFORE-AFTER-VALUE.html) 3 · Solution deep dive [4 · Why it's hard](WHY-TECHNICALLY-CHALLENGING.html) [5 · Capstone submission](PROJECT-PLANNING-DOCUMENT.html)

**Context:** a company sends personalized outbound to 10,000–100,000 prospects. Every specific sentence is a **claim** — and a wrong one is a fine, not a typo. The five capabilities below are the pieces of Provenance that make 1:1 outreach safe *and* optimizable.

① Business

Plain English. What problem this solves for Legal, Marketing, Sales, and the board — no jargon required.

② Technical

The actual mechanism: data structures, models, algorithms, and how they connect in the pipeline.

③ Solution & novelty

What we ship concretely, and why existing tools (RAG, LLM-judge, ESP A/B tests) don't already do this.

The engine 1 · Claims Library 2 · The Gate 3 · Optimizer 4 · Drift Monitor 5 · Assurance Lab

OVERVIEWThe Provenance enginethe closed loop

Business

Today you choose between **one safe generic email** (legal approved it, nobody replies) and **personalized AI emails** (people reply, but Legal can't read 100,000 versions). Provenance is the layer that sits **in front of "Send"** — like a firewall, but for factual claims.

Legal approves the **rules and the claims library once.** Marketing launches campaigns as usual. Every generated message is checked automatically: green = provably backed, red = blocked. The system also learns which *true* messages convert best — without ever being allowed to exaggerate.

Technical

```
**Claims Library** → Draft (LLM) → **The Gate** (decompose → bind → NLI+ensemble → rules) → **Optimizer** (contextual bandit) → Send → **Drift Monitor** (dependency graph + CDC) · **Assurance Lab** audits The Gate continuously
```

A **claim ledger** is the central store: each row is an atomic claim with source span, verification score, clearance status, expiry, and performance stats. Generation draws from the library; The Gate validates net-new claims in drafts; Drift Monitor invalidates rows when upstream sources change.

Solution & novelty

**What we ship:** one integrated pipeline where **verification gates optimization** — not two separate products bolted together.

**Why it's novel:** Every other stack treats generation, compliance review, and A/B testing as separate tools. Provenance treats a **claim as the unit of record** with a full lifecycle (draft → verify → clear → optimize → send → monitor → prove). The breakthrough is coupling **calibrated verification + constrained RL** in one loop — optimization happens *inside* a hard truth boundary, not after the fact.

CAPABILITY 1Claims Librarysystem of record

Business

**The problem:** "What are we allowed to say?" lives in scattered slide decks, old emails, and reps' heads. Someone reuses a claim you retired six months ago — now it's wrong, now it's an incident.

**What this gives you:** One living catalog of every factual statement the company may make — each tied to the document that proves it, with an owner and an expiry date. Reps and AI both pull from the same approved set. Retired claims simply aren't selectable.

**Analogy:** Like a formulary in pharma, but for marketing claims — not "what drugs exist" but "what sentences are allowed."

Technical

**Inputs:** product specs, clinical/trial PDFs, pricing sheets, case studies, approved-claims docs, legal holds — ingested and versioned.

**Core structure:** a **claim–evidence graph** — nodes are atomic claims (`"saves ~$10/head"`, `"egg-allergen-free"`); edges bind each claim to an exact **source span** (document ID + char offset + version hash).

- **Atomic-claim extraction:** LLM splits fluent prose into checkable units; puffery flagged as non-factual.

- **Structure-aware retrieval:** locate-then-read over docs (not flat RAG chunks) to preserve tables, footnotes, section hierarchy.

- **Provenance metadata:** owner, approved date, expiry rule (calendar or "on source change"), segment tags, performance history.

Example row`CLAIM #4471` · text: "cut reporting cycle 40%" · source: Case Study CS-2026-04 · status: verified+cleared · used in 1,240 touchpoints · 6.8% convert (health-system segment)

Solution & novelty

**What we ship:** A queryable claims database + ingestion pipeline that builds and maintains the claim–evidence graph. Generation and The Gate read/write this store — it's not a sidecar vector DB.

**Why it's novel:** Standard RAG gives you chunks; it doesn't give you **checkable, versioned, performance-tracked claim objects.** The hard part — decomposing marketing prose into atomic facts and binding each to the exact source line — is an open research problem. We're building a structured substrate where verification and optimization operate on *claims*, not on raw text blobs. The library **compounds**: every campaign adds verified rows competitors starting from zero can't replicate.

CAPABILITY 2The Gate — verify + clearbottleneck remover

Business

**The problem:** Legal reads every email, ad, and deck — 2–4 weeks per campaign. Under deadline, someone ships "clinically proven" with no study behind it. Or you send one boring approved template to everyone.

**What this gives you:** Every message is checked in seconds before it sends. Each sentence gets a green (proven), amber (uncertain — held for review), or red (blocked) light. Legal sets the rules **once**; they stop being the bottleneck on every variant.

**Key distinction:** *True* ≠ *allowed.* A claim can be factually correct and still blocked — legal hold, wrong state, missing disclaimer. The Gate enforces both.

Technical

**Pipeline (per draft message):**

```
draft → **decompose** into atomic claims → **evidence-bind** (retrieve source span per claim) → **verify** (NLI entailment + judge ensemble) → **clear** (compliance rules) → claim ledger update
```

- **NLI entailment:** does the source span logically entail the claim? (cheap, deterministic-ish first pass)

- **Judge ensemble:** diverse LLM families score uncertain cases; scores fused and **calibrated** (isotonic regression; report ECE on reliability diagram)

- **Router-referee cascade:** cheap NLI handles ~70% of claims; only low-confidence cases escalate to the expensive ensemble — keeps cost per message viable

- **Compliance rule engine:** Legal-authored rules (jurisdiction, channel, hold flags, required disclaimers) run after verification

- **Optional hidden-state probe:** classifier on intermediate LLM activations to pre-flag likely-hallucinated generations before full verification

ExampleDraft: "For your 847-bed system, Helix cuts reporting cycle 40%." → claims: [847-bed] ✓ CMS data · [40% cycle] ✓ case study · [47% TCO] ✗ MLR hold.

Solution & novelty

**What we ship:** The Gate as a load-bearing service — every outbound message passes through it; nothing sends without a claim ledger entry. Output: cited / repaired / blocked, with clickable source lines.

**Why it's novel:** The industry default is "ask GPT if this looks right" — LLM-as-judge fails >50% of bias tests and is trivially gameable. We replace a single unreliable judge with **calibrated ensemble selective prediction**: NLI for entailment structure, diverse judges for semantic nuance, explicit calibration so "94% confident" means 94%. This is the frontier problem Karpathy calls "verification is the bottleneck" — we're building verification that holds under adversarial pressure from both the generator and the optimizer, not a vibes check.

CAPABILITY 3The Optimizer — truth-bounded A/Brevenue engine

Business

**The problem:** One generic email to the whole list — flat conversion. Or manual A/B tests that take weeks, test one variable, and never reach the micro-segments that actually matter.

**What this gives you:** The system discovers which *true, approved* variant works best per audience — on email or on a landing page — and shifts automatically. It can't cheat by exaggerating.

**The safety guarantee:** It can never "learn to lie" to get more replies — false claims aren't in the competition.

Technical

**Formulation:** contextual bandit (Thompson sampling or LinUCB) where:

- **Context** = prospect/segment features (industry, size, role, geography)

- **Action space** = verified + cleared message variants only (constrained — this is the key design choice)

- **Reward** = reply / meeting booked / convert; **hard negative** = unsubscribe / spam report

- **Cold-start:** hierarchical priors — borrow strength from parent segments when a micro-segment has no data yet

- **Off-policy eval:** doubly-robust estimator on logged sends to estimate lift without re-running live experiments

- **Anytime-valid confidence:** adaptive testing that doesn't require pre-set sample sizes

ExampleFor health-system buyers, "lead with cycle-time ROI" beats "lead with HIPAA" on both email and web — adopted automatically. Only verified variants compete.

Solution & novelty

**What we ship:** A bandit policy layer that sits after The Gate, choosing among pre-cleared variants per segment — with a live leaderboard UI and logged off-policy metrics.

**Why it's novel:** Every engagement optimizer in production eventually **reward-hacks** — it learns that exaggeration gets clicks. The usual fix is human oversight or cap the reward signal (which kills performance). Our fix is **structural**: prune the action space to verified outputs only. Falsehoods never enter the reward loop, so the policy *cannot* converge to a higher-reward lie. This is constrained optimization as anti-Goodhart — a fresh answer to the problem the whole RL-for-LLMs field is stuck on, not just "we added guardrails."

CAPABILITY 4Drift Monitortruth over time

Business

**The problem:** A claim verified today can be wrong tomorrow. Legal lifts a hold but nobody re-checks 100k live messages — a now-allowed claim sits unused (lost revenue). Or a prospect's permit changes and you keep emailing "your 4,000-head operation" when they now have 2,000 (liability).

**What this gives you:** When any source document changes, every claim that depended on it is automatically re-checked. Stale claims pause before they send. Newly cleared claims unblock everywhere instantly. No manual re-audit of the whole corpus.

**Analogy:** Like cache invalidation for truth — when the upstream data changes, downstream messages update automatically.

Technical

- **Claim-dependency graph:** directed edges from claim nodes → source-version nodes. A source update triggers traversal of all dependent claims.

- **Change-data-capture (CDC):** watch source registry for diffs — document re-upload, permit API refresh, legal-hold flag flip, customer churn.

- **Targeted re-verification:** only affected claims re-run through The Gate (not the full library)

- **Send control:** auto-pause live sequences containing invalidated claims; auto-unblock when re-verification passes

ExamplesLegal lifts UTK hold → "13% feed reduction" auto-unblocks in all templates. EPA permit drops 4,000 → 2,000 head → every email still saying "4,000" paused for re-check. Reference customer churns → "trusted by ACME" pulled.

Solution & novelty

**What we ship:** A dependency graph + CDC watcher + re-verification trigger integrated with the send pipeline and claim ledger.

**Why it's novel:** Most AI "memory" work tests whether you can *retrieve* old facts — not whether those facts are still *correct.* Staleness is the named hard problem in long-running agent systems. Provenance treats truth as a **temporal property**: verification has an expiry tied to source version, not a calendar date someone sets and forgets. This is incremental cache-invalidation for factual claims — something no ESP, CRM, or compliance tool does today because they don't model claims as first-class objects with dependencies.

CAPABILITY 5Assurance Labproof the checker works

Business

**The problem:** "Trust us, the AI checks the claims" — but there's no proof. Risk committees, enterprise buyers, and regulators ask "how do you *know* it works?" and the answer is a shrug. Deals stall for months.

**What this gives you:** A dashboard with real numbers — catch-rate, false-reject rate, calibration accuracy — from continuously running tests. You can put "98.7% catch-rate at 2.1% false-reject" in front of Legal, the board, and procurement. Trust becomes a metric, not a promise.

Technical

- **Synthetic adversarial-trap generator:** mutates verified claims into subtle lies — number drift ("$10" → "$15"), unsupported superlatives, false equivalence, true-but-unsayable (passes verification, fails clearance)

- **Held-out adversarial set:** traps run through The Gate on a schedule; results logged separately from production traffic

- **Reliability profiling (decomposed, not one number):**

  - catch-rate at fixed false-reject threshold

  - paraphrase robustness (same claim, different wording)

  - calibration: ECE + reliability diagrams ("when we say 90%, we're right 90% of the time")

  - severity-weighted error buckets (blocked a puffery vs. blocked a material misstatement)

Solution & novelty

**What we ship:** An Assurance Lab module that continuously generates traps, runs them through The Gate, and produces an audit-ready reliability report — plus a bake-off comparing single-judge vs. NLI vs. ensemble on catch-rate per dollar.

**Why it's novel:** AI eval today is mostly benchmark scores that get gamed (Berkeley RDI broke 8 top agent benchmarks). A single pass-rate hides catastrophic failures in the tail. We build a **wind tunnel for the verifier itself** — adversarially attacking our own checker and reporting decomposed reliability. This is the direct answer to "how do you know the AI doesn't lie?" — not marketing copy, but a continuously updated reliability profile you can show an auditor. Fittingly, we don't present an unsourced claim as a sourced one.

How the five pieces fit

The **Claims Library** is what you're allowed to say. **The Gate** checks every new sentence against it. **The Optimizer** picks the best verified variant per segment. **Drift Monitor** keeps it all true over time. **Assurance Lab** proves the checker itself works. Together they turn "personalized vs. compliant" from a trade-off into a solved problem.

[← Page 2 · Before → After → Value](BEFORE-AFTER-VALUE.html) [Page 4 · Why it's hard →](WHY-TECHNICALLY-CHALLENGING.html)

Illustrative figures (catch-rates, volumes) labeled as such where used. Research signals and arXiv IDs anchor to the June 2026 cohort brief.

Provenance · capstone page 3 of 5 · Jun 2026 · [← page 2](BEFORE-AFTER-VALUE.html) · [page 4 →](WHY-TECHNICALLY-CHALLENGING.html) · [hub](index.html)
