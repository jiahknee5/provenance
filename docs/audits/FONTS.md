# Font audit — every user-facing template (W6-B, 2026-07-12)

Scope: all `app/templates/*.html` + the static CSS they load (`atlas.css`, `style.css`, `quiet.css`).
Expectations audited against:

- **apt-shell pages** → Inter only, loaded once by `_apt_shell.html`.
- **Replicas + ad mockups** → their brand fonts (gauntlet: Archivo + Inter + JetBrains Mono;
  planet: Montserrat, the Gotham SSm stand-in, + JetBrains Mono; skyfi: Hanken Grotesk + DM Mono).
- **No wasted loads** — no family or weight fetched that nothing renders.
- **Consistent mono stack** for code/receipts: `ui-monospace,Menlo,monospace` in consoles;
  replicas lead with their brand mono and fall back to the same stack.

Weight notes: `<b>`/`<strong>` resolve to 700, `font:` shorthand without a weight resolves to 400 —
both counted as "used".

## Apt-shell pages (Inter via `_apt_shell.html`)

| Template | Fonts loaded | Fonts used | Verdict | Fix applied |
|---|---|---|---|---|
| `_apt_shell.html` (partial) | Inter 400;500;600;700;800 | Inter 400–800 (800 used by every console's stat numerals) | OK | — |
| `_apt_sidebar.html` (partial) | — (inherits shell) | Inter | OK | — |
| `_sd_designer.html` (partial) | — (inherits shell) | Inter + `ui-monospace,Menlo,monospace` | OK | — |
| `_sd_drawer.html` (partial) | — (inherits shell) | Inter + `ui-monospace,Menlo,monospace` | OK | — |
| `api_costs.html` | shell Inter | Inter + mono stack | OK | — |
| `apt_demo_sitemap.html` | shell Inter | Inter | OK | — |
| `apt_dev_hub.html` | shell Inter | Inter | OK | — |
| `demo_channel_gallery.html` | shell Inter | Inter | OK | — |
| `demo_email_card.html` (partial) | — (inherits gallery/shell) | Inter | OK | — |
| `observatory.html` | shell Inter | Inter + mono | Mono-stack outlier: `ui-monospace,SFMono-Regular,Menlo,monospace` on `pre` | Aligned to `ui-monospace,Menlo,monospace` |
| `gauntlet_dev.html` | shell Inter | Inter + mono stack | OK | — |
| `gauntlet_dev_business.html` | shell Inter | Inter + mono stack | OK | — |
| `planet_dev.html` | shell Inter | Inter + mono stack | OK | — |
| `planet_dev_business.html` | shell Inter | Inter + mono stack | OK | — |
| `skyfi_dev.html` | shell Inter | Inter (no mono declarations of its own) | OK | — |
| `skyfi_dev_business.html` | shell Inter | Inter + mono stack | OK | — |

Consoles use `<em>` occasionally without loading Inter italic — browsers synthesize the oblique;
consistent across all consoles, left as-is (loading an italic axis for a handful of `<em>`s is the
heavier trade).

## Replicas

| Template | Fonts loaded (before) | Fonts used | Verdict | Fix applied |
|---|---|---|---|---|
| `gauntlet_site.html` | Archivo 500;600;700 + Inter 400;500;600 + JBM 400;500;700 | Archivo 600,700(`<b>`); Inter 400,500,600; JBM 400,500,700 | Archivo 500 never rendered | Trimmed Archivo → 600;700 |
| `planet_site.html` | Montserrat ital,200–700;1,400 + JBM 400;500;700 | Montserrat 200,300,400,500,600,700(`<b>`), **no italics**; JBM 400,500 | Italic-400 file + JBM 700 wasted | Montserrat → wght@200–700 upright only; JBM → 400;500 |
| `skyfi_site.html` | Hanken Grotesk 300–800 + DM Mono 400;500 | HG 300–700 (800 was only the recreated text wordmark, now replaced by the real SVG); DM Mono 400,500 | HG 800 no longer used; **bug: two labels asked DM Mono for 600, a weight DM Mono doesn't have (300/400/500 only) → synthetic faux-bold** | HG → 300–700; `font:600 … var(--mono)` → `font:500` on `.gnav .grp .lbl` and `.hero .eyebrow` |

## Ad mockups + landing-page grids

| Template | Fonts loaded (before) | Fonts used | Verdict | Fix applied |
|---|---|---|---|---|
| `gauntlet_ad.html` | Inter 400;500;600;700 + JBM 400;500 | Inter 400,500,700(`<b>`, `.av`); JBM 400 | Inter 600 + JBM 500 wasted | Inter → 400;500;700; JBM → 400 |
| `gauntlet_ad_lp.html` | Archivo 600;700 + Inter 400;500;600 + JBM 400;500 | Archivo 600,700; Inter(--ui) 400,600,**700** (×3 + 2 `<b>`); JBM 400 | **Inter 700 used but not loaded → faux bold**; Inter 500 + JBM 500 wasted | Inter → 400;600;700; JBM → 400 |
| `planet_ad.html` | Montserrat ital,200–700;1,400 + JBM 400;500;700 | Montserrat(--sans/--ui) 400,600 (+`<b>`); JBM 400; X-post body uses the system `--x-font` stack by design | 5 of 7 Montserrat files + 2 JBM weights wasted | Montserrat → 400;600;700; JBM → 400 |
| `planet_ads.html` | Montserrat ital,200–700;1,400 + JBM 400;500;700 | Montserrat 400,600,700; JBM 400; `--x-font` system stack for the timeline cards | Same waste as `planet_ad` | Montserrat → 400;600;700; JBM → 400 |
| `planet_ad_lp.html` | Montserrat ital,200–700;1,400 + JBM 400;500;700 | Montserrat 400,600,700; JBM 400,700 | Extra Montserrat weights + JBM 500 wasted | Montserrat → 400;600;700; JBM → 400;700 |

The X-post mockups intentionally render post bodies in `--x-font`
(`-apple-system,…` system stack) to match real X timeline styling — that is faithful, not a gap.

## Plain apt pages (atlas.css / style.css / quiet.css)

| Template | Fonts loaded | Fonts used | Verdict | Fix applied |
|---|---|---|---|---|
| `site.html`, `site_cta.html`, `form.html`, `thanks.html` | none (atlas.css/style.css) | system stack `-apple-system,…` from `atlas.css` body rule | OK — intentional plain look, zero font requests | — |
| `gauntlet_image_decisions.html`, `planet_image_decisions.html` | none (atlas.css/style.css) | system stack + `ui-monospace,Menlo,monospace` | OK | — |
| `showcase.html` | Inter 400;500;600;700 + **Newsreader (ital+opsz)** via quiet.css vars | Inter 400,500,600,650→700,700 via `--font-display`/`--font-ui`; `--font-serif`(.q-serif) **never used on the page** | Newsreader fetched and never rendered | Removed Newsreader from the fonts link |

quiet.css's `--font-display` names "Inter Display" first; only "Inter" is loaded so it falls through
to Inter — harmless fallback naming, no request made, left as-is.

## Cross-cutting verdicts

- **Mono stacks** now: consoles/partials `ui-monospace,Menlo,monospace` (uniform, incl. observatory);
  replicas `'<brand mono>',ui-monospace,'SF Mono',Menlo,monospace`. Consistent per class of page.
- **One real rendering bug fixed**: `gauntlet_ad_lp.html` bold UI text was synthesized (Inter 700
  missing from the load); `skyfi_site.html` mono labels asked for a nonexistent DM Mono 600.
- **SkyFi logo**: the replica's recreated text wordmark ("Sky" white + "Fi" yellow, weight 800) was
  unfaithful — the real mark is a monochrome custom-letterform SVG. Replaced with the actual brand
  assets downloaded from `https://skyfi.com/logos/skyfiLogoWhite.svg` / `skyfiLogoBlack.svg`,
  self-hosted at `app/static/skyfi/` (no hotlinking), white variant wired into nav, hero and footer
  via `{{ static_prefix }}` so the portal mount (`/skyfiapt/static/…` → `/static/…` rewrite) serves it.
