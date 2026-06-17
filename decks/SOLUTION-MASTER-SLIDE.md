Where it lives & how it works🔵 business reading · ⚙ technical reading

# The funnel shows where we plug in. The claim pipeline shows how we work. You need both.

**Is the funnel the right diagram?** Only for placement. Every pillar concentrates at one point — the moment a claim is made — so they'd pile up on the funnel. They line up cleanly on the **claim pipeline** instead. So: two views.

WHERE The marketing funnel — we own the message moment, not the whole funnel

big tech (acquisition)

Awareness

ads, reach

our zone ▶

Consideration

personalized, provable outreach

Intent

claims that must be exact

Conversion

the message that closes

Retention

provable re-touch

▲ Every pillar fires here, at the outbound message — which is exactly why the funnel can't show how they relate.

So flip the lens: a claim isn't a funnel stage, it's an object with a life. **The pillars are stations on its assembly line.**

HOW The claim pipeline — where each pillar lives

```
    Claims Library→
    Draft→
    The Gate · verify + clear→
    The Optimizer→
    Send→
    Drift Monitor
  
```

↩ Drift Monitor feeds changes back into the Claims Library — the loop that keeps it true.

🧪 The Assurance Lab — continuously audits The Gate with adversarial traps (proof the checker actually works)

Claims Library

UsesA claim store + source registry (a database of claim rows).

HowEvery claim is a row bound to its source — your single source of truth for what you may say.

"saves ~$10/head" ↦ Economics Sheet v3 ✓

🔵 Your approved-claims source of truth.

⚙ Claim store + source registry; the corpus the verifier checks against.

The Gate · verify + clear

UsesNLI entailment + LLM-judge ensemble + a compliance rules engine; cheap-first cascade.

HowDecompose → bind to source → entail (cheap check first, escalate the uncertain) → "sayable?" rule.

"same enzyme" → no source → rewritten · "cuts feed 13%" → legal hold → blocked

🔵 A fact-checker + compliance reviewer on every line.

⚙ Decompose→retrieve-bind→NLI+ensemble (calibrated)→rule engine; router+referee for cost.

The Optimizer

UsesA contextual bandit (auto-A/B) per segment.

HowTests only verified + cleared variants; reply/convert = reward, unsubscribe = penalty.

Feedlot segment learns the "$/head" opener wins ~2:1

🔵 Auto-A/B that can't learn to lie.

⚙ Contextual bandit over a verified action space (constrained optimization).

Drift Monitor

UsesA source-change watcher + re-verification trigger.

HowWhen a source changes or expires, re-verify dependent claims; pause or unblock sends.

permit 4,000→2,000 → pause "4,000 head" · UTK hold lifts → unblock "13%"

🔵 Keeps every claim true over time, automatically.

⚙ Source-version diff → claim dependency graph → targeted re-verification.

🧪 Assurance Lab

UsesAn adversarial trap generator + a reliability-profile evaluator.

HowMutate true claims into subtle lies, run continuously, score catch-rate / false-reject / calibration / severity.

98.7% trap catch-rate · 2.1% false-reject · ±3% calibrated

🔵 Proof the checker works — audit-ready, board-ready.

⚙ Synthetic adversarial eval + reliability profiling (pass@k, paraphrase robustness, ECE, severity).

**Read it in one line:** the funnel says we live at the message moment; the pipeline says a claim is *drafted → verified & cleared (The Gate) → optimized → sent → monitored for drift*, with the Assurance Lab proving the Gate works. Five pillars, one claim, two audiences. Provenance · master view · Jun 2026

⌘P to export as PDF (landscape)
