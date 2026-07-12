# Seam contract — Per-decision cleared pool (`pipeline/personalization/decision_pool.py`)

> Pinned P6a-gate contract. The ONE object that binds Gate + bandit + drift + provenance per personalization decision (PRD §5 "one system, not four features"). The designer UI, serving path, and WF-DESIGN tests all consume THIS.

**Key (`[PANEL — locked]`):** posterior-store identity = `(tenant, channel)` exactly as `optimizer/live.py:77-89` today; segment string = **`audience_route`** (`b2b_hire|b2b_upskill|individual|neutral`); pool id = `tenant:section_id:target_id`. Cells with <30 resolved impressions fall back to the pooled `_all` cell.

```python
class DecisionPool:
    # --- pool construction (Art II: structural, never a filter) ---
    def cleared_pool(tenant, section_id, target_id) -> list[Variant]
        # ONLY Gate-cleared variants exist in the pool. A blocked/held/red candidate
        # is never constructed into it (build_action_pool pattern, variants.py:81).

    # --- serving (S4.2/S4.4) ---
    def pick(tenant, section_id, target_id, route: str) -> Variant     # Thompson over cleared pool; _all fallback <30
    def assign_control(visit_key) -> bool                              # random holdout slice for lift
    def reward_click(pool_id, variant_id, route) / settle(...)         # online posterior updates (live.py pattern)
    def lift_report(pool_id) -> {bandit_ctr, control_ctr, lift}

    # --- drift (S4.3) ---
    def on_claims_invalidated(claim_ids) -> paused: list[variant_id]   # pause ONLY variants using affected claims;
                                                                       # paused variants leave the bandit pool atomically

    # --- provenance (S4.1) ---
    def receipt(variant_id) -> {source_id, lawful_basis, policy, gate_verdict,
                                claim_ids, cache_key, mode, workflow, rules_version}
```

**Invariants (each is a locked test):** (1) a planted lie / superlative / competitor / hold-fact candidate is 0-servable (`pick` can never return it — mirror `test_optimizer` P1); (2) `on_claims_invalidated` pauses exactly the dependent variants, no over/under-invalidation (P3); (3) every `pick` result has a `receipt`; (4) posteriors move on real events and `lift > 0` vs control on seeded traffic; (5) same visit key → same variant on replay (Art IV).
