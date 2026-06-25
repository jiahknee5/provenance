### Artifact replacement without canonical sync

**Failure mode:** Diagrams are updated ad hoc in thread discussions, but the repository artifact set remains stale or incomplete.

**Harness fix:**
- Require any architecture-thread decision that changes events, streams, or participants to update the canonical markdown artifact set in the same PR.
- Treat the field-purpose/domain-model document as the schema-facing companion to the diagrams.
- Add a checklist item in review: "Did context map, aggregate model, runtime diagrams, and field-purpose model all update together?"

**Automated check idea:**
- When files matching `Event-Catalog*`, `Event-Envelope*`, or `Stream-Types*` change, CI requires a corresponding diff in the canonical artifact directory.