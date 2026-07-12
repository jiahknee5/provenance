"""Planet replica (/planet + /planet/dev) — entry classification, tier routing determinism,
the LOCATION signal (the Planet differentiator), the no-hold-fact invariant, the login
unlock, the unified /ads grid (W6-E: shared gauntlet-layout template, /ads-lp folded
in as a 302), and /planet/dev trace completeness.

All offline: the test client's host is not a public IP, so scene.reverse_ip() returns {}
and the IP layer routes tier 0 deterministically. Private-IP overrides exercise the ?ip=
path without any network call.
"""
from __future__ import annotations

import html

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import planet_cohort as CO
from pipeline.personalization import planet_site as PS

c = TestClient(app)


def _page_text(resp) -> str:
    return html.unescape(resp.text)

AD = "/planet?utm_source=linkedin&utm_medium=paid&utm_campaign=defense-sovereign-mission"
EMAIL = "/planet?utm_source=hubspot&utm_medium=email&utm_campaign=crisis-responders"
SEARCH = "/planet?ref=google"


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
    assert PS.classify_entry(_Req({"utm_medium": "paid"}))["channel"] == "ad"
    assert PS.classify_entry(_Req({"utm_medium": "CPC"}))["channel"] == "ad"
    assert PS.classify_entry(_Req({"utm_medium": "email"}))["channel"] == "email"
    assert PS.classify_entry(_Req({"ref": "google"}))["channel"] == "search"
    assert PS.classify_entry(_Req(headers={"referer": "https://www.bing.com/search?q=x"}))["channel"] == "search"
    assert PS.classify_entry(_Req())["channel"] == "direct"


def test_email_magic_token_identifies_the_recipient():
    tok = CO.magic_token(CO.BY_ID["kofi"])
    e = PS.classify_entry(_Req({"utm_medium": "email", "e": tok}))
    assert e["channel"] == "email" and e["token_person_id"] == "kofi"
    assert PS.classify_entry(_Req({"utm_medium": "email", "e": "pt_bogus"}))["token_person_id"] is None


def test_ad_campaign_message_match_changes_the_hero():
    generic = c.get("/planet").text
    ad = c.get(AD).text
    assert "Broad Area Management at" in ad            # enterprise campaign intent
    assert "Broad Area Management at" not in generic
    selfserve = c.get("/planet?utm_medium=paid&utm_campaign=trial-aum-2026").text
    assert "Your AOI," in selfserve


# --------------------------------------------------------------------------- #
# 2 · Tier routing determinism + LOCATION signal
# --------------------------------------------------------------------------- #
def test_tier_routing_is_deterministic():
    a = c.get(SEARCH).text
    b = c.get(SEARCH).text
    assert a == b
    d1 = c.get("/planet/dev?ref=google&as=anon").text
    d2 = c.get("/planet/dev?ref=google&as=anon").text
    assert d1 == d2


def test_private_ip_override_routes_tier_0_offline():
    t = c.get("/planet/dev?ip=10.0.0.1&as=anon").text
    assert "tier 0" in t and "private / unreachable" in t


def test_location_signal_region_templates_per_segment():
    """Region × segment → the truthful daily-coverage line, at region scale only."""
    det = {"region": "Iowa", "city": "Des Moines"}
    ag = PS.location_signal(det, 1, PS.AD_BY_VARIANT_ID["v01"])
    assert ag["mode"] == "region"
    assert ag["line"] == "Every field in Iowa, imaged today."
    assert ag["policy"] == "allude"
    assert "Des Moines" in ag["blocked_say"]           # city precision is held, never shipped
    ins = PS.location_signal({"region": "Florida", "city": None}, 1, PS.AD_BY_VARIANT_ID["v03"])
    assert "property in Florida" in ins["line"]
    default = PS.location_signal({"region": "Texas", "city": None}, 1, None)
    assert "Planet imaged Texas today" in default["line"]


