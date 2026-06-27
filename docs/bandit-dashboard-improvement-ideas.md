# Bandit Dashboard Improvement Ideas

Created 2026-06-27 after moving the dashboard under `/optimizer`.

## Functionality That Should Exist Next

- Real traffic connection: replace or supplement the simulated stream with the existing `/api/optimizer/live` snapshot so the dashboard can show actual site/outreach impressions, clicks, no-click settlements, and measured lift.
- Segment drilldown: clicking a segment should show the underlying audience definition, sample size, active claim policy, and which recipients contributed rewards.
- Arm provenance drawer: every copy arm should expose its source claims, evidence URLs, Gate verdict, policy reason, and last verification time.
- Safety audit timeline: show when an arm was added, vetoed, archived, restored, or affected by drift re-verification.
- Minimum sample guidance: add “not enough evidence yet” warnings when sends are too low for a human to act on P(Best) or credible intervals.
- Decision recommendations: translate posterior state into suggested actions such as keep exploring, archive underperformer, review unsubscribe spike, promote winner, or split segment.
- Counterfactual lie proof: show what the unconstrained bandit would have selected if the planted lie were allowed, next to the Gate-constrained result.
- Control holdout view: compare adaptive bandit traffic against random/control serving, including CTR lift and confidence.
- Reward decomposition: separate no-clicks, meetings, unsubscribes, and negative weighting so operators can see whether an arm is weak because it fails to convert or because it burns the list.
- Alert thresholds: make unsubscribe SLA, minimum P(Best), credible interval width, and regret thresholds configurable per tenant/campaign.
- Exportable run report: generate a concise experiment summary with winners, blocked arms, lift, safety events, and recommended next steps.
- Persistent injected arms: currently injected arms are session-local in the browser. Store them server-side so the experiment can be resumed and audited.
- Experiment comparison: compare two dashboard runs side by side to show how different Gate settings, priors, or segment definitions affect convergence.
- Prior editor: allow specialists to choose neutral priors, informative priors from historical campaigns, or conservative priors for riskier claims.
- Simulation scenario presets: provide canned examples like “clear winner,” “unsafe high-CTR lie,” “noisy close arms,” and “unsubscribe spike” for demos and onboarding.

## UX Improvements

- Make the left controls pane sticky so operators can pause, fast-forward, or toggle Gate masking while reviewing long arm lists.
- Add a compact legend directly under the belief curve for arm colors, status, P(Best), and credible interval width.
- Let users pin the decision stream below the belief curve on smaller screens to preserve the two-pane mental model.
- Add inline empty states for early experiments explaining what will appear after the first few sends.
- Add “why did this arm get pulled?” details to each live decision event, including sampled theta values for all active arms.
- Add a guided onboarding mode that starts with a frozen scenario and advances one send at a time.
- Add copy review controls: edit draft copy, clone an arm, retire an arm with a reason, and mark an arm ready for production.
- Add keyboard shortcuts for pause/resume, fast-forward, segment switching, and opening the guide.
- Add “safe to act?” badges that combine sample size, P(Best), credible interval width, and list-burn risk into one operational status.

## Engineering Notes

- Keep the dashboard under the Optimizer nav so the shell highlights the correct product area.
- Avoid adding more standalone styling; use `shell.html` and `quiet.css` primitives where practical.
- Preserve the current simulation because it is useful for demos, but layer real API-backed data behind a mode switch.
- Any persistent arm injection should include validation for claim IDs and Gate verdicts before an arm becomes selectable.
