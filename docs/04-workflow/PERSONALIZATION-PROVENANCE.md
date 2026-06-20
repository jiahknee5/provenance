# Super-personalization — every signal, and where it comes from

> "How personalized can a website get the instant it loads — and where does each fact come
> from?" Built as `pipeline/personalization/*`, served at **`/personalize`**. One synthetic
> persona (Maya), 52 signals, 7 escalating tiers, two render modes. DECISIONS R18.

This is the **personal** layer sitting on top of the existing claim Gate. It reuses the
funnel's [surface policy](FUNNEL-AND-CUSTOMER-RECORD.md) (`say` / `allude` / `hold`) as its
spine, so it inherits the same auditable anti-creepiness control.

---

## 1. The core idea: creepy ≠ more data, creepy = no policy

Two render modes read the **same** catalog:

| Mode | What it does | At the top tier |
|---|---|---|
| **Tasteful** | honours the surface policy | states 6 facts, steers on 17, **withholds 29** |
| **Creepy** 👁 | switches the policy off | prints **all 52**, each tagged with its source |

Flip the toggle and nothing new is *collected* — the only thing removed is the restraint.
That contrast is the lesson, and it makes "creepy" a structural property (the absence of a
surface policy), not a vibe. Every creepy line still carries its provenance — the repo's
"can't say what it can't prove" thesis, applied to what we *know about you* instead of what
*we say*.

## 2. The tiers — landing page → Google login → everything

Each tier adds one or more **provenance classes**; higher tiers inherit everything below
(monotonic — proven in `test_tiers_are_monotonic`).

| # | Tier | Login | What unlocks | Knowable facts |
|---|---|---|---|---|
| 0 | **Anonymous landing** | none | the HTTP request + a little JS | 12 |
| 1 | **Returning visitor** | cookie | our first-party behavioral logs | +6 |
| 2 | **Identified** | email | what they declared, + email-hash lookups | +5 |
| 3 | **Signed in with Google** | google | **OAuth scopes — the big jump** | +8 |
| 4 | **+ Purchased append** | google | a data-broker match | +11 |
| 5 | **+ Existing customer** | google | our own CRM | +5 |
| 6 | **Full identity graph** | google | cross-device + offline, fused | +5 |

### "If it were just a landing page, how could we personalize it?" (Tier 0, $0)
Before any login or cookie, the request itself tells us a lot — and we'd pay nothing:
- **Location** — IP → city/ZIP (MaxMind GeoIP2). Company, if it's an office IP (Clearbit Reveal).
- **Device** — User-Agent + Client Hints: model, OS, browser; infer device *age* → budget.
- **Context** — local time & timezone, language ranking, dark mode, **battery level**.
- **Intent** — the referrer + UTM params: which ad/campaign/creative sent you.
- **Identity without a cookie** — a canvas/font/GPU **fingerprint** (FingerprintJS) that
  re-identifies you on your next "anonymous" visit. *(creepiness 5)*

### "What if we had a Google login — how much more enrichment?" (Tier 3)
One tap on *Sign in with Google* is the single biggest jump. The **profile** scope is
benign (verified name, photo). But the same consent screen can grant — and most people
don't read it — `calendar.readonly`, `gmail.metadata`, YouTube history, `People` (contacts),
and Maps **location history**. That's: your appointments, who emails you (→ inferred
purchases), what you watch, your address book, and everywhere you go. `test_google_login_
unlocks_oauth_and_strictly_more` asserts the jump is real and is *all* OAuth-sourced.

## 3. Where the data comes from — the six provenance classes

| Class | Plain meaning | Real-world source | Cost |
|---|---|---|---|
| **observed** | collected by us, passively, at load | HTTP + JS; reverse-IP; fingerprint | $0 (a few ¢ for reverse-IP/fingerprint) |
| **first_party** | our own logs / CRM | site analytics, our database | $0 (we own it) |
| **declared** | they typed it | a form / newsletter / signup | $0 |
| **oauth** | granted via Google sign-in | OAuth scopes | $0 (the price is the permission) |
| **broker** | purchased append | Acxiom / Experian / Epsilon / Oracle Data Cloud | ~$0.05–0.25 / record |
| **identity_graph** | cross-device + offline | LiveRamp / Tapad; loyalty + card panels; smart-TV ACR | $$ subscription |

The full free-vs-paid vendor list (and the lawful-basis question per source) lives on the
existing [enrichment catalog](../../app/templates/enrichment_catalog.html) (`/enrichment-catalog`).

## 4. The provenance ledger — every fact carries a receipt

The page renders a ledger row per signal: **data point · synthetic value · where it's from
(class + vendor) · cost · creepiness (1–5) · surface policy · disposition**. Disposition is
exactly the policy decision (`test_ledger_disposition_matches_policy`):

- `said` — stated literally (only `say` facts: what you declared / our relationship)
- `steer` — shapes which class/offer we feature, but is never recited (`allude`)
- `withheld` — known, deliberately held back (`hold`: sensitive or non-consented)
- `shown` — printed verbatim (creepy mode only)
- `locked` — needs a higher tier

## 5. What proves it works — `tests/test_personalize.py` (10)

catalog integrity · tier monotonicity · the Google-login jump is strictly-more-and-all-OAuth
· **tasteful never surfaces a `hold` fact** (value *or* its sentence) · creepy surfaces every
available fact **with provenance** · creepy ⊇ tasteful · ledger disposition == policy ·
withheld-count grows with knowledge · deterministic replay · bad input → safe default.

## 6. Honest scope

- **100% synthetic.** One persona (Maya); every value fabricated. No real PII, no paid API
  called — broker/identity rows are *documented*, not invoked (mirrors `enrichment/catalog.py`).
- **Deterministic.** "Current time" (11:47 PM) is part of the persona — no wall clock, no RNG.
- **Text only, for now.** The same signals would drive the *layout* next: reorder sections,
  swap the hero, change the offer. The architecture (catalog → tier → policy → ledger) is
  identical; only the renderer's output target changes. That's the next layer.
