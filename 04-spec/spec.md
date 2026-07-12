# apt Section Personalization Designer — Derived Build Spec

> **RAPID P4 artifact.** Derived from `docs/01-intake/PRD-SECTION-DESIGNER.md` (authority) + `docs/04-workflow/SECTION-DESIGNER-WALKTHROUGH.md` (workflow) + `docs/04-workflow/SECTION-DESIGNER-EXAMPLES.md` (3-tenant × 10-example matrix). Governed by `CONSTITUTION.md` (Art I/II/IV/V/VII inviolable). Build order in `~/.claude/plans/vivid-jingling-pascal.md`.
> **Restructure build (PRD R22):** reuse the existing engine (`optimizer/`, `drift/`, `assurance/`, `gate/`, `personalization/`); do not rebuild.
> **Tag key:** `[FROM PRD Rn]` traces to a locked decision · `[DERIVED]` inferred · `[OPEN]` needs a decision. Each section names the pillar it serves (Provable / Optimizing / Watched / Quiet).

---

## S0 — Cohesion: one product, not parts · `[FROM PRD R39]` · Quiet (organizing objective)

The deployment is fragmented because it was built piecewise: tour plane, two consoles, dashboards, image-decisions guides, ad grids, replicas, and a ~30-route legacy plane — each its own design, IA, and data path. **Every S-section below is a unification move**, and cohesion is the acceptance lens for all of them:

| Fragment today | Unified by |
|---|---|
| Two designs (apt shell vs base/_nav legacy) | **One design system** — S8 (R38) |
| Copy slots in Python, image surfaces in YAML, prompts in a 3rd file | **One data model** — the section registry, S1 (R30) |
| Engineer console + marketer console + 6-route guides | **One console** — the designer + dev toggle, S5 (R32) |
| Optimizer / assurance / drift / costs as separate build-scoped pages | **One surface per concern, per decision** — the pillar stack, S4 (R34) |
| Nav paths that dead-end (galleries ↛ sections ↛ decisions) | **One IA:** sitemap → channels → **sections → decisions** — every page reachable from the sidebar |
| Tests scattered per page | **One test spine:** `docs/workflows.json` → the WF-DESIGN suite, S7 |

- **S0.1 Cohesion acceptance (blocking at ship):** every route reachable from the unified sidebar; no concern rendered by two different pages; single source of truth per data type (registry / claims / scenarios / prebuild manifest); zero orphan routes (`app/*.py` route sweep vs sidebar map); tenant switcher works identically on every page.
- **S0.2** A new surface that ships outside this IA is a **defect** (gap type `cohesion`), not a feature.

## S1 — Section registry (the data model) · `[FROM PRD R30]` · Provable/Quiet

A page is an ordered list of **sections**; each has 0/1/many `text_targets` and 0/1/many `image_targets`. Source of truth = `rules/<tenant>_sections.yaml` (tenant = config, Art V). Generalizes the existing triad (`surfaces:` in `image_gen.py` + `design_prompts.yaml` + the `prebuild` manifest); gives copy slots their first YAML home.

- **S1.1** Schema per the PRD "core abstraction" block: `section{id,label,region,personalize, text_targets[], image_targets[], guardrails, evals}`. `text_target{slot_id,mode(deterministic|generative),source|claims[],policy(say|allude|hold),prompt?,gate?,workflow(deterministic|prebuilt|realtime)}`. `image_target{surface_id,intent rules,prompt shape,guardrails,workflow(prebuilt|realtime|live)}`.
- **S1.2** Loader `pipeline/personalization/sections.py`: `list_sections(tenant) -> [Section]`, cached like `demo_nav.load_scenarios()`; schema-validated; unknown fields rejected. `list_text_targets(tenant)`, `list_image_targets(tenant)`.
- **S1.3** **Behavior-neutral seed (Art IV):** the initial YAML mirrors today's hardcoded slots (`gauntlet_site.build_page` `slot()` ids) + surfaces (hero/og). `build_page` output MUST be byte-identical before/after Phase 1 (the registry is descriptive first; `build_page` reads it in a later phase).
- **Acceptance:** round-trip `yaml ↔ list_sections`; every current slot+surface represented; `build_page` byte-identical.

