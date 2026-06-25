### Canonical artifact set

The repository artifact set is composed of separate markdown files:

- `01-context-map.md`
- `02-aggregate-model.md`
- `03-reaction-loop.md`
- `04-sequence-diagram.md`
- `05-safety-policy.md`
- `06-field-purpose-and-domain-data-model.md`

These files reflect the current canonical architecture, including:
- first-class identity resolution,
- `Optimizer` as the top-level decisioning participant,
- explicit `policy_evaluated` and expanded review/dispatch lifecycle paths,
- and a richer `DecisionTrace` / event-envelope model.

Rule:
When the event catalog or envelope changes, these artifacts must be updated in the same change set.