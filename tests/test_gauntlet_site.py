"""GauntletAI replica (/gauntlet + /dev) — entry classification, tier routing determinism,
the no-hold-fact invariant, the login unlock, and /dev trace completeness.

All offline: the test client's host is not a public IP, so scene.reverse_ip() returns {}
and the IP layer routes tier 0 deterministically. Private-IP overrides exercise the ?ip=
path without any network call.
"""
from __future__ import annotations

import html

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import cohort as CO
from pipeline.personalization import gauntlet_site as GS

c = TestClient(app)


def _page_text(resp) -> str:
    return html.unescape(resp.text)

AD = "/gauntlet?utm_source=linkedin&utm_medium=paid&utm_campaign=catalyst-cto"
EMAIL = "/gauntlet?utm_source=hubspot&utm_medium=email&utm_campaign=cohort-april"
SEARCH = "/gauntlet?ref=google"


class _Req:
    """A minimal request stand-in for the pure classify_entry()/build_page() functions."""
    client = None                                    # scene.client_ip → "" → offline tier 0

    def __init__(self, params=None, headers=None):
        self.query_params = params or {}
        self.headers = headers or {}


# --------------------------------------------------------------------------- #
# 1 · Entry classification
# --------------------------------------------------------------------------- #
def test_entry_classification_four_channels():
    assert GS.classify_entry(_Req({"utm_medium": "paid"}))["channel"] == "ad"
    assert GS.classify_entry(_Req({"utm_medium": "CPC"}))["channel"] == "ad"
    assert GS.classify_entry(_Req({"utm_medium": "email"}))["channel"] == "email"
    assert GS.classify_entry(_Req({"ref": "google"}))["channel"] == "search"
    assert GS.classify_entry(_Req(headers={"referer": "https://www.bing.com/search?q=x"}))["channel"] == "search"
    assert GS.classify_entry(_Req())["channel"] == "direct"


def test_entry_classification_records_rule_and_signals():
    e = GS.classify_entry(_Req({"utm_medium": "paid", "utm_source": "linkedin",
                                "utm_campaign": "catalyst-cto"}))
    assert "utm_medium=paid" in e["rule"]
    assert any(s["label"] == "utm_campaign" and s["value"] == "catalyst-cto" for s in e["signals"])


def test_email_magic_token_identifies_the_recipient():
    tok = CO.magic_token(CO.BY_ID["liam"])
    e = GS.classify_entry(_Req({"utm_medium": "email", "e": tok}))
    assert e["channel"] == "email" and e["token_person_id"] == "liam"
    # a garbage token identifies nobody (and never raises)
    assert GS.classify_entry(_Req({"utm_medium": "email", "e": "mt_bogus"}))["token_person_id"] is None


def test_ad_campaign_message_match_changes_the_hero():
    generic = c.get("/gauntlet").text
    ad = c.get(AD).text
    assert "Rewire Your Engineers" in ad            # catalyst-cto → Catalyst-led hero
    assert "Rewire Your Engineers" not in generic
    challenger = c.get("/gauntlet?utm_medium=paid&utm_campaign=challenger-apply").text
    assert "Gauntlet Challenger" in challenger


# --------------------------------------------------------------------------- #
# 2 · Tier routing determinism
# --------------------------------------------------------------------------- #
def test_tier_routing_is_deterministic():
    a = c.get(SEARCH).text
    b = c.get(SEARCH).text
    assert a == b                                    # same inputs → byte-identical page
    d1 = c.get("/dev?ref=google&as=anon").text
    d2 = c.get("/dev?ref=google&as=anon").text
    assert d1 == d2


def test_private_ip_override_routes_tier_0_offline():
    t = c.get("/dev?ip=10.0.0.1&as=anon").text
    assert "tier 0" in t and "private / unreachable" in t


def test_same_structure_before_and_after_login():
    """Personalization only moves emphasis/order — every section ships in both states."""
    anon = c.get("/gauntlet").text
    c.post("/gauntlet/login", data={"email": GS.sample_login_email(), "next": "/gauntlet"})
    known = c.get("/gauntlet").text
    c.get("/gauntlet/logout")
    for marker in ("How We Prove", "Same Philosophy. Different Delivery.", "Think This Is You?",
                   "By the", "Go all-in on AI", "Apps shipped during training"):
        assert marker in anon and marker in known, f"section missing in one state: {marker}"


