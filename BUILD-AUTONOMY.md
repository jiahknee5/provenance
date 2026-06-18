# BUILD-AUTONOMY — Provenance Demo

Standing-authorization charter for the autonomous RAPID build. With `CONSTITUTION.md` +
the locked PRD (`docs/01-intake/PRD.md`) + this file present at the project root, the
build carries **standing approval** to proceed through file creation/edit, local config,
and dependency installs **without per-step gates** — it runs to completion and logs as it
goes.

The build MUST still halt and escalate to the operator for any of the fixed
**stop conditions**:

1. **Destructive / irreversible** — deleting data the build didn't create, `git push
   --force`, rewriting history, dropping anything un-recoverable.
2. **Outward-facing** — `git push`, deploy, publishing, sending a real email/message,
   anything that leaves the machine.
3. **Spends money** — paid infra, a metered paid API beyond the agreed budget. (The demo
   defaults to **offline + Ollama (free)**; the Claude API path is opt-in and only used if
   a key is present and within the dollar-scale budget in the PRD.)
4. **Genuinely-undecidable high-stakes blocker** — a fork where both branches carry
   material, hard-to-reverse consequence and the PRD gives no basis to choose.

## Operator-signed fields
- **Deploy target:** none (local demo only — `uvicorn` on localhost). No deploy without approval.
- **Spend ceiling:** dollar-scale. Default run is $0 (offline + Ollama). Claude API path
  opt-in only.
- **One-time network actions pre-authorized:** PyPI installs of the declared dependency
  set; optional one-time HuggingFace download of `DeBERTa-v3-large-MNLI` (~1.6GB) **only
  if** the operator opts into the real-NLI upgrade. The default build does not require it.

## Decisions
PRD-silent items are decided and logged as numbered entries in
`docs/05-build/DECISIONS.md` (flagged `basis=spec` or `basis=interpretation`), not
surfaced mid-build. Only the four stop conditions above interrupt.

Signed: operator approved the plan at ExitPlanMode (2026-06-17).
