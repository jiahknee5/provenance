Provenance · capstone · page 2 of 5

# What changes, capability by capability

A practical, side-by-side read: **what happens without it**, **exactly what the solution is**, **what happens with it**, and **the value added** — for the whole campaign, then for each of the five capabilities.

[1 · Marketing promise](BUSINESS-VISION.html) 2 · Before → After → Value [3 · Solution deep dive](SOLUTION-DEEP-DIVE.html) [4 · Why it's hard](WHY-TECHNICALLY-CHALLENGING.html) [5 · Capstone submission](PROJECT-PLANNING-DOCUMENT.html)

[← Page 1 · The marketing promise](BUSINESS-VISION.html)

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

[Page 3 of 5Solution deep dive — business · technical · novel →](SOLUTION-DEEP-DIVE.html)

Timeframes, catch-rates, and volumes are illustrative — the structure of the change is the point. (Fittingly, we don't present an unsourced number as a sourced one.)

Provenance · capstone page 2 of 5 · Jun 2026 · [← page 1](BUSINESS-VISION.html) · [page 3 →](SOLUTION-DEEP-DIVE.html) · [hub](index.html).
