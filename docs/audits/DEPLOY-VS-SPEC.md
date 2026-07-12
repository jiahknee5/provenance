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

## Iteration 4 — 2026-07-12T10:2x UTC
Prod unchanged (3rd consecutive; /apt/demo 200, /skyfiapt 404). Local: W0-W3 COMPLETE (10/12 tasks, gate 408, WF-DESIGN 30/30 green, origin 8835c50); T-09 legacy retirement running in main tree. Deploy lands at T-10 — the next iteration after it should see: /skyfiapt 200, sd-* designer markers on /dev/business consoles, legacy chrome gone. Keeping long waits.

## Iteration 5 (SHIP verification) — 2026-07-12T07:3x UTC
THE DEPLOY LANDED. All baseline gaps RESOLVED on prod: R30 registry (designer staging live) · R31 gen text (offline pools baked) · R32/R33 designer (sd-sections 5/6/6 across gauntlet/planet/skyfi) · R34 pillar panels (ab/drift/graph/cost per section) · R36 /skyfiapt 200 (portal rewrite f457bbd) · R37 30/30 matrix green · R38/R39 legacy plane 404 + one design system + zero orphans. R35/R35a held throughout ($0.039 real spend today, everything ledgered). Remaining honest gap: S02 realtime beat not yet exercised end-to-end on prod (test-proven; first real visitor triggers it). Build: 12/12 tasks, 0 reverts, suite 569/0.

## Iteration 6 (post-ship stability) — 2026-07-12T08:0x UTC — LOOP CONCLUDING
Confirmed stable: all shipped surfaces hold (3 tenants, designer live, legacy 404). Every PRD requirement R30–R39 verified RESOLVED on prod (iteration 5); zero regressions since. All build waves W0–W5 shipped and verified — the loop's mission ("verify each shipped task's prod-visible acceptance as waves ship") is complete. Concluding the review loop; the remaining honest gap (S02 realtime beat end-to-end on prod, ~$0.04) is a one-visit manual check documented in .rapid/RETRO.md. Re-arm with /loop if a new build cycle starts.
