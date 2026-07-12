"""Section registry (T-01, S1/R30) — round-trip, validation rejections, seed completeness.

The registry seed is DESCRIPTIVE (Art IV): rules/{gauntlet,planet}_sections.yaml must
carry exactly the slot() ids build_page records in copy_diff today — no DETERMINISTIC
slot missing, none invented. Validation rules are pinned by
04-spec/contracts/registry-schema.md.

T-08 (W3) architecture update: the WF-DESIGN matrix's generative rows are seeded in the
registries (G05/G09, P07/P10, S04/S10 gen text slots + the G06/P08 section_backdrop and
P02 region_backdrop image surfaces). Generative slots are POOL-served
(decision_pool.cleared_pool over the real Gate), not copy_diff slot-fill, so the
build_page parity pins below apply to deterministic slots and the generative seed is
pinned explicitly per tenant.
"""
from __future__ import annotations

import pytest

from pipeline.personalization import gauntlet_site as GS
from pipeline.personalization import planet_site as PS
from pipeline.personalization import sections as SR


class _Req:
    """Minimal request stand-in for the pure build_page() (tests/test_gauntlet_site.py)."""
    client = None                                    # scene.client_ip → "" → offline tier 0

    def __init__(self, params=None, headers=None):
        self.query_params = params or {}
        self.headers = headers or {}


# --------------------------------------------------------------------------- #
# 1 · Round-trip: YAML ↔ loader API
# --------------------------------------------------------------------------- #
def test_round_trip_gauntlet_sections():
    secs = SR.list_sections("gauntlet")
    assert [s["id"] for s in secs] == ["hero", "prove", "challenger", "compare", "cta"]
    for s in secs:
        assert s["region"] and s["label"]
        assert s["personalize"] is True
    hero = SR.get_section("gauntlet", "hero")
    assert hero["region"] == "hero"
    assert [t["slot_id"] for t in hero["text_targets"]] == \
        ["hero_eyebrow", "hero_sub", "hero_cta", "hero_sub_gen"]
    assert [t["surface_id"] for t in hero["image_targets"]] == ["hero", "og"]


def test_round_trip_planet_sections():
    secs = SR.list_sections("planet")
    assert [s["id"] for s in secs] == ["hero", "location", "prove", "research", "compare", "cta"]
    loc = SR.get_section("planet", "location")
    assert loc["region"] == "location"
    assert [t["slot_id"] for t in loc["text_targets"]] == ["hero_location"]


def test_get_section_unknown_id_raises():
    with pytest.raises(KeyError):
        SR.get_section("gauntlet", "nope")


def test_flattened_targets_carry_section_id():
    for t in SR.list_text_targets("gauntlet"):
        assert t["section_id"] in {"hero", "prove", "challenger", "compare", "cta"}
        if t["mode"] == "deterministic":
            # deterministic slot-fill stays realtime/$0 with no prompt (the T-01 seed)
            assert t["workflow"] == "realtime"
            assert not t["prompt"]
        else:
            # T-08 generative rows: pool-served, prompt + gate mandatory (schema rules)
            assert t["mode"] == "generative"
            assert t["workflow"] in {"prebuilt", "realtime"}
            assert t["prompt"] and t["gate"]
    imgs = {t["surface_id"]: t for t in SR.list_image_targets("gauntlet")}
    assert set(imgs) == {"hero", "og", "section_backdrop"}
    assert imgs["hero"]["section_id"] == "hero"
    assert imgs["og"]["section_id"] == "hero"
    assert imgs["section_backdrop"]["section_id"] == "prove"      # G06 backdrop row


def test_image_workflows_mirror_prebuild_manifests():
    # gauntlet_prebuild.yaml flags hero+og states → prebuilt; the prove
    # section_backdrop has no manifest entry → realtime (G06).
    g = {t["surface_id"]: t["workflow"] for t in SR.list_image_targets("gauntlet")}
    assert g == {"hero": "prebuilt", "og": "prebuilt", "section_backdrop": "realtime"}
    # planet_prebuild.yaml flags ONLY the location region_backdrop (P02, S3.3
    # manifest accounting); hero/og and the prove backdrop stay realtime.
    p = {t["surface_id"]: t["workflow"] for t in SR.list_image_targets("planet")}
    assert p == {"hero": "realtime", "og": "realtime",
                 "region_backdrop": "prebuilt", "section_backdrop": "realtime"}


