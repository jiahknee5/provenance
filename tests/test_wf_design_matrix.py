"""WF-DESIGN eval harness (task-00). Immutable once locked (Art VII). Skip-guards
activate as build waves land; ALL 30 must pass at the W5 ship gate.

One test per row of the 30-row matrix (SECTION-DESIGNER-EXAMPLES.md §3, PRD R37) —
WF-DESIGN-G01..G10 (Gauntlet), P01..P10 (Planet), S01..S10 (SkyFi). The machine-readable
journeys live in docs/workflows.json (WF-DESIGN-*), which is authoritative; this file is
their pytest materialization (see .rapid/EVAL/README.md for precedence).

Row tests activate in waves via pytest.importorskip guards (never xfail, never weakened):
  sections registry  -> pipeline.personalization.sections       (T-01, W0)
  decision pool      -> pipeline.personalization.decision_pool  (T-02, W1) — gen-text rows
  skyfi tenant       -> pipeline.personalization.skyfi_site     (T-07, W1) — S-rows
  scenario seed      -> rules/demo_scenarios.yaml               (T-08, W3)

Pinned scenario schema (T-08 builds rules/demo_scenarios.yaml TO this harness, not the
other way around):

    scenarios:
      - id: WF-DESIGN-G01            # matrix row id
        tenant: gauntlet             # gauntlet | planet | skyfi
        channel: direct              # direct|search|ads-x|ads-google|ads-meta|email
        element: "hero sub (text)"   # verbatim from ROWS below
        mode: det                    # det | gen | det-text/gen-image  (verbatim)
        workflow: realtime           # realtime|text-prebuilt|image-prebuilt|image-realtime|realtime-by-key
        strategy: neutral-baseline   # verbatim from ROWS below
        guardrail: "..."             # verbatim from ROWS below
        targets:                     # >=1 binding into rules/<tenant>_sections.yaml
          - {kind: text,  section_id: hero, slot_id: hero_sub}
          - {kind: image, section_id: hero, surface_id: hero}

Engine invariants that pass TODAY (real Gate, no decision-logic mocks) close the file:
R35a cost-logging, hold-never-ships (gauntlet + planet), and the copy-gate block of
competitor / comparative / superlative lines.
"""
from __future__ import annotations

import base64
import importlib
import json
from pathlib import Path

import pytest
import yaml
from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import creative as CR

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_PATH = ROOT / "rules" / "demo_scenarios.yaml"

c = TestClient(app)

# Guard-name -> module that must exist before the row can run (importorskip).
_MODULES = {
    "sections": "pipeline.personalization.sections",
    "decision_pool": "pipeline.personalization.decision_pool",
    "skyfi": "pipeline.personalization.skyfi_site",
}

# Row workflow token -> required registry workflow for a bound TEXT target.
# (Deterministic text is always realtime/$0 per the registry-schema validation rules;
# rows whose workflow token describes the image lane still carry det text at realtime.)
_TEXT_WF = {
    "realtime": "realtime",
    "realtime-by-key": "realtime",
    "text-prebuilt": "prebuilt",
    "image-prebuilt": "realtime",
    "image-realtime": "realtime",
}
# Row workflow token -> required registry workflow for a bound IMAGE target.
_IMAGE_WF = {
    "image-prebuilt": "prebuilt",
    "image-realtime": "realtime",
}

