"""T-04 (S4/S5, R34) — the per-section observability panels render REAL data (Art I).

Every sd-graph / sd-evals / sd-observe / sd-ab / sd-drift panel and the per-section
cost row must be fed from an actual run, never hand-typed:

  • sd-graph — the per-element flow resolve→select→assemble→gate→cache/serve→receipt
    as Observatory-contract nodes (lane + tools + input/decision/output), bound to THIS
    visit's channel/route/shipped copy;
  • sd-evals — counts MEASURED from this visit (targets bound, held strings leak-checked
    against shipped copy, brain score honest about when it is scored);
  • sd-observe — a per-request event ledger with a monotonic seq across the visit's
    sections and per-target gate/serve/receipt rows, closed by a cost row summed from
    the real api-cost ledger by the section's cache keys;
  • sd-ab — posterior means + lift vs control that EQUAL what the live seeded
    DecisionPool measures (never fabricated), labeled seeded;
  • sd-drift — the surgical pause: exactly the hero_sub pool shows the c_tco arm paused,
    every other target keeps serving.
"""
from __future__ import annotations

import re

import pytest
from starlette.testclient import TestClient

from app.main import app
from pipeline.observability import api_costs as AC
from pipeline.personalization import section_obs as OBS
from pipeline.personalization import sections as SEC
from pipeline.personalization.decision_pool import DecisionPool

c = TestClient(app)

CONSOLES = {
    "gauntlet": "/gauntletapt/dev/business",
    "planet": "/planetapt/dev/business",
}
ROUTES = {
    "gauntlet": ["b2b_hire", "b2b_upskill", "individual", "neutral"],
    "planet": ["enterprise", "selfserve", "research", "neutral"],
}
TENANTS = list(CONSOLES)
FLOW = ["resolve", "select", "assemble", "gate", "serve", "receipt"]

_cache: dict[str, str] = {}


def _page(tenant: str) -> str:
    if tenant not in _cache:
        r = c.get(CONSOLES[tenant] + "?as=anon")
        assert r.status_code == 200, tenant
        _cache[tenant] = r.text
    return _cache[tenant]


def _tid(name: str) -> str:
    return f'data-testid="{name}"'


def _cards(tenant: str) -> dict[str, str]:
    """Slice the page into per-section card texts (same slicing as the locked suite)."""
    t = _page(tenant)
    secs = SEC.list_sections(tenant)
    starts = [t.find(_tid(f"sd-section-{s['id']}")) for s in secs]
    out = {}
    for i, sec in enumerate(secs):
        if i + 1 < len(secs):
            end = starts[i + 1]
        else:
            # W10-D: each card now carries its own sd-devfold (engineering
            # panels fold, R32), so "first devfold after start" would cut the
            # last card short. The Proof zone cap follows the card list on
            # every console.
            end = t.find('zone-cap">Proof', starts[i])
            if end == -1:
                end = len(t)
        out[sec["id"]] = t[starts[i]:end]
    return out


# --------------------------------------------------------------------------- #
# sd-graph — Observatory-contract flow nodes bound to this visit
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_graph_renders_the_six_flow_nodes_per_section(tenant):
    for sid, card in _cards(tenant).items():
        for nid in FLOW:
            assert f'data-sd-node="{nid}"' in card, f"{tenant}/{sid}: missing node {nid}"
        # the Observatory node contract: input / decision / output + tools, per node
        assert card.count("<b>in:</b>") >= len(FLOW), f"{tenant}/{sid}"
        assert card.count("<b>decision:</b>") >= len(FLOW), f"{tenant}/{sid}"
        assert card.count("<b>out:</b>") >= len(FLOW), f"{tenant}/{sid}"
        assert card.count("tools:") >= len(FLOW), f"{tenant}/{sid}"
        # nodes carry their engine lane, not a generic label
        for lane in ("website", "gate", "optimizer", "library"):
            assert f'<span class="lane">{lane}</span>' in card, f"{tenant}/{sid}: {lane}"


