# .rapid/EVAL — the locked WF-DESIGN eval harness (task-00)

**One source of truth, in precedence order:**

1. **`docs/workflows.json` (`WF-DESIGN-*` entries) is authoritative.** Each entry is one
   matrix row (SECTION-DESIGNER-EXAMPLES.md §3, PRD R37): per-node `{in, proc, out}`,
   a `golden` assertion, and the `test` that materializes it.
2. **`tests/test_wf_design_matrix.py` is the pytest materialization** of those entries —
   one test per row plus the four engine invariants that pass today (R35a cost-logging,
   hold-never-ships ×2, copy-gate blocks superlative/comparative/competitor).
3. **This directory is the locked snapshot** (`MANIFEST.json`): which row maps to which
   test, its activation status, and the ship-gate rule. It never redefines a row — if
   MANIFEST and workflows.json ever disagree, workflows.json wins and MANIFEST is
   regenerated from it.

**Lock semantics (CONSTITUTION Art VII):** the harness is immutable once locked. Row
tests may not be edited, weakened, xfailed, or deleted by build waves. They activate on
their own as waves land, via `pytest.importorskip` guards (sections registry → T-01/W0,
decision_pool → T-02/W1, skyfi_site → T-07/W1) plus the `rules/demo_scenarios.yaml`
seed (T-08/W3). The 5 pre-existing property tests are untouched and stay immutable.

**Ship gate:** all 30 rows active (no skips) and green at W5, alongside the 4
always-active invariants. A skipped row at W5 is a ship blocker, not a pass.