# --------------------------------------------------------------------------- #
# The 30-row matrix — SECTION-DESIGNER-EXAMPLES.md §3, verbatim tokens.
# --------------------------------------------------------------------------- #
ROWS: list[dict] = [
    # --- 3.1 GauntletAI ----------------------------------------------------- #
    {"id": "WF-DESIGN-G01", "slug": "g01_direct_cold_anon_neutral_hero", "tenant": "gauntlet",
     "channel": "direct", "who": "cold anon, no signals (tier 0)", "element": "hero sub (text)",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "neutral-baseline",
     "guardrail": "say only what's provable with zero data",
     "golden": "With zero signals the hero sub ships the neutral baseline — nothing unprovable ships.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-G02", "slug": "g02_direct_corporate_ip_allude", "tenant": "gauntlet",
     "channel": "direct", "who": "corporate IP (Apple netblock), anon B2B",
     "element": "hero sub + prove intro (text)",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "firmographic-allude",
     "guardrail": "employer alluded, never recited (hold)",
     "golden": "Corporate-IP arrival personalizes hero sub + prove intro at allude — the employer is never recited.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-G03", "slug": "g03_search_organic_authority_headline", "tenant": "gauntlet",
     "channel": "search", "who": "organic Google, intent-neutral", "element": "hero headline (text)",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "authority",
     "guardrail": "no comparative vs a CS degree",
     "golden": "Organic search gets an evidence-led headline with no comparative against a CS degree.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-G04", "slug": "g04_ads_x_v09_prebuilt_hero_image", "tenant": "gauntlet",
     "channel": "ads-x", "who": "v09 keyword 'AI hiring'", "element": "hero headline + hero image",
     "mode": "det-text/gen-image", "workflow": "image-prebuilt", "latency": "0 ms",
     "strategy": "message-match", "guardrail": "image must_avoid real logos",
     "golden": "v09 arrival message-matches the headline and paints the prebuilt hero image in 0 ms; real logos excluded by must_avoid.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-G05", "slug": "g05_ads_google_gen_prebuilt_hero_sub", "tenant": "gauntlet",
     "channel": "ads-google", "who": "search-ad 'switch into AI'", "element": "hero sub (text)",
     "mode": "gen", "workflow": "text-prebuilt", "latency": "0 ms", "strategy": "loss-aversion-honest",
     "guardrail": "candidate pool Gate-cleared; no superlative",
     "golden": "The hero sub serves only from a Gate-cleared prebuilt generative pool — a superlative candidate is 0-servable.",
     "needs": ("sections", "decision_pool")},
    {"id": "WF-DESIGN-G06", "slug": "g06_ads_meta_realtime_backdrop", "tenant": "gauntlet",
     "channel": "ads-meta", "who": "broad-audience awareness", "element": "section backdrop image",
     "mode": "gen", "workflow": "image-realtime", "latency": "~2 s gradient→swap",
     "strategy": "curiosity", "guardrail": "tier-gated; gradient fallback offline",
     "golden": "Meta awareness arrival gets a realtime Nano Banana backdrop (~2 s gradient→swap); offline the deterministic gradient ships at $0.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-G07", "slug": "g07_email_liam_token_eyebrow", "tenant": "gauntlet",
     "channel": "email", "who": "HubSpot cohort — Liam (magic token)",
     "element": "hero eyebrow 'Welcome back, Liam'",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "commitment-open-loop",
     "guardrail": "say-level name (token); abandoned-app fact = hold",
     "golden": "Liam's magic token says his name at say level; the abandoned-application fact stays hold and never ships.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-G08", "slug": "g08_email_maya_peer_logos", "tenant": "gauntlet",
     "channel": "email", "who": "known exec — Maya (logged in)",
     "element": "prove card (peer-logo, text+logo)",
     "mode": "det", "workflow": "image-prebuilt", "latency": "0 ms",
     "strategy": "social-proof-peer-matched", "guardrail": "all peer logos Gate-cleared",
     "golden": "Maya's prove card shows only Gate-cleared peer logos from the prebuilt set.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-G09", "slug": "g09_direct_known_gen_cta_by_key", "tenant": "gauntlet",
     "channel": "direct", "who": "returning known, high intent", "element": "cta (text)",
     "mode": "gen", "workflow": "realtime-by-key", "latency": "<100 ms", "strategy": "scarcity-honest",
     "guardrail": "a scarcity claim must be a provable deadline or it's dropped",
     "golden": "The generative CTA serves cache-by-key (<100 ms); a scarcity claim without a provable deadline is dropped from the pool.",
     "needs": ("sections", "decision_pool")},
    {"id": "WF-DESIGN-G10", "slug": "g10_ads_x_v03_objection_reframe", "tenant": "gauntlet",
     "channel": "ads-x", "who": "v03 cost-objection creative", "element": "challenger body (text)",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "objection-reframe",
     "guardrail": "reframe at allude; blocked_say recite console-only",
     "golden": "v03 cost-objection arrival gets the reframe at allude; the blocked_say recite exists only on the console.",
     "needs": ("sections",)},
    # --- 3.2 Planet --------------------------------------------------------- #
    {"id": "WF-DESIGN-P01", "slug": "p01_direct_cold_neutral_hero", "tenant": "planet",
     "channel": "direct", "who": "self-serve cold (tier 0)", "element": "hero (text)",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "neutral-baseline",
     "guardrail": "no region line ships without confidence",
     "golden": "Cold self-serve visit ships the neutral hero — no region line without confidence.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-P02", "slug": "p02_direct_ag_midwest_prebuilt_region_backdrop", "tenant": "planet",
     "channel": "direct", "who": "ag enterprise, Midwest IP", "element": "location line + region backdrop",
     "mode": "det-text/gen-image", "workflow": "image-prebuilt", "latency": "0 ms",
     "strategy": "location-relevance", "guardrail": "region scale only; city/field = hold",
     "golden": "Midwest ag arrival gets the location line + prebuilt top-crop-belt backdrop in 0 ms; region scale only, city/field held.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-P03", "slug": "p03_ads_x_v01_crop_belts_match", "tenant": "planet",
     "channel": "ads-x", "who": "v01 crop-belts creative", "element": "hero headline + location line",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "message-match",
     "guardrail": "theater-line for defense, never visitor loc",
     "golden": "v01 crop-belts ad message-matches headline + location line; defense theater copy never uses visitor location.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-P04", "slug": "p04_ads_x_v02_defense_theater_image", "tenant": "planet",
     "channel": "ads-x", "who": "v02 defense/sovereign", "element": "hero image (theater, not visitor region)",
     "mode": "gen", "workflow": "image-realtime", "latency": "~2 s", "strategy": "authority",
     "guardrail": "uses AOR/theater, never the visitor's location",
     "golden": "The defense hero image is generated for the AOR/theater in realtime — never the visitor's region.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-P05", "slug": "p05_search_region_location_line", "tenant": "planet",
     "channel": "search", "who": "organic, region resolves", "element": "location line",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "location-relevance",
     "guardrail": "default daily-coverage line at region scale",
     "golden": "Organic search with region resolve ships the daily-coverage location line at region scale.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-P06", "slug": "p06_email_kofi_crisis_relief", "tenant": "planet",
     "channel": "email", "who": "crisis-responders — Kofi (token)", "element": "hero eyebrow + cta",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "reciprocity-relief-context",
     "guardrail": "relief-org context; income/PII = hold",
     "golden": "Kofi's crisis-responder email personalizes eyebrow + CTA in relief context; income/PII stays hold.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-P07", "slug": "p07_email_amara_gen_prebuilt_prove_intro", "tenant": "planet",
     "channel": "email", "who": "enterprise agronomy — Amara (login)", "element": "prove intro (text)",
     "mode": "gen", "workflow": "text-prebuilt", "latency": "0 ms", "strategy": "authority",
     "guardrail": "Gate-bounded; declared goals say-level",
     "golden": "Amara's prove intro serves from a Gate-cleared prebuilt generative pool; declared goals ride at say level.",
     "needs": ("sections", "decision_pool")},
    {"id": "WF-DESIGN-P08", "slug": "p08_ads_meta_longtail_realtime_backdrop", "tenant": "planet",
     "channel": "ads-meta", "who": "awareness, long-tail region", "element": "section backdrop image",
     "mode": "gen", "workflow": "image-realtime", "latency": "~2–3 s swap", "strategy": "curiosity",
     "guardrail": "long-tail region → realtime; common → prebuilt",
     "golden": "Long-tail region backdrop generates realtime (~2–3 s swap); common regions stay prebuilt at 0 ms.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-P09", "slug": "p09_direct_insurance_no_competitor", "tenant": "planet",
     "channel": "direct", "who": "corporate IP, insurance cat-risk", "element": "compare emphasis (text)",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "loss-aversion",
     "guardrail": "no competitor named; comparatives blocked",
     "golden": "Insurance cat-risk emphasis shifts the compare section with no competitor named — comparatives are structurally blocked.",
     "needs": ("sections",)},
    {"id": "WF-DESIGN-P10", "slug": "p10_direct_known_gen_cta_by_key", "tenant": "planet",
     "channel": "direct", "who": "returning known", "element": "cta (text)",
     "mode": "gen", "workflow": "realtime-by-key", "latency": "<100 ms", "strategy": "scarcity-honest",
     "guardrail": "provable deadline only",
     "golden": "The generative CTA serves cache-by-key; only a provable deadline may carry scarcity.",
     "needs": ("sections", "decision_pool")},
    # --- 3.3 SkyFi ---------------------------------------------------------- #
    {"id": "WF-DESIGN-S01", "slug": "s01_direct_cold_neutral_hero", "tenant": "skyfi",
     "channel": "direct", "who": "cold anon (tier 0)", "element": "hero (text)",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "neutral-baseline",
     "guardrail": "no location/sector claim without confidence",
     "golden": "Cold visit ships the neutral hero — no location or sector claim without confidence.",
     "needs": ("sections", "skyfi")},
    {"id": "WF-DESIGN-S02", "slug": "s02_direct_mining_realtime_region_sector_backdrop", "tenant": "skyfi",
     "channel": "direct", "who": "mining operator, AZ IP + PDL sector",
     "element": "hero sub + region×sector backdrop",
     "mode": "det-text/gen-image", "workflow": "image-realtime",
     "latency": "~2 s gradient→swap, cached by key", "strategy": "location-relevance",
     "guardrail": "basin/region scale; exact mine = hold (arm Ex)",
     "golden": "AZ mining operator watches the region×sector backdrop generate live (~2 s gradient→swap, cached by key); basin scale only — the exact mine is hold (arm Ex).",
     "needs": ("sections", "skyfi")},
    {"id": "WF-DESIGN-S03", "slug": "s03_ads_x_monitor_site_realtime_hero", "tenant": "skyfi",
     "channel": "ads-x", "who": "paid 'monitor your site'", "element": "hero headline + hero image",
     "mode": "det-text/gen-image", "workflow": "image-realtime", "latency": "~2 s",
     "strategy": "message-match", "guardrail": "generated backdrop is region-generic, license-safe",
     "golden": "Paid 'monitor your site' arrival gets a message-matched headline + realtime region-generic, license-safe backdrop.",
     "needs": ("sections", "skyfi")},
    {"id": "WF-DESIGN-S04", "slug": "s04_ads_google_gen_prebuilt_hero_sub", "tenant": "skyfi",
     "channel": "ads-google", "who": "'satellite imagery on demand'", "element": "hero sub (text)",
     "mode": "gen", "workflow": "text-prebuilt", "latency": "0 ms", "strategy": "authority",
     "guardrail": "Gate-bounded; no 'clearest/best' superlative",
     "golden": "The hero sub serves only from a Gate-cleared prebuilt generative pool — no 'clearest/best' superlative can ship.",
     "needs": ("sections", "skyfi", "decision_pool")},
    {"id": "WF-DESIGN-S05", "slug": "s05_search_region_location_line", "tenant": "skyfi",
     "channel": "search", "who": "organic, region resolves", "element": "location line (text)",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "location-relevance",
     "guardrail": "region scale; declared-AOI = say, else hold",
     "golden": "Organic search ships the region-scale location line; a declared AOI is say, everything else holds.",
     "needs": ("sections", "skyfi")},
    {"id": "WF-DESIGN-S06", "slug": "s06_email_construction_peer_card", "tenant": "skyfi",
     "channel": "email", "who": "construction/EPC — known account",
     "element": "prove card (project-region, text)",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "social-proof-sector-peer",
     "guardrail": "peer refs Gate-cleared",
     "golden": "The construction/EPC prove card shows Gate-cleared sector-peer references only.",
     "needs": ("sections", "skyfi")},
    {"id": "WF-DESIGN-S07", "slug": "s07_email_defense_strict_hold", "tenant": "skyfi",
     "channel": "email", "who": "defense/gov — cleared contact", "element": "hero eyebrow + cta",
     "mode": "det", "workflow": "realtime", "latency": "0 ms", "strategy": "authority",
     "guardrail": "strict hold: AOR framing, never a specific asset",
     "golden": "Defense/gov contact gets AOR-framed eyebrow + CTA under strict hold — never a specific asset.",
     "needs": ("sections", "skyfi")},
    {"id": "WF-DESIGN-S08", "slug": "s08_ads_meta_rare_sector_realtime_backdrop", "tenant": "skyfi",
     "channel": "ads-meta", "who": "awareness, rare sector×region", "element": "section backdrop image",
     "mode": "gen", "workflow": "image-realtime", "latency": "~2–3 s swap", "strategy": "curiosity",
     "guardrail": "long-tail → realtime; anti-surveillance mood rules",
     "golden": "Rare sector×region backdrop generates realtime under anti-surveillance mood rules; long-tail never blocks paint.",
     "needs": ("sections", "skyfi")},
    {"id": "WF-DESIGN-S09", "slug": "s09_direct_declared_aoi_exact_allowed", "tenant": "skyfi",
     "channel": "direct", "who": "declared first-party AOI (their own asset)",
     "element": "hero image (their basin)",
     "mode": "gen", "workflow": "image-realtime", "latency": "~2 s", "strategy": "location-relevance",
     "guardrail": "exact-AOI allowed because declared; receipt says 'you told us'",
     "golden": "The declared first-party AOI renders exact — allowed because they told us; the receipt says so.",
     "needs": ("sections", "skyfi")},
    {"id": "WF-DESIGN-S10", "slug": "s10_direct_known_insurance_gen_cta", "tenant": "skyfi",
     "channel": "direct", "who": "returning known, insurance cat-risk", "element": "compare emphasis (text)",
     "mode": "gen", "workflow": "realtime-by-key", "latency": "<100 ms", "strategy": "loss-aversion",
     "guardrail": "no competitor; comparatives blocked",
     "golden": "The insurance CTA serves generative cache-by-key with competitors and comparatives structurally blocked.",
     "needs": ("sections", "skyfi", "decision_pool")},
]

