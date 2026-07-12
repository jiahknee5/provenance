# Gauntlet Console Handoff

Handoff for agents continuing work on the **Gauntlet personalization demo** — the pixel-faithful `gauntletai.com` replica plus engineer (`/dev`) and marketer (`/dev/business`) decisioning consoles, deployed at **johnnycchung.com/gauntletapt** via Vercel rewrite to Railway.

Read this file first. Do not assume chat history. Always `git status` before editing — concurrent sessions may have uncommitted changes.

---

## 1. Purpose

This project area is a **live, deterministic personalization demo** for GauntletAI:

- **Live replica** — `/gauntlet` (local) and `/gauntletapt` (production portal mount): every copy block is a personalization slot filled from entry channel (UTM/referrer) × IP tier × login/CRM identity.
- **Engineer console** — `/dev`: full decision trace, process map with drill-downs, plain-English story, audit ledger.
- **Marketer console** — `/dev/business`: campaign-ops language, 8-section sidebar, staged YAML config diffs (client-side only), prebuild manifest toggles.
- **Image decisions guide** — `/dev/image-decisions`: educational pipeline doc + Part 6 pre-cached vs live inventory.

No LLM in the copy path. No server-side sessions. State lives in **query params + one cookie** (`gauntlet_email`). Same inputs → same page (CONSTITUTION Art IV).

---

## 2. Page map

Two mount prefixes register identical handlers in `app/gauntlet.py` (`MOUNTS["legacy"]` and `MOUNTS["portal"]`).

| Route (legacy) | Route (portal) | Audience | What it shows |
|---|---|---|---|
| `/gauntlet` | `/gauntletapt` | Visitor / demo | Live personalized replica |
| `/gauntlet/login` (POST) | `/gauntletapt/login` | Visitor | Sets `gauntlet_email` cookie |
| `/gauntlet/logout` | `/gauntletapt/logout` | Visitor | Clears cookie |
| `/dev` | `/gauntletapt/dev` | **Engineer** | Decision trace, process map, plain story, hero image panel |
| `/dev/business` | `/gauntletapt/dev/business` | **Marketer** | 8-section console, staged config diffs, delivery inventory |
| `/dev/image-decisions` | `/gauntletapt/dev/image-decisions` | Marketer / ops | Image pipeline guide (Parts 1–6) |
| `/gauntlet/ad`, `/gauntlet/ad-lp` | `/gauntletapt/ad`, `/gauntletapt/ad-lp` | Demo entry | X ad mockups + 12-variant grid |
| `/gauntlet/direct`, `/gauntlet/email` | `/gauntletapt/direct`, `/gauntletapt/email` | Demo entry | Curated direct + email channel galleries |
| `/apt/demo` | `/apt/demo` | Visitor tour | Demo sitemap — tenant picker + four channel tiles |
| `/apt/dev` | `/apt/dev` | Ops hub | Site picker + console deep-links (marketer card first) |
| `/api/gauntlet/hero-image` | `/gauntletapt/api/hero-image` | Client JS | Async hero generation JSON (hero surface only today) |

**Aliases (legacy mount only unless noted):**

| Alias | Resolves to |
|---|---|
| `/gauntlet/dev/business` | Same as `/dev/business` |
| `/image-decisions` | Same as `/dev/image-decisions` |
| `/gauntlet/image-decisions` | Same as `/dev/image-decisions` |
| `/gauntletapt/image-decisions` | Portal image-decisions (no `/dev` in path) |
| `/ad-lp` | Root alias → legacy `/gauntlet/ad-lp` |

**`as` query param** on `/dev` and `/dev/business`: `as=anon` forces anonymous; `as=known` forces known cohort (cookie or sample email). Preserved across toggles except `as` itself is dropped from cross-links.

**Showcase entry links** (`ENTRY_LINKS` in `app/gauntlet.py`): X ads grid, paid ad, email (with magic token), search, direct — used on the main showcase card (legacy paths).

---

## 3. Architecture

### Request → page

```
HTTP request (query params + Referer + cookie)
    │
    ▼
GS.build_page(request, email=…)
    ├── classify_entry()          → ad | email | search | direct
    ├── scene.resolve_ip()        → tier 0–3, firmographics (allude only)
    ├── identity                  → cohort CRM | work-email domain | anon
    ├── resolve_ad_variant()      → 12 X catalog variants (if paid click)
    ├── audience + objections     → copy slots + blocked say-variants
    ├── IG.resolve_surface_image() × 2  → hero + og (cache check only; no blocking)
    └── trace + ledger + copy_diff
    │
    ├── /gauntlet (replica HTML)     gauntlet_site.html
    ├── /dev                         + GS.process_map(page) + GS.plain_story(page)
    ├── /dev/business                + GDB.build_business_dev_view(page)
    └── /dev/image-decisions         + GID.build_image_decisions_view() (static guide)
```