def test_location_signal_defense_uses_theater_never_visitor_location():
    det = {"region": "Virginia", "city": "Arlington"}
    loc = PS.location_signal(det, 2, PS.AD_BY_VARIANT_ID["v02"])
    assert loc["mode"] == "theater"
    assert "Virginia" not in loc["line"]
    assert loc["line"] == PS.THEATER_LINE


def test_location_signal_holds_at_tier_0():
    loc = PS.location_signal({}, 0, None)
    assert loc["mode"] == "none" and loc["line"] == ""
    assert loc["policy"] == "hold"


def test_location_stage_in_trace_and_page_contract():
    page = PS.build_page(_Req())
    stages = [t["stage"] for t in page["trace"]]
    assert "Location signal" in stages
    assert page["location"]["mode"] == "none"          # offline — no region resolves
    assert page["sections"]["hero"]["location_line"] == ""
    assert any(d["slot"] == "hero_location" for d in page["copy_diff"])


def test_same_structure_before_and_after_login():
    """Personalization only moves emphasis/order — every section ships in both states."""
    anon = _page_text(c.get("/planet"))
    c.post("/planet/login", data={"email": PS.sample_login_email(), "next": "/planet"})
    known = _page_text(c.get("/planet"))
    c.get("/planet/logout")
    for marker in ("How We Make Change", "Look Broader. Look Closer.",
                   "Your Study Area, Daily Since 2016", "By the",
                   "See your world change daily", "Earth's entire landmass, imaged every day"):
        assert marker in anon and marker in known, f"section missing in one state: {marker}"


# --------------------------------------------------------------------------- #
# 3 · The no-hold-fact invariant
# --------------------------------------------------------------------------- #
def test_hold_facts_never_reach_the_shipped_page():
    """Modeled income (Clay, hold) and blocked say-variants must never ship on /planet —
    for any cohort user, on any entry channel."""
    for p in CO.COHORT:
        c.post("/planet/login", data={"email": p["email"], "next": "/planet"})
        for url in ("/planet", AD, EMAIL, SEARCH):
            t = c.get(url).text
            income = p["clay"].get("income_band")
            if income:
                assert income not in t, f"hold fact (income) shipped for {p['id']} at {url}"
            assert "we noticed" not in t and "de-anonymized" not in t.replace("/planet/dev", "")
        c.get("/planet/logout")


def test_blocked_say_variants_appear_only_on_dev():
    """The recite variants exist for contrast on /planet/dev, and only there, marked blocked."""
    c.post("/planet/login", data={"email": "kofi.tanaka@pacificrelief.org", "next": "/planet"})
    dev = c.get("/planet/dev").text
    site = c.get("/planet").text
    c.get("/planet/logout")
    assert "Blocked — the say variant the policy holds" in dev
    # kofi abandoned the trial signup — /planet/dev may show the blocked recite; the site not
    assert "You bailed at the" in dev
    assert "You bailed at the" not in site
    assert "You abandoned the trial signup" not in site
    # the shipped close alludes instead
    assert "Finish what you started" in site


# --------------------------------------------------------------------------- #
# 4 · Login unlock
# --------------------------------------------------------------------------- #
def test_login_unlocks_say_level_copy_and_logout_clears_it():
    anon = c.get("/planet").text
    assert "Welcome back, Amara" not in anon
    r = c.post("/planet/login", data={"email": "amara.diallo@meridianagronomy.com", "next": "/planet"},
               follow_redirects=False)
    assert r.status_code == 303
    known = c.get("/planet").text
    assert "Welcome back, Amara" in known              # say — she logged in
    assert "monitor two million acres of seed production" in known   # declared goal — say
    assert "Meridian Agronomy" not in known            # Vector company — allude, never recited
    c.get("/planet/logout")
    after = c.get("/planet").text
    assert "Welcome back, Amara" not in after


def test_magic_token_jumps_to_known_prelogin():
    tok = CO.magic_token(CO.BY_ID["kofi"])
    t = c.get(f"{EMAIL}&e={tok}").text
    assert "Welcome back, Kofi" in t                   # identified with no login
    assert "Pacific Relief" not in t                   # his employer stays allude


