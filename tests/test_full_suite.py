"""Full acceptance suite — the loop's gate (PRD §7, SPEC §E, plan.md exit criteria).

Deterministic, offline. Proves the WHOLE site is functioning and aligned to the spine:
  • every route renders (200),
  • zero dead internal links / buttons (functional link audit),
  • the ⌘K palette resolves to real routes,
  • create-record persists; filter / sort / view do real work,
  • the composer Gate blocks held facts,
  • the variant→source receipt drill-down (placement + injection + receipt + blocked-never-selected),
  • provenance completeness, persona journeys, and one-design consistency across all surfaces.
"""
from __future__ import annotations

import pathlib
import re

from starlette.routing import Mount, Route
from starlette.testclient import TestClient

from app.composer import check as composer_check
from app.main import app
from pipeline.agent import intents as A
from pipeline.common.store import ActionPool
from pipeline.personalization import cloner
from pipeline.personalization import demo_scenarios as DS

c = TestClient(app)
TPL = pathlib.Path(__file__).resolve().parents[1] / "app" / "templates"

# Surfaces on the Quiet-Workspace shell.
SHELL_PAGES = ["workspace", "records", "records_new", "composer", "optimizer", "agent",
               "assurance", "sources", "demo", "demo_monitor"]
SHELL_ROUTES = ["/workspace", "/records", "/records/new", "/composer", "/optimizer", "/agent",
                "/assurance", "/sources", "/demo", "/demo/monitor"]
# All legacy/lab routes (now light) — param routes filled with valid demo values.
TOKEN = __import__("pipeline.personalization.cohort", fromlist=["x"]).magic_token(
    __import__("pipeline.personalization.cohort", fromlist=["x"]).COHORT[1])
LAB_ROUTES = ["/", "/lead", "/personalize", "/inspector", "/observatory", "/funnel",
              "/admin/landings", "/admin/landing/maya", "/google", "/enrichment-catalog",
              "/lp", "/lp?email=maya.chen@gauntletai.com"]


# ---- registered-route matcher (for the dead-link audit) -----------------------
def _route_patterns():
    pats = []
    for r in app.routes:
        if isinstance(r, Route):
            pats.append(re.compile("^" + re.sub(r"\{[^}]+\}", r"[^/]+", r.path) + "$"))
        elif isinstance(r, Mount):
            pats.append(re.compile("^" + re.escape(r.path) + "(/.*)?$"))
    return pats


_PATS = _route_patterns()


def _is_registered(path: str) -> bool:
    return any(p.match(path) for p in _PATS)


# ============================ render =============================================
def test_every_route_renders():
    for route in SHELL_ROUTES + LAB_ROUTES:
        assert c.get(route).status_code == 200, f"{route} did not render 200"


# ============================ functional link/button audit ======================
def test_no_dead_internal_links_on_any_surface():
    """Every internal href/action on every surface points at a registered route."""
    bad = {}
    for route in SHELL_ROUTES + LAB_ROUTES:
        html = c.get(route).text
        links = set(re.findall(r'(?:href|action)="(/[^"#?]*)', html))
        for link in links:
            if link.startswith("//"):
                continue
            if not _is_registered(link):
                bad.setdefault(route, set()).add(link)
    assert not bad, f"dead internal links: { {k: sorted(v) for k, v in bad.items()} }"


def test_no_styled_button_without_target_in_shell_templates():
    """The original bug: an <a class="q-btn ..."> with no href is a dead button. Forbid it."""
    offenders = {}
    for name in SHELL_PAGES + ["shell"]:
        body = (TPL / f"{name}.html").read_text()
        for m in re.finditer(r'<a\b[^>]*class="[^"]*\bq-btn\b[^"]*"[^>]*>', body):
            tag = m.group(0)
            if "href=" not in tag:
                offenders.setdefault(name, []).append(tag[:70])
    assert not offenders, f"dead q-btn anchors (no href): {offenders}"


def test_cmdk_palette_items_resolve():
    html = c.get("/workspace").text
    assert 'id="cmdk"' in html and 'id="cmdk-input"' in html and 'id="cmdk-btn"' in html
    items = re.findall(r'class="qi[^"]*"[^>]*href="(/[^"#?]*)"', html)
    assert len(items) >= 10
    for href in items:
        assert _is_registered(href), f"palette item -> dead route {href}"


