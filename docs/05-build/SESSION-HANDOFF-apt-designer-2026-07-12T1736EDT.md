# SESSION HANDOFF — apt section-designer build + W6/W7 polish

**Session:** apt-designer · **Written:** 2026-07-12T1736EDT · **Branch:** `deploy/railway` (== origin, HEAD `7bd11b0`)
**Resume prompt:** `Read the latest SESSION-HANDOFF-*.md. git status. Continue Next #1.`

---

## TL;DR for the next session

The product is **apt** (renamed from Provenance): a marketer platform — "personalization that proves every word." This session ran the full RAPID build of the **Section Personalization Designer** (12 tasks, zero reverts) plus two polish waves (W6, W7). **Everything is deployed and verified on https://johnnycchung.com.** Suite: **610 passed, 0 failed** (whole `tests/` dir, single process). Local == origin.

## What exists now (all LIVE on prod)

- **3 tenants** (config-driven): `gauntlet`, `planet`, `skyfi` (new — replica + real logo SVGs + cohort + basin-scale/declared-AOI guardrails). Mounts: `/{tenant}apt/*` portal + legacy local paths.
- **Section registry** `rules/<tenant>_sections.yaml` + `pipeline/personalization/sections.py` — THE data model: page sections → 0..n text targets + 0..n image targets (mode deterministic|generative, workflow prebuilt|realtime, policy say/allude/hold).
- **Per-decision pillar stack** `decision_pool.py` — Gate-cleared pool + Thompson A/B (segment=audience_route, `_all` fallback <30) + surgical drift pause + receipts. Proven: 0-lie-servable, lift>control.
- **Designer UI** (marketer consoles ×3): one collapsible card per section, sd-* DOM contract (`04-spec/contracts/designer-dom.md`), staged YAML drawer (client-side; nothing saves live), per-section agent graph/evals/observe/A-B/drift/cost from REAL data. Dev/audit toggle folds engineer trace.
- **Generative text lane** `generative_text.py` + `scripts/warm_copy_cache.py` — prompt → candidates → real Gate → cleared pool → cached ($0 offline default; Anthropic cost-logged if keyed).
- **Image lane**: registry-driven surfaces; prebuild caps K=8/target, 24/tenant, 80 global (warm script `--check` fails deploy gate on violation, wired into `deploy/railway.sh`); realtime Nano Banana ~2s gradient→swap, $5/day/tenant ceiling (`APT_REALTIME_CEILING_USD`), **every call cost-logged** (R35a — incl. 429s).
- **30-scenario WF-DESIGN matrix** (10/tenant, all channels) — locked harness `tests/test_wf_design_matrix.py`, 30/30 green.
- **Navigation**: marketer IA (Campaigns / Personalization / Results / Your website), collapsible groups + nested Channels clusters (Direct / Search / Social ads X·Meta·LinkedIn-planned / Other ads-planned / Email — presence-driven from scenarios), Playbook item, website dropdown + "Add new website" onboarding stub.
- **Playbook** `/apt/playbook` — 4 chapters from live config: images (intents + predicted-NOT-measured labeling), copy (5 persuasion strategies), animated (FUTURE RELEASE, grounded in planet motion), AEO (ROADMAP/POV — "proof is the ranking function"). Customize chips on every block.
- **Unified X-ads grid** `ads_grid.html` (one template, 3 tenants, per-brand tokens; planet `/ads-lp` → 302). Per-variant six-beat "The thinking" explainers (`ad_explainers.py`) on grids + two-column single-ad pages.
- **Logo v2**: "checked-a" monogram (counter of the `a` IS a checkmark) + custom wordmark; `app/static/apt/` + `BRAND.md`; v1 diamond + alternates in `concepts/`. Inlined in `_apt_sidebar.html`; favicons in `_apt_shell.html`.
- **Mobile**: 25/25 routes overflow-clean at 390px; details-based mobile menu; desktop byte-identical. Portal-prefixed static now served in-app (`app/server.py` mounts) — no more local-only 404s.
- **Legacy plane RETIRED** (T-09): ~38 routes gone, `base.html`/`_nav.html` deleted; exceptions kept for property tests (`/lead`, `/submit`, `/site/<token>`, showcase index) — see `docs/RECONCILIATION.md`.
- **Showcase video** (W6-D): `video/apt-showcase/` — 78.5s draft render at `renders/apt-showcase-verify.mp4`, delivered to operator. `video/` is git+railway ignored (1.5GB).

## The contract corpus (read before touching anything)