### Determinism (CONSTITUTION)

- **Art IV** — Every artifact reproducible from inputs + seed. `build_page()` is a pure function of request + email; no RNG, no LLM.
- **Art III** — Demo runs offline without API keys; keys only *upgrade* (image generation, rich profile).
- **Surface policy** — `say` / `allude` / `hold` enforced in `gauntlet_site.py`. Hold facts never reach the shipped replica; blocked say-variants appear only on `/dev` and consoles.

### Staged config vs live writes

| Surface | Editable today | How changes apply |
|---|---|---|
| Image guardrails | `rules/gauntlet_image.yaml` | Staged in marketer console drawer → copy YAML diff → commit → deploy |
| Prebuild manifest | `rules/gauntlet_prebuild.yaml` | Staged toggles in console → edit YAML → `warm_hero_cache` → deploy |
| Copy slot policy | **Code only** (`gauntlet_site.py`) | Console shows **proposals** only — no YAML equivalent yet |

The staged-changes drawer (`#staged-changes` in `gauntlet_dev_business.html`) is **client-side only**. Nothing is saved server-side.

### Process map stages (`GS.process_map`)

11 stages, always visible (skipped stages dimmed): entry → ad variant → IP → tier → identity → archetype → audience → objections → policy → compose → hero image. Each stage has branches (taken path flagged) + `detail` drill-down evidence.

Marketer console adds a 12th workflow node **Image surfaces** (hero + og outcomes) via `GDB._workflow()`.

---

## 4. What was built this session

Chronological summary of the console platform work (verify in git diff — much may be deployed but uncommitted):

1. **Process map + drill-downs on `/dev`** — `GS.process_map()`: inputs panel, 11-stage diagram, expandable `detail` rows with fired markers; template CSS in `gauntlet_dev.html`.
2. **Chapter nav → left sidebar on `/dev`** — Five chapters (visitor, decisions, data, shipped, audit) + cross-links to image-decisions, business view, live page.
3. **Plain-English story + say/allude/hold legend** — `GS.plain_story()`: four beats (arrival, network, identity, what the page did); legend in TLDR panel on both `/dev` and `/dev/business`.
4. **`/dev/image-decisions` route + nav link** — `gauntlet_image_decisions.py` + template; linked from `/dev` sidebar and showcase.
5. **Hero cache warming + `.dockerignore` shipping** — `scripts/warm_hero_cache.py`; `!data/demo/image_cache/**` in `.dockerignore` so pre-generated images ship in the Docker image (Railway FS is ephemeral).
6. **JPEG from API + cache format** — Gemini responses stored as `.jpg` when mime is JPEG (`image_gen.py` ext detection); cache currently ~68 JPG + ~24 PNG on disk. *No explicit recompression step found in repo.*
7. **Part 6 pre-cached vs live on image-decisions guide** — `GID.precached_vs_live()`: decision graph + live disk inventory + ops rule.
8. **Marketer console rebuild (`/dev/business`)** — 8 sidebar sections: Overview, Workflow, Data in, Decisions, Copy, Images (per-surface sub-nav), Guardrails, Delivery. Staged YAML diffs for image rules, tier gates, prebuild flags; copy-policy proposals only.
9. **Multi-image surfaces: hero + og** — `build_page()` resolves `image_surfaces: {hero, og}` with separate cache keys, prompts, and provenance. Console renders one card per surface. **OG is not yet wired into live page `<meta>` tags** — resolved in page dict for console/prebuild only.

---

## 5. Deploy workflow (CRITICAL)

**Production deploys via Railway CLI upload — `git push` does NOT deploy.**

From repo root:

```bash
# 1. Warm cache (needs IMAGE_GEN_API_KEY from Railway env)
railway run python -m scripts.warm_hero_cache

# 2. Deploy (operator workflow — blocks until CI/build completes)
railway up --ci -m "describe the change"

# Retry on timeout — Railway builds can stall; re-run the same command.
```

Alternate script (runs subset of tests first, uses `--detach`):

```bash
./deploy/railway.sh   # pytest gauntlet/planet/hero tests, then railway up --detach
```

**Verify production** (not local uvicorn):

```bash
curl -sI https://johnnycchung.com/gauntletapt/dev?as=anon | head -1
curl -sI https://johnnycchung.com/gauntletapt/dev/business?as=anon | head -1
curl -sI https://johnnycchung.com/gauntletapt/dev/image-decisions | head -1
```

Local preview (`uvicorn app.main:app --port 8099`) is for development only — **not** used for user-facing QA.

**API-key scripts** must use Railway env:

```bash
railway run python -m scripts.warm_hero_cache
railway run python -m scripts.warm_hero_cache --tenant planet
railway run python -m scripts.warm_hero_cache --dry-run   # list states, no API calls
```

