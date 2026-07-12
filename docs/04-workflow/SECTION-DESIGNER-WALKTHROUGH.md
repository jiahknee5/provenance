# Section Designer — Web-Designer Walkthrough & E2E Test Derivation

> **Status:** SPEC (drives the section-designer build + its test suite).
> **Companion:** `docs/01-intake/PRD-SECTION-DESIGNER.md` (requirements), `../05-build/GENERATION-PROMPT-WORKFLOW.md` (two-lane engine), `CONSTITUTION.md` (Art I/II/IV/V/VII).
> **Method (per project CLAUDE.md):** the workflow declares data-in → processing → data-out per decision; **tests derive from this doc**. Every numbered step below yields a `WF-DESIGN-*` E2E test.

This doc walks **the mind of the person doing the personalization** — a growth marketer / web designer configuring a website in apt — decision by decision, asking *why* at each setting. The walkthrough is the acceptance test: if a real operator can answer every question below **inside the product, easily**, the designer works.

---

## 1. The mental model — the 11 questions a designer asks per personalized element

For **each website**, for **each element** (a text target or an image target) they consider personalizing, the operator walks this loop. Each question maps to one UI affordance and one config field in `rules/<tenant>_sections.yaml`, and each becomes a test assertion.

| # | The designer asks… | Config field | Why it exists (the pillar it serves) |
|---|--------------------|--------------|--------------------------------------|
| Q1 | **Which** element do I want to personalize? | section `id` + `text_targets[]` / `image_targets[]` | Scope: 0/1/many per section. You personalize where relevance moves conversion, not everywhere. |
| Q2 | **Why** — what's the goal of personalizing this one? | target `goal` | Forces intent. "Reframe the top objection" ≠ "prove a number." Prevents personalization theatre. |
| Q3 | **From what channel** does the data come? | target `channels[]` (direct/search/ads/email) | Data richness gates what you *can* say. Email brings CRM identity; direct brings only IP. You can't design a say-level line for a channel that only yields allude-level data. |
| Q4 | **How** will I do it — deterministic or generative; pre-built or real-time? | target `mode` (deterministic\|generative) + `workflow` (prebuilt\|realtime\|live) | Provability vs flexibility, and latency vs freshness. Deterministic = provable-by-construction, $0. Generative = a prompt, Gate-bounded + cached. Pre-built = instant; real-time = fresh, cached-by-key. |
| Q5 | **What sales/marketing strategy** am I applying? | target `strategy` (objection-reframe \| social-proof \| authority \| scarcity-honest \| loss-aversion \| location-relevance …) | The persuasion lens. In apt a strategy changes the *frame*, never the *facts* (`persuasion.py`). It selects *which provable claim leads*, in what order. |
| Q6 | **What guardrails & provenance** will govern it? | target `policy` (say/allude/hold) + `gate` (rule set) + `claims[]` / `source` | The truth boundary. Every candidate must clear the Gate; `hold` facts never ship; no competitor/comparative/superlative. The on-page receipt proves it. |
| Q7 | **How will I observe** this decision in flight? | section `observability` (event-ledger view) | You can't trust hands-off personalization you can't watch. Per-section append-only event ledger (poll-since-seq). |
| Q8 | **What's the latency**? | derived from `workflow` + cache state | Pre-built/warm = instant paint; real-time = gradient→swap (async); live = blocking (discouraged). The designer must *see* the latency budget before shipping. |
| Q9 | **What's the cost**? | derived from `mode`/`workflow` + `api_costs` ledger | Deterministic text = $0. Generative/image = per-generation cost, keyed by cache_key. Pre-built amortizes; real-time recurs. Shown per section. |
| Q10 | Can I **trace the agent graph** for this decision? | section `agent_graph` (derived) | The "why it decided that" for *this* element: resolve signals → select intent/claims → assemble prompt/plan → **Gate** → cache/serve → receipt. Reuses the observatory node contract. |
| Q11 | Is this workflow **easy to find, follow, understand**? | UX acceptance (not a field) | The product test. A RevOps/marketer persona completes Q1–Q10 for a section without reading code, in one screen, with plain-English labels. |