# ============================ create / filter / sort ============================
def test_create_record_persists_and_appears():
    before = c.get("/records?view=all").text.count('class="q-rec"')
    r = c.post("/records/new", data={"name": "Zoe Quill", "email": "zoe@quill.io",
               "company": "Quill", "title": "Founder", "industry": "SaaS",
               "lifecycle": "sql", "lead_score": "81", "source": "manual"})
    assert r.status_code == 200  # followed the 303 redirect to /records
    after = c.get("/records?view=all").text
    assert "Zoe Quill" in after
    assert after.count('class="q-rec"') == before + 1


def test_create_then_undo_removes_record():
    """Agency/forgiveness (WWDC26): a just-created record can be undone."""
    r = c.post("/records/new", data={"name": "Temp Undo", "email": "tu@x.io",
               "lifecycle": "lead", "lead_score": "5"})
    assert "Temp Undo" in c.get("/records?view=all").text
    assert 'action="/records/undo"' in r.text and "Undo" in r.text  # the create banner offers undo
    rid = re.search(r'name="rid" value="([^"]+)"', r.text).group(1)
    c.post("/records/undo", data={"rid": rid})
    assert "Temp Undo" not in c.get("/records?view=all").text


def test_demo_live_renders_inspector_overrides_and_real_imagery():
    """The by-IP landing: IP + manual overrides, allude/say toggle, the captured-data
    inspector, and real licensed imagery with attribution."""
    t = c.get("/demo/live").text
    assert 'id="ip-in"' in t and 'id="sel-loc"' in t and 'id="sel-ind"' in t   # IP + manual overrides
    assert 'id="seg-policy"' in t                                              # allude/say toggle
    assert 'class="lv-hero"' in t and "Everything captured" in t and 'id="cap-body"' in t
    assert "license" in t.lower() and ("staticflickr" in t or "wikimedia" in t)  # real CC photo


def test_scene_engine_deterministic_and_sourced():
    from pipeline.personalization import scene as SC
    a = SC.build_scene("Arizona", "mining", detected=True, company="Acme Mining")
    assert a == SC.build_scene("Arizona", "mining", detected=True, company="Acme Mining")  # deterministic
    assert "Arizona" in (a["headline"] + a["sub"] + a["eyebrow"])
    assert a["image"]["url"].startswith("http") and a["image"]["license"]
    assert all(r["source"] and r["policy"] for r in a["receipt"])  # every row sourced + policied
    assert SC._industry_to_bucket("Oil & Energy") == "energy"      # real industry→bucket mapping
    assert SC._industry_to_bucket("Computer Software") == "technology"


def test_scene_say_recites_allude_does_not():
    from pipeline.personalization import scene as SC
    allude = SC.build_scene("Arizona", "technology", detected=True, company="Apple Inc", city="Cupertino", policy="allude")
    say = SC.build_scene("Arizona", "technology", detected=True, company="Apple Inc", city="Cupertino", policy="say")
    assert "Apple Inc" not in allude["headline"]       # allude never recites the company
    assert "Apple Inc" in say["headline"]              # say (ungated) recites it
    assert say["blocked"] is True and allude["blocked"] is False
    assert any(r["policy"] == "say" and "company" in r["signal"] for r in say["receipt"])


def test_default_industry_is_neutral_not_a_sector():
    """When no industry resolves, the fallback is a TRUE neutral default — not a specific
    sector (the 'why is my industry mining' bug), and not industry-inferred imagery."""
    from pipeline.personalization import scene as SC
    assert SC.DEFAULT_INDUSTRY == "general"
    g = SC.BY_KEY[SC.DEFAULT_INDUSTRY]
    assert g["label"] == "General"                     # badge reads "General", not a sector
    s = SC.build_scene("Texas", SC.DEFAULT_INDUSTRY, detected=True)
    blob = (s["eyebrow"] + s["headline"] + s["sub"]).lower()
    for sector in ("mining", "energy", "healthcare", "logistics", "manufacturing", "construction"):
        assert sector not in blob                       # neutral copy names no sector
    # backdrop is a brand wash — no inferred photo — and still carries a provenance receipt
    assert s["image"]["id"] == "neutral-wash" and not s["image"]["url"].startswith("http")
    assert all(r["source"] and r["policy"] for r in s["receipt"])


