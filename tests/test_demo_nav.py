"""Tests for /apt/demo visitor tour sitemap and demo_scenarios.yaml."""
from __future__ import annotations

import json
from pathlib import Path

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import cohort as CO
from pipeline.personalization import demo_nav as NAV

c = TestClient(app)

WORKFLOWS_PATH = Path(__file__).resolve().parents[1] / "docs" / "workflows.json"
V09_QS = (
    "?utm_source=x&utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09"
)


def test_demo_scenarios_yaml_loads():
    data = NAV.load_scenarios()
    assert data["version"] == 1
    assert "gauntlet" in data["tenants"]
    assert "planet" in data["tenants"]
    assert len(data["scenarios"]) >= 10


def test_demo_scenario_ids_unique():
    data = NAV.load_scenarios()
    ids = [s["id"] for s in data["scenarios"]]
    assert len(ids) == len(set(ids))


def test_resolve_scenario_magic_token_in_urls():
    liam = next(s for s in NAV.load_scenarios()["scenarios"] if s["id"] == "g-email-liam-token")
    urls = NAV.resolve_scenario_urls(liam)
    assert "utm_medium=email" in urls["landing_url"]
    assert "e=mt_" in urls["landing_url"]
    assert "as=known" in urls["console_deep_link"]


def test_wf_demo_001_sitemap_tour_gauntlet_channels():
    # W9 (R42/R43): /apt/demo is the workspace Home; channel cards land on
    # PRODUCT setup pages, never straight on galleries or landing URLs.
    r = c.get("/apt/demo")
    assert r.status_code == 200
    t = r.text
    assert "/apt/demo" in t
    assert "Launch personalization on" in t     # J1 checklist
    assert "GauntletAI" in t
    assert "Planet" in t
    # Default active site = gauntlet → its four channel cards → setup pages.
    for ch in ("direct", "search", "ads", "email"):
        assert f'href="/apt/channel/{ch}?site=gauntlet"' in t, ch
    assert 'href="/gauntletapt/ad-lp"' not in t  # no raw landing links on Home
    assert 'href="/apt/dev' in t
    # The sidebar website selector switches the active tenant.
    assert 'href="/apt/demo?site=planet"' in t
    # …and ?site=planet surfaces planet's four channel setup pages.
    p = c.get("/apt/demo?site=planet").text
    for ch in ("direct", "search", "ads", "email"):
        assert f'href="/apt/channel/{ch}?site=planet"' in p, ch


def test_direct_email_galleries_return_200():
    paths = [
        "/gauntletapt/direct",
        "/gauntletapt/email",
        "/planetapt/direct",
        "/planetapt/email",
        "/gauntlet/direct",
        "/gauntlet/email",
        "/planet/direct",
        "/planet/email",
    ]
    for path in paths:
        assert c.get(path).status_code == 200, path


def test_audience_tabs_filter_scenarios():
    all_r = c.get("/gauntletapt/direct")
    biz = c.get("/gauntletapt/direct?audience=business")
    con = c.get("/gauntletapt/direct?audience=consumer")
    assert all_r.status_code == 200
    assert biz.status_code == 200
    assert con.status_code == 200
    assert "Corporate IP" in biz.text
    assert "Cold visit" not in biz.text
    assert "Cold visit" in con.text
    assert "Corporate IP" not in con.text
    assert "Corporate IP" in all_r.text
    assert "Cold visit" in all_r.text
    assert 'class="aud-tog"' in biz.text


def test_landing_urls_contain_expected_query_params():
    corp = c.get("/gauntletapt/direct?audience=business")
    assert "ip=17.253.144.10" in corp.text
    email = c.get("/gauntletapt/email")
    assert "utm_medium=email" in email.text
    assert "e=mt_" in email.text
    assert "email-card" in email.text
    assert "HubSpot" in email.text


def test_wf_demo_002_direct_gallery_corporate_ip_to_business_console():
    r = c.get("/gauntletapt/direct?audience=business")
    assert r.status_code == 200
    t = r.text
    assert "Corporate IP" in t
    assert "ip=17.253.144.10" in t
    assert "/gauntletapt/dev?ip=17.253.144.10" in t
    assert "as=anon" in t
    assert "/gauntletapt/dev/business?ip=17.253.144.10" in t
    con = c.get("/gauntletapt/direct?audience=consumer")
    assert "Cold visit" in con.text


