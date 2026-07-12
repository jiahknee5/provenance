# Demo Nav — Original Vision Gap Report

**Date:** 2026-07-11  
**Scope:** Audit of Johnny’s original demo-navigation vision vs what’s shipped in `provenance` (code + production).  
**Sources:** Original ask (this session), `DEMO-NAV-PLAN.md`, `DEMO-NAV-PANEL-REVIEW.md`, `GENERATION-PROMPT-WORKFLOW.md`, `SESSION-HANDOFF-demo-nav-2026-07-11T1914EDT.md`, `/tmp/demo-nav-phase-status.json`, spot-checks of `apt_demo.py`, `demo_nav.py`, `apt_dev_hub.py`, `gauntlet_dev_business.*`, gallery templates, production curls.

**Note on phase status:** `/tmp/demo-nav-phase-status.json` marks phases 1–6 `true` (iteration-2 console polish). That does **not** mean plan Phase 6 (Google/Meta ad stubs) shipped — those remain deferred. Treat the JSON as “nav tour + cross-links + workflows iteration done,” not “original vision complete.”

---

## 1. Verdict

**Partially implemented** — the visitor demo tour (sitemap → channel galleries → personalized replica → consoles) is live and demoable; the original “HubSpot/Clay generation console with editable prompts per asset lane, multi-platform ads, realtime secondary images, and cost/agent-graph observability” is only partly there, with several items correctly deferred by the two-lane generation model.

---

## 1b. Verified re-audit (2026-07-11, post-deploy) — independent check of code + live prod

Re-ran the audit against actual code and live URLs (3 parallel verifiers + manual curls), not the plan’s claims. Prior verdicts mostly hold. **Material corrections:**

- **CORRECTION — `/graph`, `/agent`, `/inspector`, `/funnel` are BUILT, not missing.** Registered in `app/main.py:78–94`; return **200 on Railway upstream**. They 404 on `johnnycchung.com` only because the **Vercel portal doesn’t rewrite those paths**. → *Portal-rewrite gap, not a build gap.* The observability/agent-graph surfaces the vision asked for partly EXIST — just unreachable from the public demo domain. Fix = add rewrites in `johnnycchung-portal`, not build.
- **Persuasion (sales tactics) is API-only.** `/api/persuasion/plan|strategies` (`app/persuasion.py`); **not** wired into the Gauntlet/Planet replica serving path (`app/site.py`/`gauntlet.py` don’t import it). Engine built + tested, but the demo pages don’t use it → sales-tactics-on-landing = **PARTIAL (built, not demoed).**

**Confirmed gaps (verified):**
- Image surfaces = **hero + og only** (`rules/gauntlet_image.yaml:342`); no section/secondary/backdrop. **og:image is NOT on the live replica `<meta>`** (curl empty) → “additional realtime images beyond hero” = **MISSING.**
- **Motion/animation = Planet-only** (`app/planet.py` 15 refs, `app/gauntlet.py` 0).
- **No editable-prompt→regenerate flow.** Console shows image prompts + stages YAML **client-side** (“Copy patch” → commit/deploy); no regenerate endpoint. Copy has no prompt by design → **deferred (correctly, two-lane model).**
- **Ads = X-only, no Business/Consumer tabs.** Only `/direct` + `/email` have audience tabs — and those **do filter server-side** via `?audience=`. 0 consumer-tagged ad scenarios; Google = search-referrer only; Meta absent.
- **Site picker = Gauntlet + Planet only** (`apt_dev_hub.py:18 _SITES`); no “new/other” stub.
- **Marketer console sections** = Arrival · Copy · Images(hero) · Guardrails · Delivery; no lanes for secondary/section/email assets.

**Confirmed working (verified live):** channel classification resolves genuinely different data per channel; magic-token→identity pre-login (Liam `mt_…`, Kofi `pt_…`); UTM→hero message-match (v09 changes the H1); `/direct`+`/email` audience tabs filter server-side; all tour + console routes 200 on portal; `/apt/demo` now carries the flow diagram (this session).