**Design invariants** (from the pillars, tested on every element): a personalized element **cannot ship anything the Gate blocks** (Art II, structural — the target's variant pool is Gate-cleared, never special-cased); the page is **byte-identical on replay** for a given input (Art IV — pre-built/real-time both cache); every number shown is **from a real run** (Art I).

---

## 2. Worked walkthrough A — Gauntlet, hero sub-headline (deterministic, objection-reframe)

*The operator is Maya, a growth marketer at GauntletAI. She opens the section designer for `gauntletai.com`.*

- **Q1 Which?** The **hero section**. Within it, the **sub-headline** text target. *Why:* the hero is the first thing every visitor reads; the sub is where relevance lands hardest. She leaves the headline generic (proven, high-stakes) and personalizes the sub.
- **Q2 Why this one?** Goal = **reframe the visitor's top objection** before they bounce. *Why:* a cold engineer's #1 doubt ("is a bootcamp worth it vs. self-study?") kills the scroll; naming it converts.
- **Q3 Channel?** `[direct, search, ads]` — anonymous channels. *Why:* she's designing for the *cold* visitor; email/known visitors get a different target. Ads bring `utm_content=vNN` → she can message-match; direct brings only IP tier.
- **Q4 How?** `mode: deterministic`, `workflow: realtime`. *Why:* the reframe is drawn from a **pre-authored objection catalog** (`OBJECTION_CATALOG`), not written live — so it's provable-by-construction and $0. "Realtime" here = filled per request from the catalog, no generation.
- **Q5 Strategy?** `objection-reframe`. *Why:* apt scores the visitor's objection stack (`prioritize_objections`) and inserts the top objection's `reframe` string at `policy: allude`. The strategy picks *which* provable reframe leads.
- **Q6 Guardrails/provenance?** `policy: allude`; `gate: helix_tenant`; the reframe's `blocked_say` recite (the too-strong version) stays console-only. *Why:* alluding to the objection is safe; reciting inferred data about the person is `hold`. The Gate blocks comparatives ("better than a CS degree").
- **Q7 Observe?** The hero section's event ledger shows: objection resolved, reframe selected, policy applied, Gate verdict. *Why:* she can confirm the *right* objection fired for a sample visitor.
- **Q8 Latency?** ~0 ms — deterministic fill, no network. *Why:* text never blocks paint.
- **Q9 Cost?** $0. *Why:* no LLM, no API.
- **Q10 Agent graph?** 5 nodes: `resolve signals → score objections → select reframe → surface-policy Gate → fill slot (+ receipt)`. She clicks a node to see its input→decision→output. *Why:* to defend the choice to a skeptical exec.
- **Q11 Easy?** She did all of the above on the hero card, in the designer, without touching Python. ✅

→ Yields **WF-DESIGN-001** (deterministic objection-reframe text target): assert the shipped sub contains the top objection's `reframe`, `policy=allude`, the `blocked_say` recite is **absent** from the page but **present** in the console, Gate verdict = pass, cost = 0, latency non-blocking, the 5-node graph resolves.

---

## 3. Worked walkthrough B — Gauntlet, hero sub-headline (generative opt-in, Gate-bounded)

*Same target, but Maya wants tighter copy than the catalog offers, for the `ads` channel only.*

- **Q4 How?** She flips the target to `mode: generative`, `workflow: prebuilt`. *Why:* she'll author a **prompt**, apt generates N candidates **offline**, each is **Gate-checked**, the cleared pool is cached and replayed byte-identically (Art IV). Real-time is available but she chooses pre-built for the ad landing (instant + amortized cost).
- **Q5 Strategy?** `authority` — lead with the source-bound proof. *Why:* paid-ad clicks are high-intent; evidence converts them.
- **Q6 Guardrails/provenance?** `gate: helix_tenant`; candidates that name a competitor, use a comparative/superlative, or inline a `hold` fact are **structurally excluded from the pool** (Art II) — she cannot ship them even by choosing them. *Why:* this is the thesis — generation is *bounded*, not free.
- **Q9 Cost?** Per-candidate generation cost (shown from `api_costs`), incurred **once** at pre-build; $0 per visit thereafter.
- **Q10 Agent graph?** 6 nodes: `resolve signals → assemble prompt → generate candidates → **Gate (pool construction)** → select cleared winner → cache/serve (+ receipt)`.

→ Yields **WF-DESIGN-002** (generative Gate-bounded text target): assert **no** candidate that fails the Gate can be served (feed a planted lie / superlative / competitor / hold-fact candidate → 0 servable, mirroring `test_optimizer` P1); assert deterministic replay from cache; assert cost recorded once, $0/visit; assert the receipt lists prompt + cleared claim + cache_key.

---

## 4. Worked walkthrough C — Planet, location line + region image (mixed text+image, drift-sensitive)

*Operator is an ops marketer at planet.com. The section is the hero; it has BOTH a text target (the location line) and an image target (the region backdrop).*

- **Q1 Which?** Hero → text target `hero_location` + image target `hero` backdrop.
- **Q3 Channel?** `[direct, ads]` with IP→region resolution. *Why:* location is an IP signal; it needs region confidence.
- **Q5 Strategy?** `location-relevance`. *Why:* referencing the visitor's region proves Planet understands their world.
- **Q6 Guardrails/provenance?** Text `policy: allude` at **region** scale only — city/exact-site is `hold` (the anti-surveillance ceiling; blocked arm `Ex`). Image guardrails: `tier_gates` (region_mood:1), `must_avoid` a specific asset. *Why:* pinpointing the exact mine is the creepy line apt refuses.
- **Q8 Latency?** Image `workflow: prebuilt` for the top regions (instant); `realtime` fallback for the long tail (gradient→async swap). Text ~0 ms.
- **This section carries the Phase-2 machinery** (§5 of the PRD): a **long-running A/B** over its cleared variants, **drift prevention** (if the region source changes, re-verify only this section's claims → pause the affected variant), and **A/B optimization** (bandit picks the winning cleared variant per segment).

→ Yields **WF-DESIGN-003** (mixed section): assert text stays region-scoped (city/exact-site never ship — reuse `test_location_signal_*`), image respects `must_avoid`, pre-built regions paint instantly, and the section exposes its own A/B + drift + cost.

---

## 5. The generalized E2E suite (derived from the walkthrough)

Each website × each candidate section produces a `WF-DESIGN-*` journey. The suite asserts the **11 questions are answerable in-product** and the **invariants hold**. Layered:

**A. Config-round-trip (unit).** `rules/<tenant>_sections.yaml` ↔ `list_sections(tenant)` round-trips; every current slot + surface is represented; unknown fields rejected.

**B. Designer-render (HTTP TestClient).** For each tenant, the designer renders one card per section; each card exposes Q1–Q10 controls; the staged-diff drawer targets `*_sections.yaml`; **easy-to-find:** the section, its targets, and each setting are reachable without leaving the console (assert selectors present).

**C. Invariant / property (real Gate — Art VII, additive, never weakened).**
- **Gate-bounded (Q6):** for a generative target, a planted lie/superlative/competitor/`hold` candidate is **0-servable** (structural, per Art II).
- **Determinism (Q4/Q8):** same input → byte-identical shipped element (pre-built and real-time both replay from cache).
- **Hold-never-ships:** no `hold` fact on any surface, any channel (reuse `test_hold_facts_never_reach_the_shipped_page`).
- **Provenance (Q6):** every shipped personalized element carries a receipt (source + policy + Gate verdict); nothing renders un-receipted.

**D. Observability / cost / graph (Q7/Q9/Q10).** Each section exposes its event ledger (poll-since-seq), its cost row (from `api_costs`, keyed by cache_key), and a resolvable agent graph (observatory node contract). Numbers computed from a real `scripts.trace`-style run (Art I).

**E. Phase-2 per-decision (see PRD §5).** Each personalized decision exposes: a **long-running A/B** (bandit over its cleared variants), **drift prevention** (source change → re-verify only affected claims → pause variant), **A/B optimization** (winning cleared variant per segment), each with its provenance.

**F. Ease-of-use (Q11) — the product test.** A scripted journey (agent-browser or TestClient) completes "mark a section → add a text target → set channel/strategy/mode/workflow/guardrails → read latency+cost → open the agent graph" **in one screen, with plain-English labels, no code**. Failure = the workflow is hard to find/follow/understand.

---

## 6. Coverage matrix (website × section × the 11 questions)

The suite must cover, per tenant, at least: **hero** (text+image), **prove** (text, social-proof/authority), **challenger** (text, objection-reframe), **compare** (text, guardrail-heavy — where comparatives are blocked), **cta** (text, scarcity-honest); Planet adds **location** (drift-sensitive). Each cell answers Q1–Q11. Gaps in the matrix are the backlog.

---

*Tests derive from this doc. When a `WF-DESIGN-*` scenario is added to `tests/`, cite its step here.*
