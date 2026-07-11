# Demo Nav + Generation Workflow — Expert Panel Review

**Date:** 2026-07-10 (updated 2026-07-11 — Phase 2 complete)  
**Status:** Phases 1–2 shipped; Phase 3 cross-links in progress  
**Artifacts reviewed:**
- `docs/05-build/DEMO-NAV-PLAN.md`
- `docs/05-build/GENERATION-PROMPT-WORKFLOW.md`
- `docs/05-build/GAUNTLET-CONSOLE-HANDOFF.md` (context)

**Method:** Expert-panel skill — 8 instantiated personas (≥3 1st-order, ≥2 2nd-order, ≥1 3rd-order), each with verdict, strengths, concerns, and one falsifiable ship requirement.

---

## Panel roster

| # | Persona | Order | Lens |
|---|---------|-------|------|
| 1 | **Morgan Keane** — B2B demand gen (HubSpot + Google Ads) | 1st | Channel taxonomy, UTM fidelity, nurture→landing message-match |
| 2 | **James Okonkwo** — Enterprise AE | 1st | Live demo walkthrough, buyer psychology, 15-min script |
| 3 | **Priya Shah** — Frontend / web perf engineer | 1st | Routing, async hero, portal rewrites, gallery UX |
| 4 | **Dr. Lin Wei** — Personalization architect | 1st | Determinism, signal fusion, CONSTITUTION Art IV |
| 5 | **Dr. Sarah Okoye** — Behavioral psychologist / persuasion researcher | 2nd | say/allude/hold, Tribe v2 claims, dark-pattern avoidance |
| 6 | **Alex Rivera** — Performance marketing / paid social (X) | 2nd | UTM stacks, utm_content variants, ad→LP continuity |
| 7 | **Sam Ortiz** — DevOps / demo operator | 2nd | Railway deploy, Vercel rewrites, prebuild warm, pytest gates |
| 8 | **Jordan Blake** — CRO / accessibility wildcard | 3rd | Conversion path friction, WCAG, gallery card scanability |

---

## Individual reviews

### 1. Morgan Keane — B2B demand gen marketer

**Verdict:** The two-plane architecture (visitor tour vs ops console) is the right GTM mental model — it mirrors how we actually sell: channel story first, decision trace second. Not optimal yet because Phase 1 links to `/direct` and `/email` galleries that do not exist, which will erode trust on the first live demo.

**Top 2 strengths**
1. Channel richness ordering (`direct < search < ads < email`) matches how we explain signal stacking in pipeline reviews.
2. YAML scenario catalog with HubSpot-style UTMs and magic tokens is reusable for sales one-pagers and QA — not throwaway nav.

**Top 3 concerns**
1. Phase 1 sitemap links to 404 galleries for Direct/Email — breaks WF-DEMO-001 steps 5–7 until Phase 2 ships.
2. No explicit “campaign name” field on email cards in the spec beyond `utm_campaign` — marketers will want subject-line mock on the gallery card (Phase 2).
3. Search channel bypasses a gallery entirely; fine for v1 but loses a place to show `ref=` vs Referer header distinction.

**Required before ship:** Add a visible “Coming soon” or stub 200 page for `/gauntletapt/direct` and `/email` if Phase 1 ships before Phase 2, **or** gate those tiles until galleries exist. Falsifiable: zero 404s from `/apt/demo` click paths in WF-DEMO-001.

---

### 2. James Okonkwo — Enterprise AE

**Verdict:** WF-DEMO-007’s 15-minute arc is strong — email → console → ads → corporate IP is exactly how I run a technical buyer call. Ship with changes: the plan assumes the presenter knows when to toggle `as=` vs real login; that needs to be on-page, not tribal knowledge.

**Top 2 strengths**
1. Click-by-click workflows with selectors and talk tracks — rare in eng docs, immediately usable in prep.
2. `console_deep_link_pattern` on every scenario keeps “same state on replica and console” — the #1 demo failure mode I see.

**Top 3 concerns**
1. Identity hints document preconditions but galleries do not auto-login — presenter must manually POST login for Maya/Amara scenarios; easy to fumble mid-demo.
2. Engineer console still default entry in some cross-links (ad-lp chip without UTMs noted in WF-DEMO-004 step 6) — undermines marketer-first narrative from Phase 4.
3. Planet vs Gauntlet ad gallery asymmetry (`ad-lp` vs full `/ads`) may confuse “why does Planet get richer mockups?” without a one-line callout on the sitemap.