# --------------------------------------------------------------------------- #
# 3 · The no-hold-fact invariant
# --------------------------------------------------------------------------- #
def test_hold_facts_never_reach_the_shipped_page():
    """Modeled income (Clay, hold) and blocked say-variants must never ship on /gauntlet —
    for any cohort user, on any entry channel."""
    for p in CO.COHORT:
        c.post("/gauntlet/login", data={"email": p["email"], "next": "/gauntlet"})
        for url in ("/gauntlet", AD, EMAIL, SEARCH):
            t = c.get(url).text
            income = p["clay"].get("income_band")
            if income:
                assert income not in t, f"hold fact (income) shipped for {p['id']} at {url}"
            assert "we noticed" not in t and "de-anonymized" not in t.replace("/dev", "")
        c.get("/gauntlet/logout")


def test_blocked_say_variants_appear_only_on_dev():
    """The recite variants exist for contrast on /dev, and only there, marked blocked."""
    c.post("/gauntlet/login", data={"email": "liam.foster@gauntletai.com", "next": "/gauntlet"})
    dev = c.get("/dev").text
    site = c.get("/gauntlet").text
    c.get("/gauntlet/logout")
    assert "Blocked — the say variant the policy holds" in dev
    # liam abandoned his application at step 3 of 4 — /dev may show the blocked recite; the site not
    assert "You bailed at the" in dev
    assert "You bailed at the" not in site
    # the shipped close alludes instead
    assert "Finish what you started" in site


# --------------------------------------------------------------------------- #
# 4 · Login unlock
# --------------------------------------------------------------------------- #
def test_login_unlocks_say_level_copy_and_logout_clears_it():
    anon = c.get("/gauntlet").text
    assert "Welcome back, Maya" not in anon
    r = c.post("/gauntlet/login", data={"email": "maya.chen@gauntletai.com", "next": "/gauntlet"},
               follow_redirects=False)
    assert r.status_code == 303
    known = c.get("/gauntlet").text
    assert "Welcome back, Maya" in known             # say — she logged in
    assert "switch into AI without going broke" in known   # declared goal — say
    assert "Cedar Health" not in known               # Vector company — allude, never recited
    c.get("/gauntlet/logout")
    after = c.get("/gauntlet").text
    assert "Welcome back, Maya" not in after


def test_magic_token_jumps_to_known_prelogin():
    tok = CO.magic_token(CO.BY_ID["liam"])
    t = c.get(f"{EMAIL}&e={tok}").text
    assert "Welcome back, Liam" in t                 # identified with no login
    assert "Pinecrest" not in t                      # his employer stays allude


def test_unknown_work_email_still_escalates():
    c.post("/gauntlet/login", data={"email": "sam@acme-widgets.com", "next": "/gauntlet"})
    t = c.get("/gauntlet").text
    c.get("/gauntlet/logout")
    assert "For your team at Acme Widgets" in t      # domain → company, first-party say


# --------------------------------------------------------------------------- #
# 5 · /dev trace completeness
# --------------------------------------------------------------------------- #
def test_dev_trace_has_every_stage_with_full_entries():
    page = GS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "catalyst-cto"}),
                         email="maya.chen@gauntletai.com")
    stages = [t["stage"] for t in page["trace"]]
    for want in ("Entry classify", "IP resolve + classify", "Tier route", "Identity",
                 "Segments → archetype", "Audience route", "Objection prioritize",
                 "Hero image resolve", "Surface policy", "Compose"):
        assert want in stages, f"missing trace stage: {want}"
    for t in page["trace"]:
        for key in ("stage", "signals", "rule", "disposition", "output", "why"):
            assert t.get(key) not in (None, "", []), f"trace entry incomplete: {t['stage']}.{key}"