def test_isp_is_classified_not_a_company():
    """A consumer ISP/carrier behind the IP is the provider, not the visitor's company."""
    from pipeline.personalization import scene as SC
    assert SC._looks_like_isp("AT&T Services, Inc.") is True
    assert SC._looks_like_isp("Comcast Cable Communications") is True
    assert SC._looks_like_isp("Apple Inc") is False  # a real corporate org is not an ISP


def test_creative_agents_and_the_gate():
    from pipeline.personalization import creative as CR
    a = CR.angle_copy("mining", "peer", "Arizona")
    assert a == CR.angle_copy("mining", "peer", "Arizona")          # deterministic angle
    assert "mining" in a["headline"].lower()
    # the Gate blocks the unprovable, clears the provable
    assert CR.verify_copy(["The #1 platform for mining"], "industry=mining", None, "allude")[0]["ok"] is False
    assert CR.verify_copy(["Acme Mining, welcome back"], "x", "Acme Mining", "allude")[0]["ok"] is False
    assert CR.verify_copy(["Built for mining teams across Arizona"], "x", "Acme Mining", "allude")[0]["ok"] is True
    d = CR.ai_copy(industry="mining", region="Arizona", company=None, city=None, angle="peer", policy="allude")
    assert d["source"] == "template" and d["headline"] and d["blocked_example"]["ok"] is False  # falls back, Gate visible


def test_loss_angle_is_provable_and_ships():
    """Pass-2 action layer: the cost-of-inaction angle frames the status quo without inventing a
    number, so it's provable by construction and clears the Gate."""
    from pipeline.personalization import creative as CR
    assert any(a["key"] == "loss" for a in CR.ANGLES)                       # the angle exists
    a = CR.angle_copy("mining", "loss", "Arizona")
    assert a == CR.angle_copy("mining", "loss", "Arizona")                  # deterministic
    assert not re.search(r"\d", a["headline"] + a["sub"])                   # never fabricates a number
    checks = CR.verify_copy([a["headline"], a["sub"]], "industry=mining", None, "allude")
    assert all(ch["ok"] for ch in checks)                                   # loss-framed AND provable → ships


def test_gate_axis_b_persuasion_hygiene():
    """Axis B: AI-generated tells and em-dash overuse are unshippable — but clean copy is untouched."""
    from pipeline.personalization import creative as CR

    def ok(line):
        return CR.verify_copy([line], "x", None, "allude")[0]["ok"]

    assert ok("I hope this email finds you well, just circling back.") is False   # AI-tell phrases
    assert ok("We leverage robust, seamless synergy to elevate teams.") is False  # AI-tell words
    assert ok("Built for scale — at the pace of growth — across your region.") is False  # >1 em-dash
    # the hygiene axis must NOT flip clean, provable copy
    assert ok("Every claim ships with its source and policy") is True
    assert ok("From planting to yield — built for growers across Arizona") is True  # one em-dash is fine


def test_message_gate_one_ask_length_calendar_spam():
    """The message Gate (Axis B at message scale): one ask, short, no cold calendar link, no
    spam-promise wording — and every honest variant clears it while the planted lie does not."""
    from pipeline.generation.variants import build_variants
    from pipeline.personalization import creative as CR

    def ok(body, **kw):
        return CR.verify_message(body, **kw)["ok"]

    assert ok("Quick q for {company}? Worth a look →") is True                        # one soft ask, short
    assert ok("Book a demo → or start a trial →") is False                            # two CTAs
    assert ok("Grab time on my Calendly: https://calendly.com/me/30min →") is False   # cold calendar link
    assert ok("Limited time — act now, it's risk-free →") is False                    # spam-promise wording
    assert ok("word " * 200 + "→") is False                                           # over the cold length cap
    # every honest variant ships; the planted lie is hygiene-blocked too (provable OR clean, never spam)
    vs = [v for arms in build_variants("email").values() for v in arms]
    assert all(CR.verify_message(v.template)["ok"] for v in vs if not v.planted_lie)
    assert all(not CR.verify_message(v.template)["ok"] for v in vs if v.planted_lie)


def test_sequence_gate_rejects_single_touch_and_dupes():
    """The sequence Gate: never single-touch, and no follow-up repeats a prior step verbatim."""
    from pipeline.personalization import creative as CR
    assert CR.verify_sequence(["only one touch"])["ok"] is False                       # single-touch
    assert CR.verify_sequence(["new angle A", "new angle A"])["ok"] is False           # repeated step
    assert CR.verify_sequence(["hook: hiring", "hook: funding", "breakup"])["ok"] is True


