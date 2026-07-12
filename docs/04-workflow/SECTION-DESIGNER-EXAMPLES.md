# Section Designer — 3-Tenant Example Catalog & Test Matrix

> **Status:** SPEC (hardens `SECTION-DESIGNER-WALKTHROUGH.md` + `../01-intake/PRD-SECTION-DESIGNER.md` to **3 demo tenants** with a concrete 30-scenario matrix).
> **Tenants:** `gauntlet` (GauntletAI — AI hiring fellowship), `planet` (Planet — Earth observation), **`skyfi` (SkyFi.com — on-demand satellite imagery, NEW replica needed)**.
> **Each row is one `WF-DESIGN-*` scenario** — a channel × personalization option × mode × workflow, chosen to showcase breadth. Rows become both `rules/demo_scenarios.yaml` entries and E2E tests.

## 1. Real image generation is now funded (Nano Banana)

`R35` — **A real text-to-image key (Nano Banana / Gemini Flash Image) is budgeted.** This promotes **real-time image sections** from "aspirational" to a first-class workflow. The design must make the **pre-built vs real-time trade-off explicit per image target**, because latency and cost now differ materially:

| Image `workflow` | When it renders | Latency (visitor) | Cost | Use when |
|---|---|---|---|---|
| **prebuilt** | baked into the Docker image at deploy (`warm_hero_cache`) | **0 ms** (instant paint) | one-time at build; **$0/visit** | high-traffic segments, ad landings, the top N region/industry combos |
| **realtime** | generated on first visit via Nano Banana, then **cached by key** | **~1–3 s** async: gradient → swap (never blocks paint) | **$/first visit**, $0 thereafter (Art IV replay) | the long tail (rare region×industry), fresh/one-off combos |
| **live** | generated per visit, blocking | seconds, blocking | $/visit | **discouraged** — violates the "never block paint" rule |

Invariant (Art IV): real-time is still **deterministic on replay** — same input → same `cache_key` → same image. Cost is recorded once in `api_costs` keyed by `cache_key`; the section card shows *first-visit latency* and *$/gen* so the operator chooses with eyes open (Q8/Q9).

**Cost-logging invariant (REQUIRED — `R35a`): every Nano Banana / image-API call is cost-logged, no exceptions.** *Verified in code today:* `_call_image_api` (`pipeline/personalization/image_gen.py:797`) is the single entry point for **every** image API call (OpenAI-compatible and Gemini/Nano Banana alike, keyed by `IMAGE_GEN_API_KEY`/`NANO_BANANA_API_KEY`), and it calls `_record_image_api_cost → api_costs.record_call` **unconditionally after every call** (`:821`) — on success *and* on error/429 (`images_generated = 1 if status=="success" else 0`, `:830`), per best-of-N candidate. There is no code path that hits the API without recording a ledger row (request_id, vendor, model, operation, cache_key, status, duration_ms, cost). **This is now a locked test requirement:** an eval asserts `record_call` fires once per `_call_image_api` invocation, including a simulated 429, so a future refactor cannot introduce an uncosted call. Provenance (PRD §5.1) includes cost — an uncosted generation is a provenance violation.

## 2. SkyFi tenant — replica to build

`R36` — **Add `skyfi` as the 3rd tenant** (Gauntlet + Planet already have replicas; SkyFi does not). Per `docs/USE-CASES.md` UC2, SkyFi sells **on-demand satellite imagery — the geography *is* the product**. Replica requirements (parallel to `gauntlet_site.py` / `planet_site.py`):

- **Replica page** faithful to skyfi.com — style, **logo/wordmark**, palette (SkyFi's dark/space aesthetic), hero, "how it works," pricing/AOI CTA. Standalone template `skyfi_site.html` (self-contained CSS, like the others).
- **Personalization thesis: location × industry.** Resolve operator + region/sector (IP → region, PDL industry); swap copy **and** a **license-tagged / generated region×sector backdrop**.
- **The signature guardrail (the sale, not a limit):** region+sector scale only. **Exact-AOI / specific-asset pinpointing is `hold`** (blocked arm `Ex`) — *unless* it's a declared/first-party AOI (they told you, or it's their own asset), which the receipt then surfaces honestly. This is the anti-surveillance ceiling and SkyFi's sharpest demo beat.
- **Mounts** (portal + legacy), `MOUNTS` dict, cohort (`skyfi_cohort.py`), `rules/skyfi_*.yaml` (image, prebuild, tenant-gate, **sections**), a `skyfi` entry in `_TENANT_META` / `_TENANT_LOGO` (green/space swatch) so it flows through `console_shell_ctx` + the demo dropdown automatically.
- Verticals to seed (from UC2): mining, precision-ag, construction/EPC, commercial real estate/site selection, insurance cat-risk, energy/utilities, logistics/maritime, defense/gov (strict hold).