**Required before ship:** Sitemap and Phase 2 gallery cards must show a **“Setup”** chip per scenario (`Clear cookies` / `Login as maya@…` / `Use magic link — no login`) derived from `identity_hint`. Falsifiable: presenter can run WF-DEMO-003 without reading YAML.

---

### 3. Priya Shah — Frontend / web perf engineer

**Verdict:** Navigation-only layer on top of deterministic `build_page()` is architecturally sound and avoids duplicate personalization paths. Not optimal until portal mount consistency and async-image demo path are documented on the sitemap itself.

**Top 2 strengths**
1. No new server-side state — query + cookie model preserved; galleries are static HTML + href assembly.
2. Shared `demo_nav.py` loader with template variable resolution keeps URL building DRY across tenants.

**Top 3 concerns**
1. Phase 1 links to Phase 2 routes — broken links in production until Phase 2 or stubs ship.
2. Hero async swap (gradient → image) not mentioned on demo tour; first-time viewers may think personalization is “broken” for 30s on cold cache.
3. Planet `/ads` vs Gauntlet `/ad-lp` — different templates, different perf characteristics; no shared gallery component in plan until Phase 2 `demo_channel_gallery.html`.

**Required before ship:** Phase 1 sitemap footer or channel tile subcopy must note **“Hero images may load async; pre-built states instant after warm deploy.”** Falsifiable: WF-DEMO-010 talk track visible from `/apt/demo` link to Delivery docs.

---

### 4. Dr. Lin Wei — Personalization architect

**Verdict:** Plan correctly refuses to merge `demo_scenarios.py` (bandit) with nav YAML and correctly treats nav as URL assembly only — this is optimal for CONSTITUTION Art IV. One gap: magic token resolution must use tenant-specific cohort modules (`cohort` vs `planet_cohort`).

**Top 2 strengths**
1. Explicit determinism inheritance — `classify_entry()` unchanged; scenarios are pure query-string recipes.
2. GENERATION-PROMPT-WORKFLOW.md pushback on “prompt → text” prevents product misrepresentation — critical for Art I truthfulness.

**Top 3 concerns**
1. `${magic:kofi}` in plan assumes `CO.BY_ID["kofi"]` but Kofi lives in `planet_cohort` — loader must not import wrong module (implementation bug if missed).
2. `landing_url_pattern` duplicates query strings already in `query_params` — drift risk when campaign names change.
3. Phase 4 marketer-console IA deferred while demo nav promises marketer-first tour — temporal inconsistency for external narrative.

**Required before ship:** `demo_nav.py` must resolve magic tokens via the same modules as `gauntlet_site` / `planet_site` (`CO` for Liam, `PCO` for Kofi). Falsifiable: `test_resolve_scenario_magic_token_in_urls` passes for both tenants.

---

### 5. Dr. Sarah Okoye — Behavioral psychologist / persuasion researcher

**Verdict:** The plan’s emphasis on say/allude/hold in WF-DEMO-009 and the generation doc’s correction of “AI writes copy” is ethically aligned — not optimal for persuasion *research* demos until brain_sim / Tribe v2 is clearly labeled proxy, not neurometric truth.

**Top 2 strengths**
1. Email richest → direct coldest progression teaches appropriate inference gradient without over-claiming identity knowledge.
2. Hold facts blocked on replica, visible on console only — good transparency pattern for informed consent in B2B demos.

**Top 3 concerns**
1. Magic-token “Welcome back, Liam” without login may feel creepy to privacy-sensitive buyers unless framed as opted-in email link.
2. GENERATION-PROMPT-WORKFLOW §3.5 — Planet enables brain_sim by default; demo nav does not route to a “proxy scoring” explainer before showing scores.
3. Corporate IP allude copy needs explicit demo script line: “We shape, we don’t recite employer” — in plan for WF-DEMO-002 but not on sitemap.

**Required before ship:** Add link from `/apt/demo` to say/allude/hold legend (or `/gauntletapt/dev/business` anchor `#legend`) with copy: **“Surface policy — what we say vs allude vs never show.”** Falsifiable: link present in sitemap HTML; WF-DEMO-009 step 4 reachable in ≤2 clicks from sitemap.

---

### 6. Alex Rivera — Performance marketing / paid social (X)

**Verdict:** Ad variant catalog integration (v01–v12, utm_content message-match) is best-in-class for a demo nav spec — better than most production LP ops. Ship with changes: ad-lp → `/dev` chip dropping UTMs (WF-DEMO-004 step 6) is a P0 message-match break.