def test_policies_message_hygiene_is_locked():
    """Outbound message hygiene (one-CTA, word cap, no cold calendar link) is a locked anti-slop standard."""
    from app import policies as P
    cards = P._antislop_cards()
    assert any("One ask" in card["name"] for card in cards) and all(card["rule"] == "block" for card in cards)
    t = c.get("/policies").text
    assert "One ask per message" in t and "cold first touch" in t                      # rendered, locked


def test_classifier_confidence_and_tier():
    """The deterministic router: network type → per-field confidence → personalization tier."""
    from pipeline.personalization import scene as SC

    def rv(**k):
        b = dict(mobile=False, proxy=False, hosting=False, is_isp=False, corp_via_vpn=False,
                 is_corporate=False, org="X", isp="X")
        b.update(k); return b

    # clean corporate + resolved industry → Tier 2, everything high, competitive-eligible
    c = SC._classify(rv(is_corporate=True, org="Apple Inc"), "Apple Inc", "technology")
    assert c["tier"] == 2 and c["confidence"]["industry"] == "high" and c["competitive_eligible"]
    # corporate IP but PDL gave nothing → drop to Tier 1, NO sector guessed
    c = SC._classify(rv(is_corporate=True, org="Acme LLC"), "Acme LLC", None)
    assert c["tier"] == 1 and c["confidence"]["industry"] == "low" and not c["competitive_eligible"]
    # corporate-VPN exception → Tier 2 but capped at MEDIUM (not a clean office IP)
    c = SC._classify(rv(proxy=True, corp_via_vpn=True, is_corporate=True, org="Acme Corp"), "Acme Corp", "manufacturing")
    assert c["tier"] == 2 and c["confidence"]["company"] == "medium"
    # consumer ISP → Tier 1 location-aware, company void (the AT&T case)
    c = SC._classify(rv(is_isp=True, isp="AT&T"), None, None)
    assert c["tier"] == 1 and c["confidence"]["location"] == "high" and c["confidence"]["company"] == "none"
    # commercial VPN / hosting → Tier 0 neutral, location not trustworthy
    assert SC._classify(rv(proxy=True, isp="NordVPN"), None, None)["tier"] == 0
    assert SC._classify(rv(hosting=True, isp="Amazon"), None, None)["confidence"]["location"] == "low"
    # commercial VPN provider names are distinguished from a corporate org
    assert SC._looks_like_vpn("NordVPN") is True and SC._looks_like_vpn("Acme Corporation") is False


def test_gate_blocks_comparative_and_competitor_claims():
    """Comparative superiority + reciting an inferred competitor are the highest-scrutiny class."""
    from pipeline.personalization import creative as CR
    hints = CR.COMPETITOR_HINTS
    assert CR.verify_copy(["We're faster than the rest"], "x", None, "allude")[0]["ok"] is False
    assert CR.verify_copy(["Switch from your old tool today"], "x", None, "allude")[0]["ok"] is False
    assert CR.verify_copy(["Unlike legacy CRMs, we never guess"], "x", None, "allude")[0]["ok"] is False
    assert CR.verify_copy(["Beat Clay at de-anonymization"], "x", None, "allude", competitors=hints)[0]["ok"] is False
    # a provable, category-level differentiator clears the Gate
    assert CR.verify_copy(["Every claim ships with its source and policy"], "x", None, "allude", competitors=hints)[0]["ok"] is True


def test_tier3_competitor_agent_is_gated():
    """Tier-3 competitive copy leads with provable differentiators; the creepy arm is blocked."""
    from pipeline.personalization import creative as CR
    b = CR.competitor_brief(industry="technology", region="Texas")
    assert b["differentiators"] and b["source"] == "template"          # deterministic offline
    d = CR.ai_copy(industry="technology", region="Texas", company="Acme Inc", city=None,
                   angle="default", policy="allude", competitive=True)
    assert d["competitive"] is True and d["ships"] is True             # its own copy clears the Gate
    assert all(c["ok"] for c in d["checks"])                           # no comparative/competitor slip
    assert d["blocked_example"]["ok"] is False                         # the named-competitor arm is blocked


def test_demo_live_has_creative_controls():
    t = c.get("/demo/live").text
    assert 'id="sel-angle"' in t and 'id="img-pick"' in t and 'id="ai-go"' in t and "Creative agents" in t