@pytest.mark.parametrize("tenant", TENANTS)
def test_graph_binds_this_visits_channel_and_versions(tenant):
    reg = SEC.registry_version(tenant)
    gate_rv = OBS.seeded_campaign(tenant, tuple(ROUTES[tenant]))["gate_rules_version"]
    for sid, card in _cards(tenant).items():
        # resolve node states the REAL classified channel of this ?as=anon visit
        assert "channel = direct" in card, f"{tenant}/{sid}: resolve not bound to visit"
        # receipt node stamps the live Gate rules version + registry version
        assert f"rules {gate_rv[:8]}" in card, f"{tenant}/{sid}"
        assert f"registry {reg[:8]}" in card, f"{tenant}/{sid}"


def test_graph_assemble_node_quotes_rewritten_copy_on_an_ad_visit():
    r = c.get(CONSOLES["gauntlet"]
              + "?utm_source=x&utm_medium=paid&utm_campaign=x-keyword-ai-hiring"
              + "&utm_content=v09&as=anon")
    assert r.status_code == 200
    t = r.text
    assert "channel = ad" in t                       # resolve bound to the paid click
    assert "assembled this visit: “" in t            # assemble quotes real shipped copy
    m = re.search(r"assembled this visit: “([^”]+)", t)
    assert m and len(m.group(1)) > 10                # an actual copy fragment, not a stub


# --------------------------------------------------------------------------- #
# sd-evals — measured this visit
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_evals_report_measured_counts_and_leak_check(tenant):
    for sec in SEC.list_sections(tenant):
        card = _cards(tenant)[sec["id"]]
        n = len(sec.get("text_targets") or [])
        assert re.search(rf"measured this visit: \d+/{n} text target\(s\)", card), \
            f"{tenant}/{sec['id']}: gate_pass not measured"
        assert re.search(r"checked \d+ held string\(s\) against this section", card), \
            f"{tenant}/{sec['id']}: hold check not run"
        assert "0 leaked this visit" in card, f"{tenant}/{sec['id']}: leak check failed"
        if "brain_score" in (sec.get("evals") or []):
            assert re.search(r"\d\.\d\d · ", card) or "not scored this visit" in card, \
                f"{tenant}/{sec['id']}: brain_score neither scored nor honest"


# --------------------------------------------------------------------------- #
# sd-observe — per-request ledger, monotonic seq, per-target rows, cost row
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_ledger_seq_monotonic_across_the_whole_visit(tenant):
    seqs = [int(m) for m in re.findall(r'<td class="seq">(\d+)</td>', _page(tenant))]
    assert seqs, tenant
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs), \
        f"{tenant}: seq not strictly monotonic across sections"


@pytest.mark.parametrize("tenant", TENANTS)
def test_ledger_has_gate_serve_receipt_rows_per_target(tenant):
    cards = _cards(tenant)
    for sec in SEC.list_sections(tenant):
        card = cards[sec["id"]]
        assert f'>resolve {sec["id"]}</td>' in card, f"{tenant}/{sec['id']}"
        for tt in sec.get("text_targets") or []:
            for ev in ("select", "gate", "serve", "receipt", "pool"):
                assert f'>{ev} {tt["slot_id"]}</td>' in card, \
                    f"{tenant}/{sec['id']}: no {ev} row for {tt['slot_id']}"
        for it in sec.get("image_targets") or []:
            assert f'>image {it["surface_id"]}</td>' in card
            assert f'>receipt {it["surface_id"]}</td>' in card
        assert f'>cost {sec["id"]}</td>' in card, f"{tenant}/{sec['id']}: no cost event"


@pytest.mark.parametrize("tenant", TENANTS)
def test_cost_row_per_section_reads_the_real_ledger(tenant):
    cards = _cards(tenant)
    for sec in SEC.list_sections(tenant):
        card = cards[sec["id"]]
        assert _tid(f"sd-cost-row-{sec['id']}") in card, f"{tenant}/{sec['id']}"
        if not sec.get("image_targets"):
            # a text-only section holds no cache keys — structurally $0
            assert "deterministic slot-fill only; this section holds no cache keys" \
                in card, f"{tenant}/{sec['id']}"
        else:
            assert re.search(
                r"\$\d+\.\d+ across \d+ ledger call\(s\)"
                r"|\$0 — no api-cost ledger rows"
                r"|\$0 — deterministic slot-fill only", card), f"{tenant}/{sec['id']}"


