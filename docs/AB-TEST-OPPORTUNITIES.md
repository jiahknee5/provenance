<!--
Generated 2026-06-23 by the `ab-test-research-swarm` workflow (run wf_232c4b39-b48):
10 parallel CRO research lanes (5 per-surface + 5 cross-cutting levers) → adversarial
verification → synthesis. 68 hypotheses produced; verification complete (1,057 web look-ups).

VERIFICATION OUTCOME: every high-confidence/high-impact hypothesis was adversarially
verified against its cited evidence and the product's truth boundary. The verifiers
downgraded almost every lift (most public CRO numbers are B2C single-test outliers or
mis-attributed) and CUT 6 hypotheses (refuted and/or truth-boundary-violating) — see §3
"Cut". Lifts marked 📉 are verification-corrected; use those, not the proposers' ranges.
Verdict column: qualified = kept with a corrected number; null = not independently verified.
-->

# A/B Test Opportunities — Provenance Funnel

## 1. Executive summary

Provenance runs two tenants on one truth-bounded contextual bandit. Every hypothesis below stays inside the CONSTITUTION's "can't say what it can't prove" boundary — variants only re-order, re-frame, or re-emphasize **already-Gate-cleared** claims, or change pure UI/layout. Adversarial verification downgraded almost every cited lift: the public CRO evidence is overwhelmingly B2C e-commerce/SaaS, and the famous hero numbers (Aagaard +90%, HubSpot/Expedia "remove a field +50%", testimonial +34%) are single-test outliers or mis-attributed. **Use the corrected lifts below, not the proposers' optimistic ranges.**

**Highest-leverage tests (by adjusted ICE + signal speed):**

| Rank | Test | Why it leads |
|---|---|---|
| 1 | `helix-clinops-numbers-arm-C` | Pure new bandit arm in `variants.py`, zero truth-risk (verbatim `c_los`), clears Gate by construction. Corrected lift modest (0–4%) but ~free to ship. |
| 2 | `edu-cta-first-person-outcome-verb` | Brings the **entire education CTA into the optimizer** (currently 100% static); per-archetype B-arm; warm consumer-like audience where evidence transfers best. |
| 3 | `cta-lp-entry-value-not-go` / `edu-gate-button-first-person-value` | "Go →" is contentless; near-B2C audience makes the evidence most applicable here; needs only entry-gate logging. |
| 4 | `helix-form-proof-beside-form` | SOC2/HIPAA strip sourced from real `claim_ids` (`c_soc2/c_hipaa/c_deployed`); SOC 2 is a genuine B2B-healthcare procurement gate. |
| 5 | `helix-cfo-loss-frame-arm-C` | New CFO arm; doubles as the MLR legal-hold demo (auto-suppressed when `c_tco` is on hold). |
| 6 | `prov-tier-dial-as-bandit-context` | The signature mechanism: makes the personalization tier a learnable context dimension with tier-4 held out — the product's core thesis made measurable. |
| 7 | `helix-form-risk-reversal-under-button` | Cheap, but **split affirmative vs negation framing** — the "never sell" wording has measured backfire risk (Aagaard −18.7%). |

**Single biggest KPI opportunity per tenant:**
- **Helix (B2B-healthcare):** the **form-completion** step (`form.html` → `/submit`). It has 9 fields including 5 friction-heavy selects and no proof/trust signal at the conversion point. Realistic corrected upside is single-digit (not the 15–40% cited) and must be measured against *downstream booked rate*, not raw submits, because deferring/cutting firmographic fields risks lead-quality dilution and can starve the bandit's segment key (which is keyed on role **+ company_size**).
- **Academy (education):** the **landing→signup-CTA** step. The education funnel's CTAs and proof-block selection are currently **deterministic and outside the bandit entirely** — the single highest-value move is wiring them in as arms. This is a near-B2C audience, the one place the cited CRO evidence transfers best.

---

## 2. Funnel → KPI map

| Surface | Funnel stage | Primary KPI | # tests (surviving) |
|---|---|---|---|
| `lp_entry.html` (edu gate) | Email capture | Go-submit / email-capture rate | 8 |
| `landing.py` / `landing.html` (edu) | Landing → signup CTA | landing→signup CTA CTR | 11 |
| `segments.py` (edu archetypes) | Landing → signup CTA | signup CTA CTR | 2 |
| `form.html` (Helix) | Lead capture | form-completion (`/submit`) | 12 |
| `site.html` (Helix) | Site → ROI assessment | site→CTA CTR (booked) | 8 |
| `thanks.html` (Helix) | Post-conversion momentum | thanks→site CTR | 4 |
| `site_cta.html` (Helix) | Post-booking | no-show reduction / attend | 2 |
| `variants.py` (Helix ROLE_ANGLES) | Site hero / email | site→CTA CTR per role | 4 |