def test_policies_corpus_and_claims_model():
    """Policies lead with the corpus (cite-or-don't-say) + an approved/forbidden claim list."""
    t = c.get("/policies").text
    assert c.get("/policies").status_code == 200
    for tab in ('data-tab="corpus"', 'data-tab="claims"', 'data-tab="provability"',
                'data-tab="disclosure"', 'data-tab="antislop"', 'data-tab="data"'):
        assert tab in t
    # corpus docs editable; claims have a can-say (with cite) + a cannot-say editor
    assert 'name="c_name"' in t and 'name="cs_claim"' in t and 'name="cs_cite"' in t and 'name="cannot"' in t
    # provability is the locked Gate, framed around grounded-in-corpus + citation
    assert "platform standard · inviolable" in t and "grounded in the corpus" in t.lower() and "cite" in t.lower()


def test_policies_edit_persists_and_resets():
    """Tenant edits (a corpus doc + a forbidden claim + a disclosure rule) persist; reset reverts."""
    from app import policies as P
    P._clear_overrides()
    assert any("Involuntary" in d["name"] for d in P._disclosure({}))   # a seed default is present
    c.post("/policies/save", data={
        "c_name": "Trust center", "c_kind": "url", "c_ref": "https://x/trust",
        "cs_claim": "SOC 2 Type II since 2024", "cs_cite": "Trust center",
        "cannot": "FDA-approved", "d_name": "First-party", "d_desc": "say it", "d_rule": "say",
        "sensitive": "biometrics", "consent_required": "on"})
    ovr = P._overrides()
    assert ovr["corpus"][0]["name"] == "Trust center" and ovr["corpus"][0]["kind"] == "url"
    assert ovr["can_say"][0]["cite"] == "Trust center" and "FDA-approved" in ovr["cannot_say"]
    assert ovr["disclosure"][0]["rule"] == "say"               # tenant-set disclosure rule persisted
    # the Gate's provability rules are code-defined — never part of the tenant override
    assert "corpus" not in str(P._provability_cards()) or all(card["rule"] for card in P._provability_cards())
    c.post("/policies/reset")
    assert P._overrides() == {}                                # back to defaults


def test_corpus_files_are_grounded_and_served():
    """Seed corpus docs carry real (synthetic) content, served for citation + the View modal."""
    from app import policies as P
    seeded = [d for d in P._corpus({}) if d["hasfile"]]
    assert len(seeded) >= 4                                    # the synthetic files exist on disk
    body = c.get("/policies/corpus/product-one-pager").text
    assert "12-week" in body and "cite" in body.lower()        # practical + on-thesis content
    assert c.get("/policies/corpus/pricing-packaging").text.count("$12,000") >= 1
    assert c.get("/policies/corpus/nope-not-real").status_code == 404   # unknown slug is honest


def test_help_aligns_with_the_app():
    """Help is organized to mirror the nav and documents the real surfaces — incl. Policies + graph."""
    idx = c.get("/help")
    assert idx.status_code == 200
    for cat in ("Core workflow", "Live demo", "Lab", "provenance"):   # nav-aligned categories
        assert cat in idx.text
    # the two surfaces that existed but were undocumented now have articles, pointing at real routes
    pol = c.get("/help/surface-policies").text
    assert "corpus" in pol.lower() and 'href="/policies"' in pol
    gr = c.get("/help/surface-graph").text
    assert "decision tree" in gr.lower() and 'href="/graph"' in gr


def test_archive_moves_noncore_surfaces_off_the_nav():
    """Non-core/lab surfaces are off the sidebar and collected in /archive; routes still resolve."""
    assert c.get("/archive").status_code == 200
    from app import archive as AR
    lab = [it["route"] for g in AR.ARCHIVE if g["group"] != "Internal decks" for it in g["items"]]
    assert "/personalize" in lab and "/inspector" in lab and "/enrichment-catalog" in lab
    for rt in lab:
        assert c.get(rt).status_code == 200, rt              # every archived surface still works
    shell = c.get("/workspace").text
    sidebar = shell.split("q-cmdk-scrim")[0]                 # nav markup, before the ⌘K palette
    assert 'href="/archive"' in sidebar                      # Archive reachable from the shell
    assert 'href="/personalize"' not in sidebar              # but the lab surfaces are off the sidebar
    assert 'href="/inspector"' not in sidebar


