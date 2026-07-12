# Design principles alignment — WWDC26 "Principles of great design" + M3 Expressive

> Source: Apple Developer, *WWDC26: Principles of great design* (youtu.be/Xa9L2yx_QH8) +
> Material 3 Expressive. The loop drives the app toward following these. Status per principle:

| # | Apple principle | How Provenance follows it | Status |
|---|---|---|---|
| 1 | **Purpose** (intention; what *not* to build) | The whole app is one spine — "prove every move." Vanity CRUD was cut; every section maps to a pillar. | ✅ strong |
| 2 | **Agency** (control + **forgiveness**: undo, confirm destructive) | Filter/Sort/View are non-destructive query params; create has Cancel. Composer *forgives* by blocking an unshippable send and naming why. | ◑ add success/undo affordance |
| 3 | **Responsibility** (privacy: ask at the right moment, only what's needed, say *why*; safety: anticipate AI error; → trust) | **This is the product.** say/allude/hold surface policy, consent on the form, the Gate blocks unprovable AI claims by construction, drift re-verifies, the receipt shows *why*. | ✅ core |
| 4 | **Familiarity** (metaphors, conventions; don't reinvent icons) | Standard CRM metaphors, ⌘K, Phosphor icons used to convention, records/pipeline language. | ✅ |
| 5 | **Consistency** (look-same → behave-same; consistent placement) | One design system (quiet.css) across every page; nav, buttons, pills, pageheads identical everywhere. | ✅ |
| 6 | **Flexibility** (context/device/ability; personalization) | Responsive breakpoints; reduced-motion honoured; filter/sort/view personalize the table. *Gaps: deeper a11y, saved views.* | ◑ deepen |
| 7 | **Simplicity / Clarity** (strip the unnecessary; hierarchy of order/spacing/contrast) | Quiet Workspace: color only in data, strong type hierarchy, generous spacing, the agent distills complex state into a sourced answer. | ✅ |
| 8 | **Craft** (high-quality materials: fonts, light/dark, icons, **responsive animation w/ immediate feedback**, no jank) | Inter/Inter Display, Spatial Liquid Glass, spring press, scroll-reveal, focus-visible rings, global reduced-motion guard, sizes matched to attio. **Light-only by decision** (brand appearance is light like attio.com — does not follow OS dark). | ✅ |
| 9 | **Delight** (target an emotion — relaxed/confident — not confetti) | The calm Quiet Workspace + restrained spring motion is engineered for "confident, unhurried." | ✅ |

**M3 Expressive layer:** spring-physics motion (`--ease-spring`), expressive scroll-reveal, shape-morph on press, bold display type, Spatial Liquid Glass depth. ✅ applied (light-compatible; dark Carved-Hardware canvas deliberately skipped).

## Roadmap (loop order)
1. ✅ Craft pass — focus-visible feedback, expressive shape-morph press, global reduced-motion guard (v1.4).
2. ✅ **Light/dark** — built full `prefers-color-scheme` dark mode, then **removed it by decision**: the product is light-only to match attio.com (which does not follow OS appearance). Token indirection (`--surface`/`--on-*`) kept for clean light values.
3. ✅ **Agency/forgiveness** — create-record lands on a success banner with **Undo** (`/records/undo` → `cohort.remove`); transparent "stamped source: manual".
4. ✅ **Flexibility/a11y** — skip-to-content link + `#q-main` landmark, focus-visible rings, reduced-motion guard. *(Deeper: aria-option roles, contrast audit — ongoing.)*

**Status: the app now follows the WWDC26 + M3 Expressive principles** across all primary surfaces. Remaining follow-up: dark mode for the legacy atlas/style lab pages (currently light-only).
