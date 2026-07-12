# PRD — apt Section Personalization Designer

> **Status:** DERIVED (extends `PRD-derived.md`; follows the `BUILD-AUTONOMY.md` decision protocol, numbered `Rn`).
> **Authority:** `CONSTITUTION.md` (Art I/II/IV/V/VII inviolable) > this PRD > decks.
> **Companions:** `../04-workflow/SECTION-DESIGNER-WALKTHROUGH.md` (the operator journey → E2E tests), `../05-build/GENERATION-PROMPT-WORKFLOW.md` (two-lane engine), the approved plan `~/.claude/plans/vivid-jingling-pascal.md`.
> **Acceptance = the test suite passes** (WF-DESIGN-* derived from the walkthrough) **AND** an operator can complete the 11-question workflow per section in one screen, no code (Q11).

## 1. Vision & wedge

**The Section Designer is the product surface of apt.** Today apt *is* a personalization engine with a console that reports decisions grouped by asset type. This makes it the surface where a marketer **designs** personalization: they pick the exact page elements to personalize, decide *how* and *why* for each, and every choice is **provable, optimized, watched** — the four pillars, brought down from the campaign level to **each individual personalization decision**.

**One line:** *"Point at any element on your site, say how it should personalize — and apt proves every version, A/B-optimizes it inside the truth boundary, and re-verifies it forever."*

**Pillars (per decision, not just per campaign):**
1. **Provable** — every personalized element binds to a source + lawful basis + surface policy + Gate verdict; nothing renders un-receipted.
2. **Optimizing** — each element with ≥2 Gate-cleared variants runs a long-running per-segment bandit that *cannot win by lying* (Art II bounds its pool).
3. **Watched** — each element's claims are drift-monitored; a source change surgically re-verifies only the affected variants and pauses them.
4. **Quiet** — one section-oriented designer replaces four overlapping consoles; plain-English labels; the workflow is *findable, followable, understandable*.

## 2. Personas & JTBD

Inherits the `PRD-derived.md` cast; the primary operator here is **P3 Maya — Growth marketer / web designer**. Secondary: **P1 Renata (RevOps)** who audits, **P5 Dr. Chen (skeptical exec/CISO)** who must be able to defend any element's copy.

**Primary JTBD:** *"I want to personalize specific parts of my site to who's visiting — and be able to prove, optimize, and monitor each one — without a data-science team and without risking a claim I can't back."* The bottleneck apt removes: **verification at scale** — you can't hand-review 100k unique messages, so today you pick generic-but-safe or personal-but-unverified. The designer lets Maya pick **personal AND verified, per element**.

## 3. Locked decisions