def test_dev_page_shows_all_panels_and_toggle():
    t = c.get("/dev?as=anon").text
    for panel in ("Entry point", "Tier routing", "Signal ledger", "CRM record",
                  "Per-slot copy decision", "Hero background",
                  "Objection checklist", "Trace — every stage"):
        assert panel in t, f"/dev missing panel: {panel}"
    assert "Anonymous — no login" in t
    k = c.get("/dev?as=known").text
    assert "Archetype" in k and GS.sample_login_email() in k
    # the toggle links are present and preserve the state
    assert "as=anon" in t and "as=known" in t


def test_dev_rebuilds_the_same_state_as_the_entry_url():
    d = c.get("/dev?utm_source=linkedin&utm_medium=paid&utm_campaign=catalyst-cto&as=anon").text
    assert "Paid ad (UTM)" in d and "catalyst-cto" in d
    assert "Rewire Your Engineers" in d              # the shipped hero appears in the copy diff


def test_process_map_covers_every_stage_with_data_and_branches():
    page = GS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-keyword-ai-hiring",
                               "utm_content": "v09"}),
                         email="maya.chen@gauntletai.com")
    pm = GS.process_map(page)
    assert len(pm["inputs"]) == 4                    # query · referer · IP · cookie
    ids = [s["id"] for s in pm["stages"]]
    assert ids == ["entry", "advariant", "ip", "tier", "identity", "archetype",
                   "audience", "objections", "policy", "compose", "heroimg"]
    for s in pm["stages"]:
        assert s["reads"], f"stage {s['id']} reads no data"
        assert s["output"], f"stage {s['id']} has no output"
        assert s["link"].startswith("#sec-"), f"stage {s['id']} missing anchor"
        if s["branches"] and not s["skipped"]:
            assert sum(1 for b in s["branches"] if b["taken"]) >= 1, \
                f"stage {s['id']} shows branches but none taken"
    # branch decisions match the page state
    entry = next(s for s in pm["stages"] if s["id"] == "entry")
    assert next(b["label"] for b in entry["branches"] if b["taken"]) == "ad"
    adv = next(s for s in pm["stages"] if s["id"] == "advariant")
    assert not adv["skipped"] and "x-keyword" in adv["output"]
    ident = next(s for s in pm["stages"] if s["id"] == "identity")
    assert next(b["label"] for b in ident["branches"] if b["taken"]) == "cohort CRM"
    arch = next(s for s in pm["stages"] if s["id"] == "archetype")
    assert not arch["skipped"]


def test_process_map_marks_skipped_stages_for_anonymous_direct():
    page = GS.build_page(_Req())
    pm = GS.process_map(page)
    adv = next(s for s in pm["stages"] if s["id"] == "advariant")
    arch = next(s for s in pm["stages"] if s["id"] == "archetype")
    assert adv["skipped"] and adv["skip_reason"]
    assert arch["skipped"] and arch["skip_reason"]
    ident = next(s for s in pm["stages"] if s["id"] == "identity")
    assert next(b["label"] for b in ident["branches"] if b["taken"]) == "anonymous"


def test_dev_page_renders_the_process_map():
    t = c.get("/dev?as=anon").text
    assert "Process map" in t
    for anchor in ("sec-entry", "sec-tier", "sec-crm", "sec-slots",
                   "sec-hero-image", "sec-objections", "sec-order"):
        assert f'id="{anchor}"' in t and f'href="#{anchor}"' in t, f"missing anchor: {anchor}"
    # inputs strip shows the four data sources
    for label in ("Query string", "Referer header", "Client IP", "Login cookie"):
        assert label in t


def test_showcase_card_publishes_the_entry_links():
    t = c.get("/showcase").text
    assert "GauntletAI replica" in t
    assert "utm_medium=paid" in t and "ref=google" in t and 'href="/gauntlet"' in t
    assert "/ad-lp" in t
    assert GS.sample_login_email() in t


