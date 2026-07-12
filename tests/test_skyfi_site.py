"""SkyFi replica (/skyfi + /skyfi/dev) — entry classification, tier routing determinism,
the LOCATION × INDUSTRY signal (basin/region scale — the SkyFi differentiator), the
declared-AOI say/hold flip (S09), the strict defense/gov AOR hold (S07), the
no-hold-fact invariant, the login unlock, the portal mount prefix, the descriptive
registry seed, the tenant gate rules, and config-only shell/dropdown integration.

All offline: the test client's host is not a public IP, so scene.reverse_ip() returns {}
and the IP layer routes tier 0 deterministically. Private-IP overrides exercise the ?ip=
path without any network call. Deterministic, $0.
"""
from __future__ import annotations

import html

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import sections as SR
from pipeline.personalization import skyfi_cohort as CO
from pipeline.personalization import skyfi_site as SS

c = TestClient(app)


def _page_text(resp) -> str:
    return html.unescape(resp.text)


AD = "/skyfi?utm_source=x&utm_medium=paid&utm_campaign=x-monitor-your-site&utm_content=sv01"
EMAIL = "/skyfi?utm_source=hubspot&utm_medium=email&utm_campaign=tasking-program"
SEARCH = "/skyfi?ref=google"


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
    assert SS.classify_entry(_Req({"utm_medium": "paid"}))["channel"] == "ad"
    assert SS.classify_entry(_Req({"utm_medium": "CPC"}))["channel"] == "ad"
    assert SS.classify_entry(_Req({"utm_medium": "email"}))["channel"] == "email"
    assert SS.classify_entry(_Req({"ref": "google"}))["channel"] == "search"
    assert SS.classify_entry(_Req(headers={"referer": "https://www.bing.com/search?q=x"}))["channel"] == "search"
    assert SS.classify_entry(_Req())["channel"] == "direct"


def test_email_magic_token_identifies_the_recipient():
    tok = CO.magic_token(CO.BY_ID["ingrid"])
    e = SS.classify_entry(_Req({"utm_medium": "email", "e": tok}))
    assert e["channel"] == "email" and e["token_person_id"] == "ingrid"
    assert SS.classify_entry(_Req({"utm_medium": "email", "e": "sk_bogus"}))["token_person_id"] is None


def test_ad_campaign_message_match_changes_the_hero():
    generic = c.get("/skyfi").text
    ad = c.get(AD).text
    assert "Monitor Your Site," in ad                 # sv01 message-match
    assert "Monitor Your Site," not in generic
    selfserve = c.get("/skyfi?utm_medium=paid&utm_campaign=order-aoi-2026").text
    assert "Your AOI," in selfserve                   # campaign keyword intent fallback


# --------------------------------------------------------------------------- #
# 2 · Tier routing determinism + LOCATION × INDUSTRY signal
# --------------------------------------------------------------------------- #
def test_tier_routing_is_deterministic():
    a = c.get(SEARCH).text
    b = c.get(SEARCH).text
    assert a == b
    d1 = c.get("/skyfi/dev?ref=google&as=anon").text
    d2 = c.get("/skyfi/dev?ref=google&as=anon").text
    assert d1 == d2


def test_private_ip_override_routes_tier_0_offline():
    t = c.get("/skyfi/dev?ip=10.0.0.1&as=anon").text
    assert "tier 0" in t and "private / unreachable" in t


def test_location_signal_basin_templates_per_sector():
    """Region × sector → the basin/region-scale line; the exact site is held (arm Ex)."""
    det = {"region": "Arizona", "city": "Phoenix"}
    mine = SS.location_signal(det, 2, SS.AD_BY_VARIANT_ID["sv01"])
    assert mine["mode"] == "region"
    assert mine["line"] == "Fresh imagery over Arizona's mining basins — searchable now, taskable today."
    assert mine["policy"] == "allude"
    assert "Phoenix" in mine["blocked_say"]           # exact-site precision held, never shipped
    assert "exact site" in mine["blocked_say"]
    ins = SS.location_signal({"region": "Florida", "city": None}, 1, SS.AD_BY_VARIANT_ID["sv04"])
    assert "before-picture of Florida" in ins["line"]
    default = SS.location_signal({"region": "Texas", "city": None}, 1, None)
    assert "archive already covers Texas" in default["line"]