def test_cost_row_sums_exactly_what_the_ledger_holds(tmp_path, monkeypatch):
    monkeypatch.setattr(AC, "LEDGER_PATH", tmp_path / "ledger.jsonl")
    AC.record_call(tenant="gauntlet", service="gemini_image",
                   model="gemini-2.5-flash-image", operation="image_generate",
                   cache_key="k_t04", images_generated=1)
    AC.record_call(tenant="gauntlet", service="gemini_image",
                   model="gemini-2.5-flash-image", operation="image_generate",
                   cache_key="k_t04", images_generated=1, status="429")
    want = AC.costs_for_cache_key("k_t04")
    row = OBS.cost_row("hero", ["k_t04", "—", None])
    assert row["calls"] == len(want["calls"]) == 2         # 429s are ledgered too (R35a)
    assert row["usd"] == want["estimated_cost_usd"]        # the sum IS the ledger's sum
    assert "k_t04" in row["label"] and f"${row['usd']:.3f}" in row["label"]


# --------------------------------------------------------------------------- #
# sd-ab — the numbers on the page EQUAL what the pool measured
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_ab_posteriors_and_lift_match_the_live_pool(tenant):
    routes = ROUTES[tenant]
    seed = OBS.seeded_campaign(tenant, tuple(routes))
    dp: DecisionPool = seed["dp"]
    page = _page(tenant)
    for sec in SEC.list_sections(tenant):
        for tt in sec.get("text_targets") or []:
            sid, slot = sec["id"], tt["slot_id"]
            i = page.find(_tid(f"sd-ab-{slot}"))
            assert i != -1, f"{tenant}: no ab panel for {slot}"
            panel = page[i:i + 5000]
            pid = DecisionPool.pool_id(tenant, sid, slot)
            for route in routes:
                cell = dp.serving_cell(tenant, sid, slot, route)
                active = dp.active(tenant, sid, slot, cell)
                mean = max(dp.posterior_mean(tenant, cell, v) for v in active)
                assert f"posterior mean {round(mean, 3):.3f}" in panel, \
                    f"{tenant}/{slot}/{route}: page number != pool measurement"
            lift = dp.lift_report(pid)
            assert lift["lift"] is not None, pid
            assert f"{lift['lift']:+.4f}" in panel, \
                f"{tenant}/{slot}: lift on page != measured lift"
            assert f"{lift['bandit_ctr']:.4f}" in panel
            assert f"{lift['control_ctr']:.4f}" in panel


@pytest.mark.parametrize("tenant", TENANTS)
def test_ab_seeded_pools_are_labeled_and_image_targets_stay_honest(tenant):
    page = _page(tenant)
    assert "seeded offline campaign" in page
    assert "· seeded" in page                        # the panel summary carries the label
    for it in SEC.list_image_targets(tenant):
        i = page.find(_tid(f"sd-ab-{it['surface_id']}"))
        assert i != -1
        panel = page[i:i + 3000]
        assert "no pool for this image target yet" in panel, \
            f"{tenant}/{it['surface_id']}: image ab panel must not fake a pool"
        assert "no posterior yet · lift vs control —" in panel


# --------------------------------------------------------------------------- #
# sd-drift — surgical pause: exactly hero_sub, nothing else
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("tenant", TENANTS)
def test_drift_pause_is_surgical(tenant):
    seed = OBS.seeded_campaign(tenant, tuple(ROUTES[tenant]))
    assert seed["paused"] == [f"{tenant}:hero:hero_sub__D"]   # measured, exactly one
    page = _page(tenant)
    for sec in SEC.list_sections(tenant):
        for tt in sec.get("text_targets") or []:
            slot = tt["slot_id"]
            i = page.find(_tid(f"sd-drift-{slot}"))
            assert i != -1
            badge = page[i:page.find("</span>", i)]
            if slot == "hero_sub":
                assert "drift: 1 arm paused" in badge, f"{tenant}: pause not surfaced"
                assert "c_tco invalidated" in badge           # attributable to the claim
            else:
                assert "drift: active" in badge, \
                    f"{tenant}/{slot}: pause leaked beyond the dependent pool"


def test_paused_arm_is_listed_in_the_hero_sub_ab_panel():
    for tenant in TENANTS:
        page = _page(tenant)
        i = page.find(_tid("sd-ab-hero_sub"))
        panel = page[i:i + 5000]
        assert "arm D" in panel and "c_tco" in panel, tenant