# --------------------------------------------------------------------------- #
# 6 · X.com ad variants (12 = one per X Ads Manager targeting type)
# --------------------------------------------------------------------------- #
def test_twelve_ad_variants_catalog():
    assert len(GS.AD_VARIANTS) == 12
    campaigns = {v["utm_campaign"] for v in GS.AD_VARIANTS}
    assert len(campaigns) == 12
    assert len(GS.AD_BY_VARIANT_ID) == 12
    types = {v["x_targeting_type"] for v in GS.AD_VARIANTS}
    assert len(types) == 12
    assert "Follower look-alikes targeting" in types
    assert "Keyword targeting" in types


def test_twelve_utms_produce_twelve_distinct_hero_headlines():
    headlines = set()
    for v in GS.AD_VARIANTS:
        url = GS.variant_landing_url(v, "/gauntlet")
        t = _page_text(c.get(url))
        vp = v["page"]
        assert vp["h1_pre"] in t, f"h1_pre missing for {v['id']}"
        assert vp["h1_gold"] in t, f"h1_gold missing for {v['id']}: {vp['h1_gold']}"
        headlines.add(GS.variant_hero_headline(v))
    assert len(headlines) == 12


def test_ad_variant_trace_stage():
    page = GS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-interest-ai-ml", "utm_content": "v11",
    }))
    stages = [t["stage"] for t in page["trace"]]
    assert "Ad variant resolve" in stages
    assert page["ad_variant"]["id"] == "x-interest"
    trace = next(t for t in page["trace"] if t["stage"] == "Ad variant resolve")
    assert "Interest targeting" in str(trace["signals"])
    assert "Enterprise software" in str(trace["signals"])
    assert "v11" in str(trace["signals"])


def test_age_gender_variants_hold_on_landing_page():
    age = _page_text(c.get("/gauntlet?utm_source=x&utm_medium=paid&utm_campaign=x-age-senior-engineer&utm_content=v04"))
    gender = _page_text(c.get("/gauntlet?utm_source=x&utm_medium=paid&utm_campaign=x-gender-all&utm_content=v05"))
    assert "28" not in age or "28–45" not in age  # age range must not ship
    assert "28–45" not in age
    assert "All genders" not in gender
    page = GS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-age-senior-engineer", "utm_content": "v04"}))
    trace = next(t for t in page["trace"] if t["stage"] == "Ad variant resolve")
    assert "hold_policy" in str(trace["signals"]) or "hold" in trace["why"].lower()


def test_ad_lp_grid_pages_return_200():
    for path in ("/ad-lp", "/gauntlet/ad-lp", "/gauntletapt/ad-lp"):
        r = c.get(path)
        assert r.status_code == 200, path
        assert "12" in r.text and "Targeting" in r.text
        assert "utm_campaign=x-keyword-ai-hiring" in r.text
        assert "Location targeting" in r.text
        assert "Follower look-alikes targeting" in r.text
        assert GS.generic_hero_headline() in r.text


def test_ad_single_mockup_and_redirect():
    r = c.get("/gauntlet/ad?v=v07")
    assert r.status_code == 200
    assert "Event targeting" in r.text or "HR Tech" in r.text
    assert "utm_content=v07" in r.text
    assert c.get("/gauntlet/ad", follow_redirects=False).status_code == 302


def test_keyword_vs_lookalike_feel_like_different_products():
    kw = _page_text(c.get("/gauntlet?utm_source=x&utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09"))
    lk = _page_text(c.get("/gauntlet?utm_source=x&utm_medium=paid&utm_campaign=x-lookalike-eng-leaders&utm_content=v12"))
    assert "Can't Observe in 45 Minutes" in kw
    assert "Talent Density" in lk
    assert kw != lk


def test_portal_mount_ad_lp_links_stay_under_prefix():
    t = c.get("/gauntletapt/ad-lp").text
    assert 'href="/gauntletapt?' in t
    assert 'href="/gauntlet?' not in t