def test_location_signal_defense_uses_aor_never_visitor_location():
    """S07: defense/gov is strict hold — AOR framing, never region/city/asset."""
    det = {"region": "Virginia", "city": "Arlington"}
    loc = SS.location_signal(det, 2, SS.AD_BY_VARIANT_ID["sv06"])
    assert loc["mode"] == "aor"
    assert "Virginia" not in loc["line"] and "Arlington" not in loc["line"]
    assert loc["line"] == SS.AOR_LINE
    # a defense cohort contact gets the same register even with no ad
    ident = {"kind": "cohort", "view": CO.view(CO.BY_ID["ingrid"])}
    loc2 = SS.location_signal(det, 2, None, ident)
    assert loc2["mode"] == "aor" and loc2["line"] == SS.AOR_LINE


def test_location_signal_holds_at_tier_0():
    loc = SS.location_signal({}, 0, None)
    assert loc["mode"] == "none" and loc["line"] == ""
    assert loc["policy"] == "hold"


# --------------------------------------------------------------------------- #
# 3 · The declared-AOI flip (S09) — exact scale is say ONLY because they told us
# --------------------------------------------------------------------------- #
def test_declared_aoi_flips_hold_to_say_with_you_told_us_receipt():
    ident = {"kind": "cohort", "view": CO.view(CO.BY_ID["sana"])}
    loc = SS.location_signal({"region": "Arizona", "city": "Tucson"}, 1,
                             None, ident)
    assert loc["mode"] == "declared_aoi"
    assert loc["policy"] == "say"
    assert "West Basin quarry" in loc["line"]
    assert loc["blocked_say"] is None                 # nothing blocked — it's allowed
    r = loc["receipt"]
    assert r["basis"] == "declared_first_party"
    assert "You told us" in r["say_reason"]
    assert r["aoi_label"] == "West Basin quarry — Pima County, AZ"


def test_declared_aoi_person_without_login_gets_no_exact_claim():
    """The SAME visitor anonymous (no declaration in play) → the region ceiling holds."""
    loc = SS.location_signal({"region": "Arizona", "city": "Tucson"}, 1, None, None)
    assert loc["mode"] == "region"
    assert "West Basin quarry" not in loc["line"]
    assert loc["blocked_say"] and "exact site" in loc["blocked_say"]


def test_declared_aoi_ships_on_page_with_receipt_only_for_the_declarer():
    """Sana logged in → her declared AOI is recited (say) + the 'you told us' close.
    Every other cohort login → her AOI never appears anywhere."""
    c.post("/skyfi/login", data={"email": "sana.okafor@westbasinaggregates.com", "next": "/skyfi"})
    t = _page_text(c.get("/skyfi"))
    c.get("/skyfi/logout")
    assert "West Basin quarry" in t                   # say — SHE declared it
    assert "Your AOI is on file" in t                 # the S09 close
    assert "you told us where" in t
    for p in CO.COHORT:
        if p["id"] == "sana":
            continue
        c.post("/skyfi/login", data={"email": p["email"], "next": "/skyfi"})
        other = _page_text(c.get("/skyfi"))
        c.get("/skyfi/logout")
        assert "West Basin quarry" not in other, f"declared AOI leaked to {p['id']}"


