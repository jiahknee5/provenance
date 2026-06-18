# CONSTITUTION — Provenance Demo

Inviolable guardrails for the Provenance end-to-end demo build. Agents (human or AI)
are checked against these before any merge. Articles I–V are **inviolable**; VI–X are
**overridable only with a logged decision** in `docs/05-build/DECISIONS.md`.

This demo is itself a system whose entire thesis is *"can't say what it can't prove."*
The Constitution holds the build to the same bar the product holds outbound copy.

## I — Truthfulness (no fabrication)
No fabricated results, metrics, or capabilities. Demo numbers (catch-rate, regret,
ECE) are **computed from a real run**, never hand-typed. Any illustrative figure is
labelled "illustrative." A claim the code cannot substantiate is a bug, not a feature.
Fabrication is a CRITICAL violation that halts the build.

## II — The truth boundary is load-bearing
The Optimizer may only ever select **Gate-cleared** variants. A blocked/unverified
variant must be *structurally* unable to enter the action pool — never filtered out by a
hand-coded special case. If you find yourself hard-excluding the planted lie, stop: the
pool construction is wrong.

## III — Data handling & secrets
No real PII. All recipient data is synthetic + seeded. No secret (API key, token) is
ever committed; `.env` and `*.key`/`*.pem` stay gitignored. The demo runs fully offline
with no key; keys only *upgrade* model quality.

## IV — Reversibility & determinism
Every artifact (users, ledgers, campaign runs, metrics) is reproducible from
`scripts/` + the global seed. Keep-or-revert: a change that regresses the eval harness is
reverted, not patched over. No step mutates a committed source of truth in place without a
version bump.

## V — Scope discipline
Build the end-to-end thin slice the PRD describes — real where it matters (Gate, NLI,
Assurance math, the form/website), simulated where it is theatre (CTA oracle). No
production auth, no real sending, no multi-tenant beyond "tenant = config."

## VI — Spec authority
`docs/01-intake/PRD.md` is the authority. The decks are context, not contract. A conflict
between deck prose and the PRD resolves to the PRD; reconcile the deck as a *documented*
edit, never silently.

## VII — No test theatre
The eval harness (`tests/`) is immutable once written. Tests are never weakened, skipped,
or rewritten to make code pass. The 5 headline-property tests hit the **real Gate** (no
mocks of the decision logic) and assert inequalities/floors, not hardcoded numbers.

## VIII — Honest reporting
Report what actually ran vs. what was only inspected, per layer. "Compiles" ≠ "works."
A layer that could not be exercised is surfaced as a gap, never reported green.

## IX — Pushback discipline
If a requested change violates an Article or the PRD, say so and propose the compliant
alternative. Do not capitulate without a reason; do not invent a reason to comply.

## X — Root-cause discipline
Fix causes, not symptoms. No try/except-and-continue, retry loops, or fallbacks that mask
a real failure. When unsure about an API/flag/behaviour, verify it — don't guess.