---

## 2. Original ask → status table

| # | Original ask | Status | Evidence |
|---|--------------|--------|----------|
| 1 | Demo navigation page showing the sitemap | **Done** | `GET /apt/demo` → `app/apt_demo.py`, `app/templates/apt_demo_sitemap.html`; prod **200** |
| 2 | Entry channels: direct, ads (Google, Meta, **or** X), email → different landing data | **Partial** | Direct / email / X ads / search live; **Google & Meta ad galleries not started** (`DEMO-NAV-PLAN.md` Phase 6 deferred). Ads UTMs are `utm_source=x` only in `rules/demo_scenarios.yaml` |
| 3 | Email: additional CRM data | **Done** | HubSpot-style cards + magic tokens (`demo_email_card.html`, Liam/Kofi scenarios); gallery `/gauntletapt/email`, `/planetapt/email` **200** |
| 4 | Direct: IP, location, company (+ enrichment story) | **Done** | Corporate IP scenarios (e.g. Apple `17.253.144.10`, Planet ag `19.7.0.1`); galleries `/…/direct` **200** |
| 5 | Ads: enriched targeting (UTM) | **Done** (X only) | `/gauntletapt/ad-lp` 12-variant grid; `/planetapt/ads` full X mockups; UTM message-match into replica |
| 6 | Each entry point → page of potential entries (like `/ad`) | **Done** | `/direct`, `/email`, ads grids; search skips gallery → `?ref=google` (plan-allowed) |
| 7 | Create `/direct` and `/email` with poignant examples | **Done** | Shared `demo_channel_gallery.html` + YAML catalog (13 scenarios); tags/story on cards |
| 8 | Each links to personalized website | **Done** | Card `landing_url` → `/gauntletapt` / `/planetapt` with query params; console deep-links too |
| 9 | `/ad`, `/direct`, `/email` each have consumer **and** business versions | **Partial** | **Direct + email:** real audience tabs (`Companies`/`Individuals`, `Enterprise`/`Self-serve`) in `demo_channel_gallery.html`. **Ads:** variant “Best for {audience_fit}” labels only — **no first-class Business/Consumer gallery tabs**; YAML ads scenarios are mostly `audience: business` |
| 10 | Landing: personalized words + images; main image pre-designed; **additional images realtime (possibly animated)**; sales tactics + Tribe v2 | **Partial** | Personalized copy + hero (prebuild/warm/live) shipped. Planet hero **motion** (animated WebP) when enabled. Tribe/brain_sim = **opt-in proxy scoring**, not neurometric conversion. **Secondary/section realtime images** and live `og:image` still missing (`GENERATION-PROMPT-WORKFLOW.md` §6.5) |
| 11 | Dev view like HubSpot / Google Ads Manager / Clay — select website first (planet, gauntlet, **or new/other**) | **Partial** | `/apt/dev` site picker: **Gauntlet + Planet only** (`apt_dev_hub.py` `_SITES`) — **no “new/other”**. Marketer console has Clay-style data ledger + HubSpot-ish email gallery aesthetic; **not** a multi-platform Ads Manager |
| 12 | Sections per generation area: (1) main copy (2) main images (+ other text/images) | **Partial** | `/dev/business` sidebar: Copy + Images (hero/og) + Guardrails + Delivery. No separate lanes for section/email secondary assets |
| 13 | Per section: data usable, guardrails/provenance, prompt, **editable to generate prompt** | **Partial** | Image: intent, prompt text, guardrails, staged YAML diffs, read-only `design_prompts` catalog. Copy: slot provenance + say/allude/hold — **no prompt** (correct per two-lane model). **Not** a free-form “edit prompt → regenerate asset” studio |
| 14 | Observability, cost, agent graphs | **Partial / mostly separate** | Global nav → `/observatory` **200**, `/costs` **200**. Image receipts show token-save hints, not a marketer cost panel. `/graph` and `/agent` **404** on production. Not embedded as first-class marketer-console stages |
| 15 | Push back and recommend; don’t change concept, just UI workflow | **Done** (docs) | `GENERATION-PROMPT-WORKFLOW.md` two-lane correction; panel review; plan §F scope boundaries |

