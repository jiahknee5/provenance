"""Designer UI DOM contract tests (T-03/S5, T-07b) — 04-spec/contracts/designer-dom.md.

The marketer consoles (gauntlet + planet + skyfi) render one sd-section-{id} card
per registry section, Q1–Q10 controls read-only-bound to registry + page state, a
staged drawer that targets rules/<tenant>_sections.yaml (kind "sections"), and a
dev/audit toggle (sd-devtoggle) folding the engineer trace/audit sections.
"""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import sections as SEC

c = TestClient(app)

CONSOLES = {
    "gauntlet": "/gauntletapt/dev/business",
    "planet": "/planetapt/dev/business",
    "skyfi": "/skyfiapt/dev/business",
}
TENANTS = list(CONSOLES)

_cache: dict[str, str] = {}


def _page(tenant: str) -> str:
    if tenant not in _cache:
        r = c.get(CONSOLES[tenant] + "?as=anon")
        assert r.status_code == 200, tenant
        _cache[tenant] = r.text
    return _cache[tenant]


def _tid(name: str) -> str:
    return f'data-testid="{name}"'


# --------------------------------------------------------------------------- #
# Section cards — one per registry section, page order
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_section_cards_render_in_page_order(tenant):
    t = _page(tenant)
    positions = []
    for sec in SEC.list_sections(tenant):
        marker = _tid(f"sd-section-{sec['id']}")
        assert marker in t, f"{tenant}: missing section card {sec['id']}"
        assert t.count(marker) == 1, f"{tenant}: duplicate section card {sec['id']}"
        positions.append(t.find(marker))
    assert positions == sorted(positions), f"{tenant}: cards out of registry (page) order"


@pytest.mark.parametrize("tenant", TENANTS)
def test_q1_personalize_toggle_and_add_target_buttons(tenant):
    t = _page(tenant)
    for sec in SEC.list_sections(tenant):
        sid = sec["id"]
        for name in (f"sd-personalize-{sid}", f"sd-add-text-{sid}", f"sd-add-image-{sid}"):
            assert _tid(name) in t, f"{tenant}: missing {name}"
    # the add buttons stage registry diffs through the drawer's "sections" kind
    assert 'data-sd-op="add"' in t


@pytest.mark.parametrize("tenant", TENANTS)
def test_q2_goal_and_q3_channel_chips(tenant):
    t = _page(tenant)
    for sec in SEC.list_sections(tenant):
        sid = sec["id"]
        assert _tid(f"sd-goal-{sid}") in t
        assert _tid(f"sd-channels-{sid}") in t
        # every registry channel renders as a chip somewhere in the card
        for ch in sec.get("channels") or []:
            assert ch in t


# --------------------------------------------------------------------------- #
# Text targets — Q4/Q5/Q6 controls + gate/receipt/latency/cost/A-B/drift
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_text_target_cards_carry_all_controls(tenant):
    t = _page(tenant)
    for tt in SEC.list_text_targets(tenant):
        slot, sid = tt["slot_id"], tt["section_id"]
        for name in (
            f"sd-text-{sid}-{slot}",
            f"sd-mode-{slot}",          # Q4 deterministic | generative
            f"sd-workflow-{slot}",      # Q4 prebuilt | realtime
            f"sd-strategy-{slot}",      # Q5
            f"sd-policy-{slot}",        # Q6 say | allude | hold
            f"sd-prompt-{slot}",
            f"sd-gate-{slot}",          # Q6 verdict badge
            f"sd-receipt-{slot}",       # S4.1
            f"sd-latency-{slot}",       # Q8
            f"sd-cost-{slot}",          # Q9
            f"sd-ab-{slot}",            # S4.2
            f"sd-drift-{slot}",         # S4.3
        ):
            assert _tid(name) in t, f"{tenant}: missing {name}"


@pytest.mark.parametrize("tenant", TENANTS)
def test_prompt_editor_hidden_iff_deterministic(tenant):
    t = _page(tenant)
    for tt in SEC.list_text_targets(tenant):
        marker = _tid(f"sd-prompt-{tt['slot_id']}")
        i = t.find(marker)
        assert i != -1
        tag_end = t.find(">", i)
        tag = t[i:tag_end]
        if tt["mode"] == "deterministic":
            assert "hidden" in tag, f"{tenant}: prompt visible on deterministic {tt['slot_id']}"
        else:
            assert "hidden" not in tag, f"{tenant}: prompt hidden on generative {tt['slot_id']}"


