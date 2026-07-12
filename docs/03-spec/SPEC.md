# Provenance — Technical Spec (derived)

> Companion to `docs/01-intake/PRD-derived.md`. Drives the restructure build (Phases 2–5).
> Principle: **restructure on the engine** (R22) — reuse the pipeline, rebuild the product/UI layer.

## A. Architecture (what we keep vs. build)

**Keep (the engine — untouched logic):**
- `pipeline/gate/*` — claim Gate (decompose → retrieve → NLI + ensemble → rules).
- `pipeline/optimizer/*` — `ThompsonBandit`, reward `oracle`, `campaign`, `ActionPool`/`PosteriorStore`.
- `pipeline/drift/monitor.py` — source-change → re-verify → pause/unblock arms.
- `pipeline/assurance/*` — adversarial traps + reliability harness.
- `pipeline/enrichment/*`, `pipeline/personalization/*`, `pipeline/customer/*`, `pipeline/common/*`.
- The provenance ledger (profiles + fact receipts), the observe stream.

**Build (the product/UI layer):**
- `app/templates/base.html` → the Quiet-Workspace **shell** (sidebar + topbar + ⌘K). One token set in `app/static/atlas.css` `:root`.
- `app/agent.py` + `pipeline/agent/*` — the deterministic navigator (intents over engine state).
- Restructured surfaces (PRD §5) as thin view layers over existing pipeline data.
- `app/static/icons.js` — Phosphor (web font or inline SVG sprite, MIT).

## B. Design tokens (Quiet Workspace — from `insp-attio`, real values)

```css
:root{
  --paper:#FFFFFF; --ink:#1A1C20; --slate:#2E353D; --muted:#6B7480; --label:#9AA6B4;
  --hairline:#E5E9EF; --border:#C9D2DC; --fill:#F1F3F5; --cta:#1B1E23;
  --signal:#2E6FF5;                 /* the ONE product accent (primary actions) */
  --v:#6B4BD6;--vbg:#F4F1FE; --a:#B5731B;--abg:#FEF4E8; --g:#1E8A53;--gbg:#EAF7EF; --bbg:#EAF1FE; /* tag tints */
  --r-btn:10px; --r-card:14px; --r-pill:7px;
  --ease:cubic-bezier(.2,0,0,1); --t:.28s;
  --font-display:"Inter Display",Inter,system-ui,sans-serif;
  --font-ui:Inter,system-ui,sans-serif; --font-serif:Newsreader,Georgia,serif;
}
```
**Type scale:** display 600 (H1 48–64/lh1.0/-0.032em, H2 28–32, H3 18–20); UI 400/500 @ 13–16 (-0.01em); label 600 12 uppercase +0.06em `--label`; serif for pull-quotes only.
**Components (canonical):** button (ink / outline / signal, 10px), pill-eyebrow, tag-pill (tint+dot), record-table, sidebar-nav-item, workspace-switcher, underline-tabs, command-palette, stat/trust card. Each defined once in `atlas.css`; pages compose, never restyle.
**Shell contract:** every navigable page `{% extends "base.html" %}` and renders into the record-first main; no page sets its own `max-width`/palette (the UI-consistency test asserts this).

## C. Deterministic agent (R23)

A navigator over engine state — **no LLM by default**. Lives at ⌘K (palette) + a right-side panel.

- **Intents** (deterministic handlers, each returns structured result + provenance):
  - `why-did-variant-win(segment)` → reads `PosteriorStore` + oracle → winner, posterior, the data that drove it, "blocked arm never selected" proof.
  - `optimize(segment|all)` → runs/extends a bandit campaign → reports lift toward KPI.
  - `explain-metric(kpi)` → drills a KPI to its source records (provenance).
  - `check-claim(text)` → runs the Gate → say/allude/hold verdict + source.
  - `drift-status()` / `assurance-status()` → current watch + trap catch-rate.
  - `find-record(query)` / `go(surface)` → navigation.
- **Surface:** results render as cards with a "show provenance" expander. Guided flows = chained intents ("tune this segment" → optimize → why-won → apply).
- **LLM layer (opt-in, key-gated):** if `ANTHROPIC_API_KEY` set, a thin NL→intent router maps free text to the deterministic intents (the intents still do the work + carry provenance). Default OFF; tests run with it off.
- **API:** `GET /api/agent/intents`, `POST /api/agent/run {intent, args}` → `{result, provenance[], followups[]}`.

## D. Minimalist Assurance + Drift (R26)

One surface, three numbers + one live list:
- **Trust score** (composite of trap catch-rate + provenance coverage + 0 hold-in-copy).
- **Drift watch**: TTL-governed facts; any stale/retracted → the paused variant(s) listed with the source that changed. Reuses `pipeline/drift/monitor.py` + `ActionPool.pause`.
- **Hallucination/overclaim**: trap catch-rate (assurance harness) + "ungated arms selected: 0".
No charts-for-charts'-sake; quiet cards in the Quiet-Workspace style.

## E. Tests — multi-user matrix (Phase 5 acceptance)

`tests/test_restructure.py` (+ existing suites stay green). Deterministic, offline.

| ID | Persona | Test | Asserts |
|---|---|---|---|
| T-P1a | Renata | metric → record drill | every KPI leaf resolves to ≥1 sourced record |
| T-P1b | Renata | agent `why-did-variant-win` | returns winner + posterior + provenance; names the blocked arm |
| T-P2a | Sam | composer sends clean copy | passes the Gate |
| T-P2b | Sam | composer blocks a `hold`/unverified fact | send refused with a reason (the creepiness invariant) |
| T-P3a | Maya | bandit converges | learned winner == honest best arm per segment |
| T-P3b | Maya | blocked/ungated arm | selected 0× (provable, not filtered) |
| T-P4a | Liam | set source TTL → expire | Drift pauses the dependent variant(s) |
| T-P4b | Liam | re-clear source | Drift unblocks; arm returns to pool |
| T-P5a | Dr. Chen | assurance panel | renders trust score + drift + trap catch-rate; coverage==100% |
| T-P6a | Visitor | demo renders | /demo + /demo/monitor 200, provenance present |
| T-INV1 | all | provenance completeness | no surface renders a fact without a source |
| T-INV2 | all | no-hold-in-copy | no rendered copy contains a `hold` fact |
| T-UI1 | all | shell extension | every navigable template `extends base.html` |
| T-UI2 | all | token discipline | no template defines an off-system color / rogue `max-width` outside tokens |
| T-DET1 | all | determinism | byte-identical baked artifacts at the seed on re-run |

**UI-consistency harness** (`scripts/ui_consistency.py`): renders every navigable route, asserts (a) it includes the shell markers, (b) computed palette ⊆ token set, (c) one type family, (d) buttons use `--r-btn`. The `/loop` runs build → tests → this harness until all green.

## F. Phase plan (file-level)

- **P2:** rewrite `base.html` + `_nav.html` → shell; consolidate `atlas.css` tokens; add Phosphor; migrate each surface template to the shell (form, records, composer, optimizer, assurance, catalog, demo).
- **P3:** `pipeline/agent/intents.py` + `app/agent.py` + `agent.html` panel + ⌘K.
- **P4:** `app/assurance.py` minimalist view wired to drift + harness.
- **P5:** `tests/test_restructure.py` + `scripts/ui_consistency.py`; run the loop.
- **P6:** deploy (operator go).