ROWS_BY_ID = {r["id"]: r for r in ROWS}
assert len(ROWS) == 30 and len(ROWS_BY_ID) == 30


# --------------------------------------------------------------------------- #
# Row runner — guards, scenario seed, registry binding, gen-pool Gate check.
# --------------------------------------------------------------------------- #
def _activate_or_skip(row: dict) -> None:
    """importorskip guards at the top of every row test — skip until the wave lands."""
    for need in row["needs"]:
        pytest.importorskip(_MODULES[need])


def _scenario_or_skip(row: dict) -> dict:
    if not SCENARIOS_PATH.exists():
        pytest.skip("rules/demo_scenarios.yaml not seeded yet (T-08, W3)")
    data = yaml.safe_load(SCENARIOS_PATH.read_text(encoding="utf-8")) or {}
    scenarios = data.get("scenarios") or []
    sc = next((s for s in scenarios if isinstance(s, dict) and s.get("id") == row["id"]), None)
    if sc is None:
        pytest.skip(f"{row['id']} not seeded in rules/demo_scenarios.yaml yet (T-08, W3)")
    return sc


def _variant_text(v) -> str:
    if isinstance(v, dict):
        parts = [v.get(k) for k in ("headline", "template", "text", "copy", "line")]
    else:
        parts = [getattr(v, k, None) for k in ("headline", "template", "text", "copy", "line")]
    parts = [p for p in parts if p]
    assert parts, f"cleared-pool variant carries no visible text: {v!r}"
    return " ".join(str(p) for p in parts)


