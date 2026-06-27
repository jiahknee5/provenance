# Bandit Dashboard Feature Log

Logged before UI changes on 2026-06-27.

## Current Feature Inventory

- Two operating modes: `Prod SRE View` for live monitoring and `Bandit Specialist Deep-Dive` for statistical diagnostics.
- Live simulation stream that continuously sends traffic through Thompson sampling.
- Stream controls: inject candidate copy arm, pause/resume live stream, fast-forward 100 sends, reset AI memory, and adjust traffic stream pace from 100ms to 2500ms.
- Lawful Gate Masking toggle that vetoes unverified/planted lie arms while preserving visibility into their existence.
- SRE production KPIs: outreach sends, meetings booked, list burn/unsubs, and gate veto count.
- Specialist KPIs: estimated cumulative regret, policy entropy, average KL divergence, and active arm pool size.
- Exploit vs explore meter showing the current balance between winner exploitation and challenger exploration.
- Four segment tabs: CFO core tier, CFO enterprise IDN, clinical operations core tier, and enterprise IT security.
- Live posterior belief curve canvas for active copy arms, including Beta distribution curves, latent truth markers, current Monte Carlo draw dots, and chosen-arm winner annotations.
- Specialist-only cumulative regret trace canvas.
- Candidate copy arm cards showing label, internal code, copy preview, claim tags, status, sends, clicks, Beta belief parameters, estimated CTR, P(Best), and 95% credible interval.
- Arm states: learned leader, gate-vetoed lie, active, and archived with data preserved.
- Under-the-hood diagnostic accordion per arm, including alpha hits, beta misses, win confidence, Monte Carlo credible interval, and explanatory math.
- Archive/restore controls per eligible arm.
- Real-time decision stream showing segment, timestamp, selected copy arm, exploit/explore reason, Thompson sample value, and outcome.
- Specialist tables: head-to-head pairwise win probability matrix, posterior parameter table with mean/mode/variance/KL divergence, and posterior drift log.
- Inject-arm modal with angle label, internal code, email copy body, verified claim tags, simulated ground truth CTR, and simulated unsub rate.
- Engineer tour powered by Driver.js covering mode switcher, candidate injection, Monte Carlo canvas, and statistical confidence cards.
- Bayesian/statistical engine: Beta PDF, Gamma/Beta sampling, digamma, Beta KL divergence, Monte Carlo P(Best), pairwise superiority, credible intervals, policy entropy, regret tracking, and Thompson sampling choice.

## Workspace UI/UX Reference

Source inspected: deployed `/workspace` HTML at `https://provenance-production-6aa8.up.railway.app/workspace`, plus local `shell.html`, `workspace.html`, and `quiet.css`.

- Product shell: fixed left sidebar, sticky top bar, compact command button, and a single white main canvas.
- Visual language: quiet white surfaces, near-black headings, cool gray secondary text, thin hairline borders, subtle shadows, and color used only for product data/status.
- Layout density: operational, table-first, and scan-friendly. No dark glass, neon glows, radial backgrounds, large gradients, oversized cards, or decorative effects.
- Typography: Inter-based UI, small uppercase labels for metrics, 30px page title, 13-14px controls/table text, tabular mono only for data-like numbers.
- Controls: compact Phosphor icon buttons, outlined dropdown summaries, black primary action, blue signal action, ghost secondary action, mechanical switches.
- Cards and panels: 14px product-system radius, 1px hairline border, white background, minimal padding, grouped by workflow importance.
- Status treatment: `q-pill` style chips with small dot indicators; blue for SQL/provable/signal, green for customer/pass, amber for caution, red for failed or unsafe states, purple only if semantically required by an existing lifecycle category.
- Workspace UX pattern: page head first, stat cards second, main panel/table third. Toolbars keep title left and actions right. Rows/cards should be easy to compare without visual noise.

## Redesign Requirements

- Keep every feature listed above.
- Move the dashboard into the same `shell.html`/`quiet.css` design language as `/workspace`.
- Remove the purple-heavy/dark “vibe coded” appearance.
- Preserve all IDs and JavaScript hooks unless intentionally updating the corresponding script.
- Prefer Phosphor icons and existing `q-*` primitives where possible.
- Keep specialist depth available, but make it feel like an internal product diagnostic surface rather than a sci-fi control center.