@pytest.mark.parametrize("tenant", TENANTS)
def test_receipts_carry_cache_key_and_rules_version(tenant):
    t = _page(tenant)
    assert "cache_key" in t
    assert "rules_version" in t
    # the live registry hash is stamped on every receipt + drift badge
    assert SEC.registry_version(tenant) in t


@pytest.mark.parametrize("tenant", TENANTS)
def test_latency_badges_use_contract_labels(tenant):
    t = _page(tenant)
    for tt in SEC.list_text_targets(tenant):
        if tt["mode"] == "deterministic":
            assert _tid(f"sd-latency-{tt['slot_id']}") + ">instant<" in t
    for it in SEC.list_image_targets(tenant):
        want = {"prebuilt": "instant", "realtime": "~2s swap", "live": "blocking⚠"}[it["workflow"]]
        assert _tid(f"sd-latency-{it['surface_id']}") + f">{want}<" in t


@pytest.mark.parametrize("tenant", TENANTS)
def test_cost_badges_show_dollars_per_gen(tenant):
    t = _page(tenant)
    assert "$0 / visit" in t                      # deterministic text lane
    for it in SEC.list_image_targets(tenant):
        marker = _tid(f"sd-cost-{it['surface_id']}")
        i = t.find(marker)
        assert i != -1
        assert "$0.039/gen" in t[i:i + 300], f"{tenant}: no $/gen on {it['surface_id']}"


# --------------------------------------------------------------------------- #
# Image targets — card, workflow select (live warns), thumbnail + load badge
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_image_target_cards_carry_all_controls(tenant):
    t = _page(tenant)
    for it in SEC.list_image_targets(tenant):
        surf, sid = it["surface_id"], it["section_id"]
        for name in (
            f"sd-image-{sid}-{surf}",
            f"sd-workflow-{surf}",
            f"sd-gate-{surf}",
            f"sd-receipt-{surf}",
            f"sd-latency-{surf}",
            f"sd-cost-{surf}",
            f"sd-ab-{surf}",
            f"sd-drift-{surf}",
        ):
            assert _tid(name) in t, f"{tenant}: missing {name}"
    assert "load-badge" in t
    assert 'value="live"' in t          # live offered…
    assert "sd-livewarn" in t           # …but warns (discouraged)


@pytest.mark.parametrize("tenant", TENANTS)
def test_ab_panel_lists_routes_and_control(tenant):
    t = _page(tenant)
    routes = {"gauntlet": ["b2b_hire", "b2b_upskill", "individual", "neutral"],
              "planet": ["enterprise", "selfserve", "research", "neutral"],
              "skyfi": ["enterprise", "selfserve", "neutral"]}[tenant]
    for r in routes:
        assert r in t
    assert "lift vs control" in t


# --------------------------------------------------------------------------- #
# Per-section graph / evals / observability panels
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_graph_evals_observe_panels_per_section(tenant):
    t = _page(tenant)
    for sec in SEC.list_sections(tenant):
        sid = sec["id"]
        for name in (f"sd-graph-{sid}", f"sd-evals-{sid}", f"sd-observe-{sid}"):
            assert _tid(name) in t, f"{tenant}: missing {name}"
        for e in sec.get("evals") or []:
            assert e.replace("_", " ") in t


# --------------------------------------------------------------------------- #
# Staged drawer targets the registry; dev/audit toggle folds the trace
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_staged_drawer_targets_sections_registry(tenant):
    t = _page(tenant)
    assert _tid("sd-staged") in t
    assert 'id="staged-changes"' in t
    assert f'data-sections-config="rules/{tenant}_sections.yaml"' in t
    assert 'data-stage="sections"' in t
    assert "Staged changes" in t and "Copy patch" in t


