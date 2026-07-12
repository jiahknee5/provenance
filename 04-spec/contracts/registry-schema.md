# Seam contract — Section Registry schema (`rules/<tenant>_sections.yaml`)

> Pinned P6a-gate contract. Both lanes (text/image), the designer UI, the decision pool, and the tests all build against THIS. Changes require a logged decision.

```yaml
version: 1
tenant: gauntlet            # gauntlet | planet | skyfi
sections:                   # ordered = page order
  - id: hero                # unique per tenant; matches build_page region key
    label: "Hero"           # designer display name (plain English)
    region: hero            # existing page region: hero|prove|challenger|compare|cta|location
    personalize: true       # master toggle (Q1); false = section ships generic
    goal: ""                # Q2 — why this section personalizes (free text, shown on card)
    channels: [direct, search, ads, email]   # Q3 — which arrivals may personalize here
    text_targets:           # 0..n
      - slot_id: hero_headline        # unique per tenant; existing slot ids preserved
        label: "Headline"
        mode: deterministic           # deterministic | generative   (Q4)
        workflow: realtime            # deterministic→realtime only; generative→prebuilt|realtime
        strategy: objection-reframe   # Q5 — objection-reframe|social-proof|authority|scarcity-honest|loss-aversion|location-relevance|message-match|neutral
        policy: allude                # Q6 — say | allude | hold
        source: catalog               # catalog | claims
        claims: []                    # claim_ids when source=claims
        prompt: ""                    # REQUIRED iff mode=generative, else must be empty
        gate: gauntlet_tenant         # Gate rule set bounding the candidate pool (generative)
    image_targets:          # 0..n
      - surface_id: hero              # extends image_gen surfaces beyond hero|og
        label: "Hero backdrop"
        workflow: prebuilt            # prebuilt | realtime | live(discouraged, warn in UI)
        intent_rules: inherit         # inherit tenant rules/<tenant>_image.yaml or inline override
        guardrails: inherit           # inherit | inline {must_avoid:[], tier_gates:{}}
        prebuilt_states_cap: 8        # max manifest states pre-built for this target [PANEL default]
    guardrails: {}          # per-section overrides pushed down from tenant defaults
    evals: [gate_pass, hold_never_ships]   # + brain_score for image targets
```

**Validation rules (loader rejects):** unknown top-level/field keys; duplicate `id`/`slot_id`/`surface_id`; `mode: generative` with empty `prompt` or missing `gate`; `mode: deterministic` with non-empty `prompt`; `workflow: prebuilt` on a deterministic text target (meaningless — deterministic is always realtime $0); `policy` not in {say,allude,hold}.

**Loader API (`pipeline/personalization/sections.py`):**
```python
list_sections(tenant: str) -> list[dict]        # validated, cached (mirror demo_nav.load_scenarios)
get_section(tenant, section_id) -> dict
list_text_targets(tenant) -> list[dict]          # flattened, each carries section_id
list_image_targets(tenant) -> list[dict]
registry_version(tenant) -> str                  # content hash — drift attribution (rules_version)
```

**Behavior-neutral seed (Art IV):** initial YAML mirrors the existing hardcoded `slot()` ids in `gauntlet_site.py`/`planet_site.py` and surfaces hero+og. `build_page` byte-identical before/after introduction.