## S2 — Text lane · `[FROM PRD R31]` · Provable

Two modes per text target. **Deterministic (default):** slot-fill from catalogs/claims + say/allude/hold, no prompt, $0 — the current provable path (`slot()`+`copy_diff`, `OBJECTION_CATALOG` reframes). **Generative (opt-in):** a `prompt` → LLM candidates (`creative.ai_copy`) → **every candidate passes the Gate** (`creative.verify_copy` / `variants.build_action_pool`) → the cleared pool is cached; `workflow: prebuilt` (offline `warm_copy_cache` script, byte-identical replay) or `realtime` (cache-by-visit-key).

- **S2.1** A generative target's servable set is a **Gate-cleared pool** — structurally excluded candidates (competitor / comparative / superlative / `hold` fact) can never be served, never a special-case (Art II). Mirror `test_optimizer` P1 at the target grain.
- **S2.2** Bind text targets to `claim_id`s (`library.ClaimNode`) where a claim backs the copy; carry `source`+`policy` otherwise.
- **Acceptance:** planted lie/superlative/competitor/hold candidate → 0 servable; deterministic replay from cache; hold-never-ships (reuse `test_hold_facts_never_reach_the_shipped_page`).

## S3 — Image lane + Nano Banana · `[FROM PRD R35/R35a]` · Provable/Watched

Reuse the image lane (`surfaces`/`intents`/`build_structured_prompt`/`get_surface_image`). Generalize surfaces beyond hero+og to any registered image target. Workflow per target: `prebuilt` (0 ms, baked via `warm_hero_cache`, $0/visit), `realtime` (Nano Banana ~1–3 s async gradient→swap, $/first-visit then cache-by-key), `live` (discouraged).