def test_integrations_show_base_vs_connect():
    """Landing + Help show the built-in enrichment base vs the connectable stack (data + value each)."""
    assert "/help/integrations" in c.get("/").text           # landing links to the detail
    t = c.get("/help/integrations")
    assert t.status_code == 200
    assert "Built in" in t.text and "Connect your stack" in t.text
    assert "People Data Labs" in t.text and "Reverse-IP" in t.text   # the wired base
    assert "HubSpot" in t.text and "Clay" in t.text and "Vector" in t.text  # connectable
    assert "Adds:" in t.text and "Value:" in t.text          # the per-integration data + value


def test_graph_page_embeds_the_exhibit():
    r = c.get("/graph")
    assert r.status_code == 200
    assert "/static/mockups/decision-tree.html" in r.text and "Agent graph" in r.text


def test_api_aicopy_gate_verified():
    d = c.get("/api/demo/aicopy?industry=energy&region=Texas&angle=peer").json()
    assert d["headline"] and isinstance(d["checks"], list) and d["blocked_example"]["ok"] is False


def test_resolve_ip_is_honest_offline():
    from pipeline.personalization import scene as SC
    d = SC.resolve_ip("10.0.0.1")   # private — no network, honest reason, no captured data
    assert d["company"] is None and d["captured"] == [] and "local" in d["reason"].lower()


def test_resolve_email_first_party_lane():
    """The email lane IDs any company (a startup's domain), and its facts are SAY (first-party)."""
    from pipeline.personalization import scene as SC
    bad = SC.resolve_email("not-an-email")
    assert bad["company"] is None and bad["tier"] == 0 and "work email" in bad["reason"]
    consumer = SC.resolve_email("jordan@gmail.com")          # personal mailbox → no company
    assert consumer["company"] is None and "personal mailbox" in consumer["reason"]
    # a work email at a startup reverse-IP can't see — offline, company falls back to the domain
    d = SC.resolve_email("jordan@gauntletai.com")
    assert d["company"] and d["tier"] >= 1 and d["confidence"]["company"] == "high"
    assert d["captured"] and all(r["policy"] == "say" for r in d["captured"] if r["label"] != "Personalization tier")


def test_api_demo_scene_preview():
    d = c.get("/api/demo/scene?region=Texas&industry=energy").json()
    assert d["industry"] == "energy" and "Texas" in d["sub"]


def test_skip_link_and_main_landmark():
    """Accessibility (WWDC26 Flexibility): keyboard users skip straight to content."""
    html = c.get("/workspace").text
    assert 'class="q-skip"' in html and 'href="#q-main"' in html and 'id="q-main"' in html


def test_light_only_no_auto_dark():
    """By decision the product is LIGHT ONLY (matches attio.com) — it must not flip with the OS."""
    css = (pathlib.Path(__file__).resolve().parents[1] / "app" / "static" / "quiet.css").read_text()
    assert "prefers-color-scheme: dark" not in css  # no OS-driven dark theme
    assert "--surface" in css and "--on-cta" in css   # token indirection retained (light values)


def test_filter_view_narrows_records():
    alln = c.get("/records?view=all").text.count('class="q-rec"')
    cust = c.get("/records?view=customers").text.count('class="q-rec"')
    assert 0 < cust < alln


def test_sort_reorders_records():
    import re as _re
    names = lambda v: _re.findall(r'class="q-rec">.*?\s([A-Z][a-z]+ [A-Z][a-z]+)<', c.get(v).text)
    by_name = c.get("/records?sort=name").text
    # the name sort is A→Z: first rendered record name <= last
    order = re.findall(r'q-rec"><span class="av"[^>]*>[^<]*</span>([^<]+)<', by_name)
    assert order == sorted(order, key=str.lower), "name sort not A→Z"


# ============================ composer gate ====================================
def test_composer_clears_clean_and_blocks_held():
    assert composer_check("Hi Maya, want the next start dates?")["blocked"] is False
    r = composer_check("On your income you can easily afford this — we noticed you've been comparing us with other bootcamps")
    assert r["blocked"] is True and len(r["hits"]) >= 2
    assert all(h["source"] for h in r["hits"])


def test_composer_examples_are_clickable():
    html = c.get("/composer").text
    assert html.count('href="/composer?msg=') >= 2  # the Try-it examples pre-fill the box


# ============================ variant→source receipt drill-down =================
def test_every_variant_has_a_known_placement():
    for s in DS.SCENARIOS:
        for v in s.variants:
            assert v.placement in DS.PLACEMENT, f"{v.id} placement {v.placement!r} unknown"
            assert v.place[0] and v.place[1]  # label + where