---

## 3. What we shipped

- **Visitor tour plane:** `/apt/demo` sitemap (Gauntlet + Planet × Ads / Direct / Email / Search) with richness narrative.
- **Scenario catalog:** `rules/demo_scenarios.yaml` + `pipeline/personalization/demo_nav.py` (magic tokens via correct cohort modules).
- **Channel galleries:** `/gauntletapt|planetapt/{direct,email}` with audience tabs, HubSpot email cards, replica + engineer/marketer console links.
- **Existing ads grids:** Gauntlet `/ad-lp`, Planet `/ads` (X), wired from sitemap.
- **Ops hub:** `/apt/dev` website toggle + anon/known preview + console cards; link back to demo sitemap.
- **Marketer console polish:** Copy \| Images sidebar caps, channel strip, `design_prompts` reference panel, Delivery inventory, staged image YAML (client-side).
- **Cross-links / workflows:** Demo ↔ galleries ↔ replica ↔ `/dev` / `/dev/business`; `docs/workflows.json` WF-DEMO-001–010; pytest smoke coverage (incl. 008/009/010 per phase-status notes).
- **Ad-lp → `/dev` sample chip:** preserves v09 UTM stack (`gauntlet.py` `dev_sample`).
- **UI mockups gallery:** `/apt/mockups` (15 static variants: sitemap/hub/direct/email/ads × a/b/c) — design exploration, not live templates. Grok redesign aborted (handoff).
- **Production (2026-07-11 curls):** `/apt/demo`, `/apt/dev`, `/apt/mockups`, `/gauntletapt/{direct,email,ad-lp,dev/business}`, `/planetapt/{direct,email,ads}`, `/costs`, `/observatory` → **200**. `/graph`, `/agent` → **404**.

---

## 4. What’s still missing vs original ask

### P0 — Biggest demo / trust gaps (vs original ask)

1. **Realtime secondary / animated images on the landing (beyond hero)**  
   Original ask: main image pre-designed; *additional* images realtime (possibly animated). Today: hero (+ Planet motion) only; og not on live `<meta>`; no section backdrops in prebuild. Evidence: `GENERATION-PROMPT-WORKFLOW.md` §6.5; `rules/gauntlet_image.yaml` surfaces = `hero`, `og`.

2. **True “generation sections” with editable prompts per asset lane**  
   Original ask: per section data + guardrails + prompt + editable generate. Today: image prompt is **shown** and YAML is **staged** (commit/deploy to apply); copy has **no** prompt by design; no one-click regenerate from console. Closest: Images panel + `design_prompts` read-only catalog.

3. **Cost + agent-graph observability inside the marketer console**  
   Original ask implied console-native observability. Today: separate `/costs` and `/observatory`; `/graph` 404; business console has delivery/token hints, not visit cost or agent graph. Nav links alone ≠ the vision.

### P1 — Channel / IA completeness

4. **Google / Meta ad galleries (not just X)**  
   Explicitly in original ads channel list; plan Phase 6 deferred. No `utm_source=google|meta` gallery stubs.

5. **Website picker “new / other”**  
   `/apt/dev` only Gauntlet + Planet. No stub for onboarding a third site.

6. **Consumer vs business as first-class tabs on ads galleries**  
   Real on `/direct` and `/email`. Ads grids use per-variant audience-fit labels, not the same tab model. Catalog under-represents consumer paid scenarios.

7. **Presenter Setup chips (panel P1)**  
   Cards show data tags (`identity_hint`, IP, UTMs), not “Clear cookies / Login as Maya / Magic link — no login.” Still easy to fumble mid-demo.

### P2 — Polish / deferred-by-design