def test_unknown_work_email_still_escalates():
    c.post("/planet/login", data={"email": "sam@acme-widgets.com", "next": "/planet"})
    t = c.get("/planet").text
    c.get("/planet/logout")
    assert "For your team at Acme Widgets" in t        # domain → company, first-party say


# --------------------------------------------------------------------------- #
# 5 · /planet/dev trace completeness
# --------------------------------------------------------------------------- #
def test_dev_trace_has_every_stage_with_full_entries():
    page = PS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-location-crop-belts",
                               "utm_content": "v01"}),
                         email="amara.diallo@meridianagronomy.com")
    stages = [t["stage"] for t in page["trace"]]
    for want in ("Entry classify", "IP resolve + classify", "Tier route", "Location signal",
                 "Identity", "Segments → archetype", "Audience route", "Objection prioritize",
                 "Hero image resolve", "Hero motion resolve", "Surface policy", "Compose"):
        assert want in stages, f"missing trace stage: {want}"
    for t in page["trace"]:
        for key in ("stage", "signals", "rule", "disposition", "output", "why"):
            assert t.get(key) not in (None, "", []), f"trace entry incomplete: {t['stage']}.{key}"


def test_dev_page_shows_all_panels_and_toggle():
    t = c.get("/planet/dev?as=anon").text
    for panel in ("Entry point", "Tier routing", "Location signal", "Signal ledger", "CRM record",
                  "Per-slot copy decision", "Hero background",
                  "Objection checklist", "Trace — every stage"):
        assert panel in t, f"/planet/dev missing panel: {panel}"
    assert "Anonymous — no login" in t
    k = c.get("/planet/dev?as=known").text
    assert "Archetype" in k and PS.sample_login_email() in k
    assert "as=anon" in t and "as=known" in t


def test_dev_rebuilds_the_same_state_as_the_entry_url():
    d = c.get("/planet/dev?utm_source=x&utm_medium=paid&utm_campaign=x-location-crop-belts"
              "&utm_content=v01&as=anon").text
    assert "Paid ad (UTM)" in d and "x-location-crop-belts" in d
    assert "Every Field in Your Region," in d          # the shipped hero appears in the copy diff


def test_process_map_covers_every_stage_with_data_and_branches():
    page = PS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-location-crop-belts",
                               "utm_content": "v01"}),
                         email="amara.diallo@meridianagronomy.com")
    pm = PS.process_map(page)
    assert len(pm["inputs"]) == 4                      # query · referer · IP · cookie
    ids = [s["id"] for s in pm["stages"]]
    assert ids == ["entry", "advariant", "ip", "tier", "location", "identity", "archetype",
                   "audience", "objections", "policy", "compose", "brainsim", "heroimg",
                   "heromotion"]
    for s in pm["stages"]:
        assert s["reads"], f"stage {s['id']} reads no data"
        assert s["output"], f"stage {s['id']} has no output"
        assert s["link"].startswith("#sec-"), f"stage {s['id']} missing anchor"
        assert s["detail"], f"stage {s['id']} has no drill-down detail"
        for r in s["detail"]:
            assert r["k"] and r["v"] not in (None, ""), f"empty drill-down row in {s['id']}"
        if s["branches"] and not s["skipped"]:
            assert sum(1 for b in s["branches"] if b["taken"]) >= 1, \
                f"stage {s['id']} shows branches but none taken"
    entry = next(s for s in pm["stages"] if s["id"] == "entry")
    assert next(b["label"] for b in entry["branches"] if b["taken"]) == "ad"
    adv = next(s for s in pm["stages"] if s["id"] == "advariant")
    assert not adv["skipped"] and "x-agriculture" in adv["output"]
    ident = next(s for s in pm["stages"] if s["id"] == "identity")
    assert next(b["label"] for b in ident["branches"] if b["taken"]) == "cohort CRM"
    arch = next(s for s in pm["stages"] if s["id"] == "archetype")
    assert not arch["skipped"]