**Top 2 strengths**
1. Scenarios reference existing `AD_CATALOG` / prebuild states — paid social story ties to Delivery inventory.
2. Separate Planet `/ads` full mockups vs Gauntlet compact grid — correctly surfaces creative richness difference.

**Top 3 concerns**
1. Ad-lp fixed chip to `/dev` without query string — breaks attribution story mid-demo.
2. No `utm_term` / click-id placeholders — fine for synthetic demo, but performance marketers will ask; document as out-of-scope in v1 (plan §F does).
3. X vs “Twitter” naming — plan uses `utm_source=x` consistently; good, but gallery UI should show “X (Twitter)” once for older buyers.

**Required before ship:** Phase 3 must fix ad-lp chip hrefs to preserve full UTM stack (already noted in plan); **until then**, sitemap Ads tile subcopy should deep-link to a featured scenario URL (e.g. v09) not only `/ad-lp`. Falsifiable: Gauntlet Ads channel tile or featured link includes `utm_content=v09` in href option.

---

### 7. Sam Ortiz — DevOps / demo operator

**Verdict:** Phased plan with pytest gate (`test_demo_nav.py` + `test_apt_dev_hub.py`) before `railway up` is operator-friendly. Not optimal until Vercel rewrite for `/apt/demo` is explicitly in deploy checklist — plan mentions it but handoff §11 omits it.

**Top 2 strengths**
1. Scope boundaries (§F) prevent scope creep — no HubSpot integration, no server-side staged saves.
2. GENERATION-PROMPT-WORKFLOW ties prebuild manifest to warm script + Delivery — three-consumer pattern already proven in handoff.

**Top 3 concerns**
1. `git push` does not deploy — demo nav doc must stay synced with handoff §5 or operators will verify stale production.
2. Phase 5 e2e against johnnycchung.com network-dependent — good to defer, but WF-DEMO-007 smoke in CI should not assume `/direct` 200 until Phase 2.
3. Concurrent sessions + uncommitted `.qa/` screenshots — handoff warning valid; demo nav adds more untracked surface area.

**Required before ship:** Add `/apt/demo` to handoff §11 production URL table **and** Vercel rewrite verification step. Falsifiable: `curl -sI https://johnnycchung.com/apt/demo | head -1` returns 200 after deploy.

---

### 8. Jordan Blake — CRO / accessibility wildcard

**Verdict:** Information architecture (tenant → channel → scenario → replica → console) minimizes cognitive steps — good for conversion of *attention* in a sales demo. Not optimal for accessibility: plan has zero WCAG requirements for gallery tabs and email cards.

**Top 2 strengths**
1. Featured scenarios + audience tabs (Phase 2) support progressive disclosure — reduces Hick’s law paralysis on 12 ad variants.
2. Breadcrumb / back-link requirements in Phase 3 prevent dead-end replicas — important for live demo recovery.

**Top 3 concerns**
1. Four channel tiles × two tenants on one page — acceptable, but needs heading hierarchy (`h1` → `h2` tenant → `h3` channel) for screen readers.
2. Email gallery HubSpot-style cards — plan mentions `.email-card` but no focus states or keyboard path in spec.
3. 15-min WF-DEMO-007 may run long; no “fast path” (5 min) variant for executive skim.

**Required before ship:** `apt_demo_sitemap.html` must use semantic `<section>` + `aria-labelledby` per tenant (implemented in Phase 1). Phase 2 galleries must use `<a>` cards with visible focus ring, not click-only divs. Falsifiable: axe-core or manual tab-through completes sitemap without traps.

---

## Synthesis

### Cross-expert themes

**Agreements (convergent)**
- **Two-plane model is correct** — visitor tour vs ops console; do not merge (Keane, Okonkwo, Lin, Ortiz).
- **Nav must not touch personalization engine** — YAML + href assembly only (Lin, Shah, Ortiz).
- **GENERATION-PROMPT-WORKFLOW correction is load-bearing** — copy is not prompt-generated; must not be sold as LLM copy (Lin, Okoye, Keane).
- **WF-DEMO-* workflows are high value** — especially 007 sales script and 009 hold verification (Okonkwo, Okoye, Ortiz).
- **Phase 1 → 2 dependency is the main ship risk** — Direct/Email 404s from sitemap (Keane, Shah, Rivera, Ortiz).

