# Seam contract — Designer DOM (`data-testid` map the WF-DESIGN E2E suite drives)

> Pinned P6a-gate contract. The designer UI (T-03/T-04) exposes these; the E2E suite (T-08) asserts against these — both sides build to THIS, never to whatever got built. Naming: `sd-` prefix, kebab-case, ids interpolated.

| Element | `data-testid` | Notes (maps to walkthrough Q) |
|---|---|---|
| Section card | `sd-section-{section_id}` | one per registry section, page order |
| Personalize toggle | `sd-personalize-{section_id}` | Q1; off = section generic |
| Goal text | `sd-goal-{section_id}` | Q2 |
| Channel chips | `sd-channels-{section_id}` | Q3 |
| Add text/image target | `sd-add-text-{section_id}` / `sd-add-image-{section_id}` | Q1 (0/1/many) |
| Text target card | `sd-text-{section_id}-{slot_id}` | contains mode/policy/strategy/workflow controls |
| Mode select | `sd-mode-{slot_id}` | Q4: deterministic \| generative |
| Workflow select | `sd-workflow-{slot_id}` / `sd-workflow-{surface_id}` | Q4: prebuilt \| realtime (live shows warning) |
| Strategy select | `sd-strategy-{slot_id}` | Q5 |
| Policy select | `sd-policy-{slot_id}` | Q6: say/allude/hold |
| Prompt editor | `sd-prompt-{slot_id}` | visible iff mode=generative |
| Gate verdict badge | `sd-gate-{target_id}` | Q6; pass/blocked + reason |
| Receipt panel | `sd-receipt-{target_id}` | S4.1 fields incl. cache_key + rules_version |
| Image target card | `sd-image-{section_id}-{surface_id}` | thumbnail + load badge |
| Latency badge | `sd-latency-{target_id}` | Q8: `instant` \| `~2s swap` \| `blocking⚠` |
| Cost badge | `sd-cost-{target_id}` | Q9: $/gen + baked-states count ("8 of 30") |
| Agent graph | `sd-graph-{section_id}` | Q10; nodes clickable → input/decision/output |
| Evals panel | `sd-evals-{section_id}` | gate_pass, hold_never_ships, brain_score |
| Observability ledger | `sd-observe-{section_id}` | per-section event rows (poll-since-seq) |
| A/B panel | `sd-ab-{target_id}` | posteriors per route + lift vs control (S4.2) |
| Drift status | `sd-drift-{target_id}` | active/paused + rules_version attribution (S4.3) |
| Staged diff drawer | `sd-staged` (existing `#staged-changes` gains testid) | every edit stages YAML to `rules/<tenant>_sections.yaml` |
| Dev/audit toggle | `sd-devtoggle` | folds in engineer trace/audit (R32) |

**Ease-of-use assertion (Q11, walkthrough §5.F):** all of the above for one section reachable within its `sd-section-{id}` card (one screen, no code); labels plain-English.