| R | Decision | Type |
|---|----------|------|
| **R30** | **The section is the atomic unit.** A page = an ordered list of sections; each has 0/1/many text targets + 0/1/many image targets. Source of truth = `rules/<tenant>_sections.yaml` (tenant = config, Art V). Generalizes the existing `surfaces:` + `design_prompts.yaml` + prebuild-manifest triad; gives copy slots their first YAML home. | operator |
| **R31** | **Text: deterministic default + Gate-bounded generative opt-in.** Deterministic slot-fill (no prompt, $0) is the provable default. A target may opt into generative: prompt → LLM candidates → **every candidate passes the Gate** → cached (prebuilt or realtime-by-key). Compliant with Art I/II/IV *because* Gate-gated + cached. The forever-deferred thing (free-form ungated live regenerate) stays deferred. | operator |
| **R32** | **Consolidate to one console.** The marketer console becomes the designer; the engineer console folds into a "developer/audit" toggle; the 6-route image-decisions guides fold into a per-section methodology panel; one ad-grid per tenant. Keep replica, galleries, `/apt/demo`, `/observatory`, `/costs`. | operator |
| **R33** | **Mark + configure existing regions** (hero/prove/challenger/compare/cta[/location]); adding brand-new page regions is a later extension. | operator |
| **R34** | **Every personalization decision carries the full pillar stack** — provenance + long-running A/B + drift prevention + A/B optimization — at the per-element grain (§5). Reuse the existing engine (`optimizer/`, `drift/`, `assurance/`, provenance ledger); do not rebuild. | operator |
| **R35** | **Real image generation is funded (Nano Banana / Gemini Flash Image).** Real-time image sections are first-class. Each image target declares `workflow: prebuilt` (0 ms, $0/visit, baked at deploy) or `realtime` (~1–3 s async gradient→swap, $/first-visit then cached-by-key, Art IV replay). `live`/blocking is discouraged. Latency + $/gen shown per target (Q8/Q9). | operator |
| **R36** | **Three demo tenants: `gauntlet`, `planet`, `skyfi`.** SkyFi.com needs a **new replica** (style/logo/palette, standalone template) parallel to the other two; thesis = location × industry (on-demand satellite imagery), signature guardrail = basin/region scale, **exact-AOI is `hold` unless declared/first-party**. Flows through `console_shell_ctx` + the demo dropdown by config (tenant = config, Art V). See `../04-workflow/SECTION-DESIGNER-EXAMPLES.md` §2. | operator |
| **R37** | **10 solid examples per tenant across all channels** (direct/search/ads[X+Google+Meta]/email), mixing deterministic/generative text and prebuilt/real-time images, chosen to showcase distinct personalization options and the latency/cost trade-off. The 30-row matrix (`SECTION-DESIGNER-EXAMPLES.md` §3) is the source for both `rules/demo_scenarios.yaml` and the `WF-DESIGN-*` E2E suite. | operator |
| **R39** [AMENDMENT] | **Cohesion is the organizing objective.** The current deployment is fragmented — the tour plane, consoles, dashboards, replicas, ad grids, and legacy plane were built separately. This PRD + spec exist to bring them together as ONE product: **one design system** (R38), **one data model** (the section registry, R30), **one console** (the designer, R32), **one engine surface per concern** (the per-decision pillar stack, R34), **one nav/IA** (sitemap → channels → sections → decisions), **one test spine** (`workflows.json` → WF-DESIGN). Acceptance: every surface reachable from the unified sidebar; no concern rendered twice by different pages; single source of truth per data type; zero orphan routes. Any new surface that ships outside this IA is a defect. | operator |
| **R38** [AMENDMENT] | **One design system; retire the legacy plane.** Escalation of R32: the HubSpot/X-Ads **apt console shell** (`_apt_shell.html` + `_apt_sidebar.html`) is the **single** design for the entire product; **`base.html` / `_nav.html` legacy chrome is removed** and the **~30-route pre-unification "Provenance/Helix" plane is retired** (`/demo*`, `/showcase*`, `/workspace`, `/records*`, `/inspector`, `/personalize`, `/assurance`, `/optimizer`, `/funnel`, `/composer`, `/policies`, `/graph`, `/help*`, `/archive`, `/sources`, `/agent`, `/admin/landings`, `/lp`, `/enrichment-catalog`, `/` home). Still-needed content **folds into the shell**: assurance/optimizer/drift → the per-decision pillar stack (§5); inspector/graph → per-section agent-graph + observability; enrichment-catalog → the section's Data panel; everything else is cut (logged in `docs/RECONCILIATION.md`). **Exception:** the personalized **replica** pages (`gauntletapt`/`planetapt`/`skyfiapt`) and the X-style **ad mockups** keep their own external-site styling — they must look like the real sites being demoed, not the apt product. This is a substantial retirement with test churn → its own build phase. | operator |

## 4. The workflow (what the product must let an operator do)

Per website, per element, the operator answers the **11 questions** (full detail + worked examples + per-question "why" in `SECTION-DESIGNER-WALKTHROUGH.md`): **Q1** which element · **Q2** why/goal · **Q3** which channel(s) · **Q4** how (deterministic\|generative × prebuilt\|realtime) · **Q5** which sales/marketing strategy · **Q6** guardrails + provenance (say/allude/hold, Gate, claims) · **Q7** observability · **Q8** latency · **Q9** cost · **Q10** agent-graph trace · **Q11** is it easy to find/follow/understand.

**Requirement:** all eleven are answerable **in the designer, in one screen, in plain English, without editing code.** Q11 is a first-class acceptance test, not a nicety.

## 5. Phase-2 requirements — the pillar stack per decision (the hard requirement)