def test_wf_demo_003_email_gallery_liam_token_trace():
    r = c.get("/gauntletapt/email")
    assert r.status_code == 200
    t = r.text
    assert "Liam" in t
    assert "utm_medium=email" in t
    assert "e=mt_" in t
    assert "email-card" in t
    assert "liam.foster@gauntletai.com" in t
    landing = c.get("/gauntletapt?utm_source=hubspot&utm_medium=email&utm_campaign=cohort-april&e="
                    + NAV._magic_tokens()["liam"])
    assert landing.status_code == 200
    assert "Welcome back, Liam" in landing.text
    assert "Pinecrest" not in landing.text


def test_wf_demo_004_ad_lp_v09_clickthrough():
    r = c.get("/gauntletapt/ad-lp")
    assert r.status_code == 200
    t = r.text
    assert "utm_content=v09" in t
    assert "/gauntletapt?utm_source=x" in t and "utm_campaign=x-keyword-ai-hiring" in t
    assert "/gauntletapt/dev?utm_source=x" in t and "utm_content=v09" in t and "as=anon" in t
    assert 'href="/apt/demo"' in t


def test_wf_demo_005_identity_preview_toggle_persists():
    anon = c.get("/apt/dev?site=gauntlet&as=anon").text
    assert "as=anon" in anon
    known = c.get("/apt/dev?site=gauntlet&as=known").text
    assert "as=known" in known
    assert "/gauntletapt/dev" in known and "as=known" in known
    assert "/gauntletapt/dev/business" in known and "as=known" in known


def test_wf_demo_006_hub_site_switch_preserves_as():
    t = c.get("/apt/dev?site=gauntlet&as=known").text
    assert 'href="/apt/dev?site=planet&amp;as=known"' in t
    assert "/gauntletapt/dev" in t and "as=known" in t


def test_apt_dev_hub_is_preview_not_console_launcher():
    # W8-A menu merge: /apt/dev no longer renders console-launcher cards (they
    # duplicated the sidebar). It is the Preview step: live CTA + entry chips.
    t = c.get("/apt/dev").text
    assert "Preview as visitor" in t
    assert "hub-grid" not in t
    assert "Marketer console" not in t and "Engineer console" not in t
    assert "hub-live" in t                       # open-the-live-page CTA
    assert "Or arrive from a campaign" in t      # entry simulation row


def test_apt_dev_hub_links_demo_sitemap():
    # Campaigns overview stays one canonical route away — via the sidebar tree
    # (the redundant topbar "Demo sitemap →" button was removed in W8-A).
    t = c.get("/apt/dev").text
    assert 'href="/apt/demo?site=' in t


def test_demo_sitemap_prompt_reference_count():
    # W9 (R45): engineering vocabulary left the Home page — the prompt catalog
    # lives on the marketer console (and the file itself stays the SSOT).
    t = c.get("/apt/demo").text
    assert "design_prompts.yaml" not in t
    t2 = c.get("/gauntletapt/dev/business?as=anon").text
    assert "Prompt reference" in t2 and "design_prompts.yaml" in t2


def test_wf_demo_007_sales_demo_urls_all_return_200():
    """Smoke: sitemap + galleries + existing ad routes + search entry return 200."""
    paths = [
        "/apt/demo",
        "/gauntletapt/ad-lp",
        "/gauntletapt/direct",
        "/gauntletapt/email",
        "/planetapt/ads",
        "/planetapt/direct",
        "/planetapt/email",
        "/gauntletapt?ref=google",
        "/planetapt?ref=google",
        "/apt/dev",
    ]
    for path in paths:
        assert c.get(path).status_code == 200, path


def test_workflows_json_exports_wf_demo_001_through_010():
    data = json.loads(WORKFLOWS_PATH.read_text(encoding="utf-8"))
    ids = [w["id"] for w in data["workflows"]]
    for n in range(1, 11):
        want = f"WF-DEMO-{n:03d}"
        assert want in ids, want
    by_id = {w["id"]: w for w in data["workflows"]}
    assert by_id["WF-DEMO-008"]["test"].endswith("test_wf_demo_008_planet_location_signal_direct")
    assert by_id["WF-DEMO-009"]["test"].endswith("test_wf_demo_009_hold_never_on_replica_blocked_on_dev")
    assert by_id["WF-DEMO-010"]["test"].endswith("test_wf_demo_010_prebuild_delivery_inventory")


