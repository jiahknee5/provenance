# Attio.com landing — high-fidelity design prompt (our design language)

> Reverse-designed from the live attio.com landing page (captured 2026-06-24 via Playmwright:
> computed styles + woff2 font files + full-page scroll). Real values only. This is the design
> the Provenance app replicates. The app's tokens (`app/static/quiet.css`) already match Attio's;
> what this adds is the **landing composition** — the big hero, showcase, logo strip, spacing.

## The recreation prompt

Build a calm, premium B2B SaaS landing page that signals engineering rigor and restraint.
**Canvas** pure white `#FFFFFF` (very slightly cool). **Ink** near-black `#16181D`; **body/secondary**
a desaturated blue-slate `#525C6E`; hairline borders `#E5E9EF`, stronger control borders `#C7CFD9`;
the only "fill" is `#F1F3F5`. **One** accent used sparingly: a calm blue `#2E6FF5` for links/active.
**Type:** `Inter Display` for headings, `Inter` for UI/body, `Tiempos Text` (use `Newsreader`) for
editorial/quotes. **Hero:** centered, enormous — an eyebrow pill (rounded, 1px hairline, soft shadow,
small chevron) → a display headline `clamp(44px, 6.2vw, 84px)`, weight **600**, letter-spacing **-0.02em**,
line-height **~1.0** (very tight, 2 lines) → a 20px medium subhead in slate, max ~46ch, line-height 1.3 →
two CTAs: a **black pill** (`#1B1E23`, white text, radius **10px**, 14px/500, ~`10px 16px`) + a **white
outline** pill (1px `#C7CFD9`). Massive vertical breathing room (hero ~120px top padding). **Product
showcase** directly below: a horizontal **tab switcher** (Ask · Data model · Workflows · Reporting) with a
1px baseline and a 2px ink underline under the active tab, framing a large **rounded screenshot card**
(radius ~14px, hairline border, soft shadow) of the real product. **Logo strip:** a centered row of ~6
**monochrome** customer wordmarks, evenly spaced, muted. **Feature sections:** generous, often on a faint
**dotted-grid** background; bento cards with hairline borders and soft shadows; section headers reuse the
display type at `clamp(30px, 3.5vw, 48px)`. **Motion:** calm, short (0.15–0.28s, `cubic-bezier(.2,0,0,1)`);
nothing bounces. **Restraint:** color only in product data; no gradients-as-decoration, no heavy shadows.

## Measured values (verbatim from attio.com)

| Role | Value (real) | Our token |
|---|---|---|
| Page bg | `lab(99.99%…)` ≈ `#FFFFFF` | `--paper` ✓ |
| Hero headline | `Inter Display` 64px / **600** / `-1.28px` (-0.02em) / lh **64px (1.0)**, color ≈ `#16181D` | `--font-display`, new `.q-display` |
| Subhead | `Inter` 20px / 500 / `-0.2px` / lh 26px, color ≈ `#525C6E` | new `--slate2`, `.q-lede` |
| Primary CTA | bg ≈ `#1B1E23`, text ≈ `#F3F4F6`, radius **10px**, 14px/500 | `--cta`, `--r-btn` ✓ |
| Outline CTA | 1px `#C7CFD9`, text `#525C6E`, radius 10px | `--border` ✓ |
| Nav height | `68px` | new `--landing-nav-h` |
| Fonts loaded | Inter (reg/med/semi/bold), Inter Display (med/semi/bold), Tiempos Text (reg/italic) | Inter / Inter Display / Newsreader ✓ |

## Landing vocabulary to build (components)
1. **Hero** — eyebrow pill · `.q-display` headline · `.q-lede` subhead · dual CTA · centered, huge spacing.
2. **Product showcase** — `.q-showcase` tab switcher (underline indicator) + rounded screenshot frame.
3. **Logo strip** — `.q-logos` centered monochrome wordmarks.
4. **Dotted-grid section** — `.q-dotgrid` faint background for feature blocks.
5. **Section header** — `.q-display.sm` + `.q-lede` centered.

## Diff vs the current app (what changes)
- The app already uses Attio's exact fonts + palette + 10px radius. ✓
- ADD: the big-hero display scale, the showcase tabs, the logo strip, the dotted-grid, landing spacing.
- `/` becomes the Attio-style **home** featuring the live demo; `/demo` is the front door.
- Shell pages adopt the bigger `.q-display` page-heads + more generous spacing for consistency.