apt already ships these mechanisms at the **campaign/claim** level; Phase 2 brings each **down to the individual personalization decision** (a target's variant choice). Each is a testable requirement.

### 5.1 Provenance per decision — **REQUIRED**
Every shipped personalized element carries a receipt: `{source_id, lawful_basis, surface_policy(say/allude/hold), gate_verdict, claim_id(s), cache_key, mode, workflow}`. Surfaced **on-page** (the DATA-USED strip) *and* in the section card. No element renders without one. *Reuse:* `copy_diff[]`, the image receipt, `schemas.MessageLedger`, `library.ClaimNode`. *Test:* provenance-invariant — un-receipted element = fail.

### 5.2 Long-running A/B testing per decision — **REQUIRED**
Any element with ≥2 Gate-cleared variants runs a **persistent, per-segment contextual bandit** (Thompson) over its **cleared** pool: impressions/clicks update posteriors online, warm-started across restarts, running indefinitely (not a fixed-duration test). A **random control holdout** measures lift. *Reuse:* `optimizer/bandit.py`, `optimizer/live.py` (`assign`/`reward_click`/`settle`/`lift_report`), `common/store.py` (warm-start). *Bring to the section-decision grain* (keyed by `tenant:section:target:segment`). *Test:* posteriors move on real events; serving converges to the winner; lift(bandit) > control.

### 5.3 Drift prevention per decision — **REQUIRED**
Each variant binds to the claim(s) it uses. On a **source change or legal-hold flip**, re-verify **only** the affected claims and **pause only** the variants that used them — surgically, no redeploy, attributable to `rules_version` alone (property P2/P3). A paused variant is removed from the bandit pool (so 5.2 can't keep serving a now-stale claim). *Reuse:* `drift/monitor.py`. *Test:* flip a hold → exactly the dependent variants pause; no over/under-invalidation.

### 5.4 A/B optimization per decision, inside the truth boundary — **REQUIRED**
The bandit converges each element's traffic to the **winning Gate-cleared variant per segment**, and is **structurally unable** to select a blocked/unverified variant — never a special-case filter (Art II). The planted lie gets **0 selections** while an unconstrained twin converges to it. *Reuse:* `optimizer/campaign.py`, `optimizer/oracle.py` (offline), `optimizer/live.py` (online), the P1 property test pattern. *Test:* mirror `test_optimizer` P1 at the per-element grain.

> **These four are one system, not four features:** a decision's *cleared variant pool* (5.4) is the object the bandit optimizes (5.2), that drift pauses (5.3), and that provenance receipts (5.1). Build them against the shared per-decision pool object.

## 6. Scope & phasing (from the approved plan)

- **Phase 0 (this doc + the walkthrough)** — requirements + the E2E test derivation. ← *current.*
- **Phase 1** — the section registry (`rules/<tenant>_sections.yaml` + `sections.py` + `list_sections`), behavior-neutral (mirrors today's slots+surfaces); `build_page` byte-identical.
- **Phase 2 (this PRD §5)** — the pillar stack per decision: provenance, long-running A/B, drift prevention, A/B optimization, on the shared per-decision cleared-pool object.
- **Phase 3** — the Section Designer UI (rework the marketer console into the per-section list; per-section graph/evals/observability/cost; staged-diff drawer against the registry).
- **Phase 4** — Gate-bounded generative text mode (prebuilt + realtime), reusing `ai_copy`/`verify_copy`/`build_action_pool`.
- **Phase 5** — consolidation cuts (engineer console → dev toggle; image-decisions → panel; dedup ad-grids).

*(Note: numbering here follows the PRD's build order; the plan file's phase list is the same work in a UI-first order. Reconcile in `docs/RECONCILIATION.md` if they diverge.)*

## 7. Acceptance criteria

1. **The 11-question workflow (Q1–Q11)** is completable per section in the designer, one screen, plain English, no code. (WF-DESIGN suite §5.B + §5.F.)
2. **Invariants hold per element** (§5.C): Gate-bounded (0 blocked servable), deterministic replay, hold-never-ships, provenance on every element.
3. **The pillar stack works per decision** (§5): each element exposes its provenance, its long-running A/B + measured lift, its drift behavior (surgical pause), its Gate-bounded optimization (0 lie selections).
4. **Observability/cost/graph per section** (Q7/Q9/Q10) render from a **real run** (Art I).
5. **Consolidation** (R32): four console surfaces → one; all former routes still resolve; the full deploy gate stays green; the 5 property tests are **untouched** (Art VII).
6. **Determinism** (Art IV): the section registry and both workflows replay byte-identically; the app still runs offline, $0, no key.

## 8. Non-goals (pushback — keep out of scope)

- **Free-form "AI writes the page live" per visit, ungated.** Deferred forever (violates Art I/II/IV). Generative text is *always* Gate-bounded + cached.
- **A visual page-builder that adds arbitrary new regions.** Later extension (R33).
- **Real multi-tenant beyond "tenant = config"** (Art V). "Add new website" scaffolds config, not a new runtime.
- **Selling the brain-simulator score as measured conversion/neurometrics.** It is *predicted* proxy scoring, labeled as such.
- **Exact-site / surveillance pinpointing.** The creepy ceiling stays a blocked arm.