def _variant_flag(v, name: str) -> bool:
    if isinstance(v, dict):
        return bool(v.get(name))
    return bool(getattr(v, name, False))


def _run_row(row: dict) -> None:
    sections = importlib.import_module(_MODULES["sections"])
    sc = _scenario_or_skip(row)

    # 1 · the scenario mirrors the matrix row verbatim (the matrix is the contract)
    for k in ("tenant", "channel", "element", "mode", "workflow", "strategy", "guardrail"):
        assert sc.get(k) == row[k], (
            f"{row['id']}: scenario field {k!r} = {sc.get(k)!r} != matrix {row[k]!r}")

    # 2 · the scenario binds real registry targets with the row's mode/workflow
    targets = sc.get("targets") or []
    assert targets, f"{row['id']}: scenario must bind >=1 target in rules/{row['tenant']}_sections.yaml"
    text_reg = {t.get("slot_id"): t for t in sections.list_text_targets(row["tenant"])}
    image_reg = {t.get("surface_id"): t for t in sections.list_image_targets(row["tenant"])}
    for t in targets:
        kind = t.get("kind")
        assert kind in ("text", "image"), f"{row['id']}: target kind {kind!r}"
        assert t.get("section_id"), f"{row['id']}: target missing section_id"
        if kind == "text":
            reg = text_reg.get(t.get("slot_id"))
            assert reg is not None, f"{row['id']}: slot {t.get('slot_id')!r} not in the section registry"
            assert reg.get("section_id") == t["section_id"], f"{row['id']}: slot bound to wrong section"
            expected_mode = "generative" if row["mode"] == "gen" else "deterministic"
            assert reg.get("mode") == expected_mode, (
                f"{row['id']}: slot mode {reg.get('mode')!r} != {expected_mode!r}")
            assert reg.get("workflow") == _TEXT_WF[row["workflow"]], (
                f"{row['id']}: slot workflow {reg.get('workflow')!r} != {_TEXT_WF[row['workflow']]!r}")
            if expected_mode == "deterministic":
                assert not reg.get("prompt"), f"{row['id']}: deterministic slot carries a prompt"
        else:
            reg = image_reg.get(t.get("surface_id"))
            assert reg is not None, f"{row['id']}: surface {t.get('surface_id')!r} not in the section registry"
            assert reg.get("section_id") == t["section_id"], f"{row['id']}: surface bound to wrong section"
            assert reg.get("workflow") != "live", f"{row['id']}: 'live' image workflow is discouraged — never in the matrix"
            expected_wf = _IMAGE_WF.get(row["workflow"])
            if expected_wf:
                assert reg.get("workflow") == expected_wf, (
                    f"{row['id']}: surface workflow {reg.get('workflow')!r} != {expected_wf!r}")

    # 3 · generative text rows: the servable set is a Gate-cleared pool (Art II) —
    #     every pool member passes the real copy gate; a planted lie is structurally absent.
    if "decision_pool" in row["needs"]:
        dp = importlib.import_module(_MODULES["decision_pool"])
        for t in targets:
            if t.get("kind") != "text":
                continue
            pool = dp.cleared_pool(row["tenant"], t["section_id"], t["slot_id"])
            assert pool, f"{row['id']}: generative target has an empty cleared pool"
            for v in pool:
                txt = _variant_text(v)
                unclean = CR._line_is_unclean(txt)
                assert unclean is None, (
                    f"{row['id']}: cleared pool served un-Gate-able copy ({unclean}): {txt!r}")
                assert not _variant_flag(v, "planted_lie"), (
                    f"{row['id']}: planted lie present in the cleared pool")