def test_loader_caches_like_demo_nav():
    assert SR.list_sections("gauntlet") is SR.list_sections("gauntlet")


def test_registry_version_is_a_stable_content_hash():
    v = SR.registry_version("gauntlet")
    assert isinstance(v, str) and v
    assert v == SR.registry_version("gauntlet")
    assert v != SR.registry_version("planet")


# --------------------------------------------------------------------------- #
# 2 · Validation rejections — one case per pinned rule (registry-schema.md)
# --------------------------------------------------------------------------- #
def _text_target(**over) -> dict:
    t = {"slot_id": "hero_sub", "label": "Hero sub", "mode": "deterministic",
         "workflow": "realtime", "strategy": "neutral", "policy": "allude",
         "source": "catalog", "claims": [], "prompt": ""}
    t.update(over)
    return t


def _section(**over) -> dict:
    s = {"id": "hero", "label": "Hero", "region": "hero", "personalize": True,
         "goal": "", "channels": ["direct"], "text_targets": [_text_target()],
         "image_targets": [], "guardrails": {}, "evals": ["gate_pass"]}
    s.update(over)
    return s


def _registry(sections) -> dict:
    return {"version": 1, "tenant": "gauntlet", "sections": sections}


def _rejects(data, match):
    with pytest.raises(ValueError, match=match):
        SR.validate_registry(data, tenant="gauntlet")


def test_rejects_unknown_top_level_key():
    _rejects({**_registry([_section()]), "surprise": 1}, "unknown top-level keys")


def test_rejects_unknown_section_field_key():
    _rejects(_registry([_section(bonus=1)]), "unknown section field keys")


def test_rejects_unknown_text_target_field_key():
    _rejects(_registry([_section(text_targets=[_text_target(extra="x")])]),
             "unknown text_target field keys")


def test_rejects_unknown_image_target_field_key():
    img = {"surface_id": "hero", "workflow": "prebuilt", "mystery": 1}
    _rejects(_registry([_section(image_targets=[img])]), "unknown image_target field keys")


def test_rejects_duplicate_section_id():
    _rejects(_registry([_section(), _section(text_targets=[])]), "duplicate section id")


def test_rejects_duplicate_slot_id():
    _rejects(_registry([_section(),
                        _section(id="cta", region="cta", text_targets=[_text_target()])]),
             "duplicate slot_id")


def test_rejects_duplicate_surface_id():
    img = {"surface_id": "hero", "workflow": "prebuilt"}
    _rejects(_registry([_section(image_targets=[img, dict(img)])]), "duplicate surface_id")


def test_rejects_generative_with_empty_prompt():
    t = _text_target(mode="generative", prompt="", gate="gauntlet_tenant")
    _rejects(_registry([_section(text_targets=[t])]), "generative with empty prompt")


def test_rejects_generative_missing_gate():
    t = _text_target(mode="generative", prompt="Write a truthful hero sub.")
    _rejects(_registry([_section(text_targets=[t])]), "generative missing gate")


def test_rejects_deterministic_with_prompt():
    t = _text_target(prompt="should not be here")
    _rejects(_registry([_section(text_targets=[t])]), "deterministic with non-empty prompt")


def test_rejects_prebuilt_deterministic_text_target():
    t = _text_target(workflow="prebuilt")
    _rejects(_registry([_section(text_targets=[t])]), "prebuilt on a deterministic")


def test_rejects_bad_policy():
    _rejects(_registry([_section(text_targets=[_text_target(policy="shout")])]),
             "policy 'shout' not in")


def test_rejects_bad_mode():
    _rejects(_registry([_section(text_targets=[_text_target(mode="psychic")])]),
             "mode 'psychic' not in")