- `docs/01-intake/PRD-SECTION-DESIGNER.md` — R30–R39 locked decisions (R39 cohesion is the organizing objective; R38 single design; R35a cost-logging invariant)
- `04-spec/spec.md` — S0–S8 + traceability matrix + wave execution plan
- `04-spec/contracts/` — registry-schema · decision-pool · designer-dom (pinned seams)
- `docs/04-workflow/SECTION-DESIGNER-{WALKTHROUGH,EXAMPLES}.md` — the 11-question operator model + 30-row matrix
- `.rapid/` — TASKS.json (all done), MEMORY.md (full build log), RETRO.md (morning report), EVAL/ (locked)
- `CONSTITUTION.md` — Articles I–V inviolable. **Art VII: locked tests** = the 5 property tests, `test_wf_design_matrix.py`, the harness. NEVER edit; architecture-updates to other tests need documented reasons.

## Hard-won gotchas (do not relearn these)

1. **Deploy = `railway up --ci` retry loop** (NEVER `| tail` inside the `if` — pipes mask exit codes; that bug shipped a fake success once). CLI must be ≥5.x (`brew upgrade railway` fixed 30 consecutive timeouts — 4.43's upload path is dead). Verify PROD MARKERS after deploy, never trust deploy logs.
2. **`git push` does NOT deploy.** Vercel portal (`~/johnnycchung-portal/next.config.js`) rewrites `/{tenant}apt/*` + `/apt/*` + `/costs` + `/observatory` + `/api/observe/*` → Railway; new top-level paths need a rewrite + portal push (auto-deploys).
3. **Tests never write the prod cost ledger** — autouse fixture in `tests/conftest.py` isolates `api_costs.LEDGER_PATH` (R35a logs fake test calls too; unisolated suites trip the S3.3 ceiling — this failed the P6 gate once, root-fixed).
4. **Worktree agent pattern**: spawn with `isolation: worktree`, brief includes BASE GUARD (`git merge deploy/railway` if key files missing), commit on-branch only, orchestrator merges sequentially with whole-suite gate between merges, cleans worktrees after. Common rules: `.rapid/prompts/_w1_common.md`.
5. **Nano Banana key** in `.env` + Railway (`IMAGE_GEN_API_KEY`); gemini-2.5-flash-image default; $0.039/gen. Real spend to date ≈ $0.08. Global ceiling default $10/day was a logged interpretation — operator never set one.
6. **Jinja**: `grp.items` = dict method, use `grp['items']`; autoescape mangles quoted font tokens in `<style>` (use `|safe` on server-authored tokens only).

## In progress / open items (Next)

1. **NEXT #1 — Exercise the S02 real-time beat end-to-end on prod** (~$0.04): visit `https://johnnycchung.com/skyfiapt?ip=68.2.45.10` logged in as `rhea.calder@copperlineresources.com`, watch gradient→swap, confirm ledger row. (Test-proven + key-validated; never run live on prod.)
2. **Video finals**: human listen of the audio mix; full-quality render: `cd video/apt-showcase && HYPERFRAMES_SKIP_SKILLS=1 npx hyperframes render . --output renders/apt-showcase.mp4 --quality high --fps 30`. Studio: `npx hyperframes studio` → `#project/apt-showcase`.
3. **LinkedIn ads platform** — top roadmap rec (3 B2B tenants); slots into the X-ads machinery. Currently a "planned" chip in Channels.
4. **Gold receipt-dot** (`concepts/w7c-signed-a.svg` + v1 concept-2) as secondary brand motif for decks.
5. **Deferred long-tail**: skyfi hero-image single-ad page uses the 6-variant catalog; playbook could gain per-tenant deep-links from scenario cards; `/api/api/hero-image` double-prefix alias quirk (documented, harmless).

## Do not touch

- `tests/test_wf_design_matrix.py`, the 5 property tests, `.rapid/EVAL/` (Art VII locked)
- `rules/gauntlet_prebuild.yaml` caps without running `warm_hero_cache --check`
- The replicas' external styling (they must look like the real brands, not apt)
- `video/` (1.5GB, owned by the video pipeline; ignored by git+railway)

## State snapshot

- Suite: 610 passed / 0 failed (whole dir) · WF-DESIGN 30/30 · caps check OK
- Prod: all surfaces 200; logo v2 + mobile + playbook + grids verified live 2026-07-12T19:07Z
- Ledgers: `docs/audits/DEPLOY-VS-SPEC.md` (deploy-vs-spec review, concluded), `docs/audits/FONTS.md`, `.rapid/COHESION.md`, `.rapid/RETRO.md`