def test_process_map_location_stage_shows_full_decision_space():
    page = PS.build_page(_Req())
    pm = PS.process_map(page)
    loc = next(s for s in pm["stages"] if s["id"] == "location")
    # all segment templates listed as the decision space, plus theater + guardrail rows
    tmpl_rows = [r for r in loc["detail"] if r["k"].startswith("template ·")]
    assert len(tmpl_rows) >= len(PS.LOCATION_LINES) + 2
    assert next(b["label"] for b in loc["branches"] if b["taken"]) == "no claim (tier 0)"
    assert any(r["pol"] == "hold" for r in loc["detail"])   # the anti-surveillance guardrail row


def test_process_map_marks_skipped_stages_for_anonymous_direct():
    page = PS.build_page(_Req())
    pm = PS.process_map(page)
    adv = next(s for s in pm["stages"] if s["id"] == "advariant")
    arch = next(s for s in pm["stages"] if s["id"] == "archetype")
    assert adv["skipped"] and adv["skip_reason"]
    assert arch["skipped"] and arch["skip_reason"]
    ident = next(s for s in pm["stages"] if s["id"] == "identity")
    assert next(b["label"] for b in ident["branches"] if b["taken"]) == "anonymous"
    assert any("catalogued" in r["v"].lower() or "variant" in r["v"].lower()
               for r in adv["detail"])
    assert len(arch["detail"]) == 6                        # all six archetypes listed


def test_process_map_drilldowns_carry_evidence_and_fired_markers():
    page = PS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-location-crop-belts",
                               "utm_content": "v01"}),
                         email="amara.diallo@meridianagronomy.com")
    pm = PS.process_map(page)
    by_id = {s["id"]: s for s in pm["stages"]}
    entry_rules = [r for r in by_id["entry"]["detail"] if r["k"].startswith("rule ·")]
    assert len(entry_rules) == 4 and sum(1 for r in entry_rules if r["fired"]) == 1
    assert any(r["k"] == "Ad · trigger" for r in by_id["advariant"]["detail"])
    assert any(r["k"] == "Slots overridden" for r in by_id["advariant"]["detail"])
    assert any(r["k"] == "Segment" for r in by_id["advariant"]["detail"])
    tier_rules = [r for r in by_id["tier"]["detail"] if r["k"].startswith("tier ")]
    assert len(tier_rules) == 4 and sum(1 for r in tier_rules if r["fired"]) == 1
    id_pols = {r["pol"] for r in by_id["identity"]["detail"] if r["pol"]}
    assert "say" in id_pols and "allude" in id_pols
    rungs = by_id["audience"]["detail"]
    assert len(rungs) == 5 and sum(1 for r in rungs if r["fired"]) == 1
    assert rungs[0]["fired"]                               # ad variant wins the precedence
    assert len([r for r in by_id["policy"]["detail"] if not r["k"].startswith("blocked")]) \
        == len(page["copy_diff"])
    orders = [r for r in by_id["compose"]["detail"] if r["k"].startswith("order ·")]
    assert len(orders) >= 4 and sum(1 for r in orders if r["fired"]) >= 1


def test_dev_page_renders_the_process_map():
    t = c.get("/planet/dev?as=anon").text
    assert "Process map" in t
    for anchor in ("sec-entry", "sec-tier", "sec-location", "sec-brain-sim", "sec-crm", "sec-slots",
                   "sec-hero-image", "sec-objections", "sec-order"):
        assert f'id="{anchor}"' in t and f'href="#{anchor}"' in t, f"missing anchor: {anchor}"
    for label in ("Query string", "Referer header", "Client IP", "Login cookie"):
        assert label in t