def test_rejects_bad_image_workflow():
    img = {"surface_id": "hero", "workflow": "telepathic"}
    _rejects(_registry([_section(image_targets=[img])]), "workflow 'telepathic' not in")


def test_accepts_valid_registry_and_generative_shape():
    gen = _text_target(slot_id="gen_sub", mode="generative", workflow="prebuilt",
                       prompt="Write a truthful hero sub.", gate="gauntlet_tenant")
    data = _registry([_section(text_targets=[_text_target(), gen])])
    assert SR.validate_registry(data, tenant="gauntlet") is data


# --------------------------------------------------------------------------- #
# 3 · Seed completeness — every build_page slot id is in the registry; the
#     deterministic registry invents none. Generative slots (T-08) are pool-served
#     (decision_pool.cleared_pool), never copy_diff slot-fill — pinned explicitly.
# --------------------------------------------------------------------------- #
def _observed_slot_ids(mod) -> set[str]:
    """Union of copy_diff slot ids across a direct visit and an ad visit whose
    variant reorders the stats (the one conditional slot, numbers_order)."""
    v = next(v for v in mod.AD_VARIANTS if v["page"].get("stat_highlight") is not None)
    reqs = [_Req(), _Req({"utm_medium": "paid", "utm_campaign": v["utm_campaign"],
                          "utm_content": v["variant_id"]})]
    ids: set[str] = set()
    for r in reqs:
        ids |= {d["slot"] for d in mod.build_page(r)["copy_diff"]}
    return ids


def _registry_by_mode(tenant: str) -> tuple[set[str], set[str]]:
    det = {t["slot_id"] for t in SR.list_text_targets(tenant)
           if t["mode"] == "deterministic"}
    gen = {t["slot_id"] for t in SR.list_text_targets(tenant)
           if t["mode"] == "generative"}
    return det, gen


def test_seed_completeness_gauntlet():
    observed = _observed_slot_ids(GS)
    det, gen = _registry_by_mode("gauntlet")
    assert observed - (det | gen) == set(), \
        f"build_page slots missing from registry: {observed - (det | gen)}"
    assert det - observed == set(), \
        f"registry invents deterministic slots build_page never ships: {det - observed}"
    # the T-08 generative seed, exactly (G05 prebuilt pool + G09 cache-by-key)
    assert gen == {"hero_sub_gen", "cta_gen"}
    assert gen & observed == set(), "generative slots are pool-served, never copy_diff"


def test_seed_completeness_planet():
    observed = _observed_slot_ids(PS)
    det, gen = _registry_by_mode("planet")
    assert observed - (det | gen) == set(), \
        f"build_page slots missing from registry: {observed - (det | gen)}"
    assert det - observed == set(), \
        f"registry invents deterministic slots build_page never ships: {det - observed}"
    # the T-08 generative seed, exactly (P07 prebuilt pool + P10 cache-by-key)
    assert gen == {"prove_intro_gen", "cta_gen"}
    assert gen & observed == set(), "generative slots are pool-served, never copy_diff"


# --------------------------------------------------------------------------- #
# 4 · SkyFi — seeded by T-07 (was an empty stub in W0; now asserted like the others)
# --------------------------------------------------------------------------- #
def test_round_trip_skyfi_sections():
    secs = SR.list_sections("skyfi")
    assert [s["id"] for s in secs] == ["hero", "location", "how", "pricing", "compare", "cta"]
    loc = SR.get_section("skyfi", "location")
    assert loc["region"] == "location"
    assert [t["slot_id"] for t in loc["text_targets"]] == ["hero_location"]
    hero = SR.get_section("skyfi", "hero")
    assert [t["surface_id"] for t in hero["image_targets"]] == ["hero", "og"]
    # empty prebuild manifest by design (S02 realtime beat) → all image workflows realtime
    assert {t["workflow"] for t in SR.list_image_targets("skyfi")} == {"realtime"}
    assert isinstance(SR.registry_version("skyfi"), str) and SR.registry_version("skyfi")
