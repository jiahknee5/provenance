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
| /demo, /demo/variant, /demo/monitor, /demo/live, /api/demo/* | **RETIRED (T-09 G2)** | tour: /apt/demo; monitors: per-section obs (T-04). Deleted `app/demo.py` + `demo.html`, `demo_monitor.html`, `demo_live.html`. Engine behind the demo APIs (scene/creative/demo_sim/demo_scenarios) untouched and still pipeline-tested (`test_demo.py`, full-suite engine tests). |
| / (home), /talk, /guide | **RETIRED (T-09 G2)** | `/` now 302 → `/apt/demo` (the sitemap owns the front door); Attio-style `home.html` deleted. `/talk` + `/guide` deck redirects cut — the decks stay at `/static/talk/deck.html` + `/static/mockups/copy-research-guide.html`. No property test exercises `/` — the KEEP clause wasn't triggered. |
| /workspace, /records, /records/new, /records/undo | **RETIRED (T-09 G4)** | apt shell consoles (/apt/dev + per-tenant /dev, /dev/business). Deleted `app/workspace.py`, `workspace.html`, `records.html`, `records_new.html`. Removed full-suite tests that asserted only this surface: cmdk palette, create/undo/filter/sort records, skip-link (all Quiet-Workspace-shell UI); the provenance/engine invariants they rode on remain asserted by the kept engine tests. |
| /inspector, /graph, /agent | retire | per-section agent graph + observability (T-04) |
| /assurance, /optimizer, /funnel | retire | per-decision pillar panels (S4) |
| /personalize, /composer, /policies, /help*, /archive, /sources, /admin/landings, /lp, /google* | retire | designer Data panel + docs |
| /showcase/{slug}, /showcase/{slug}/production, /showcase/{slug}/observability | **RETIRED (T-09 G1)** | tour narrative → /apt/demo; per-decision observability → per-section consoles (S4/T-04). Deleted `use_case.html`, `use_case_rich.html`, `pipeline/personalization/showcase.py`. |
| /showcase (index) | **KEPT — exception (T-09 G1)** | Locked deploy-gate tests (`test_gauntlet_site.py`/`test_planet_site.py::test_showcase_card_publishes_the_entry_links`, part of the 408 gate baseline) pin the index's replica entry-link content; gate tests win over retirement. Index trimmed to the two replica cards (live-demo card + use-case grid removed); standalone apt styling, no legacy chrome. Reachable via /apt galleries' footer links. |
| /enrichment-catalog | fold | section Data panel note |
| /help, /help/{slug} | **RETIRED (T-09 G3)** | Product docs now live in the repo corpus (`docs/`, RUNBOOK); the in-app corpus (`app/help_corpus.json`) + `help.html`/`help_article.html` deleted. **Pre-existing failure resolved here:** `test_full_suite.py::test_integrations_show_base_vs_connect` — root cause: the `integrations` article body used `type:"table"` blocks, but `help_article.html`'s renderer only implemented `p/h/ul/ol/note/kv/code`, so the table (People Data Labs / What it adds / Why it matters) silently rendered as nothing; the test asserted a renderer branch that never existed. The surface is retired, so test + route were removed together rather than implementing a `table` branch for a dead page. `test_help_aligns_with_the_app` + `test_version_tag_and_whats_new_in_foot` removed with it (assert only /help content). |
| / (home), /lead, /submit, /site/<token>* | KEEP if property tests exercise them (property tests win over retirement — T-09 logs exceptions here) |