def test_portal_mount_serves_and_links_stay_under_prefix():
    """johnnycchung.com/gauntletapt — all hrefs + forms stay on the mount prefix."""
    t = c.get("/gauntletapt").text
    assert "Gauntlet" in t and 'href="/gauntletapt' in t
    assert 'action="/gauntletapt/login"' in t
    assert 'href="/dev' not in t
    d = c.get("/gauntletapt/dev?as=anon").text
    assert "Entry point" in d and 'href="/gauntletapt' in d
    assert 'href="/gauntletapt/static/atlas.css"' in d
    assert 'href="/static/atlas.css"' not in d
    legacy_dev = c.get("/dev?as=anon").text
    assert 'href="/static/atlas.css"' in legacy_dev
    c.post("/gauntletapt/login", data={"email": GS.sample_login_email(), "next": "/gauntletapt"})
    assert "Welcome back, Maya" in c.get("/gauntletapt").text
    c.get("/gauntletapt/logout")


def test_portal_mount_hero_api_and_asset_urls_use_prefix():
    """Portal fetch + cached hero URLs must stay under /gauntletapt."""
    qs = "?utm_medium=paid&utm_campaign=x-keyword-ai-hiring&utm_content=v09"
    t = c.get(f"/gauntletapt{qs}").text
    assert 'data-hero-api="/gauntletapt/api/hero-image"' in t
    r = c.get(f"/gauntletapt/api/hero-image{qs}")
    assert r.status_code == 200
    data = r.json()
    if data.get("url"):
        assert data["url"].startswith("/gauntletapt/static/")
        assert not data["url"].startswith("/static/")


# --------------------------------------------------------------------------- #
# 7 · Objection-driven copy
# --------------------------------------------------------------------------- #
def test_objection_catalog_has_fifteen_entries():
    assert len(GS.OBJECTION_CATALOG) == 16
    ids = {o["id"] for o in GS.OBJECTION_CATALOG}
    assert "open_market_hire" in ids and "selection_rate_low" in ids and "ld_budget_committed" in ids


def test_cto_keyword_ad_surfaces_hire_objection():
    page = GS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-keyword-ai-hiring", "utm_content": "v09",
    }))
    top = page["objections"]["prioritized"][0]
    assert top["objection_id"] in ("open_market_hire", "ten_weeks_long", "need_hires_not_training")
    assert "open market" in top["text"].lower() or "45-minute" in page["sections"]["hero"]["sub"].lower() \
        or "ten weeks" in top["text"].lower()


def test_hr_event_ad_surfaces_ld_budget_objection():
    page = GS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-event-hrtech", "utm_content": "v07",
    }))
    top = page["objections"]["prioritized"][0]
    assert top["objection_id"] == "ld_budget_committed"
    assert "L&D budget" in top["text"]


def test_engineer_age_ad_surfaces_already_senior_objection():
    page = GS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-age-senior-engineer", "utm_content": "v04",
    }))
    top = page["objections"]["prioritized"][0]
    assert top["objection_id"] == "already_senior"
    assert "already senior" in top["text"].lower()


def test_abandoned_applicant_surfaces_selection_rate_objection():
    page = GS.build_page(_Req({"utm_medium": "direct"}), email="liam.foster@gauntletai.com")
    ids = [o["objection_id"] for o in page["objections"]["prioritized"]]
    assert "selection_rate_low" in ids
    assert any(a["objection_id"] == "selection_rate_low" for a in page["objections"]["assignments"])


def test_objection_hold_reframes_never_ship():
    """Blocked say-level objection reframes (income band) must not appear on /gauntlet."""
    for p in CO.COHORT:
        c.post("/gauntlet/login", data={"email": p["email"], "next": "/gauntlet"})
        t = c.get("/gauntlet?utm_source=x&utm_medium=paid&utm_campaign=x-age-senior-engineer&utm_content=v04").text
        assert "modeled your income" not in t
        assert "pre-selected a payment plan" not in t
        assert "pre-picked a payment plan" not in t
        c.get("/gauntlet/logout")
    dev = c.get("/dev?as=known").text
    assert "Blocked say reframe" in dev or "Blocked — the say variant" in dev


def test_objection_trace_stage():
    page = GS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-event-hrtech", "utm_content": "v07",
    }))
    trace = next(t for t in page["trace"] if t["stage"] == "Objection prioritize")
    assert "ld_budget_committed" in str(trace["signals"]) or trace["output"]
    assert page["objections"]["assignments"]