def test_cloner_injects_per_placement_with_markers():
    fake = ("<html><head></head><body><header><h1>Acme</h1></header>"
            "<main><p>body</p><a href='/signup'>Get started</a></main></body></html>")
    orig = cloner.fetch_raw
    cloner.fetch_raw = lambda url, cache=None: {"ok": True, "status": 200, "html": fake, "error": ""}
    try:
        for sid, vid in [("A", "A2"), ("A", "A3"), ("B", "B2")]:
            s, v = DS.find_variant(sid, vid)
            out = cloner.clone("https://x.test", s.id, v)
            html = out["html"]
            assert 'id="prov-demo-overlay"' in html
            assert f'data-prov-placement="{v.placement}"' in html
            assert "↳ maps to:" in html and v.place[0] in html
            # the overlay must actually be injected (not appended past </body> only)
            assert html.index("prov-demo-overlay") < html.index("</body>")
    finally:
        cloner.fetch_raw = orig


def test_focus_drilldown_renders_receipt():
    html = c.get("/demo?scenario=B&v=B2").text
    assert "Receipt" in html and "Maps to" in html
    assert "Data used" in html and "Optimizes" in html
    # numbered data rows tie back to the overlay markers
    assert 'class="rcv"' in html


def test_blocked_arm_provably_never_selected():
    # the optimizer surface shows the blocked arm at 0× and never a winner
    t = c.get("/optimizer").text
    assert "selected 0" in t and "relies on a hold fact" in t
    for s in DS.SCENARIOS:
        b = DS.blocked_variant(s)
        assert b is not None and b.blocked


# ============================ provenance invariant =============================
def test_every_gated_fact_has_a_source_and_no_hold_in_copy():
    for s in DS.SCENARIOS:
        for v in DS.gated_variants(s):
            assert v.data_used
            assert not v.uses_hold_in_copy, f"{v.id} recites a hold fact"
            for d in v.data_used:
                assert d.source and d.source_label


# ============================ drift behaviour ==================================
def test_drift_pause_then_unblock():
    pool = ActionPool("t", "web")
    pool.add("seg", "v1"); pool.add("seg", "v2")
    assert "v1" in pool.active("seg")
    pool.pause(["v1"]); assert "v1" not in pool.active("seg")
    pool.unblock(["v1"]); assert "v1" in pool.active("seg")


# ============================ agent / persona journeys =========================
def test_agent_explains_win_with_provenance():
    r = A.run("why did a variant win")
    assert r["cards"] and r["table"] and r["provenance"]
    assert "hold" in (r["note"] or "").lower()


def test_assurance_panel_renders():
    t = c.get("/assurance").text
    assert "Trust score" in t and "Drift watch" in t and "Trap catch-rate" in t


# ============================ one-design consistency ===========================
def test_all_shell_pages_extend_shell():
    for name in SHELL_PAGES:
        body = (TPL / f"{name}.html").read_text()
        assert 'extends "shell.html"' in body, f"{name}.html must extend the shell"


def test_shell_pages_carry_no_off_token_raw_hex():
    """Shell templates use only quiet.css tokens (var(--…)) — no 6-digit raw hex (data
    colours come from Python via inline style, not literal hex in the template)."""
    hex_re = re.compile(r"#[0-9a-fA-F]{6}\b")
    offenders = {}
    for name in SHELL_PAGES + ["shell"]:
        found = sorted(set(hex_re.findall((TPL / f"{name}.html").read_text())))
        if found:
            offenders[name] = found
    assert not offenders, f"raw hex outside the token set: {offenders}"


def test_home_is_attio_landing_featuring_the_demo():
    html = c.get("/").text
    assert 'class="q-display"' in html and 'class="q-hero"' in html  # the big attio hero
    assert 'class="q-showtabs"' in html and 'id="showframe"' in html  # tabbed product showcase
    assert 'href="/demo"' in html and 'href="/workspace"' in html  # demo is the front door
    assert "prove every move" in html.lower()


def test_pages_lead_with_the_proves_spine_line():
    for route in ["/workspace", "/records", "/composer", "/optimizer", "/agent",
                  "/assurance", "/sources", "/demo"]:
        assert "Proves:" in c.get(route).text, f"{route} missing its 'Proves:' spine line"