def test_showcase_card_publishes_the_entry_links():
    t = c.get("/showcase").text
    assert "Planet replica" in t
    # W6-E: one X-ads grid per tenant — the separate LP-variants entry is gone.
    assert 'href="/planetapt"' in t and "/planetapt/ads" in t
    assert "/planetapt/ads-lp" not in t
    assert PS.sample_login_email() in t


# --------------------------------------------------------------------------- #
# 6 · X.com ad variants (12 = one per X Ads Manager targeting type × segment)
# --------------------------------------------------------------------------- #
def test_twelve_ad_variants_catalog():
    assert len(PS.AD_VARIANTS) == 12
    campaigns = {v["utm_campaign"] for v in PS.AD_VARIANTS}
    assert len(campaigns) == 12
    assert len(PS.AD_BY_VARIANT_ID) == 12
    types = {v["x_targeting_type"] for v in PS.AD_VARIANTS}
    assert len(types) == 12
    assert "Follower look-alikes targeting" in types
    assert "Keyword targeting" in types
    # the spine: the researched market segments are all represented
    segments = {v["segment"] for v in PS.AD_VARIANTS}
    for seg in ("agriculture", "defense", "insurance", "forestry", "energy",
                "government", "maritime", "disaster", "research"):
        assert seg in segments, f"missing market segment: {seg}"
    # 2 categories × 6
    for cat in ("vertical", "audience"):
        assert sum(1 for v in PS.AD_VARIANTS if v["category"] == cat) == 6


def test_twelve_utms_produce_twelve_distinct_hero_headlines():
    headlines = set()
    for v in PS.AD_VARIANTS:
        url = PS.variant_landing_url(v, "/planet")
        t = _page_text(c.get(url))
        vp = v["page"]
        assert vp["h1_pre"] in t, f"h1_pre missing for {v['id']}"
        assert vp["h1_blue"] in t, f"h1_blue missing for {v['id']}: {vp['h1_blue']}"
        headlines.add(PS.variant_hero_headline(v))
    assert len(headlines) == 12


def test_ad_variant_trace_stage():
    page = PS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-interest-maritime", "utm_content": "v07",
    }))
    stages = [t["stage"] for t in page["trace"]]
    assert "Ad variant resolve" in stages
    assert page["ad_variant"]["id"] == "x-maritime"
    trace = next(t for t in page["trace"] if t["stage"] == "Ad variant resolve")
    assert "Interest targeting" in str(trace["signals"])
    assert "segment=maritime" in str(trace["signals"])
    assert "v07" in str(trace["signals"])


def test_age_gender_variants_hold_on_landing_page():
    age = _page_text(c.get("/planet?utm_source=x&utm_medium=paid&utm_campaign=x-age-early-career&utm_content=v11"))
    gender = _page_text(c.get("/planet?utm_source=x&utm_medium=paid&utm_campaign=x-gender-all&utm_content=v12"))
    assert "25–44" not in age                          # age range must not ship
    assert "All genders" not in gender
    page = PS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-age-early-career", "utm_content": "v11"}))
    trace = next(t for t in page["trace"] if t["stage"] == "Ad variant resolve")
    assert "hold_policy" in str(trace["signals"]) or "hold" in trace["why"].lower()


def test_defense_variant_carries_theater_guardrail_note():
    page = PS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-lookalike-defense",
                               "utm_content": "v02"}))
    assert "theater-of-interest" in (page["ad_variant"].get("hold_note") or "")
    assert page["location"]["mode"] == "theater"
    assert page["sections"]["hero"]["location_line"] == PS.THEATER_LINE


# --------------------------------------------------------------------------- #
# 7 · The unified /ads grid (W6-E: shared gauntlet-layout template; /ads-lp is a
#     302 into it — one grid per tenant carries ad copy AND the hero shift)
# --------------------------------------------------------------------------- #
V01_TRIGGER = "Every field in the corn belt, imaged today."


