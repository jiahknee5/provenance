# Deployment vs Spec/PRD — Review Ledger (append-only)

> Loop artifact: each iteration appends ONLY new/changed/resolved findings. Spec: `04-spec/spec.md` · PRD: `docs/01-intake/PRD-SECTION-DESIGNER.md` · Tasks: `.rapid/TASKS.json`.

## Baseline — 2026-07-12T04:2x UTC (iteration 1)

**Prod state:** all 12 apt-plane surfaces 200 with the shell, zero legacy chrome; replicas correctly shell-free; the legacy plane is **unreachable from the prod domain** (Vercel rewrites only the apt paths — 404s), so R38 is *prod-clean but code-dirty*.

| Req | Requirement | Prod status | Gap | Sev |
|---|---|---|---|---|
| R39/S0.1 | Cohesion: one design, no legacy chrome, zero orphans | 12/12 apt surfaces shell-clean; legacy 404 from prod; `/` → 307 (portal home) | Code still carries legacy routes/templates (Railway upstream + base.html) — retirement is T-09 work, invisible to prod users today | MED (code) / LOW (prod) |
| R30 | Section registry served | absent (no `_sections.yaml` markers) | **OPEN — T-01 not built** | HIGH (planned) |
| R31 | Generative text mode | absent | OPEN — T-05 | HIGH (planned) |
| R32/R33 | Designer UI (`sd-*` testids) | absent on /dev/business | OPEN — T-03/T-04 | HIGH (planned) |
| R34 | Per-decision pillar stack panels | absent (A/B+drift per section) | OPEN — T-02/T-04 | HIGH (planned) |
| R35 | Real-time image gen funded+wired | **RESOLVED**: key in prod env; validated call cost-logged $0.039 | — | ✅ |
| R35a | Every image call cost-logged | **HOLDS in code + live** (`_call_image_api→record_call`, incl. 429 path); regression test pending (T-06) | test not yet locked | LOW |
| R36 | SkyFi tenant | `/skyfiapt` **404** | OPEN — T-07 | HIGH (planned) |
| R37 | 30-example matrix | 13 scenarios live (old catalog); 30-row WF-DESIGN absent | OPEN — T-08 | MED (planned) |
| R38 | Single design / retire legacy | prod-clean (legacy 404 via portal); code retains ~30 routes + base/_nav chrome | OPEN — T-09 (code-side) | MED |

**Verdict:** deployment matches everything shipped so far; all OPEN gaps are exactly the planned build waves (W0–W5) — no *unplanned* drift found. Next check: after any wave deploys.

## Iteration 2 — 2026-07-12T06:3x UTC
Zero prod changes since baseline (canaries: /apt/demo 200+shell, /skyfiapt 404, /costs 200+shell). Expected — waves W1/W2 are building locally (T-00/T-01/T-02 merged on branch, gate 283; not yet deployed). No new/changed/resolved gaps. Next material check: after the W5 deploy (or any interim wave deploy).

## Iteration 3 — 2026-07-12T08:1x UTC
Zero prod changes (2nd consecutive) — /apt/demo 200, /skyfiapt 404 (R36 open on prod), designer sd-* not yet deployed (expected). Local build far ahead: W1 complete + T-05 merged (gate 370, origin c16ce1f) — prod deploy comes at W5/T-10. Lengthening loop wait per pacing rule.