@pytest.mark.parametrize("tenant", TENANTS)
def test_devtoggle_folds_trace_audit_sections(tenant):
    t = _page(tenant)
    assert _tid("sd-devtoggle") in t
    assert 'id="sd-devtoggle-input"' in t
    # the engineer trace/audit sections render folded (still in the DOM)
    assert 'class="sec sd-devfold"' in t


# --------------------------------------------------------------------------- #
# Q11 ease-of-use — everything for a section lives inside its card
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_section_card_contains_all_its_target_controls(tenant):
    t = _page(tenant)
    secs = SEC.list_sections(tenant)
    starts = [t.find(_tid(f"sd-section-{s['id']}")) for s in secs]
    for i, sec in enumerate(secs):
        start = starts[i]
        if i + 1 < len(secs):
            end = starts[i + 1]
        else:
            # W10-D: cards now carry their own sd-devfold (engineering panels
            # fold, R32), so "first devfold after start" lands inside the last
            # card. The Proof zone cap is the first thing after the card list
            # on every console.
            end = t.find('zone-cap">Proof', start)
            if end == -1:
                end = len(t)
        card = t[start:end]
        for tt in sec.get("text_targets") or []:
            for name in (f"sd-mode-{tt['slot_id']}", f"sd-policy-{tt['slot_id']}",
                         f"sd-latency-{tt['slot_id']}", f"sd-cost-{tt['slot_id']}"):
                assert _tid(name) in card, f"{tenant}/{sec['id']}: {name} outside its card"
        for it in sec.get("image_targets") or []:
            assert _tid(f"sd-workflow-{it['surface_id']}") in card
        for name in (f"sd-graph-{sec['id']}", f"sd-evals-{sec['id']}",
                     f"sd-observe-{sec['id']}"):
            assert _tid(name) in card, f"{tenant}/{sec['id']}: {name} outside its card"


# --------------------------------------------------------------------------- #
# Read-only binding — the card shows this visit's real state
# --------------------------------------------------------------------------- #
def test_gauntlet_ad_visit_binds_page_state_into_cards():
    r = c.get(CONSOLES["gauntlet"]
              + "?utm_source=x&utm_medium=paid&utm_campaign=x-keyword-ai-hiring"
              + "&utm_content=v09&as=anon")
    assert r.status_code == 200
    t = r.text
    assert _tid("sd-section-hero") in t
    assert "ads — this visit" in t          # Q3 chip marks the arriving channel
    assert "Shipped this visit" in t        # shipped vs generic bound from copy_diff


def test_planet_direct_visit_binds_location_section():
    r = c.get(CONSOLES["planet"] + "?ip=19.7.0.1&as=anon")
    assert r.status_code == 200
    t = r.text
    assert _tid("sd-section-location") in t
    assert _tid("sd-text-location-hero_location") in t
    assert "direct — this visit" in t


def test_skyfi_direct_visit_binds_location_section():
    r = c.get(CONSOLES["skyfi"] + "?ip=19.7.0.1&as=anon")
    assert r.status_code == 200
    t = r.text
    assert _tid("sd-section-location") in t
    assert _tid("sd-text-location-hero_location") in t
    assert "direct — this visit" in t


def test_skyfi_realtime_images_wear_the_swap_class():
    # S02 beat: skyfi's registry seeds every image workflow realtime — the latency
    # badge is the ~2s gradient→swap class on each image surface, never blocking.
    t = _page("skyfi")
    for it in SEC.list_image_targets("skyfi"):
        assert it["workflow"] == "realtime", f"registry drifted: {it['surface_id']}"
        i = t.find(_tid(f"sd-latency-{it['surface_id']}"))
        assert i != -1
        tag_start = t.rfind("<span", 0, i)
        assert 'class="sd-badge lat swap"' in t[tag_start:i], it["surface_id"]
        assert t[i:].split(">", 1)[1].startswith("~2s swap")


def test_skyfi_dev_business_serves_both_mounts():
    # T-07b replaces the 302→/dev redirect with the real designer on both mounts.
    for path in ("/skyfi/dev/business", "/skyfiapt/dev/business"):
        r = c.get(path + "?as=anon")
        assert r.status_code == 200, path
        assert not r.history or all(h.status_code != 302 for h in r.history), path
        assert _tid("sd-staged") in r.text, path