def test_ads_grid_shows_all_twelve_variants_with_hero_shift():
    for path in ("/planet/ads", "/planetapt/ads"):
        r = c.get(path)
        assert r.status_code == 200, path
        t = _page_text(r)
        for v in PS.AD_VARIANTS:
            assert f"utm_campaign={v['utm_campaign']}" in t, f"{path} missing {v['id']}"
            assert v["ad"]["trigger"] in t, f"{path} missing ad copy for {v['id']}"
        assert "Location targeting" in t and "Follower look-alikes targeting" in t
        assert "Promoted" in t
        # W6-E unified contract: the grid ALSO carries the generic→personalized
        # hero shift that used to live on the separate /ads-lp page.
        assert "Hero shift" in t
        assert PS.generic_hero_headline() in t
        for v in PS.AD_VARIANTS:
            assert PS.variant_hero_headline(v) in t, f"{path} missing personalized hero for {v['id']}"


def test_ads_lp_redirects_into_the_unified_grid():
    # /ads-lp is redundant now (one grid per tenant) — it 302s to /ads on both mounts.
    for path, target in (("/planet/ads-lp", "/planet/ads"),
                         ("/planetapt/ads-lp", "/planetapt/ads")):
        resp = c.get(path, follow_redirects=False)
        assert resp.status_code == 302, path
        assert resp.headers["location"] == target


def test_ads_grid_cards_click_through_to_landing_urls():
    ads = c.get("/planet/ads").text
    # every card clicks through to its personalized landing URL
    for v in PS.AD_VARIANTS:
        landing = PS.variant_landing_url(v, "/planet")
        assert landing in html.unescape(ads)


def test_ad_single_mockup_and_redirect():
    r = c.get("/planet/ad?v=v03")
    assert r.status_code == 200
    assert "Event targeting" in r.text
    assert "utm_content=v03" in r.text
    # no match → redirect to the /ads grid (not ad-lp)
    resp = c.get("/planet/ad", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "/planet/ads"


def test_ads_route_with_v_param_renders_single_mockup():
    r = c.get("/planet/ads?v=v05")
    assert r.status_code == 200
    assert "Keyword targeting" in r.text
    assert "utm_content=v05" in r.text
    assert "All 12 ads" in r.text                      # single-mockup view, not the grid
    assert "12 Targeting Types" not in r.text


def test_crop_belt_vs_maritime_feel_like_different_products():
    ag = _page_text(c.get("/planet?utm_source=x&utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01"))
    ma = _page_text(c.get("/planet?utm_source=x&utm_medium=paid&utm_campaign=x-interest-maritime&utm_content=v07"))
    assert "Every Field in Your Region," in ag
    assert "Dark Vessels," in ma
    assert ag != ma


def test_portal_mount_ads_links_stay_under_prefix():
    t = c.get("/planetapt/ads").text
    assert 'href="/planetapt?' in t
    assert 'href="/planet?' not in t


# --------------------------------------------------------------------------- #
# 8 · Portal mount
# --------------------------------------------------------------------------- #
def test_portal_mount_serves_and_links_stay_under_prefix():
    """johnnycchung.com/planetapt — all hrefs + forms stay on the mount prefix."""
    t = c.get("/planetapt").text
    assert "Planet" in t and 'href="/planetapt' in t
    assert 'action="/planetapt/login"' in t
    assert 'href="/planet/dev' not in t
    d = c.get("/planetapt/dev?as=anon").text
    assert "Entry point" in d and 'href="/planetapt' in d
    # The console is now a self-contained apt shell (inline CSS) — no external stylesheet
    # to leak under any prefix (this removes the old portal-static-404 workaround). Its own
    # body links + image assets still stay under /planetapt.
    assert 'ws-dd' in d  # apt shell rendered
    assert 'href="/static/atlas.css"' not in d and 'href="/planetapt/static/atlas.css"' not in d
    assert '"/static/generated' not in d  # no root-prefix asset leak
    legacy_dev = c.get("/planet/dev?as=anon").text
    assert "Entry point" in legacy_dev  # legacy mount still serves the console
    c.post("/planetapt/login", data={"email": PS.sample_login_email(), "next": "/planetapt"})
    assert "Welcome back, Amara" in c.get("/planetapt").text
    c.get("/planetapt/logout")


def test_portal_mount_hero_api_and_asset_urls_use_prefix():
    """Portal fetch + cached hero URLs must stay under /planetapt."""
    qs = "?utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01"
    t = c.get(f"/planetapt{qs}").text
    assert 'data-hero-api="/planetapt/api/hero-image"' in t
    r = c.get(f"/planetapt/api/hero-image{qs}")
    assert r.status_code == 200
    data = r.json()
    if data.get("url"):
        assert data["url"].startswith("/planetapt/static/")
        assert not data["url"].startswith("/static/")


# --------------------------------------------------------------------------- #
# 9 · Objection-driven copy
# --------------------------------------------------------------------------- #
def test_objection_catalog_has_sixteen_entries():
    assert len(PS.OBJECTION_CATALOG) == 16
    ids = {o["id"] for o in PS.OBJECTION_CATALOG}
    assert "tasked_competitor" in ids and "cloud_cover" in ids and "academic_budget" in ids


def test_crop_belt_ad_surfaces_cloud_cover_objection():
    page = PS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-location-crop-belts", "utm_content": "v01",
    }))
    top = page["objections"]["prioritized"][0]
    assert top["objection_id"] == "cloud_cover"
    assert "Cloud cover" in top["text"]


