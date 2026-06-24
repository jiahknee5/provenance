# Plan — Ground the whole app to the provenance spine, make it fully functional & on-design

> Status: in execution via `/loop`. This is the grounding doc — every page/section maps to a pillar below.

## Context
Is the overall objective defined? **Yes — crisply and consistently.** Verbatim, across docs:

- README: *"Provable ultra-personalization — outreach that can't say anything it can't prove, and optimizes itself inside the truth."*
- PRD-derived §1: *"Provenance is the GTM workspace that can prove every move… every AI-driven action carries its source, its lawful basis, and its surface policy… 'don't ship what you can't prove.'"*
- CONSTITUTION: *"can't say what it can't prove"* (inviolable).
- Competitive: *"None withholds an unprovable claim by construction. None shows a receipt."* → move #2: *"Lead every demo with the receipt."*

**Pillars:** Provable · Optimizing · Watched · Quiet. **Personas P1–P6** each map to a surface.
The spine exists; the gap is that the **UI doesn't yet visibly enforce it**: dead buttons, a
non-functional ⌘K, `/demo` + `/demo/monitor` + ~10 legacy pages on the old dark theme, and — most
important — **no variant→source "receipt" drill-down** (every variant injects at the same `<body>`
top; no per-variant placement, so you can't see where a variant maps on the site).

Decisions: **migrate everything** to one Quiet-Workspace app; **make CRUD buttons functional**.

## Objective spine (every section maps to one pillar)
| Pillar | Surfaces it owns | "Proves:" line each page leads with |
|---|---|---|
| Provable | Records/Workspace, Composer, Sources, Demo receipt | every fact carries source + basis + policy |
| Optimizing | Optimizer, KPI monitor | the bandit can only win with verified variants |
| Watched | Assurance, Drift, monitor trust-rails | drift re-verifies; traps catch overclaim |
| Quiet | the shell itself, Agent (navigator-not-dashboard) | color only in data; deterministic agent |

## Phases
0. **Spine doc** — this file.
1. **⌘K palette** — functional command palette in `shell.html` (open ⌘K, filter surfaces, ask-agent route).
2. **Dead buttons + alignment** — wire Workspace/Records Filter/Sort/Refresh (server-side params) + create-record (`POST /records/new`); make Composer "Try it" examples clickable; add "Proves:" page-heads + pillar-tagged section eyebrows on the 7 shell surfaces.
3. **Variant receipt drill-down** — add `placement` to `Variant`; parameterize `cloner.py` injection by placement with numbered ①②③ markers; `demo.html` Receipt rail (region → change → data used → KPI → provenance).
4. **KPI monitor restyle** — `demo_monitor.html` → shell + quiet.css.
5. **Migrate legacy** — Lab nav group in shell, retire `_nav.html`, migrate all legacy templates to shell + quiet.css token map; fix 2 `href="#"` CTAs.
6. **Full test suite + ship** — build a comprehensive suite (every route 200; functional link/button audit = zero dead targets; ⌘K items resolve; create-record persists & appears; filter/sort/view params work; composer gate; variant drill-down has `placement` + per-placement injection + receipt + blocked-never-selected; provenance INV; persona P1–P6 journeys; UI consistency across all surfaces; `_nav.html` retired). Run pytest + `ui_consistency` green; Playwright click-through + screenshots; push gitlab+origin; Railway deploy; verify live.

## Token map (atlas → quiet), applied to every migrated template
`--panel`→`#fff` · `--panel2`→`var(--fill)` · `--line`→`var(--hairline)` · `--mut`→`var(--muted)` ·
`--accent`→`var(--signal)` · `--radius`→`var(--r-card)` · `--say`→`var(--g)` · `--allude`→`var(--a)` ·
`--hold`→`var(--r)` · `--green`→`var(--g)` · `--amber`→`var(--a)` · `#04222a`→`#fff` ·
accent/green/amber rgba tints→`var(--bbg)/--gbg/--abg/--rbg` · chart `stroke=var(--accent)`→`var(--signal)`.

## Loop exit criteria (all true)
1. No dead `<a>`/buttons; ⌘K works; create-record + filter/sort/refresh work; variant drill-down maps + shows the receipt.
2. One design system everywhere — `_nav.html` retired; `ui_consistency` PASS across all surfaces; no off-token 6-digit hex in templates.
3. Every page leads with its "Proves:" tie and pillar-tagged sections.
4. **The full test suite passes** — comprehensive coverage (all routes 200, functional link/button audit with zero dead targets, ⌘K resolves, create-record persists, filter/sort/view, composer gate, variant drill-down `placement`+injection+receipt+blocked-never-selected, provenance INV, persona P1–P6, UI consistency across all surfaces, `_nav.html` retired). No weakened tests.
5. Playwright click-through clean (screenshots captured).
6. Pushed to gitlab + origin and deployed to Railway; live URLs verified.