`IMAGE_GEN_API_KEY` (or `NANO_BANANA_API_KEY`) must be set in Railway — not committed.

---

## 6. Image cache & prebuild

### Demo state grid

**30 semantic demo states** in `rules/gauntlet_prebuild.yaml`:

- 12 X ad variants (`v01`–`v12`) × `anon` + `known`
- `direct`, `search`, `email` × `anon` + `known`

**2 surfaces** per state: `hero` + `og` → **60 warmed entries** when all `prebuild: true`.

Known identity uses `known_email: maya.chen@gauntletai.com`. Email entry resolves magic token from cohort (`CO.BY_ID["liam"]`).

### Single source of truth

`pipeline/personalization/prebuild.py` loads the manifest. Three consumers must stay aligned:

| Consumer | Role |
|---|---|
| `scripts/warm_hero_cache.py` | Generates images before deploy |
| `/dev/image-decisions` Part 6 | Live cache inventory |
| `/dev/business` Delivery section | Per-state load policy + prebuild toggles |

### Cache location & shipping

- Disk: `data/demo/image_cache/manifest.json` + `images/<sha256-key>.{jpg,png}`
- Served at: `/static/generated/…` (portal: `/gauntletapt/static/generated/…`)
- `.dockerignore` excludes `data/` but **re-includes** `data/demo/image_cache/**` so baked images survive deploys
- Railway runtime FS is ephemeral — anything generated live post-deploy is lost on next deploy unless re-warmed and shipped

### Load policy labels (console + guide)

| Status | Meaning |
|---|---|
| pre-built | On disk + `prebuild: true` → instant, survives deploy |
| warm | On disk from runtime gen → instant until next deploy |
| live | Miss + API key → gradient first, ~30s async gen |
| fallback-only | No API key → gallery (tier≥2 industry) or CSS gradient |

---

## 7. Customization model

### Staged changes drawer (`/dev/business`)

Client-side JS stages copyable diffs for:

| `data-stage` | Target file | Notes |
|---|---|---|
| `must-avoid` | `rules/gauntlet_image.yaml` | Uncheck → remove from `prompt_defaults.must_avoid` |
| `tier-gate` | `rules/gauntlet_image.yaml` | Change `guardrails.tier_gates` levels |
| `prebuild` | `rules/gauntlet_prebuild.yaml` | Toggle `prebuild: true/false` per state × surface |
| `copy-policy` | `pipeline/personalization/gauntlet_site.py` | **Proposal only** — patches say "no YAML equivalent yet" |

### Copy policy — NOT config-driven

Copy `say`/`allude`/`hold` is enforced in Python (`gauntlet_site.py` slot calls). The marketer console lets you stage policy changes but they are **proposals pointing at code**, not editable YAML like images.

**Open follow-up:** `rules/gauntlet_copy.yaml` (or similar) to mirror `gauntlet_image.yaml`.

### Image guardrails (`rules/gauntlet_image.yaml`)

- 7 intents (`peer_proof`, `loss_avoidance`, `authority`, `aspiration`, `roi_clarity`, `retarget_warm`, `message_match`)
- Deterministic `selection.primary_rules` + `fallback_rules` chain
- `surfaces.hero` + `surfaces.og` with distinct prompt openers
- `guardrails.tier_gates`: industry ≥ 2, region_mood ≥ 1
- `brain_simulator.enabled: false` by default (opt-in best-of-N scoring)

---

## 8. Tests

```bash
uv run pytest tests/test_gauntlet_site.py -q    # expect 60 tests
```

### What `test_gauntlet_site.py` covers

| Area | Tests (representative) |
|---|---|
| Entry classification | 4 channels, rule/signals, magic token |
| Personalization | ad campaign hero, tier routing, `?ip=` override |
| Hold invariant | hold facts never on replica; blocked say only on `/dev` |
| Login / identity | cookie unlock, magic token pre-login, work-email escalation |
| `/dev` page | trace stages, panels, toggle, process map, plain story, sidebar |
| Process map | all stages, skipped anon-direct, drill-down evidence |
| Ad catalog | 12 variants, distinct heroes, ad-lp/ad routes, age/gender hold |
| Objections | 15-entry catalog, per-ad surfacing, hold reframes, trace stage |
| Portal mount | `/gauntletapt` hrefs, static prefix, hero API, login/logout |
| Marketer console | routes 200, decisioning language, same state as `/dev`, cross-links |
| Console sections | sidebar 8 sections, workflow branches, multi-surface images, guardrails, staged drawer |
| Prebuild | manifest loads, warm script uses it, delivery inventory |
| Image decisions | routes 200, intents, Part 6 graph, inventory, nav from `/dev` |

### Full suite caveat

```bash
uv run pytest -q   # full suite
```

`tests/test_full_suite.py::test_integrations_show_base_vs_connect` is allowed to fail independently (integrations help page) — not a Gauntlet regression signal.

