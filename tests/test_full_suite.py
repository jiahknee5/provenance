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