- **S3.1 Cost-logging invariant `[R35a]`:** every image-API call records a cost row — verified: `_call_image_api` (`image_gen.py:797`) calls `_record_image_api_cost → api_costs.record_call` unconditionally (`:821`), success + 429, per candidate. Locked test: `record_call` fires once per `_call_image_api`, incl. a simulated 429. No uncosted path.
- **S3.2 Latency class is explicit per target** (Q8): instant / async-swap / blocking; the section card shows first-visit latency + $/gen (Q9).
- **S3.3 Prebuild budget policy `[PANEL — locked]`:** prebuilt = **explicitly flagged states only** (`prebuild: true`, consumed by `prebuild_states`, `prebuild.py:110-122`), hard caps **K=8 states per image target, 24 baked images per tenant, 80 global** (~today's 176MB cache bulk, no Docker-layer growth); states referenced by `rules/demo_scenarios.yaml` fill the K slots first; `og`/secondary surfaces get their own explicit short lists (no YAML-anchor mirroring of hero). Everything else is `realtime` (gradient→swap, cache-by-key) governed by a **per-tenant realtime spend ceiling (default $5/day** at $0.039/gen via `api_costs`); past the ceiling the target serves its neutral prebuilt/gradient. `scripts/warm_hero_cache.py` **fails the deploy gate** if the manifest exceeds any cap.
- **S3.4 Signature real-time demo beat `[FROM operator]`:** a **direct**-channel visitor with resolved **IP→region + company/sector** (corporate netblock + PDL) triggers **real-time Nano Banana generation** of the region×sector backdrop (~2 s gradient→swap, cached by key thereafter) — matrix row **S02** (SkyFi mining operator; P02 stays prebuilt as the instant-paint contrast). This is the live showcase of R35: personalization the visitor can watch happen.
- **Acceptance:** offline → gradient/gallery fallback ($0, deterministic); with key → generate once, cache, replay identical, cost recorded once; never blocks paint.

## S4 — The per-decision pillar stack · `[FROM PRD R34, PRD §5]` · Optimizing/Watched/Provable

Bring the engine down to the per-element grain, against a shared **per-decision cleared-pool object** keyed `tenant:section:target:segment`.

- **S4.1 Provenance** (`§5.1`): every shipped element carries `{source_id, lawful_basis, policy, gate_verdict, claim_id(s), cache_key, mode, workflow}` — on-page receipt + section card. Un-receipted = fail. Reuse `copy_diff`, image receipt, `MessageLedger`.
- **S4.2 Long-running A/B** (`§5.2`): per-segment Thompson bandit over the cleared pool; online posterior updates; warm-started; random-control holdout for lift. Reuse `optimizer/bandit.py`, `optimizer/live.py`, `common/store.py`.
  **`[PANEL — locked]`** `segment` = **`audience_route`** (exactly `b2b_hire|b2b_upskill|individual|neutral`, the existing `_audience_route`, `gauntlet_site.py:812-838`); `tenant` + `channel` stay the posterior-store identity exactly as `live.py:77-89` keys today (channel×route would double-count channel). The offline seed campaign generates at the same route grain so `warm_start_from` (`live.py:84-88`) stays a key-for-key copy. Any route cell with **<30 resolved impressions serves from a pooled `_all` cell** (hierarchical fallback) so posteriors visibly move within one demo session.
- **S4.3 Drift prevention** (`§5.3`): variants bind to claims; source/hold change → re-verify only affected claims → pause only dependent variants (removed from the bandit pool), attributable to `rules_version` (P2/P3). Reuse `drift/monitor.py`.
- **S4.4 Optimization inside the boundary** (`§5.4`): bandit converges to the winning cleared variant per segment; **structurally unable** to select a blocked variant (Art II) — planted lie 0 selections vs unconstrained twin. Reuse `optimizer/campaign.py`+`live.py`.
- **Acceptance:** each element exposes provenance + A/B + measured lift + surgical drift pause + 0-lie optimization, from a real run (Art I).

## S5 — The Section Designer UI · `[FROM PRD R32/R33]` · Quiet

Rework the marketer console (`gauntlet_dev_business.*` / `planet_dev_business.*`, view `:600-945`) into a **per-section list**: one card per section (header + personalize toggle + add text/image target); text targets (`_copy_cards` extended, target-scoped, editable-via-registry); image targets (`_image_surface_card` under its section); collapsible per-section **agent-graph / evals / observability / cost** (reuse the observatory node contract + assurance + `api_costs` + brain best-of-N, scoped by section id). Every edit stages a YAML diff into `rules/<tenant>_sections.yaml` via the existing staged-changes drawer (`gauntlet_dev_business.html:612-798`). A **developer/audit toggle** folds in the engineer console's trace/audit.

- **Acceptance (Q1–Q11, walkthrough §5.B/§5.F):** an operator completes the 11-question workflow per section in one screen, plain English, no code; the staged diff targets the registry.

## S6 — Three tenants + SkyFi replica · `[FROM PRD R36]` · Provable

Tenants `gauntlet`, `planet`, `skyfi`. **SkyFi needs a new replica** (`skyfi_site.html` standalone, style/logo/palette; `MOUNTS`; `skyfi_cohort.py`; `rules/skyfi_*.yaml`; `_TENANT_META`/`_TENANT_LOGO` entry so it flows through `console_shell_ctx` + the demo dropdown by config). Thesis = location × industry; signature guardrail = **basin/region scale; exact-AOI is `hold` unless declared/first-party** (the anti-surveillance ceiling, arm `Ex`).

- **Acceptance:** parallel to `test_{gauntlet,planet}_site.py` — entry classification, region-scale location (exact-AOI never ships unless declared — the S09 say/hold flip), image guardrails; skyfi flows through the shell with no special-casing.

## S7 — 30-example demo/test matrix · `[FROM PRD R37]` · all pillars

The 30 rows (`SECTION-DESIGNER-EXAMPLES.md §3`) seed `rules/demo_scenarios.yaml` and the `WF-DESIGN-{G,P,S}01…10` E2E suite. Coverage: all channels (direct/search/ads[X+Google+Meta]/email) × both text modes × both image workflows × each tenant's signature guardrail.

## S8 — One design; retire the legacy plane · `[FROM PRD R38]` · Quiet

The apt console shell is the single design. **Remove `base.html`/`_nav.html` chrome; retire the ~30-route legacy Provenance/Helix plane**; fold still-needed content into the shell (assurance/optimizer/drift → §4; inspector/graph → per-section graph+observability; enrichment-catalog → the Data panel). **Exception:** replica pages + ad mockups keep external-site styling. Substantial retirement + test churn → its own phase.

- **Acceptance:** no route renders `base.html`/`_nav.html`; retired routes 404/redirect; deploy gate green; the 5 property tests untouched (Art VII).

---

## Architecture · `[DERIVED]`

```
rules/<tenant>_sections.yaml          # S1 registry (NEW) — the source of truth both lanes read
pipeline/personalization/
  sections.py                         # S1 loader: list_sections / list_*_targets (NEW)
  decision_pool.py                    # S4 shared per-decision cleared-pool object (NEW; wraps gate+bandit+drift+provenance)
  gauntlet_site.py / planet_site.py / skyfi_site.py   # build_page reads the registry (skyfi NEW)
  image_gen.py / image_intents.py     # generalize surfaces beyond hero+og (EXTEND)
  creative.py / generation/variants.py# generative text mode: candidates→Gate→pool (REUSE, wire to replica opt-in)
  gauntlet_dev_business.py / planet_dev_business.py / skyfi_dev_business.py  # designer view model (REWORK)
optimizer/ drift/ assurance/ library/ observability/api_costs.py            # engine — REUSE per-decision
app/gauntlet.py / planet.py / skyfi.py / apt_dev.py                          # routes; skyfi mount (NEW)
app/templates/ _apt_shell.html _apt_sidebar.html                            # single design; retire base.html/_nav.html
scripts/warm_hero_cache.py + warm_copy_cache.py                             # prebuilt image + prebuilt generative copy (copy NEW)
```

**Layer boundaries:** registry (data) → build_page (composition, reads registry) → decision_pool (gate+bandit+drift+provenance per element) → designer view (reads decision_pool state) → shell templates (render). The designer never mutates a DB — it stages YAML (Art IV/V).

## Workflow · `[FROM walkthrough]`

The user-facing state machine = the 11-question operator loop (`SECTION-DESIGNER-WALKTHROUGH.md §1`) + the per-element runtime flow (resolve signals → select intent/claims → assemble prompt/plan → **Gate (pool)** → cache/serve → receipt). Emit the machine-readable form to `docs/workflows.json` (per node: in/proc/out + golden + a bounded `exec` against the local test/e2e). Each `WF-DESIGN-*` row is one workflow journey.

## CONTRACTS · `[DERIVED]`

- `sections.py`: `list_sections(tenant:str) -> list[Section]` (Section = typed dict per S1.1).
- `decision_pool.py`: `cleared_pool(tenant, section, target, segment) -> [Variant]` (Gate-cleared only); `bandit_pick(pool, segment) -> Variant`; `receipt(variant) -> Receipt`.
- `image_gen._call_image_api` — **must** call `record_call` (S3.1); contract-tested.
- Registry YAML schema — the pinned contract both lanes + the designer build against.

---

## Task decomposition (P5 preview) · `[DERIVED]`

`T-00` eval-harness (BLOCKING, `spec_ref: ALL`): materialize the WF-DESIGN suite + the §1–§8 acceptance tests; hit the **real Gate**; immutable. Then, in plan order:

| Task | spec_ref | prd_ref | depends | Deliverable |
|---|---|---|---|---|
| T-01 section registry + loader | S1 | R30 | T-00 | `rules/*_sections.yaml` + `sections.py`, byte-neutral |
| T-02 per-decision pool object | S4 | R34 | T-01 | `decision_pool.py` (gate+bandit+drift+provenance) |
| T-03 designer UI (read-only) | S5 | R32/R33 | T-01 | per-section console + staged diff |
| T-04 per-section graph/evals/obs/cost | S4/S5 | R34 | T-02,T-03 | section cards render real graph/evals/cost |
| T-05 generative text mode | S2 | R31 | T-02 | `ai_copy`→Gate→pool, prebuilt+realtime, `warm_copy_cache` |
| T-06 image lane generalize + Nano realtime | S3 | R35 | T-01 | surfaces beyond hero+og; realtime cost-logged |
| T-07 SkyFi tenant + replica | S6 | R36 | T-01 | `skyfi_site.html` + mounts + cohort + rules |
| T-08 30-example scenarios + WF-DESIGN tests | S7 | R37 | T-01..T-07 | `demo_scenarios.yaml` + `tests/test_wf_design_*.py` |
| T-09 single design / retire legacy | S8 | R38 | T-03 | remove base.html/_nav.html + retire ~30 routes |

**Inter-stage assertion:** every S-section maps to ≥1 task; every task carries spec_ref+prd_ref; T-00 is the graph root; the 5 property tests stay immutable (Art VII).

---

## Execution plan — waves, swarms, long-running agents, overnight run · `[DERIVED]`

Sized for **one unattended overnight run** under `BUILD-AUTONOMY.md` standing authorization. Fan-out cap: **≤4 implementors + 1 watchdog** (project standard). Rule of thumb: **swarm** what is independent + bounded (per-tenant, per-page, per-test-row); **long-running agent** for what is deep, stateful, or serial (the registry the whole build reads, the pool object, the wide-churn retirement).

### Waves (the DAG, with orchestration mode per task)

| Wave | Tasks | Mode | Why |
|---|---|---|---|
| **W0** (serial spine) | T-00 eval-harness → T-01 registry | **one long-running agent** | Everything depends on these; the harness is the immutable contract, the registry is the data model every later agent reads. No parallelism until they're locked. |
| **W1** (swarm, 4-wide) | T-02 decision-pool · T-03 designer UI · T-06 image lane+Nano · T-07 SkyFi replica | **4 parallel agents, worktree-isolated** | All depend only on W0 and touch disjoint files (pipeline/ vs templates vs image lane vs new tenant). T-02 is the deepest — assign the strongest/longest-running slot. Watchdog audits each merge. |
| **W2** (pairs) | T-04 per-section graph/evals/obs/cost (needs T-02+T-03) · T-05 generative text (needs T-02) | **2 parallel long-running agents** | Both are integration-heavy (cross-module state), not bounded fan-out work. |
| **W3** (swarm, widest) | T-08: 30 WF-DESIGN scenarios + tests | **fan out per row** (batches of 4: G01–G10, P01–P10, S01–S10) | Each row is independent + bounded — the ideal swarm shape. Each subagent writes one scenario + one test, runs it against the real Gate. |
| **W4** (serial, careful) | T-09 single-design / retire legacy plane | **one long-running agent, keep-or-revert per route** | Wide test churn across ~30 routes; parallelizing this multiplies conflict risk. Route-by-route: retire → run gate → commit or revert. |
| **W5** (gate + ship) | full suite → deploy → prod verify | **orchestrator** | `railway up --ci` in the standing retry loop (~61 MB upload is flaky; retry ≤8). Verify against johnnycchung.com, not localhost. |

Checkpoint after every wave: run the full deploy-gate suite; a wave that regresses it is reverted, not patched (Art IV). All state to `.rapid/` (STATE/TASKS/HEARTBEAT/COST) so the run is resumable at any wave boundary.

### Overnight preconditions (collect BEFORE the run — nothing may interrupt mid-run)
1. **Keys in `.env` / Railway env:** `IMAGE_GEN_API_KEY` (Nano Banana), `ANTHROPIC_API_KEY` (generative text). Absent key ⇒ those targets build in offline mode ($0) and are flagged, not blocked.
2. **Spend ceiling** for Nano Banana + LLM calls (Gate-2 input; cost breaker pauses generation at 80%, build continues offline). All calls cost-logged per S3.1.
3. **Deploy pre-authorization:** standing operator instruction for this project is *always deploy* (deploy target: Railway `provenance`/production; `git push` to `deploy/railway` allowed). This satisfies the outward-facing stop condition **for this project only**.
4. **SkyFi brand reference** captured (screenshots/palette of skyfi.com) so W1's T-07 agent doesn't need a mid-run fetch decision.
5. Undecidable-batch: none open (R30–R39 resolve the known forks). Anything new mid-run → log as `basis="interpretation"` decision, don't stop (D5).

### Morning report (the run's exit artifact)
`.rapid/RETRO.md` + dashboard: per-wave pass/fail, VERIFY.json layers (build/unit/e2e, run-not-inspected), gap list by severity, **cost actuals** (Nano Banana $ from the ledger vs ceiling), deploy status + prod URLs, and the cohesion sweep (S0.1) result. Anything unverified is listed as unverified — never reported green (Art VIII).

## Traceability matrix (completeness proof) · `[DERIVED]`

Every locked PRD decision maps to spec → task → eval. No orphans in either direction. Task detail (touch lists, verify commands, waves, orchestration mode) is materialized in **`.rapid/TASKS.json`**; pinned seam contracts in **`04-spec/contracts/`** (registry-schema · decision-pool · designer-dom).

| PRD | Spec | Task(s) | Eval |
|---|---|---|---|
| R39 cohesion | S0 | T-09, T-10 | S0.1 sweep (zero orphan routes, one design, one IA) |
| R30 section registry | S1 | T-01 | A (round-trip), byte-identical build_page |
| R31 text modes | S2 | T-05 | C (0-blocked-servable, replay), hold-never-ships |
| R35/R35a images + cost | S3 | T-06 | G (record_call per call incl. 429), caps + ceiling |
| R34 pillar stack/decision | S4 | T-02, T-04 | E (lift>control, surgical pause, 0-lie), D (real-run graph/cost) |
| R32/R33 designer | S5 | T-03, T-04 | B (per-section render, staged diff), F (Q11 one-screen journey) |
| R36 SkyFi | S6 | T-07 | H (region-scale, declared-AOI flip) |
| R37 30 examples | S7 | T-00, T-08 | one WF-DESIGN test per matrix row (30) |
| R38 single design | S8 | T-09 | legacy chrome absent; property tests untouched |

**Panel decisions folded (tagged `[PANEL — locked]`):** S4.2 bandit keying (audience_route + `_all` fallback); S3.3 prebuild budget (K=8/target, 24/tenant, 80 global, $5/day/tenant realtime ceiling, fail-loud warm script). **Operator-locked:** S3.4 the S02 direct-channel IP+company → real-time generation beat.

**Inputs resolved:** `IMAGE_GEN_API_KEY` in `.env` + Railway, validated live (cost-logged $0.039 — R35a proven). **Open:** operator spend ceiling (defaulted $10/day global, `basis=interpretation`, D5-logged).

## Eval harness (P5 preview) · `[DERIVED]`

`.rapid/EVAL/` materializes: (A) registry round-trip; (B) designer render per section (Q1–Q10 controls present, staged diff targets registry); (C) invariants — **real Gate**: generative pool 0-blocked-servable, deterministic replay, hold-never-ships, provenance-on-every-element; (D) per-section graph/evals/cost from a real run; (E) the per-decision pillar stack (A/B lift, surgical drift pause, 0-lie optimization); (F) ease-of-use journey (mark→add target→configure→read latency/cost→open graph, one screen, no code); (G) **S3.1 cost-logging** (record_call per image call incl. 429); (H) SkyFi replica (region-scale, declared-AOI flip). One `WF-DESIGN-*` scenario per matrix row.
