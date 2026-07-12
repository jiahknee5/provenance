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
| /inspector, /graph, /agent, /api/agent/run | **RETIRED (T-09 G5)** | per-section agent graph + observability (T-04, gate-tested by `test_per_section_obs.py`). Deleted `app/{inspector,graph,agent}.py` + `inspector.html`, `inspector_empty.html`, `graph.html`, `agent.html`. The agent-intents engine (`pipeline/agent/intents.py`) stays and remains asserted by `test_full_suite.py::test_agent_explains_win_with_provenance`. `site_cta.html` drops its inspector cross-link. |
| /assurance, /optimizer, /funnel (+ /api/optimizer/*, /api/observe/golden, /api/observe/history, /api/observe/funnel) | **RETIRED (T-09 G6)** | per-decision pillar panels (S4, built by T-02/T-04; gate-tested by `test_decision_pool.py` + `test_per_section_obs.py`). Deleted `app/{assurance,optimizer,funnel,charts}.py` + templates (`charts.py` was only used by the retired dashboards). Engines untouched: `pipeline/assurance/*` (property T5), `optimizer/` + live bandit (property T1 + live-optimizer suite), `pipeline/customer/funnel` (`test_funnel.py`). `test_blocked_arm_provably_never_selected` keeps its engine invariant (DS blocked arm), drops only the /optimizer page-text assert. |
| /personalize (+/api/personalize), /composer, /policies*, /archive, /sources, /admin/landings, /admin/landing/{pid}, /lp, /google, /google/callback | **RETIRED (T-09 G7)** | designer Data panel + per-section consoles + repo docs. Deleted `app/{personalize,policies,archive,sources,cohort,google_login}.py` + their templates (+`composer.html`, `landing.html`, `lp_entry.html`, `admin_landing(s).html`, `shell.html` — zero shell extenders remain). `app/composer.py` kept as the send-check ENGINE (`check()`, asserted by the kept full-suite test); its page route removed. Engines untouched: `pipeline/personalization/{render,signals,cohort,landing,segments,google}` (tested by `test_personalize.py`, `test_cohort.py`, `test_google.py`); magic-token cohort modules still power the kept /apt galleries. `corpus/` seed docs stay on disk (reference material; the Gate's grounding corpus is the Library, not these files). Removed full-suite tests that asserted only these pages: policies×3, composer-examples, archive-nav, shell-template trio (extend-shell / no-raw-hex / q-btn), Proves-spine, per-page renders. |
| /showcase/{slug}, /showcase/{slug}/production, /showcase/{slug}/observability | **RETIRED (T-09 G1)** | tour narrative → /apt/demo; per-decision observability → per-section consoles (S4/T-04). Deleted `use_case.html`, `use_case_rich.html`, `pipeline/personalization/showcase.py`. |
| /showcase (index) | **KEPT — exception (T-09 G1)** | Locked deploy-gate tests (`test_gauntlet_site.py`/`test_planet_site.py::test_showcase_card_publishes_the_entry_links`, part of the 408 gate baseline) pin the index's replica entry-link content; gate tests win over retirement. Index trimmed to the two replica cards (live-demo card + use-case grid removed); standalone apt styling, no legacy chrome. Reachable via /apt galleries' footer links. |
| /enrichment-catalog | **FOLDED (T-09 G8)** | Section Data story: fold note added to the designer's per-target Receipt panel (`_sd_designer.html`); the per-source catalog engine (`pipeline/enrichment/catalog.py`) + `/api/observe/profiles` stay. `enrichment_catalog.html` deleted; observatory's link swapped for the Data-panel note. |
| base.html, _nav.html, _demo_flow.html, shell.html (chrome) | **DELETED (T-09 G7/G8)** | Zero references remain (grep-proof in `.rapid/COHESION.md`). The six kept base-extenders were converted standalone: `form/thanks/site/site_cta` keep Helix external-site styling (the /site plane is the original replica — R38's external-styling exception), `gauntlet/planet_image_decisions` render standalone (gate-pinned content unchanged). |
| /lead, /submit, /site/{token}, /site/{token}/cta | **KEPT — exception (T-09)** | Property T4 (`test_website.py`, LOCKED) exercises this plane's engine (`app.site.render_site_data`), and the live-optimizer serving path (assign→impression→reward) runs through /site; /lead+/submit are its only entry. Restyled standalone (no legacy chrome). Root-cause fix riding along: `init_db` now migrates pre-tenant `impressions` tables (dev DBs died with `no such column: tenant` on every /site visit — pre-existing, confirmed on baseline). |
| /help, /help/{slug} | **RETIRED (T-09 G3)** | Product docs now live in the repo corpus (`docs/`, RUNBOOK); the in-app corpus (`app/help_corpus.json`) + `help.html`/`help_article.html` deleted. **Pre-existing failure resolved here:** `test_full_suite.py::test_integrations_show_base_vs_connect` — root cause: the `integrations` article body used `type:"table"` blocks, but `help_article.html`'s renderer only implemented `p/h/ul/ol/note/kv/code`, so the table (People Data Labs / What it adds / Why it matters) silently rendered as nothing; the test asserted a renderer branch that never existed. The surface is retired, so test + route were removed together rather than implementing a `table` branch for a dead page. `test_help_aligns_with_the_app` + `test_version_tag_and_whats_new_in_foot` removed with it (assert only /help content). |
| / (home), /lead, /submit, /site/<token>* | KEEP if property tests exercise them (property tests win over retirement — T-09 logs exceptions here) |

## W8-A menu merge (2026-07-12, operator-directed)

Operator call: "merge the menu-inside-a-menu; simplify; chronological marketer
workflows; sections expandable but start hidden; HubSpot/X-Ads-friendly." One
menu now: the apt sidebar. Test updates below are architecture updates of
presentation-IA assertions only (none locked; engines untouched).

| Surface | Disposition | Where the value lives now |
|---|---|---|
| /apt/dev console-launcher cards (Marketer/Engineer/replica/ads-grid `hub-grid`) | **REMOVED** | Duplicated the sidebar item-for-item. Page repurposed as **Preview as visitor** (identity toggle + entry chips + open-live CTA). Tests updated: `test_apt_dev_hub.py::test_apt_dev_hub_defaults_to_gauntlet`, `test_demo_nav.py::test_apt_dev_hub_is_preview_not_console_launcher` (was `_marketer_console_first`), `test_skyfi_site.py::test_demo_hub_and_dev_hub_surface_skyfi`. |
| Gauntlet marketer console in-page rail (`gd-side`/`gb-nav`, 8 numbered links + Sections/Copy/Images/Other views) | **REMOVED** | The literal menu-inside-a-menu. Chapters are the collapsed section cards themselves, in page order; sd-* deep links from sidebar auto-expand via `_collapse.html`. Scroll-spy script deleted. Tests updated: `test_gauntlet_site.py::test_console_sidebar_sections_render_on_both_mounts`, `::test_dev_business_renders_story_sidebar_and_legend` (assert sections by id, not rail hrefs). |
| "Simulate entry" chip row on all 3 marketer consoles | **MOVED** | Lives on Personalization → Preview as visitor (/apt/dev). |
| "Demo sitemap →" topbar button on consoles + hub; "← Demo sitemap" in gauntlet channel strip | **REMOVED** | Sidebar Campaigns → Overview is the one route to /apt/demo. Tests updated: `test_demo_nav.py::test_apt_dev_hub_links_demo_sitemap`, `::test_marketer_console_channel_strip_and_prompt_catalog`. |
| Sidebar "Decision trace" item | **REMOVED** | Engineer console stays one click away: console "Technical view →" + Developer/audit fold (R32). |
| Sidebar branches auto-open for the whole active group | **CHANGED** | Branch opens only on the active trail (`sub_ids` computed in `demo_nav.console_shell_ctx`); everything else starts collapsed. |
| First designer card ships `open` | **CHANGED** | All sd-cards start collapsed; `#sd-{id}` deep links auto-expand. DOM contract (sd-* testids) unchanged. |

Engineer consoles (`/dev` pages) keep their own rails for now — technical
audience, candidate for a later wave.