def test_exact_site_recite_never_ships_for_any_cohort_or_channel():
    """The region-scale invariant: the arm-Ex recite ('your exact site …') never reaches
    a shipped page for ANY cohort user on ANY channel — declared AOI is the only exact
    reference, and only for its declarer."""
    for p in CO.COHORT:
        c.post("/skyfi/login", data={"email": p["email"], "next": "/skyfi"})
        for url in ("/skyfi", AD, EMAIL, SEARCH):
            t = _page_text(c.get(url))
            assert "your exact site" not in t.lower(), f"arm Ex shipped for {p['id']} at {url}"
            assert "no need to tell us where" not in t.lower()
        c.get("/skyfi/logout")


# --------------------------------------------------------------------------- #
# 4 · The no-hold-fact invariant
# --------------------------------------------------------------------------- #
def test_hold_facts_never_reach_the_shipped_page():
    """Modeled income (Clay, hold) and blocked say-variants must never ship on /skyfi —
    for any cohort user, on any entry channel."""
    for p in CO.COHORT:
        c.post("/skyfi/login", data={"email": p["email"], "next": "/skyfi"})
        for url in ("/skyfi", AD, EMAIL, SEARCH):
            t = c.get(url).text
            income = p["clay"].get("income_band")
            if income:
                assert income not in t, f"hold fact (income) shipped for {p['id']} at {url}"
            assert "we noticed" not in t and "de-anonymized" not in t.replace("/skyfi/dev", "")
        c.get("/skyfi/logout")


def test_blocked_say_variants_appear_only_on_dev():
    """The recite variants exist for contrast on /skyfi/dev, and only there, marked blocked."""
    c.post("/skyfi/login", data={"email": "mateo.silva@rioverdeagro.com", "next": "/skyfi"})
    dev = c.get("/skyfi/dev").text
    site = c.get("/skyfi").text
    c.get("/skyfi/logout")
    assert "Blocked — the say variant the policy holds" in dev
    # mateo abandoned the tasking order — /skyfi/dev may show the blocked recite; the site not
    assert "You bailed at the" in dev
    assert "You bailed at the" not in site
    # the shipped close alludes instead
    assert "Finish your order" in site


def test_defense_contact_page_never_references_an_asset():
    """S07: ingrid (defense/gov) — strict hold on every channel; the AOR line ships."""
    c.post("/skyfi/login", data={"email": "ingrid.solheim@nordicaerodefence.com", "next": "/skyfi"})
    for url in ("/skyfi", EMAIL):
        t = _page_text(c.get(url))
        assert SS.AOR_LINE in t
        assert "your installation" not in t.lower()
    c.get("/skyfi/logout")


# --------------------------------------------------------------------------- #
# 5 · Login unlock
# --------------------------------------------------------------------------- #
def test_login_unlocks_say_level_copy_and_logout_clears_it():
    anon = c.get("/skyfi").text
    assert "Welcome back, Noor" not in anon
    r = c.post("/skyfi/login", data={"email": "noor.haddad@terrafirmepc.com", "next": "/skyfi"},
               follow_redirects=False)
    assert r.status_code == 303
    known = c.get("/skyfi").text
    assert "Welcome back, Noor" in known              # say — she logged in
    assert "document build progress across 14 active sites" in known   # declared goal — say
    assert "Terrafirm EPC" not in known               # Vector company — allude, never recited
    c.get("/skyfi/logout")
    after = c.get("/skyfi").text
    assert "Welcome back, Noor" not in after


def test_magic_token_jumps_to_known_prelogin():
    tok = CO.magic_token(CO.BY_ID["ingrid"])
    t = c.get(f"{EMAIL}&e={tok}").text
    assert "Welcome back, Ingrid" in t                # identified with no login
    assert "Nordic Aero Defence" not in t             # her employer stays allude


def test_unknown_work_email_still_escalates():
    c.post("/skyfi/login", data={"email": "sam@acme-widgets.com", "next": "/skyfi"})
    t = c.get("/skyfi").text
    c.get("/skyfi/logout")
    assert "For your team at Acme Widgets" in t       # domain → company, first-party say