# --------------------------------------------------------------------------- #
# The 30 row tests (one per WF-DESIGN matrix row).
# --------------------------------------------------------------------------- #
def test_wf_design_g01_direct_cold_anon_neutral_hero():
    row = ROWS_BY_ID["WF-DESIGN-G01"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_g02_direct_corporate_ip_allude():
    row = ROWS_BY_ID["WF-DESIGN-G02"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_g03_search_organic_authority_headline():
    row = ROWS_BY_ID["WF-DESIGN-G03"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_g04_ads_x_v09_prebuilt_hero_image():
    row = ROWS_BY_ID["WF-DESIGN-G04"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_g05_ads_google_gen_prebuilt_hero_sub():
    row = ROWS_BY_ID["WF-DESIGN-G05"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_g06_ads_meta_realtime_backdrop():
    row = ROWS_BY_ID["WF-DESIGN-G06"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_g07_email_liam_token_eyebrow():
    row = ROWS_BY_ID["WF-DESIGN-G07"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_g08_email_maya_peer_logos():
    row = ROWS_BY_ID["WF-DESIGN-G08"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_g09_direct_known_gen_cta_by_key():
    row = ROWS_BY_ID["WF-DESIGN-G09"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_g10_ads_x_v03_objection_reframe():
    row = ROWS_BY_ID["WF-DESIGN-G10"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p01_direct_cold_neutral_hero():
    row = ROWS_BY_ID["WF-DESIGN-P01"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p02_direct_ag_midwest_prebuilt_region_backdrop():
    row = ROWS_BY_ID["WF-DESIGN-P02"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p03_ads_x_v01_crop_belts_match():
    row = ROWS_BY_ID["WF-DESIGN-P03"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p04_ads_x_v02_defense_theater_image():
    row = ROWS_BY_ID["WF-DESIGN-P04"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p05_search_region_location_line():
    row = ROWS_BY_ID["WF-DESIGN-P05"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p06_email_kofi_crisis_relief():
    row = ROWS_BY_ID["WF-DESIGN-P06"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p07_email_amara_gen_prebuilt_prove_intro():
    row = ROWS_BY_ID["WF-DESIGN-P07"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p08_ads_meta_longtail_realtime_backdrop():
    row = ROWS_BY_ID["WF-DESIGN-P08"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p09_direct_insurance_no_competitor():
    row = ROWS_BY_ID["WF-DESIGN-P09"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_p10_direct_known_gen_cta_by_key():
    row = ROWS_BY_ID["WF-DESIGN-P10"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s01_direct_cold_neutral_hero():
    row = ROWS_BY_ID["WF-DESIGN-S01"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s02_direct_mining_realtime_region_sector_backdrop():
    row = ROWS_BY_ID["WF-DESIGN-S02"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s03_ads_x_monitor_site_realtime_hero():
    row = ROWS_BY_ID["WF-DESIGN-S03"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s04_ads_google_gen_prebuilt_hero_sub():
    row = ROWS_BY_ID["WF-DESIGN-S04"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s05_search_region_location_line():
    row = ROWS_BY_ID["WF-DESIGN-S05"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s06_email_construction_peer_card():
    row = ROWS_BY_ID["WF-DESIGN-S06"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s07_email_defense_strict_hold():
    row = ROWS_BY_ID["WF-DESIGN-S07"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s08_ads_meta_rare_sector_realtime_backdrop():
    row = ROWS_BY_ID["WF-DESIGN-S08"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s09_direct_declared_aoi_exact_allowed():
    row = ROWS_BY_ID["WF-DESIGN-S09"]; _activate_or_skip(row); _run_row(row)

def test_wf_design_s10_direct_known_insurance_gen_cta():
    row = ROWS_BY_ID["WF-DESIGN-S10"]; _activate_or_skip(row); _run_row(row)


# --------------------------------------------------------------------------- #
# Engine invariants that must pass TODAY (real Gate, no decision-logic mocks).
# Only the HTTP transport is faked in the cost test — the ledger logic is real.
# --------------------------------------------------------------------------- #
def test_r35a_every_image_call_cost_logged(monkeypatch, tmp_path):
    """S3.1 / R35a: every _call_image_api invocation writes exactly one api_costs
    ledger row — success AND 429 — so no refactor can introduce an uncosted call."""
    from pipeline.observability import api_costs as AC
    from pipeline.personalization import image_gen as IG

    ledger = tmp_path / "api_cost_ledger.jsonl"
    monkeypatch.setattr(AC, "LEDGER_PATH", ledger)          # isolated ledger — never data/demo
    monkeypatch.setenv("IMAGE_GEN_API_KEY", "test-key")     # non-"AQ." key → OpenAI-compatible path
    monkeypatch.delenv("NANO_BANANA_API_KEY", raising=False)
    monkeypatch.delenv("IMAGE_GEN_API_URL", raising=False)
    monkeypatch.delenv("IMAGE_GEN_MODEL", raising=False)

    png_b64 = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 32).decode()
    calls = {"n": 0}

    class _Resp:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self._payload = payload or {}
            self.headers = {}
            self.content = b""

        def json(self):
            return self._payload

    def _fake_post(url, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _Resp(200, {"data": [{"b64_json": png_b64}]})
        return _Resp(429)

    monkeypatch.setattr(IG.httpx, "post", _fake_post)

    ok = IG._call_image_api("wf-design harness prompt", tenant="gauntlet",
                            cache_key="wf-design-cost-success")
    throttled = IG._call_image_api("wf-design harness prompt", tenant="gauntlet",
                                   cache_key="wf-design-cost-429")

    assert ok is not None and ok.get("b64") == png_b64
    assert throttled is None
    assert calls["n"] == 2

    rows = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 2, "exactly one ledger row per _call_image_api call (success + 429)"
    by_key = {r["cache_key"]: r for r in rows}
    success = by_key["wf-design-cost-success"]
    limited = by_key["wf-design-cost-429"]
    assert success["status"] == "success" and success["images_generated"] == 1
    assert success["estimated_cost_usd"] > 0, "a successful generation must carry a nonzero cost estimate"
    assert limited["status"] == "429" and limited["images_generated"] == 0
    assert limited["estimated_cost_usd"] == 0.0
    for r in rows:
        assert r.get("request_id") and r.get("service") and r.get("model") and r.get("operation")


G_URLS = ("/gauntlet",
          "/gauntlet?utm_source=linkedin&utm_medium=paid&utm_campaign=catalyst-cto",
          "/gauntlet?utm_source=hubspot&utm_medium=email&utm_campaign=cohort-april",
          "/gauntlet?ref=google")
P_URLS = ("/planet",
          "/planet?utm_source=linkedin&utm_medium=paid&utm_campaign=defense-sovereign-mission",
          "/planet?utm_source=hubspot&utm_medium=email&utm_campaign=crisis-responders",
          "/planet?ref=google")


def test_hold_never_ships_gauntlet():
    """Hold facts (modeled income) never reach the shipped /gauntlet page — any cohort
    user, any entry channel (matrix rows G02/G07 hold guardrails, S2 acceptance)."""
    from pipeline.personalization import cohort as GCO

    for p in GCO.COHORT:
        c.post("/gauntlet/login", data={"email": p["email"], "next": "/gauntlet"})
        try:
            for url in G_URLS:
                t = c.get(url).text
                income = p["clay"].get("income_band")
                if income:
                    assert income not in t, f"hold fact (income) shipped for {p['id']} at {url}"
                assert "we noticed" not in t and "de-anonymized" not in t.replace("/dev", "")
        finally:
            c.get("/gauntlet/logout")


def test_hold_never_ships_planet():
    """Hold facts (modeled income/PII) never reach the shipped /planet page — any cohort
    user, any entry channel (matrix row P06 income/PII hold, S2 acceptance)."""
    from pipeline.personalization import planet_cohort as PCO

    for p in PCO.COHORT:
        c.post("/planet/login", data={"email": p["email"], "next": "/planet"})
        try:
            for url in P_URLS:
                t = c.get(url).text
                income = p["clay"].get("income_band")
                if income:
                    assert income not in t, f"hold fact (income) shipped for {p['id']} at {url}"
                assert "we noticed" not in t and "de-anonymized" not in t.replace("/planet/dev", "")
        finally:
            c.get("/planet/logout")


def test_gate_blocks_competitor_comparative_superlative():
    """The real copy gate blocks the three signature-guardrail classes (G03/P09/S04/S10):
    superlative, comparative, and reciting an inferred competitor. All three 0-servable."""
    bad = [
        "The #1 AI fellowship — best-in-class, guaranteed outcomes",   # superlative
        "Better than a CS degree and faster than any bootcamp",       # comparative
        "Everyone at Clay is already moving their pipeline to us",    # inferred competitor
    ]
    checks = CR.verify_copy(bad, "", None, "allude", competitors=["Clay"])
    assert all(not ch["ok"] for ch in checks), f"gate let a bad line through: {checks}"
    assert "superlative" in checks[0]["reason"]
    assert "comparative" in checks[1]["reason"]
    assert "competitor" in checks[2]["reason"]