def test_wf_demo_008_planet_location_signal_direct():
    direct = c.get("/planetapt/direct")
    assert direct.status_code == 200
    assert "ip=19.7.0.1" in direct.text
    assert "Midwest" in direct.text or "Ag enterprise" in direct.text

    landing = c.get("/planetapt?ip=19.7.0.1")
    assert landing.status_code == 200
    assert "imaged" in landing.text.lower()
    assert "Dearborn" not in landing.text  # city precision held

    dev = c.get("/planetapt/dev?ip=19.7.0.1&as=anon")
    assert dev.status_code == 200
    assert "Location signal" in dev.text

    tier0 = c.get("/planetapt/dev?ip=10.0.0.1&as=anon")
    assert tier0.status_code == 200
    assert "tier 0" in tier0.text


def test_wf_demo_009_hold_never_on_replica_blocked_on_dev():
    tok = CO.magic_token(CO.BY_ID["liam"])
    landing = c.get(
        "/gauntletapt?utm_source=hubspot&utm_medium=email&utm_campaign=cohort-april&e=" + tok
    )
    assert landing.status_code == 200
    t = landing.text
    assert "You bailed at the" not in t
    assert "Welcome back, Liam" in t
    assert "Pinecrest" not in t

    dev = c.get(
        "/gauntletapt/dev?utm_source=hubspot&utm_medium=email&utm_campaign=cohort-april&e="
        + tok
    ).text
    assert "Blocked — the say variant the policy holds" in dev
    assert "You bailed at the" in dev

    c.post("/gauntletapt/login", data={"email": "maya.chen@gauntletai.com", "next": "/gauntletapt"})
    maya_site = c.get("/gauntletapt").text
    maya_dev = c.get("/gauntletapt/dev?as=known").text
    c.get("/gauntletapt/logout")
    assert "Welcome back, Maya" in maya_site
    assert "Cedar Health" not in maya_site
    assert "de-anonymized" in maya_dev or "Blocked" in maya_dev


def test_wf_demo_010_prebuild_delivery_inventory():
    t = c.get(f"/gauntletapt/dev/business{V09_QS}&as=anon").text
    assert t.count('id="b-delivery"') == 1
    assert "rules/gauntlet_prebuild.yaml" in t
    assert "ad v09 · anon" in t
    assert "railway run python -m scripts.warm_hero_cache" in t
    assert 'data-stage="prebuild"' in t

    guide = c.get("/gauntletapt/dev/image-decisions")
    assert guide.status_code == 200
    assert "pre-cached" in guide.text.lower() or "Pre-cached" in guide.text

    direct_biz = c.get("/gauntletapt/dev/business?as=anon").text
    assert "direct · anon" in direct_biz.lower() or "Direct · anon" in direct_biz


def test_marketer_console_channel_strip_and_prompt_catalog():
    # W8-A menu merge: the console's in-page rail (side-cap groups) and its
    # "← Demo sitemap" link are gone — the apt sidebar is the ONE menu. The
    # visit-context strip and the prompt catalog stay.
    t = c.get(f"/gauntletapt/dev/business{V09_QS}&as=anon").text
    assert "visit context" in t
    assert "Prompt reference" in t
    assert "rules/design_prompts.yaml" in t
    assert "gauntlet.hero.message_match.ad" in t
    assert 'id="gb-nav"' not in t and 'class="side-cap"' not in t   # no menu-inside-a-menu


def test_planet_ads_links_demo_sitemap():
    t = c.get("/planetapt/ads").text
    assert 'href="/apt/demo"' in t
    assert "← Demo sitemap" in t


def test_mockups_index_returns_200():
    r = c.get("/apt/mockups")
    assert r.status_code == 200
    t = r.text
    assert "15 UI mockups" in t
    assert "/apt/mockups/sitemap-a" in t
    assert "/apt/mockups/ads-c" in t


def test_mockup_page_serves_html():
    r = c.get("/apt/mockups/sitemap-b")
    assert r.status_code == 200
    assert "Variant B" in r.text
    assert "GauntletAI" in r.text
    assert "/apt/mockups/sitemap-c" in r.text


def test_mockup_unknown_returns_404():
    assert c.get("/apt/mockups/not-a-real-mock").status_code == 404