# --------------------------------------------------------------------------- #
# 6 · Trace + process-map completeness
# --------------------------------------------------------------------------- #
def test_dev_trace_has_every_stage_with_full_entries():
    page = SS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-monitor-your-site",
                               "utm_content": "sv01"}),
                         email="noor.haddad@terrafirmepc.com")
    stages = [t["stage"] for t in page["trace"]]
    for want in ("Entry classify", "Ad variant resolve", "IP resolve + classify", "Tier route",
                 "Location signal", "Identity", "Segments → archetype", "Audience route",
                 "Surface policy", "Compose", "Hero image resolve"):
        assert want in stages, f"missing trace stage: {want}"
    for t in page["trace"]:
        for key in ("stage", "signals", "rule", "disposition", "output", "why"):
            assert t.get(key) not in (None, "", []), f"trace entry incomplete: {t['stage']}.{key}"


def test_process_map_covers_every_stage_with_data_and_branches():
    page = SS.build_page(_Req({"utm_medium": "paid", "utm_campaign": "x-monitor-your-site",
                               "utm_content": "sv01"}),
                         email="noor.haddad@terrafirmepc.com")
    pm = SS.process_map(page)
    assert len(pm["inputs"]) == 4                     # query · referer · IP · cookie
    ids = [s["id"] for s in pm["stages"]]
    assert ids == ["entry", "advariant", "ip", "tier", "location", "identity", "archetype",
                   "audience", "policy", "compose", "heroimg"]
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


def test_process_map_location_stage_shows_full_decision_space():
    """All sector templates + the AOR + declared-AOI branches + the arm-Ex guardrail row."""
    page = SS.build_page(_Req())
    pm = SS.process_map(page)
    loc = next(s for s in pm["stages"] if s["id"] == "location")
    tmpl_rows = [r for r in loc["detail"] if r["k"].startswith("template ·")]
    assert len(tmpl_rows) >= len(SS.SECTOR_LINES) + 2
    labels = [b["label"] for b in loc["branches"]]
    assert "declared AOI (say)" in labels             # the S09 branch is always visible
    assert "AOR register (defense hold)" in labels
    assert next(b["label"] for b in loc["branches"] if b["taken"]) == "no claim (tier 0)"
    assert any(r["pol"] == "hold" for r in loc["detail"])   # the anti-surveillance guardrail row


def test_process_map_declared_aoi_branch_taken_for_declarer():
    page = SS.build_page(_Req(), email="sana.okafor@westbasinaggregates.com")
    pm = SS.process_map(page)
    loc = next(s for s in pm["stages"] if s["id"] == "location")
    assert next(b["label"] for b in loc["branches"] if b["taken"]) == "declared AOI (say)"
    assert any("you told us" in str(r["v"]).lower() or "You told us" in str(r["v"])
               for r in loc["detail"] if r.get("pol") == "say")


def test_dev_page_shows_all_panels_and_toggle():
    t = c.get("/skyfi/dev?as=anon").text
    for panel in ("Entry point", "Tier routing", "Location signal", "Signal ledger", "CRM record",
                  "Per-slot copy decision", "Hero background", "Trace — every stage",
                  "Process map"):
        assert panel in t, f"/skyfi/dev missing panel: {panel}"
    assert "Anonymous — no login" in t
    k = c.get("/skyfi/dev?as=known").text
    assert "Archetype" in k and SS.sample_login_email() in k
    assert "as=anon" in t and "as=known" in t


def test_dev_rebuilds_the_same_state_as_the_entry_url():
    d = c.get("/skyfi/dev?utm_source=x&utm_medium=paid&utm_campaign=x-monitor-your-site"
              "&utm_content=sv01&as=anon").text
    assert "Paid ad (UTM)" in d and "x-monitor-your-site" in d
    assert "Monitor Your Site," in d                  # the shipped hero appears in the copy diff