**Conflicts (divergent)**
- **Stub vs gate vs ship Phase 2 together:** Keane/Shah want no 404s; Ortiz prefers Phase 1 pytest scope without `/direct` 200; **resolution:** Ship Phase 1 with correct hrefs + Phase 2 next; smoke tests must not assert gallery 200 until Phase 2 (already reflected in test plan).
- **Featured ad deep-link vs gallery-first:** Rivera wants v09 on sitemap Ads tile; plan sends to `/ad-lp` — **resolution:** P1 add featured scenario link on sitemap or Phase 3 ad-lp fix.
- **Marketer-first vs engineer-first entry:** Okonkwo wants setup chips; Phase 4 defers marketer IA — **resolution:** P1 setup hints on cards in Phase 2, not Phase 4.

**Risks (ranked)**
1. **404 on Direct/Email galleries** — demo trust collapse (Keane, Shah) — **P0 until Phase 2**
2. **Ad-lp `/dev` chip drops UTMs** — message-match lie (Rivera) — **P0 Phase 3**
3. **Magic token wrong cohort module** — determinism break (Lin) — **P0 implementation** — **fixed in Phase 1 impl**
4. **Brain_sim oversold as conversion science** (Okoye) — **P1 narrative**
5. **Async hero looks broken** (Shah) — **P1 copy on sitemap**

---

## Overall score and recommendation

| Criterion | Score (1–5) |
|-----------|-------------|
| Architectural fit | 5 |
| Sales/demo usability | 4 |
| CONSTITUTION / truthfulness | 5 |
| Implementation clarity | 4 |
| Ship readiness (Phase 1 alone) | 3.5 |

**Overall: 4.1 / 5 — Ship with changes**

Phase 1 (`/apt/demo` sitemap + scenario YAML + loader) is approved to implement. Full plan is not optimal until Phase 2 galleries and Phase 3 cross-links land. GENERATION-PROMPT-WORKFLOW should be treated as **canonical sales-engineering truth** for console demos — not the five-step “prompt → text” model.

---

## Prioritized change list

### P0 — Blockers
| Item | Owner | Source |
|------|-------|--------|
| Resolve magic tokens via tenant cohort modules (`planet_cohort` for Kofi) | Impl | Lin |
| Phase 2 Direct/Email galleries before external demo relying on WF-DEMO-001 steps 5–7 | Impl | Keane, Shah |
| Fix ad-lp chip to preserve UTMs to `/dev` | Phase 3 | Rivera |
| Add `/apt/demo` to Vercel rewrite + handoff URL table | Ops | Ortiz |

### P1 — Should-fix
| Item | Owner | Source |
|------|-------|--------|
| Scenario **Setup** chip from `identity_hint` on gallery cards | Phase 2 | Okonkwo |
| Sitemap link to say/allude/hold legend | Phase 1/3 | Okoye |
| Async hero / prebuild note on demo tour | Phase 1 copy | Shah |
| Featured ad scenario deep-link (v09) from sitemap or Ads tile | Phase 1/3 | Rivera |
| Label brain_sim as proxy scoring in Planet demo path | Docs | Okoye |

### P2 — Nice-to-have
| Item | Owner | Source |
|------|-------|--------|
| Search gallery page (vs direct `?ref=google`) | Phase 2+ | Keane |
| WF-DEMO-007 “5-minute executive” variant | Docs | Blake |
| Email card subject-line mock metadata | Phase 2 | Keane |
| axe-core audit on gallery templates | Phase 2 | Blake |
| Copy policy YAML (`gauntlet_copy.yaml`) | Follow-up | Handoff §9 |

---

## Phase 1 implementation status

**Panel verdict:** Ship with changes → **Phase 1 implemented** (2026-07-10 session)

| Deliverable | Status |
|-------------|--------|
| `rules/demo_scenarios.yaml` | ✅ Created (14 scenarios) |
| `pipeline/personalization/demo_nav.py` | ✅ Loader + sitemap view builder |
| `app/apt_demo.py` + `/apt/demo` | ✅ Route registered |
| `app/templates/apt_demo_sitemap.html` | ✅ Template |
| `tests/test_demo_nav.py` | ✅ 5 tests |
| `app/main.py` import | ✅ Wired |

**Tests:** `uv run pytest tests/test_demo_nav.py tests/test_apt_dev_hub.py -q` → **11 passed**

**P0 fix applied during impl:** Kofi magic token via `planet_cohort`, not shared `cohort`.

**Remaining P0 (not this session):** Phase 2 galleries for `/direct` and `/email`; Vercel rewrite verification on production deploy.

---

*Panel review generated per expert-panel skill. Update when Phase 2 ships or GENERATION-PROMPT-WORKFLOW changes.*
