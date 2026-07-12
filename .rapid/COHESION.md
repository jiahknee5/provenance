# S0.1 Cohesion sweep — T-09 single-design-retire-legacy

**Date:** 2026-07-12 · **Branch:** deploy/railway · **Verified by running** (TestClient
drive + full gate + whole `tests/`), not inspection.

## 1. The sidebar map (the IA every route must hang off)

`_apt_sidebar.html` (rendered by `console_shell_ctx` / `demo_nav` on every apt-shell page):

| Sidebar item | Route |
|---|---|
| Website switcher (gauntlet / planet / skyfi / + add new) | `/apt/demo?site=<t>` · `/apt/demo?site=new` |
| Channels | `/apt/demo` |
| Consoles | `/apt/dev` |
| Observatory | `/observatory` |
| Costs | `/costs` |
| Open replica | `/<mount>` (gauntletapt / planetapt / skyfiapt) |

Tenant switcher: identical on every shell page (same `console_shell_ctx` context builder —
single source of truth). Verified: `/apt/demo`, `/apt/dev`, `/observatory`, `/costs` all
render the same `_apt_sidebar.html` partial.

## 2. Route inventory (`app/*.py` sweep, 2026-07-12) — zero orphans

95 registered routes (excluding FastAPI built-ins `/docs`, `/redoc`, `/openapi.json`,
`/docs/oauth2-redirect` and the two `/static*` mounts).

### Sidebar-direct (apt shell)
`/apt/demo`, `/apt/dev`, `/observatory`, `/costs` — the four sidebar items.

### Reachable from sidebar surfaces (1 hop)
- `/apt/mockups`, `/apt/mockups/{name}` — design-exploration gallery, linked from
  `/apt/dev` ("UI mockups gallery →"; link added by this sweep — was the one orphan found).
- Channel galleries per tenant: `/{gauntletapt,planetapt,skyfiapt}/{direct,email}`,
  `/gauntletapt/ad-lp`, `/planetapt/{ads,ads-lp}`, `/{gauntletapt,planetapt}/ad` —
  linked from the `/apt/demo` sitemap cards.
- Consoles per tenant: `/{mount}/dev`, `/{mount}/dev/business`,
  `/{gauntletapt,planetapt}/dev/image-decisions` — linked from `/apt/dev` cards.
- Hero APIs (JSON, fetched by replica pages): `/api/{gauntlet,planet,skyfi}/hero-image`,
  `/{mount}/api/hero-image`.

### Replica plane — EXEMPT (external-styled by R38 exception)
`/gauntletapt`, `/planetapt`, `/skyfiapt` + the legacy mounts `/gauntlet`, `/planet`,
`/skyfi` (both mounts are pinned by the locked gate suites), their `login`/`logout`
routes, and the X-ads mockup pages (`/planetapt/ads`, `/gauntletapt/ad-lp`, `/{mount}/ad`).
These must look like the external sites being demoed, not the apt product.

Gate-pinned legacy aliases (locked suites assert 200): `/ad-lp`,
`/gauntlet/dev/business`, `/image-decisions`, `/gauntlet/image-decisions`,
`/gauntletapt/image-decisions`, `/planet/image-decisions`, `/planetapt/image-decisions`,
`/dev`, `/dev/business`, `/dev/image-decisions` (root-mount console aliases).
Pre-existing quirk, unchanged: `/api/api/hero-image` (double-prefix legacy bookmark alias
generated for the portal mounts — "kept for bookmarks/tests" in `gauntlet.py`/`planet.py`).

### JSON APIs (not pages; consumed by kept surfaces/tests)
`/api/observe/{events,nodes,evals,meta,enrichment,profiles}` (observatory),
`/api/costs` (costs dashboard + `test_api_costs`), `/api/persuasion/{strategies,plan}`
(persuasion engine API).

### Kept exceptions (logged in docs/RECONCILIATION.md §R38)
- `/` → 307 `/apt/demo` (redirect; the sitemap owns the front door).
- `/showcase` (index only) — pinned by the locked gate suites
  (`test_{gauntlet,planet}_site.py::test_showcase_card_publishes_the_entry_links`);
  trimmed to the two replica cards; reachable from the ad-gallery footers and links
  back to `/apt/demo` + `/apt/dev`.
- `/lead`, `/submit`, `/site/{token}`, `/site/{token}/cta` — property T4's surface
  (`test_website.py`, LOCKED) + the live-optimizer online serving path; external-styled
  (Helix Analytics), standalone templates, no legacy chrome. Reachability: this is a
  magic-link plane (tokens are minted by `/submit`), documented here as the T4 exception.

**Orphan count: 0.**

## 3. No legacy chrome served — grep proofs

```
$ grep -rn "base.html\|_nav.html\|shell.html\|_demo_flow" app/ --include="*.py" --include="*.html"
(no matches — files deleted: app/templates/{base,_nav,shell,_demo_flow}.html)

$ grep -rln "extends \"base.html\"" app/templates/
(no matches — form/thanks/site/site_cta/gauntlet_image_decisions/planet_image_decisions
 converted to standalone documents)
```

Runtime check (TestClient): `/lead`, `/showcase`, `/observatory`, `/costs`,
`/gauntletapt/image-decisions`, `/planet/image-decisions`, `/site/<token>` — all 200,
none contain the legacy nav markers.

## 4. Retired routes return 404 — verified by driving

38 retired routes/APIs checked, **all 404**: `/workspace`, `/records`, `/records/new`,
`/demo`, `/demo/variant`, `/demo/monitor`, `/demo/live`, `/inspector`, `/graph`,
`/agent`, `/assurance`, `/optimizer`, `/funnel`, `/personalize`, `/composer`,
`/policies`, `/help`, `/help/integrations`, `/archive`, `/sources`, `/admin/landings`,
`/admin/landing/{pid}`, `/lp`, `/google`, `/google/callback`, `/enrichment-catalog`,
`/talk`, `/guide`, `/showcase/{slug}` (+`/production`), `/api/demo/{aicopy,scene,…}`,
`/api/optimizer/live`, `/api/observe/{funnel,golden,history}`, `/api/agent/run`,
`/api/personalize`.

## 5. Gate + suite state at sweep time

- Deploy gate (17 suites): **408 passed** · WF-DESIGN matrix: **34 passed** (30 rows + 4
  invariants) — baseline held after every route-group commit.
- Whole `tests/`: **569 passed, 0 failed** — the pre-existing
  `test_integrations_show_base_vs_connect` failure was root-caused (missing `table`
  block renderer in `help_article.html`) and resolved with the /help retirement.
- LOCKED files untouched: `tests/test_{optimizer,gate,drift,website,assurance,live_optimizer}.py`,
  `tests/test_wf_design_matrix.py`, and every gate suite.

## 6. One concern, one surface (S0 spot-check)

| Concern | Single surface |
|---|---|
| Tour / front door | `/apt/demo` |
| Consoles hub | `/apt/dev` |
| Per-section design + data receipts | designer (`_sd_designer.html`) on `/{mount}/dev/business` |
| Pipeline observability | `/observatory` (+ per-section obs panels) |
| Cost ledger | `/costs` + `/api/costs` |
| Replica entry links | `/showcase` (gate-pinned) + `/apt/demo` cards |
| Personalized-site serving (T4) | `/site/{token}` |