## 3. The 30 examples (10 per tenant)

Columns: **Channel** · **Scenario (who)** · **Element personalized** · **Mode** (det=deterministic, gen=generative) · **Workflow / latency** · **Strategy** · **Key guardrail**. Every row asserts the §5 invariants (Gate-bounded, hold-never-ships, deterministic replay, provenance).

### 3.1 GauntletAI (`WF-DESIGN-G01…G10`)

| # | Channel | Scenario | Element | Mode | Workflow · latency | Strategy | Guardrail |
|---|---|---|---|---|---|---|---|
| G01 | direct | cold anon, no signals (tier 0) | hero sub (text) | det | realtime · 0 ms | neutral baseline | say only what's provable with zero data |
| G02 | direct | corporate IP (Apple netblock), anon B2B | hero sub + prove intro (text) | det | realtime · 0 ms | firmographic-allude | employer **alluded, never recited** (hold) |
| G03 | search | organic Google, intent-neutral | hero headline (text) | det | realtime · 0 ms | authority (evidence-led) | no comparative vs "a CS degree" |
| G04 | ads (X) | `v09` keyword "AI hiring" | hero headline + **hero image** | det text / gen image | image **prebuilt** · 0 ms | message-match | image `must_avoid` real logos |
| G05 | ads (Google) | search-ad "switch into AI" | hero sub (text) | **gen** | text **prebuilt** · 0 ms | loss-aversion (honest) | candidate pool Gate-cleared; no superlative |
| G06 | ads (Meta) | broad-audience awareness | **section backdrop image** | gen | **realtime** (Nano Banana) · ~2 s swap | curiosity | tier-gated; gradient fallback offline |
| G07 | email | HubSpot cohort — Liam (magic token) | hero eyebrow "Welcome back, Liam" | det | realtime · 0 ms | commitment/open-loop | say-level name (token); **abandoned-app fact = hold** |
| G08 | email | known exec — Maya (logged in) | prove card (peer-logo, text+logo) | det | logo **prebuilt** · 0 ms | social-proof (peer-matched) | all peer logos Gate-cleared |
| G09 | direct | returning known, high intent | cta (text) | **gen** | **realtime** by-key · <100 ms | scarcity-honest | a scarcity claim must be a **provable deadline** or it's dropped |
| G10 | ads (X) | `v03` cost-objection creative | challenger body (text) | det | realtime · 0 ms | objection-reframe | reframe at allude; `blocked_say` recite console-only |

### 3.2 Planet (`WF-DESIGN-P01…P10`)

| # | Channel | Scenario | Element | Mode | Workflow · latency | Strategy | Guardrail |
|---|---|---|---|---|---|---|---|
| P01 | direct | self-serve cold (tier 0) | hero (text) | det | realtime · 0 ms | neutral | **no region line ships** without confidence |
| P02 | direct | ag enterprise, Midwest IP | location line + **region backdrop** | det text / gen image | image **prebuilt** (top belts) · 0 ms | location-relevance | **region scale only**; city/field = hold |
| P03 | ads (X) | `v01` crop-belts creative | hero headline + location line | det | realtime · 0 ms | message-match | theater-line for defense, never visitor loc |
| P04 | ads (X) | `v02` defense/sovereign | hero image (theater, not visitor region) | gen | **realtime** · ~2 s | authority | uses **AOR/theater**, never the visitor's location |
| P05 | search | organic, region resolves | location line | det | realtime · 0 ms | location-relevance | default daily-coverage line at region scale |
| P06 | email | crisis-responders — Kofi (token) | hero eyebrow + cta | det | realtime · 0 ms | reciprocity (relief context) | relief-org context; income/PII = hold |
| P07 | email | enterprise agronomy — Amara (login) | prove intro (text) | **gen** | text **prebuilt** · 0 ms | authority | Gate-bounded; declared goals say-level |
| P08 | ads (Meta) | awareness, long-tail region | **section backdrop image** | gen | **realtime** (Nano Banana) · ~2–3 s | curiosity | long-tail region → realtime; common → prebuilt |
| P09 | direct | corporate IP, insurance cat-risk | compare emphasis (text) | det | realtime · 0 ms | loss-aversion | **no competitor named**; comparatives blocked |
| P10 | direct | returning known | cta (text) | gen | realtime by-key · <100 ms | scarcity-honest | provable deadline only |