8. Dedicated **search gallery** (v1 links straight to `?ref=google`).  
9. Sitemap callouts: say/allude/hold legend link; async-hero / prebuild note (panel P1 — still thin on live sitemap).  
10. Apply a chosen `/apt/mockups` variant to live templates (handoff Next #1).  
11. Marketer-first IA default (plan Phase 4) — engineer console still co-equal.  
12. Copy policy YAML (`gauntlet_copy.yaml`) — proposals only today.

---

## 5. Recommended next sprint

Close the largest *demo-visible* gaps **without** rebuilding `build_page()` / `classify_entry()`:

1. **Console “Ops strip” on `/dev/business`:** embed a compact Cost row (from existing `/api/costs` or image receipt fields) + deep-link cards to Observatory / process map — do not invent a new agent runtime; surface what already exists.
2. **Secondary surface demo path:** pick one non-hero surface (prefer **og** meta on replica, or one section backdrop), add to prebuild + Delivery grid, document async vs pre-built on the demo sitemap. Skip full multi-surface realtime studio.
3. **Ads gallery audience parity:** add Business / Consumer (or Companies / Individuals) tabs to Gauntlet `ad-lp` filtering (reuse gallery tab pattern) + 2–3 consumer-tagged YAML ad scenarios — still X-only.
4. **Setup chips from `identity_hint`:** map hints → presenter instructions on gallery cards (panel P1).
5. **Either** a thin Google *or* Meta ads stub grid (3–4 cards, static mock + UTM landing links) **or** explicit sitemap copy: “Paid social demo = X today; Google/Meta stubs deferred” — don’t leave the original multi-network claim implied.

---

## 6. Pushback — keep deferred (align with two-lane model)

From `GENERATION-PROMPT-WORKFLOW.md` — do **not** “finish” the original ask by pretending the engine is a five-step prompt→text pipeline:

| Original impulse | Keep deferred / reframed | Why |
|------------------|--------------------------|-----|
| Editable prompt → generate **copy** | Deferred forever for replica | Copy is deterministic slot fills; no LLM prompt on Gauntlet/Planet path (Art I + Art IV) |
| Live “AI writes the page” per visit | Deferred | Misrepresents product; `creative.ai_copy()` is showcase/outbound only |
| Tribe v2 / brain stimulation as conversion science | Label as **proxy scoring**; don’t sell as neurometrics | Planet `brain_simulator` + `proxy_v1` fallback; not measured visitor brain data |
| Realtime image gen for every secondary asset | Prefer **prebuild + async hero** | PRD: curate imagery; don’t generate per-visitor by default |
| Real HubSpot / Ads Manager integrations | Deferred | Galleries are URL-assembly mockups; no send/API required for sales tour |
| Server-side staged YAML saves from console | Deferred | Client-side patch → commit/deploy (CONSTITUTION) |
| Full Google **and** Meta parity before next sales demo | Defer one platform or both until sales asks | High design cost, zero personalization gain (plan Phase 6) |
| “New/other” website as full third tenant | Stub card only if needed | Real tenant = mounts + YAML + cohort — not a picker toggle |

**Concept to preserve:** channel richness story (direct < search < ads < email) → curated scenario → same-state replica + marketer console.  
**UI workflow to refine:** make the console feel like HubSpot/Clay for *reading* decisions and *staging* image rules — not a free-form generation IDE.

---

## Appendix — Production smoke (2026-07-11)

| URL | HTTP |
|-----|------|
| `https://johnnycchung.com/apt/demo` | 200 |
| `https://johnnycchung.com/apt/dev` | 200 |
| `https://johnnycchung.com/apt/mockups` | 200 |
| `https://johnnycchung.com/gauntletapt/direct` | 200 |
| `https://johnnycchung.com/gauntletapt/email` | 200 |
| `https://johnnycchung.com/gauntletapt/ad-lp` | 200 |
| `https://johnnycchung.com/planetapt/direct` | 200 |
| `https://johnnycchung.com/planetapt/email` | 200 |
| `https://johnnycchung.com/costs` | 200 |
| `https://johnnycchung.com/observatory` | 200 |
| `https://johnnycchung.com/graph` | 404 |
| `https://johnnycchung.com/agent` | 404 |

---

*Gap audit only — no implementation in this pass.*