Pre-deploy script in `deploy/railway.sh` runs: `test_brain_simulator`, `test_gauntlet_site`, `test_hero_image`, `test_planet_site`, `test_planet_hero_image`.

---

## 9. Open follow-ups (prioritized)

1. **Copy policy YAML** — Make copy guardrails editable like image (`rules/gauntlet_copy.yaml`); wire staged drawer to real patches.
2. **Third image surface** — Section backdrop, email hero (extend `surfaces` in `gauntlet_image.yaml` + prebuild manifest).
3. **Per-surface async API routes for og** — Today only `/api/gauntlet/hero-image` exists; og resolves at `build_page()` cache-check time. Add `/api/.../og-image` if live page needs async og.
4. **Wire og into live page HTML** — `og_image` is in page dict but `gauntlet_site.html` has no `og:image` meta yet.
5. **NEvo-inspired saliency QA (offline only)** — See `docs/research/nevo-image-research.md`; candidate brain-region scoring, not conversion claims. `brain_simulator` module exists; disabled in `gauntlet_image.yaml`.
6. **Commit/sync** — At handoff time, modified but uncommitted: `gauntlet_dev_business.html`, `gauntlet_site.py`, `gauntlet_dev_business.py`, `image_gen.py`, `test_gauntlet_site.py`, plus Planet parallels. Many `.qa/` screenshots and `data/demo/image_cache/` images are untracked. Deploy via `railway up` may be ahead of git.
7. **Concurrent Cursor sessions** — Always `git status` + read this handoff before editing; do not assume your branch matches production.

---

## 10. Key files quick reference

| Path | Role |
|---|---|
| `app/gauntlet.py` | Routes, mounts, render helpers, hero API |
| `app/templates/gauntlet_dev.html` | Engineer console UI |
| `app/templates/gauntlet_dev_business.html` | Marketer console UI + staged drawer JS |
| `app/templates/gauntlet_image_decisions.html` | Image guide template (Part 6) |
| `app/templates/gauntlet_site.html` | Live replica (hero background + async API hook) |
| `pipeline/personalization/gauntlet_site.py` | `build_page`, `process_map`, `plain_story`, ad catalog |
| `pipeline/personalization/gauntlet_dev_business.py` | `build_business_dev_view`, console sections |
| `pipeline/personalization/gauntlet_image_decisions.py` | Image guide view model |
| `pipeline/personalization/image_gen.py` | Cache, prompts, surfaces, async resolve |
| `pipeline/personalization/prebuild.py` | Manifest loader (shared with warm script + consoles) |
| `rules/gauntlet_prebuild.yaml` | 30 states × 2 surfaces prebuild manifest |
| `rules/gauntlet_image.yaml` | Intents, guardrails, surface specs |
| `scripts/warm_hero_cache.py` | Pre-deploy cache warmer |
| `tests/test_gauntlet_site.py` | 60 integration tests |
| `.dockerignore` | Ships `data/demo/image_cache/` inside image |
| `deploy/railway.sh` | Test-gated deploy helper |
| `RUNBOOK.md` | General provenance demo ops (§ Gauntlet hero images) |
| `CONSTITUTION.md` | Art I–V inviolable guardrails |
| `docs/research/nevo-image-research.md` | NEvo saliency research (reference only) |

---

## 11. Production URLs to verify

Base: **https://johnnycchung.com/gauntletapt**

| URL | Check |
|---|---|
| `/gauntletapt` | Replica loads; login form posts to `/gauntletapt/login` |
| `/gauntletapt?utm_source=x&utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09` | Ad message-match hero |
| `/gauntletapt/dev?as=anon` | Process map, plain story, sidebar |
| `/gauntletapt/dev?as=known` | CRM path, Maya welcome-back copy |
| `/gauntletapt/dev/business?as=anon` | 8-section marketer console |
| `/gauntletapt/dev/image-decisions` | Part 6 inventory counts |
| `/gauntletapt/ad-lp` | 12-variant X ads grid |
| `/gauntletapt/api/hero-image` | JSON `{status, url, receipt}` |

Cross-links to verify: `/dev` → Image decisions, Marketing view; `/dev/business` → Technical view; showcase → `/dev` + `/image-decisions`.

---

## Cautions for the next agent

- **Do not run image generation APIs** unless explicitly warming cache for deploy (`railway run …`).
- **Do not modify application code** when only updating docs — but do read git status.
- **Do not commit** unless the user asks.
- Local tests use offline IP (tier 0); use `?ip=` query param in tests/pages to exercise corporate tiers.
- `RUNBOOK.md` paths reference `~/projects/lyso/provenance` — this repo is `~/projects/provenance`; commands are otherwise the same.

---

*Handoff written 2026-07-10. Regenerate or extend when major console features ship.*