(Counts are pre-cut; 6 tests are removed in §3 "Cut".)

---

## 3. The ranked backlog (top tests, ICE desc)

Lift column uses the **verification-corrected** number where the verdict adjusted it (📉 = downgraded from proposer's range). Verdict shown is the adversarial verdict; `null` = not independently verified.

| ID | Surface | Element | KPI | Current → Variant (terse) | Expected lift (corrected) | ICE | Verdict |
|---|---|---|---|---|---|---|---|
| `cta-site-first-person-roi` | site.html | cta | site→CTA | "Start your" → "Start my" | 📉 0 to +6% (~+2–3%) | 8.33 | qualified |
| `edu-cta-first-person-outcome-verb` | segments.py + landing.html | cta | landing→signup | generic CTA → first-person+outcome | 📉 +3–12% (~+5–7%) | 8.0 | qualified |
| `helix-clinops-numbers-arm-C` | variants.py | headline | clinops site→CTA | "Cut LOS…" → "Reduce avg LOS by 1.2 days" | 📉 0 to +4% | 8.0 | qualified |
| `helix-form-h1-numeric-test` | form.html | headline | form-completion | vague H1 → deliverable-named/role-anchored | 📉 +2–8% (B), +3–8% (C) | 8.0 | qualified |
| `edu-outcome-angle-salary-anchor` | landing.py | headline | landing→signup | vague salary → "+$38K within 6mo (even if non-tech)" | 📉 +3–12% (trim copy) | 8.0 | qualified |
| `edu-hero-outcome-specificity` | landing.py | headline | landing→signup | "where this takes your salary" → "+$38K median lift" | 📉 +2–8% (0/neg elsewhere) | 7.33 | qualified |
| `cta-form-kill-friction-verb` | form.html | cta | form-completion | "Send me the report" → "Get my ROI report" | 📉 −1 to +4% (~flat) | 7.67 | qualified |
| `proof-format-bandit-arm` | landing.html | proof | landing→signup | deterministic stats/testimonial → 3-arm bandit | 📉 +1–5% (maybe flat) | 7.67 | qualified |
| `edu-gate-button-first-person-value` | lp_entry.html | cta | email-capture | "Go →" → "See/Build my page →" | 📉 single-digit, maybe flat | 7.67 | qualified |
| `helix-cfo-loss-frame-arm-C` | variants.py | headline | cfo site→CTA | gain-vague → "Stop overpaying: cut TCO 47%" | 📉 −5 to +10% (~+2–5%) | 7.33 | qualified |
| `cta-lp-entry-value-not-go` | lp_entry.html | cta | email-capture | "Go →" → "Build my page →" | 📉 +3–12% (directional) | 7.33 | qualified |
| `helix-form-risk-reversal-under-button` | form.html | trust | form-completion | none → time/no-sales-call/privacy line | 📉 −5 to +10% (split framing!) | 7.33 | qualified |
| `helix-cut-to-three-fields-enrich-rest` | form.html | form | form-completion | 8 fields → 3 + enrich | 📉 +3–12% (not 10–25) | 7.33 | qualified |
| `cta-landing-readiness-arm` | segments.py | cta | landing→signup | high-commitment CTA → readiness-matched arm | 📉 +3–9% (mismatched segs only) | 6.33 | qualified |
| `helix-itsec-question-arm-C` | variants.py | headline | it_sec site→CTA | feature stack → "Will it pass security review?…" | 📉 −8 to +8% (~0) | 7.0 | qualified |
| `helix-form-cut-to-essential-fields` | form.html | form | form-completion | 9 fields → 4 + progressive | 📉 +8–12% (keep company_size!) | 7.33 | qualified |
| `helix-form-button-get-my-roi-report` | form.html | cta | form-completion | "Send me the report" → "Get my ROI report" | +2–9% (B2C-skewed) | 7.0 | null |
| `edu-gate-reassurance-microcopy` | lp_entry.html | trust | email-capture | none → "no spam / page-only use" line | +2–6% (directional) | 6.67 | null |
| `edu-intro-loss-frame-arm` | landing.py | headline | landing→signup | "free class" → "claim seat before cohort fills" | 📉 −3 to +6% (~flat) | 7.33 | qualified |
| `helix-form-proof-beside-form` | form.html | proof | form-completion | none → SOC2/HIPAA/deployed strip | 📉 +3–12% (~+5–8%) | 6.33 | qualified |
| `cta-thanks-value-suffix-vs-bare` | thanks.html | cta | thanks→site | "View your personalized page" → "See your verified ROI page" | 📉 0 to +5% (~+1–3%) | 7.33 | qualified |
| `thanks-value-first-cta-copy` | thanks.html | cta | thanks→site | "View your page" → "See my ROI report" | 📉 0 to +8% | 7.0 | qualified |
| `prov-tier-dial-as-bandit-context` | landing.py | personalization | signup CTR | manual tier param → bandit T1–T3 (T4 held out) | 📉 +1–6% (mis-tiered segs) | 6.33 | qualified |

### Cut (failed verification — verdict `refuted` or `truth_boundary_ok: false`)

| ID | Reason |
|---|---|
| `helix-cta-firstperson-riskreversal` | **Refuted + boundary breach.** "Free / no-obligation / ~15 min" can't be proven — product is priced per record, the 15-min duration is invented; no checkout = no risk-anxiety to reverse. Only a first-person-only swap would be legal. |
| `edu-gate-softening-we-already-know` | **Boundary breach.** Variant C ("info you already shared") asserts first-party consent, but `cohort.py`/`signals.py` show data is partly **purchased/PDL-enriched** — a new unprovable consent claim. (Variant B "your cohort record" alone would survive; the item as scored is cut.) |
| `helix-quality-you-frame-arm-C` | **Refuted + boundary breach.** A tenant render-block rejects the reader-directed headline, and it reframes an *averaged* 1.2-day figure as a per-reader patient promise. |
| `receipts-as-proof-onbrand` | **Boundary breach.** The "{N} sources on file" count is false as written — claims share sources (quality arm B = 3 claims → 2 distinct docs); and on-site self-rendered receipts aren't the "independent" verification the cited research describes. Fixable, but cut as specified. |
| `specificity-recency-stats` | **Boundary breach.** "92% finish — across 600+ enrollments" mixes the *hired* and *enrollment* denominators; not Gate-safe. (The 6-month relabel alone would be safe.) |
| `booked-set-expectations-timeline` | **Boundary breach.** "within one business day" is an unverifiable SLA the ops process may not honor; must downgrade to "shortly." |

---

## 4. Per-funnel-stage detail (surviving tests)

### 4A. Education email gate (`lp_entry.html`)
**Shared caveat:** this surface emits **no reward signal today** — it's a plain GET form with no arm, no `select()`, no UTM/referrer/UA capture. Every "bandit arm" here is really *"add entry-logging + an enter-rate reward FIRST, then it becomes a learnable arm."* Device is already read elsewhere (`cohort.py`, `signals.py`), so device-adaptive ordering is feasible; arrival-channel learning is net-new instrumentation.

- **`edu-gate-button-first-person-value` / `cta-lp-entry-value-not-go`** — H: "Go →" carries zero information scent; "Build my page →" names the payoff and uses the verb the body already uses ("build your page on the spot"). M: self-reference + benefit framing + scent. Evidence: Aagaard/ContentVerve first-person wins (+38–90%) are **B2C single-tests**; corrected to single-digit/maybe-flat because the cohort is captive and high-intent — *but* this near-B2C audience is where the evidence transfers best. Wiring: `ENTRY_CTA_ARMS = {A:"Go →", B:"Build my page →"}` on a one-context `ThompsonBandit` keyed `__lp_entry__`; reward = `/lp` match. claim_ids=[] → clears Gate trivially.
- **`edu-gate-reassurance-microcopy`** (verdict null) — one line under the field ("…no spam / page-only use"). Truth-watch: only true **at this step** — confirm the gate submit doesn't enqueue outreach before shipping.
- **`edu-gate-error-recovery-rewrite`** (qualified) — the real win is the product-logic own-goal: current error routes a *legitimate* cohort member to **demo addresses**. Corrected +5–12% on post-error recovery, mostly from the copy fix not inline validation. Ship as two arms (copy-only vs copy+inline) to attribute the lift. Note: gate is an **exact 10-row allowlist**, not a domain check — the dominant "not in cohort" bounce is untouched by domain-typo fixes.
- **`edu-gate-qr-first-vs-email-first`** (qualified) — device-adaptive ordering. Best as a **deterministic UA default** (mobile→email-first, desktop→QR) + an enter-rate event, not a bandit arm, since no reward exists yet. Corrected +2–8% mobile only, ~0 desktop.
- **`edu-gate-domain-friction-prefill`** (qualified) — corrected near-zero on submit (single-field forms already at ceiling); measure as **error-rate**, and keep the suffix **editable** — `johnny.c.chung@gmail.com` is a non-gauntletai cohort member who'd be locked out by a hard suffix.

### 4B. Education landing (`landing.py` / `landing.html` / `segments.py`)
This funnel is **entirely deterministic today** — bringing it onto the bandit is the headline structural change.

- **`edu-cta-first-person-outcome-verb`** — per-archetype B-arm ("Watch a free class" → "Start my free class"). Corrected +3–12% (~+5–7%), real null chance on low-traffic segments. Wiring: change `ARCHETYPES[*].cta` from a string to `[(arm,text)]`; `_cta()` calls `bandit.select(f"{arch.id}__t{tier}")`; reward = CTA click (already in `cta_events`). Both strings clear Gate (no claim).
- **`cta-landing-readiness-arm`** — lower-commitment B-arm per archetype ("Apply now" → "See if you're ready"). Direction backed by a real *education* case (CRE/All About Learning +28% with no downstream cannibalization). **Must reward on enrollment/attendance, not click**, or softer CTAs inflate a vanity metric. Net-new plumbing (education funnel has no arm wiring).
- **`edu-hero-outcome-specificity` / `edu-outcome-angle-salary-anchor`** — promote the already-proven "+$38K median / 600+ hired" into the hero. Reuses an approved `claim_id` → Gate-clears identically. Scope to `outcomes_first`/`cost_confident` (a salary hero reads transactional for explorer/prestige). **Trim the sub** — Unbounce shows education demands the lowest word count and penalizes dense/high-reading-level copy.
- **`proof-format-bandit-arm` / `edu-proof-block-bandit-stats-vs-testimonial`** — replace the deterministic `proof = "stats" if data_driven else testimonial` rule (`design.py`) with a 3-arm bandit (stats / testimonial / both). Keep the psychographic flag as a **warm-start prior**, not a hard gate. Corrected +1–5% (possibly flat/negative) — only the *narrative-identification* mechanism transfers; the CXL/+34% numbers are mis-cited B2C. 3 arms need ~1.5× traffic — warm-start to degrade gracefully on a 10-seed cohort.
- **`edu-section-order-financing-first`** (qualified) — order-as-arm, no copy change. Corrected −2 to +5% (weakest-evidenced; F-pattern direction only). Keep it a **single-axis** bandit before combining with other arms.
- **`edu-subhead-declared-goal-mirror`** (qualified) — mirror the visitor's **own declared goal** (HubSpot `say`-layer) across all tiers. Lowest truth-risk in the set. Corrected +3–12% for the submitted-with-goal subset, ~0 at tier 1 (already echoes), watch tier-4 redundancy. Gate to `has_declared_goal` context.
- **`edu-intro-loss-frame-arm`** (qualified) — soft scarcity bound to the **real** "night cohort starts in 3 weeks" fact (no fabricated timer). Corrected ~flat (−3 to +6%); Prospect Theory actually favors gain-framing on a free step. Fall back to plain `intro` if the date isn't Gate-verifiable at render.
- **`edu-credibility-numeric-arm`** (qualified, thin verdict) — promote verified "40+ orgs" into the headline for prestige archetype.

### 4C. Helix form (`form.html`) — the biggest Helix opportunity
- **`helix-form-h1-numeric-test`** — Variant C (proof-anchored "Get a verified clinical-ops ROI report") is the better challenger for this risk-averse audience; gate role-aware Variant C behind an `inferred_role_confidence` feature. Corrected +1–5% (B), +3–8% (C where role known). Native fit to `ROLE_ANGLES`.
- **`helix-cut-to-three-fields` / `helix-form-cut-to-essential-fields`** — **DO NOT drop `company_size`.** Verification found the bandit segment is keyed on **role + company_size**; dropping it starves arm selection and the synthetic-enrichment path can't recover it (only the capped/partial PDL path can). Keep role *and* company_size on screen 1; defer the rest. Corrected +3–12% (not 10–25%), and **measure downstream booked rate** — longer forms self-qualify higher-intent B2B leads (Aagaard's −14% precedent). Needs a second pre-segment `form_layout` bandit keyed on device.
- **`helix-mark-optional-not-required`** (null) / **`helix-two-step-progressive`** (qualified) / **`helix-move-heardvia-postsubmit`** (null) — progressive-disclosure siblings. For the 2-step form the **robust win is step-1 partial capture** (email+role banked even on step-2 abandon), +5–25% on captured leads; total-completion lift is ~flat-to-+10% (Helix's 8 fields sit at the *bottom* of the field-count band where multi-step helps least). Use a **graded float reward** (1.0 full / 0.5 step-1 / 0 bounce).
- **`cta-form-kill-friction-verb` / `helix-form-button-get-my-roi-report`** — both control and variant are already first-person, so the canonical +90% "my vs your" effect **doesn't apply**; corrected ~flat. Per-role arm, near-zero cost.
- **`helix-form-risk-reversal-under-button`** — **split into two arms: affirmative-privacy vs "never-sell" negation.** Aagaard measured a negation/threat line ("we will never spam you") *cutting* conversion −18.7%. Corrected −5 to +10%. New context feature `submit_reassurance ∈ {none, affirmative, never_sell, time_only}`; route through Gate (clauses must stay operationally true of the flow).
- **`helix-form-proof-beside-form`** — source the strip from real `claim_ids` (`c_deployed/c_soc2/c_hipaa`) through `gate.verify_variant`. Corrected +3–12% (~+5–8%) — SOC 2 is a documented B2B-healthcare procurement gate; the cited Hubstaff/testimonial numbers are inapplicable (testimonials forbidden by the Constitution). Let the bandit swap *which* proven claim leads per role (`c_soc2`→it_security, `c_deployed`→quality).
- **`helix-inline-validation-positive`** (null) — **on-blur only** (per-keystroke validation *increases* errors per UX Movement). Device-conditioned (mobile-weighted).
- **`helix-consent-uncheck-microcopy`** (null) — pre-checked consent is GDPR-non-compliant (Planet49); judge on **quality-adjusted reward** (propagate the form-arm id to the Recipient so a later unsubscribe `b += 3` credits the right arm).

### 4D. Helix hero / role arms (`variants.py`)
All four add a **third role arm reusing existing `claim_ids`** → Gate-clears by construction, no special-casing (Article II preserved). Corrected lifts are small and the cited 15–35% "numeric headline" stats were found **fabricated/mis-attributed** (not on the cited pages) — let the bandit, not the stats, decide.
- `helix-clinops-numbers-arm-C` (+0–4%) — `c_los` is already in arm A's body, so the only novelty is promoting it to the headline.
- `helix-cfo-loss-frame-arm-C` (−5 to +10%) — carries `c_tco`, so it doubles as the **MLR legal-hold** exhibit (auto-RED when the hold flips).
- `helix-itsec-question-arm-C` (~0, −8 to +8%) — question vs declarative is a coin-flip; low-risk arm, reviewer wants the answer up front.
- `helix-proof-headline-explicit` (qualified, −5 to +10%) — promote the muted Gate-verification line into the H2; likely positive for it_security/quality/cfo, negative for outcome-hungry clinops. **Bandit arm, never a global swap.**

### 4E. Helix site / momentum / booked
- **`cta-site-first-person-roi`** (corrected 0 to +6%) — keystone wiring: extend `variant_id` with a CTA suffix so `oracle._arm_of`/`campaign.py` treat it as a distinct Beta arm; render `{{ variant.cta_text }}`.
- **`helix-sticky-repeat-cta`** (qualified, +2–7% mobile) — repeat the **same** CTA after the proof receipts + slim sticky mobile bar; the only controlled sticky tests (Growth Rock) show +5–8%, not the cited 5–15%. **Placement is an orthogonal layout arm**, not a `ROLE_ANGLES` swap. Single-CTA-vs-competing evidence validates the no-competing-CTA rule.
- **`helix-disclosure-reframe-arm`** (qualified) — move the raw "variant B, A/B winner" jargon into an expandable receipt; keep a plain transparency line. Corrected −2 to +6%. This is **template chrome, not a per-role arm** — implement as a page-level A/B/C or context feature. Gartner: 53% of B2B buyers say over-personalization *harmed* their experience.
- **`helix-claim-count-prioritize`** (qualified) — corrected −1 to +4%; the "1–3 vs 7+ signals" stat is mis-attributed and arms already show only 3 claims. **Never drop the withheld notice** — make it *more* prominent (costly-honesty signal).
- **`helix-stakeholder-share-cta`** (null) — forward-the-verified-page secondary action; reward on the **primary** CTA so cannibalization prunes it.
- **Momentum (`thanks.html`):** `thanks-value-first-cta-copy` / `cta-thanks-value-suffix-vs-bare` (both ~0 to +8%, per-segment "my" can read consumer-y for CFO/CISO); `thanks-yes-ladder-momentum` (qualified, ~flat-to-+6% — Zeigarnik is weak per 2025 meta-analysis; "step 1 of 2" must stay literally true); `thanks-enrichment-proof-lead` (null, guard on `enrich.usable>0`); `thanks-urgency-context-feature` (null — extend context key to `role__tier__urgency`).
- **Booked (`site_cta.html`):** `booked-add-to-calendar-self-schedule` (qualified — corrected to a 3–10pt absolute no-show drop *among savers*, ~+2–8% blended; hold arm C until a real scheduler exists); `booked-inspector-vs-share-proof` (null). First lane with a **delayed reward** (attended/no-show), handled by `PosteriorStore.update` when the outcome resolves.

---

## 5. Provenance-as-a-lever (the signature finding)

**Does showing verification/receipts and dialing the tier (1→4) lift or depress conversion?** The honest answer from verification: **the mechanism is real and well-evidenced; the magnitude is not, and the direction flips by audience and tier.**

**What the evidence actually says (after correcting citations):**
- **Overt personalization is non-monotonic.** The defensible curve comes from the *Personalization Backfire* lab study (Behavioral Sciences 2025, n=360) and the inverted-U AI-ad work (JAR 2025): relevance lifts engagement up to an inflection, past which **perceived surveillance triggers reactance** and depresses intent. Crucially, the backfire fired only for **high-PII / high-intensity** personalization — *moderate, contextual* personalization did **not** backfire even under elevated privacy concern. Tiers 1–3 here are contextual; **tier 4 (naming title+company unprompted) is the high-PII regime** the literature flags.
- **The inflection is earlier for Helix.** B2B-healthcare buyers are the high-need-for-cognition, risk-averse segment for whom Lambillotte (2022) shows transparency help is *conditional*; Gartner found 53% of B2B buyers say personalization harmed their experience. Education career-switchers sit closer to the (more forgiving) B2C evidence.
- **Control beats disclosure-alone.** Tucker (2014, JMR) ~doubled personalized-ad CTR purely by adding a privacy *control* (targeting unchanged); Kim/Barasz/John (2019, JCR) show transparency backfires **only when it reveals an *unacceptable* flow** (inferred + off-site). The `lp_entry` line "even though you never filled out a form" is a textbook unacceptable-flow disclosure.
- Corrected expected effects are **low single digits** and only on **mis-tiered segments** — with a real downside tail. On a 10-seed cohort, no tier comparison is statistically detectable; the honest value is **qualitative ceiling-finding**, not a measured lift.

**Recommended transparency-dosage test design:**
1. **Tier as a capped context dimension** (`prov-tier-dial-as-bandit-context`). Extend the bandit key `segment → (segment, tier)`; route the production tier from `bandit.select()` over arms **{T1, T2, T3}**. **Tier 4 is held OUT of the live pool by an allowlist** — the privacy twin of the planted-lie arm: it must be *unreachable by construction*, not by hoping the bandit avoids it. (Tiers 1–3 only re-frame already-source-tagged facts → truth boundary safe by construction.)
2. **Reward on the downstream outcome** (booked assessment / class signup), **not the click** — plus an unsubscribe/bounce **hard negative** (`b += 3`). A creepy tier that spikes the click but tanks trust is then punished, not rewarded.
3. **Tier-4 framing sub-test (demo-gated, off live auto-pool):** A "gotcha" frame vs B "consent+control" frame (drop the unacceptable-flow clause, add a working "show me the safe version" → tier-1 switch). Measure **bounce/scroll-depth as the primary endpoint, CTA secondary**; treat a drop-to-tier-1 click as reward 0 + a creepiness flag.
4. **Provenance prominence arms** (`prov-withheld-count-prominence`: corrected +1–5% B2B / 0–3% edu; `prov-source-receipt-default-open`: segment-gate to it_security/quality/cfo, ~flat-to-negative for low-skepticism edu; `prov-justify-data-use-line`: corrected ~wash for high-NFC Helix, +1–4% for edu — **one sentence, not the long paragraph**).

**Net recommendation:** treat radical transparency as a **dosable** variable the bandit tunes per segment, with tier-4 reveal and any unprovable count permanently outside the optimizable pool. Expect the wins to be small and concentrated in mis-tiered segments; the strategic value is proving the creepiness ceiling exists and where it sits — which *is* the product thesis.

---

## 6. Recommended first wave (sequenced — highest ICE, lowest effort, fastest signal first)

| # | Change | Optimizer arm / feature to add | Metric & sample-size note |
|---|---|---|---|
| **1** | **Helix clinops headline arm C** — add `('C','specificity','Reduce average length of stay by 1.2 days',['c_los','c_deployed','c_speed'])` to `ROLE_ANGLES['clinops']`. | New 3rd Beta arm per clinops micro-segment; auto-expanded by `build_variants()`, Gate-cleared by `build_action_pool()`. Zero new code. | site→CTA CTR, clinops only. Corrected +0–4% → needs a **large n** (plan for a long run; at <~1k weekly segment sessions expect inconclusive). Cheapest possible first arm — ships the wiring pattern. |
| **2** | **Helix site CTA pronoun arm** — render `{{ variant.cta_text }}`; arms A "Start your ROI assessment" / B "Start my…". | CTA suffix on `variant_id` (`…__ctaP1/__ctaP2`) → distinct Beta arm via existing `oracle._arm_of`. No bandit changes. | site→booked CTR per role. Corrected 0 to +6% (~+2–3%). Power for a ~3pt MDE; let bandit down-weight "my" for cfo/it_security. |
| **3** | **Education CTA onto the bandit** — `ARCHETYPES[*].cta`: string → `[(A,current),(B,first-person-outcome)]`; `_cta()` calls `bandit.select(f"{arch.id}__t{tier}")`. | Brings the **entire edu CTA into the optimizer** (currently static). Reward = signup CTA click (`cta_events`). | landing→signup CTR per archetype. Corrected +3–12% (~+5–7%); warmest/most-applicable evidence in the program. Real null chance on thin segments — warm-start priors. |
| **4** | **lp_entry button + entry logging** — `ENTRY_CTA_ARMS = {A:"Go →", B:"Build my page →"}`; **first add the enter-rate event** the gate currently lacks. | One-context `ThompsonBandit` keyed `__lp_entry__`; reward = `/lp` match. claim_ids=[] → Gate-trivial. | email-capture rate. Corrected +3–12% directional. **Instrumentation is the gating work** — ship logging in this wave so the gate becomes measurable at all. |
| **5** | **Helix form proof strip** — render `c_deployed/c_soc2/c_hipaa` (verbatim, via `gate.verify_variant`) beside the form card; arms {none, strip}. | New `form_proof` context feature; bandit learns *which* proven claim leads per role. | form-completion (`/submit`), measured **and** downstream booked rate. Corrected +3–12% (~+5–8%); strongest for it_security/quality. |
| **6** | **Helix form risk-reversal — split framing** — arms {none, affirmative-privacy, never-sell-negation}, one line above the submit. | New `submit_reassurance` context feature, routed through Gate (clauses must be operationally true of the flow). | form-completion + unsubscribe-as-negative. Corrected −5 to +10% — **the test's job is to catch the negation backfire** (Aagaard −18.7%) before it ships, not to assume a win. |

**Sequencing rationale:** #1–#2 are near-zero-effort and prove the Helix arm-suffix wiring; #3–#4 unlock the two funnels currently *outside* the optimizer (edu CTA, entry gate) — the highest structural leverage; #5–#6 are cheap Helix conversion-point trust tests, with #6 deliberately framed to surface a known downside. Across all six: reward on the **deepest reliable signal** (booked/enrolled where possible, not the immediate click), warm-start posteriors from the existing deterministic rules so 10-seed-cohort demos degrade gracefully, and treat every corrected single-digit lift as a directional prior to be replaced by the surface's own measured rate — not a forecast to bank.