### 3.3 SkyFi (`WF-DESIGN-S01…S10`) — needs the replica (R36)

| # | Channel | Scenario | Element | Mode | Workflow · latency | Strategy | Guardrail |
|---|---|---|---|---|---|---|---|
| S01 | direct | cold anon (tier 0) | hero (text) | det | realtime · 0 ms | neutral | no location/sector claim without confidence |
| S02 | direct | mining operator, AZ IP + PDL sector | hero sub + **region×sector backdrop** | det text / gen image | image **REAL-TIME** (Nano Banana) · ~2 s gradient→swap, cached by key | location-relevance | **basin/region scale**; exact mine = hold (arm `Ex`) |
| S03 | ads (X) | paid "monitor your site" | hero headline + hero image | det text / gen image | image **realtime** (Nano Banana) · ~2 s | message-match | generated backdrop is region-generic, license-safe |
| S04 | ads (Google) | "satellite imagery on demand" | hero sub (text) | **gen** | text **prebuilt** · 0 ms | authority | Gate-bounded; no "clearest/best" superlative |
| S05 | search | organic, region resolves | location line (text) | det | realtime · 0 ms | location-relevance | region scale; declared-AOI = say, else hold |
| S06 | email | construction/EPC — known account | prove card (project-region, text) | det | realtime · 0 ms | social-proof (sector peer) | peer refs Gate-cleared |
| S07 | email | defense/gov — cleared contact | hero eyebrow + cta | det | realtime · 0 ms | authority | **strict hold**: AOR framing, never a specific asset |
| S08 | ads (Meta) | awareness, rare sector×region | **section backdrop image** | gen | **realtime** (Nano Banana) · ~2–3 s | curiosity | long-tail → realtime; anti-surveillance mood rules |
| S09 | direct | **declared first-party AOI** (their own asset) | hero image (their basin) | gen | **realtime** · ~2 s | location-relevance | exact-AOI **allowed because declared**; receipt says "you told us" |
| S10 | direct | returning known, insurance cat-risk | compare emphasis (text) | gen | realtime by-key · <100 ms | loss-aversion | no competitor; comparatives blocked |

## 4. What the matrix guarantees (coverage)

- **All channels** exercised per tenant: direct, search, ads (**X + Google + Meta**), email.
- **Both text modes:** deterministic (default) and Gate-bounded generative.
- **Both image workflows:** pre-built (instant, 0 ms) and real-time (Nano Banana, ~1–3 s async swap) — with the latency/cost trade-off tested per row.
- **The signature real-time beat (operator-locked):** **S02** — direct visitor, **IP→region + company/sector resolution → real-time generated region×sector backdrop**, watched live (~2 s swap), cached by key thereafter. P02 (Planet, prebuilt top crop-belts, 0 ms) is the deliberate instant-paint contrast shown beside it.
- **The signature guardrail per tenant:** Gauntlet = no competitor/comparative + hold employer; Planet = region-scale + theater-for-defense; SkyFi = basin-scale + exact-AOI-only-if-declared (the anti-surveillance ceiling).
- **The pillar stack per decision** (PRD §5) attaches to any row with ≥2 cleared variants: long-running A/B, drift pause, provenance.

## 5. Test-suite hardening tasks (derived)

1. Each `WF-DESIGN-*` row → an E2E scenario: assert the personalized element, its mode/workflow, latency class (blocking vs async vs instant), Gate-bounded pool, hold-never-ships, provenance receipt, deterministic replay.
2. **Nano Banana real-time image test:** offline → gradient/gallery fallback ($0, deterministic); with key → generate once, cache, replay identical; cost recorded once; latency non-blocking (gradient first).
3. **SkyFi replica tests** (parallel to `test_gauntlet_site.py` / `test_planet_site.py`): entry classification, region-scale location (exact-AOI never ships **unless declared**), the declared-AOI say/hold flip (S09), image guardrails.
4. **Cross-tenant shell test:** `skyfi` flows through `console_shell_ctx`, the demo dropdown, and the designer with no special-casing (tenant = config, Art V).
5. **The 3 signature-guardrail invariants** as property tests (immutable, real Gate): competitor/comparative block (all), theater-not-visitor-location (Planet defense), exact-AOI-hold-unless-declared (SkyFi).