def test_defense_ad_surfaces_sovereignty_or_tasked_competitor():
    page = PS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-lookalike-defense", "utm_content": "v02",
    }))
    top = page["objections"]["prioritized"][0]
    assert top["objection_id"] in ("sovereignty", "tasked_competitor")


def test_researcher_ad_surfaces_academic_budget_objection():
    page = PS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-movies-earth-docs", "utm_content": "v09",
    }))
    top = page["objections"]["prioritized"][0]
    assert top["objection_id"] == "academic_budget"
    assert "grant budget" in top["text"]


def test_abandoned_trial_surfaces_proof_before_buy_objection():
    page = PS.build_page(_Req({"utm_medium": "direct"}), email="kofi.tanaka@pacificrelief.org")
    ids = [o["objection_id"] for o in page["objections"]["prioritized"]]
    assert "proof_before_buy" in ids


def test_objection_hold_reframes_never_ship():
    """Blocked say-level objection reframes (budget band, abandoned step) never ship."""
    for p in CO.COHORT:
        c.post("/planet/login", data={"email": p["email"], "next": "/planet"})
        t = c.get("/planet?utm_source=x&utm_medium=paid&utm_campaign=x-gender-all&utm_content=v12").text
        assert "modeled your budget band" not in t
        assert "pre-picked a subscription tier" not in t
        assert "You abandoned the trial signup" not in t
        c.get("/planet/logout")
    dev = c.get("/planet/dev?as=known").text
    assert "Blocked say reframe" in dev or "Blocked — the say variant" in dev


def test_objection_trace_stage():
    page = PS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-location-crop-belts", "utm_content": "v01",
    }))
    trace = next(t for t in page["trace"] if t["stage"] == "Objection prioritize")
    assert "cloud_cover" in str(trace["signals"]) or trace["output"]
    assert page["objections"]["assignments"]


# --------------------------------------------------------------------------- #
# 10 · Marketing /planet/dev/business view
# --------------------------------------------------------------------------- #
CROP_QS = "?utm_source=x&utm_medium=paid&utm_campaign=x-location-crop-belts&utm_content=v01"


def test_dev_business_routes_return_200():
    for path in ("/planet/dev/business", "/planetapt/dev/business"):
        r = c.get(f"{path}?as=anon")
        assert r.status_code == 200, path


def test_dev_business_shows_decisioning_sections_including_location():
    t = _page_text(c.get(f"/planetapt/dev/business{CROP_QS}&as=anon"))
    for want in ("Arrival & attribution", "Location signal", "Audience read", "Objection stack",
                 "Copy decisions", "Visual decision", "Steering vs saying",
                 "Technical view →"):
        assert want in t, f"missing decisioning section: {want}"
    assert "Signal ledger" not in t


