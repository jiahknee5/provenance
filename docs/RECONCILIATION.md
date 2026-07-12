# Deck ↔ build reconciliation

The decks are the planning context; `docs/01-intake/PRD.md` is the contract. Where the
deck prose and the build differ, this is the documented reconciliation (per Constitution
Article VI — never a silent deck edit). The architecture diagrams are already consistent
with the build; these notes concern prose in the deck corpus.

| Deck prose | As built | Note |
|---|---|---|
| "RL loop" / "RL core" (PROJECT-PLANNING-DOCUMENT, COHORT-DEMO §3.2.7) | **contextual bandit** (Thompson) | One-step contextual decisioning, no sequential credit; the diagrams already say "bandit." See DECISIONS R1. |
| "NLI gives calibrated P(correct)" (COHORT-DEMO §3.2.4) | NLI gives a **raw** entailment score → **then** the Calibrator (isotonic/ECE) | That's exactly why the Gate has a separate calibration stage. |
| "98.7% catch / ±3% ECE / <5% FR" | reported as **illustrative**, computed from a real run; tests assert **inequalities/floors**, not point values | Tiny-N synthetic traps; lead with catch-rate-at-fixed-FR. |
| "Assurance Lab for each channel" | **one** harness, results **sliced** per channel | Two labs would imply two Gates and contradict "same Gate, two channels." |
| "Full stack live on stage" | **deterministic seeded replay** (pre-recorded run trace) | The deck's own risk mitigation (pre-cache), extended from pages to the run. |
| Real Gauntlet-cohort dataset ("Tom") for the website | **100% synthetic, seeded** recipients | Avoids the consent/PII blockers the cohort docs flag; fully reproducible. |

These are wording reconciliations only — the product definition, the 5 modules, and the
"constrained optimization as a structural fix for reward-hacking" thesis are unchanged and
are what the build proves.

## R38 retirement mapping (pre-seeded for T-09; update as routes are cut)
| Legacy route(s) | Disposition | Where the value lives now |
|---|---|---|
| /demo, /demo/variant, /demo/monitor, /demo/live | retire | tour: /apt/demo; monitors: per-section obs (T-04) |
| /workspace, /records* | retire | apt shell consoles |
| /inspector, /graph, /agent | retire | per-section agent graph + observability (T-04) |
| /assurance, /optimizer, /funnel | retire | per-decision pillar panels (S4) |
| /personalize, /composer, /policies, /help*, /archive, /sources, /showcase*, /admin/landings, /lp, /google* | retire | designer Data panel + docs |
| /enrichment-catalog | fold | section Data panel note |
| / (home), /lead, /submit, /site/<token>* | KEEP if property tests exercise them (property tests win over retirement — T-09 logs exceptions here) |
