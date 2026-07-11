"""Tests for /apt/demo visitor tour sitemap and demo_scenarios.yaml."""
from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import demo_nav as NAV

c = TestClient(app)


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
    r = c.get("/apt/demo")
    assert r.status_code == 200
    t = r.text
    assert "/apt/demo" in t
    assert "demo tour" in t.lower() or "visitor demo" in t.lower()
    assert "GauntletAI" in t
    assert "Planet" in t
    assert 'href="/gauntletapt/ad-lp"' in t
    assert 'href="/gauntletapt/direct"' in t
    assert 'href="/gauntletapt/email"' in t
    assert 'href="/gauntletapt?ref=google"' in t
    assert 'href="/planetapt/ads"' in t
    assert 'href="/planetapt/direct"' in t
    assert 'href="/planetapt/email"' in t
    assert 'href="/planetapt?ref=google"' in t
    assert 'href="/apt/dev' in t


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


def test_apt_dev_hub_marketer_console_first():
    t = c.get("/apt/dev").text
    m_pos = t.find("Marketer console")
    e_pos = t.find("Engineer console")
    assert m_pos != -1 and e_pos != -1
    assert m_pos < e_pos


def test_apt_dev_hub_links_demo_sitemap():
    t = c.get("/apt/dev").text
    assert 'href="/apt/demo"' in t


def test_demo_sitemap_prompt_reference_count():
    t = c.get("/apt/demo").text
    assert "design_prompts.yaml" in t
    assert "Prompt reference" in t


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