def test_dev_business_same_state_as_dev_for_same_params():
    qs = CROP_QS + "&as=anon"
    dev = c.get(f"/planet/dev{qs}").text
    biz = c.get(f"/planet/dev/business{qs}").text
    assert "Every Field in Your Region," in dev and "Every Field in Your Region," in biz
    assert "Location targeting" in biz
    assert "x-location-crop-belts" in dev and "x-location-crop-belts" in biz


def test_dev_business_build_view_carries_location_decision():
    from pipeline.personalization import planet_dev_business as PDB

    page = PS.build_page(_Req({
        "utm_source": "x", "utm_medium": "paid",
        "utm_campaign": "x-location-crop-belts", "utm_content": "v01",
    }))
    biz = PDB.build_business_dev_view(page)
    arrival_labels = {r["label"] for r in biz["arrival"]["rows"]}
    assert "utm_campaign" in arrival_labels
    assert "Market segment" in arrival_labels
    assert biz["location"]["decision"].startswith("Decision:")
    loc_labels = {r["label"] for r in biz["location"]["rows"]}
    assert "Region (geo-IP)" in loc_labels and "Register" in loc_labels
    assert biz["audience_read"]["segment"]
    assert biz["total_slots"] >= 8
    assert len(biz["copy_decisions"]) == biz["total_slots"]
    assert biz["visual"]["paired_cta"]


def test_dev_and_business_cross_link():
    t = c.get("/planet/dev?as=anon").text
    assert "Marketing view →" in t and 'href="/planet/dev/business' in t
    b = _page_text(c.get("/planetapt/dev/business?as=anon"))
    assert "Technical view →" in b and 'href="/planetapt/dev' in b


def test_portal_dev_business_links_stay_under_prefix():
    t = c.get("/planetapt/dev/business?as=anon").text
    assert 'href="/planetapt/dev/business' in t
    assert 'href="/planet/dev/business' not in t


# --------------------------------------------------------------------------- #
# 11 · Image decisions guide page
# --------------------------------------------------------------------------- #
INTENT_NAMES = (
    "regional_truth", "change_proof", "mission_authority", "archive_advantage",
    "aspiration_research", "retarget_warm", "message_match",
)


def test_image_decisions_routes_return_200():
    for path in (
        "/planet/dev/image-decisions",                # canonical (lives under /planet/dev)
        "/planetapt/dev/image-decisions",             # canonical, portal mount
        "/planet/image-decisions",                    # pre-/dev aliases
        "/planetapt/image-decisions",
    ):
        r = c.get(path)
        assert r.status_code == 200, path


def test_image_decisions_contains_all_intents_and_why_sections():
    t = _page_text(c.get("/planetapt/image-decisions"))
    for name in INTENT_NAMES:
        assert name in t, f"missing intent: {name}"
    assert "Why it works" in t
    assert "Why each intent" in t
    assert "Two-tier token" in t
    assert "Provenance" in t
    assert "drives_action" in t
    assert "Part 1" in t and "Part 5" in t
    assert "planet:base:" in t                        # tenant cache keys documented


def test_image_decisions_nav_links_from_dev():
    t = c.get("/planet/dev?as=anon").text
    assert "Image decisions →" in t
    assert 'href="/planet/dev/image-decisions"' in t
    p = c.get("/planetapt/dev?as=anon").text
    assert 'href="/planetapt/dev/image-decisions"' in p


def test_image_decisions_renders_decided_rejected_section():
    r = c.get("/planetapt/dev/image-decisions")
    assert r.status_code == 200
    t = _page_text(r)
    assert "Decided vs rejected" in t
    assert 'id="part-decided"' in r.text
    assert "Candidate galleries" in t
    assert "brain_score" in t or "demo scenarios have full candidate galleries" in t
