# apt — mini brand spec (W7-C)

**The idea in one sentence:** the counter of the `a` is a checkmark — the proof
lives inside the word itself, so at small sizes it reads as a normal `a` and at
size the verification reveals.

Wordmark-first system: the custom geometric wordmark `apt` came first; the
monogram is its `a`, extracted. One glyph, one system — never pair the chip and
the wordmark side by side (the `a` would appear twice).

## Grid + construction

- 64-unit em, strict grid. Wordmark: baseline y=50, x-height 32 (y 18–50),
  `p` descender to y=63, `t` ascender to y=10.
- Bowls are full circles (R=16 at wordmark scale); stems occupy the bowl's
  outermost stroke-width, squared to x-height/baseline.
- Stroke: 11 units. One optical exception: the `t` crossbar is 9.5 (horizontals
  read heavier than verticals at equal weight).
- Terminals cut square (no round caps). Letter gaps 6 units, stem-to-stem;
  the `t` sits 2 units tighter against the `p` bowl's curve.
- Monogram tile: the same `a` at bowl R=22 / stroke 11, centered on 64×64
  (x-height 44, y 10–54).
- The check counter: two 45° strokes (band 7 units at monogram scale, scaling
  with the counter) clipped inside the round r=11 counter. It is cut geometry —
  a single evenodd path, never a mask or overlay. Generator provenance is
  documented in the SVG comments; all files share the identical path data.

## Clearspace + minimum sizes

- Clearspace = the width of the check (the counter diameter: 22/64 of the mark's
  height) on all four sides. Same rule for the wordmark, measured on its `a`.
- Minimum sizes: mark 16px (reads as an `a`; the check is designed to reveal at
  ≥24px and reads clearly at 32px). Wordmark 32px wide. App chip 16px.
- Do not expect the check to communicate below 24px — that is by design
  (second-read principle), not a defect.

## Color

- Ink: `#0f1729` on light surfaces (`logo-mark.svg`, `logo-lockup.svg`).
- White: `#ffffff` on dark or brand surfaces (`logo-mark-dark.svg`).
- App chip: white mark on the `#2E6FF5 → #1B4DD1` gradient, rounded square,
  radius 14/64 (`favicon.svg`, rasters). The gradient lives on the chip only.
- Gold `#c9a24b` is the product's receipt-dot accent. It belongs to product UI
  (and the shelved "signed-a" concept) — it is not part of the shipped mark.

## Don'ts

- No stretching, skewing, or rotating.
- No recoloring beyond ink / white / white-on-chip.
- No gradient on the mark itself at small sizes — gradient is chip-only.
- No round caps, no outlines around the mark, no drop shadows.
- Never place the chip next to the wordmark (double-`a`).
- Don't redraw the check; it is fixed geometry, not a glyph from a font.

## Files

- `logo-mark.svg` / `logo-mark-dark.svg` — monogram, ink / white.
- `logo-lockup.svg` — the wordmark (the lockup IS the wordmark).
- `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png` — app chip.
- `concepts/` — v1 diamond system (`v1-*.svg`), earlier sketches, and the two
  unshipped W7-C treatments (`w7c-signed-a.svg`, `w7c-proof-stroke.svg`).
- Evaluation evidence: `.qa/w7c-evaluation-sheet.png` (squint / monochrome /
  silhouette / lineup / in-situ gates, all three treatments).