def test_dev_business_serves_the_marketer_designer():
    # T-07b: the placeholder 302 → /skyfi/dev is gone — the per-section designer
    # (S5 sd-* DOM contract) serves directly, same visitor state as /skyfi/dev.
    r = c.get("/skyfi/dev/business?as=anon", follow_redirects=False)
    assert r.status_code == 200
    t = r.text
    assert 'data-testid="sd-section-hero"' in t
    assert 'data-sections-config="rules/skyfi_sections.yaml"' in t
    assert '/skyfi/dev' in t                       # technical-view link keeps the pairing


# --------------------------------------------------------------------------- #
# 7 · Portal mount
# --------------------------------------------------------------------------- #
def test_portal_mount_serves_and_links_stay_under_prefix():
    """johnnycchung.com/skyfiapt — all hrefs + forms stay on the mount prefix."""
    t = c.get("/skyfiapt").text
    assert "SkyFi" in t and 'href="/skyfiapt' in t
    assert 'action="/skyfiapt/login"' in t
    assert 'href="/skyfi/dev' not in t
    d = c.get("/skyfiapt/dev?as=anon").text
    assert "Location signal" in d and 'href="/skyfiapt' in d
    assert 'ws-dd' in d                               # apt shell rendered
    assert '"/static/generated' not in d              # no root-prefix asset leak
    legacy_dev = c.get("/skyfi/dev?as=anon").text
    assert "Location signal" in legacy_dev            # legacy mount still serves the console
    c.post("/skyfiapt/login", data={"email": SS.sample_login_email(), "next": "/skyfiapt"})
    assert "Welcome back, Noor" in c.get("/skyfiapt").text
    c.get("/skyfiapt/logout")


def test_portal_mount_hero_api_and_asset_urls_use_prefix():
    """Portal fetch + cached hero URLs must stay under /skyfiapt."""
    qs = "?utm_medium=paid&utm_campaign=x-monitor-your-site&utm_content=sv01"
    t = c.get(f"/skyfiapt{qs}").text
    assert 'data-hero-api="/skyfiapt/api/hero-image"' in t
    r = c.get(f"/skyfiapt/api/hero-image{qs}")
    assert r.status_code == 200
    data = r.json()
    if data.get("url"):
        assert data["url"].startswith("/skyfiapt/static/")
        assert not data["url"].startswith("/static/")


# --------------------------------------------------------------------------- #
# 8 · Registry seed (descriptive, Art IV) + prebuild-by-design
# --------------------------------------------------------------------------- #
def test_registry_seed_matches_build_page_slots_exactly():
    """Every copy_diff slot id is in rules/skyfi_sections.yaml, and the deterministic
    registry invents none. Generative slots (T-08: S04 prebuilt pool + S10
    cache-by-key) are pool-served via decision_pool.cleared_pool, never copy_diff
    slot-fill — pinned explicitly."""
    reqs = [_Req(), _Req({"utm_medium": "paid", "utm_campaign": "x-monitor-your-site",
                          "utm_content": "sv01"})]
    observed: set[str] = set()
    for r in reqs:
        observed |= {d["slot"] for d in SS.build_page(r)["copy_diff"]}
    det = {t["slot_id"] for t in SR.list_text_targets("skyfi")
           if t["mode"] == "deterministic"}
    gen = {t["slot_id"] for t in SR.list_text_targets("skyfi")
           if t["mode"] == "generative"}
    assert observed - (det | gen) == set(), \
        f"build_page slots missing from registry: {observed - (det | gen)}"
    assert det - observed == set(), \
        f"registry invents deterministic slots build_page never ships: {det - observed}"
    assert gen == {"hero_sub_gen", "compare_gen"}
    assert gen & observed == set(), "generative slots are pool-served, never copy_diff"


def test_registry_image_targets_realtime_matching_empty_prebuild():
    """S02 is the realtime beat: the prebuild manifest is empty by design and every
    image target is workflow=realtime."""
    from pipeline.personalization.prebuild import load_prebuild_manifest
    from pathlib import Path

    manifest = load_prebuild_manifest(
        Path(__file__).resolve().parents[1] / "rules" / "skyfi_prebuild.yaml")
    assert manifest["tenant"] == "skyfi"
    assert manifest["states"] == []
    assert not manifest.get("surfaces")
    assert {t["workflow"] for t in SR.list_image_targets("skyfi")} == {"realtime"}


def test_image_config_loads_with_anti_surveillance_guardrails():
    from pipeline.personalization import image_intents as II

    cfg = II.load_image_config("skyfi")
    assert cfg["tenant"] == "skyfi"
    avoid = " ".join((cfg.get("prompt_defaults") or {}).get("must_avoid") or [])
    avoid += " " + " ".join((cfg.get("brand") or {}).get("must_avoid_additions") or [])
    assert "basin/region" in avoid
    sel = II.select_image_intent({"channel": "direct", "ad_variant_id": None,
                                  "audience_route": "neutral", "industry": "general",
                                  "top_objections": []}, cfg)
    assert sel["primary"]["intent_id"] == "basin_truth"
    sel_def = II.select_image_intent({"channel": "ad", "ad_variant_id": "x-defense",
                                      "audience_route": "enterprise", "industry": "general",
                                      "top_objections": []}, cfg)
    assert sel_def["primary"]["intent_id"] == "aor_authority"


# --------------------------------------------------------------------------- #
# 9 · Tenant gate rules (rules/skyfi_tenant.yaml — copy-gate side of the ceiling)
# --------------------------------------------------------------------------- #
def test_tenant_gate_blocks_superlative_comparative_and_exact_aoi():
    from pipeline.common.config import RULES_DIR
    from pipeline.gate.rules import RulesEngine

    eng = RulesEngine.load(RULES_DIR / "skyfi_tenant.yaml")
    assert eng.rules_version().startswith("r_")
    bad = [
        "The clearest imagery on the market, guaranteed",             # superlative + guarantee
        "Better than Maxar on every order",                            # competitor comparative
        "We can see your exact site — no need to tell us where",      # arm Ex recite
        "Tomorrow's pass covers your installation",                    # defense asset reference
    ]
    for line in bad:
        out = eng.apply(line, None)
        assert out.verdict is not None and out.verdict.value == "red", f"gate passed: {line!r}"
    ok = eng.apply("Search the archive over your region and task a new capture.", None)
    assert ok.verdict is None


# --------------------------------------------------------------------------- #
# 10 · Shell + dropdown flow-through by config (no special-casing)
# --------------------------------------------------------------------------- #
def test_console_shell_ctx_picks_up_skyfi_from_config():
    from pipeline.personalization import demo_nav as NAV

    ctx = NAV.console_shell_ctx("skyfi", "consoles")
    assert ctx["active"]["name"] == "SkyFi"
    assert ctx["active"]["logo_bg"] == "#060b16" and ctx["active"]["logo_ch"] == "S"
    ids = [t["id"] for t in ctx["tenants"]]
    assert ids == ["gauntlet", "planet", "skyfi"]
    assert next(t for t in ctx["tenants"] if t["id"] == "skyfi")["active"]
    assert ctx["nav"]["replica"] == "/skyfiapt"


def test_demo_hub_and_dev_hub_surface_skyfi():
    t = c.get("/apt/demo?site=skyfi").text
    assert "SkyFi" in t and 'href="/skyfiapt' in t
    hub = c.get("/apt/dev?site=skyfi").text
    assert "/skyfiapt/dev" in hub          # sidebar Page sections → /skyfiapt/dev/business
    assert "Preview as visitor" in hub     # W8-A: /apt/dev is the Preview step now
    # the sidebar dropdown lists skyfi on the OTHER tenants' pages too (config-driven)
    g = c.get("/apt/dev?site=gauntlet").text
    assert "SkyFi" in g


def test_channel_galleries_serve_for_skyfi():
    for path in ("/skyfi/direct", "/skyfi/email", "/skyfiapt/direct", "/skyfiapt/email"):
        r = c.get(path)
        assert r.status_code == 200, path
        assert "SkyFi" in r.text
