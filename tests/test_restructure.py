"""Phase 5 — multi-user + UI-consistency acceptance suite (PRD §7, SPEC §E).

Deterministic, offline. Exercises each persona journey + the cross-cutting invariants and
the UI-consistency discipline that the /loop gates on.
"""
from __future__ import annotations

import pathlib
import re

from starlette.testclient import TestClient

from app.composer import check as composer_check
from app.main import app
from pipeline.agent import intents as A
from pipeline.common.store import ActionPool
from pipeline.personalization import demo_scenarios as DS

c = TestClient(app)
TPL = pathlib.Path(__file__).resolve().parents[1] / "app" / "templates"
SHELL_PAGES = ["workspace", "records", "agent", "assurance", "optimizer", "sources", "composer"]
NAV_ROUTES = ["/workspace", "/records", "/agent", "/assurance", "/optimizer", "/sources", "/composer"]


# --- surfaces render -----------------------------------------------------------
def test_all_nav_surfaces_render():
    for path in NAV_ROUTES:
        assert c.get(path).status_code == 200, f"{path} did not render"


# --- P1 RevOps: agent explains the win with provenance, names the blocked arm ---
def test_P1b_agent_why_won_carries_provenance_and_names_blocked():
    r = A.run("why did a variant win")
    assert r["cards"] and r["table"] and r["provenance"]
    assert "hold" in (r["note"] or "").lower()


def test_P1a_records_surface_shows_sourced_records():
    t = c.get("/workspace").text
    assert "Pipeline" in t and "Source" in t  # every record row carries a source column


# --- P2 SDR: composer blocks any hold/unverified fact, clears clean copy --------
def test_P2a_composer_clears_clean_copy():
    assert composer_check("Hi Maya, want the next start dates?")["blocked"] is False


def test_P2b_composer_blocks_hold_fact_with_source():
    r = composer_check("On your income you can easily afford this — we noticed you've been comparing us with other bootcamps")
    assert r["blocked"] is True and len(r["hits"]) >= 2
    assert all(h["source"] for h in r["hits"])  # each blocked fact names its source


# --- P3 Growth: optimizer surface shows the learned winner + blocked arm --------
def test_P3_optimizer_shows_winner_and_blocked_arm():
    t = c.get("/optimizer").text
    assert "learned winner" in t and "selected 0" in t and "relies on a hold fact" in t


# --- P4 Admin: drift pauses on source change, unblocks on re-clear --------------
def test_P4_drift_pause_then_unblock():
    pool = ActionPool("t", "web")
    pool.add("seg", "v1")
    pool.add("seg", "v2")
    assert "v1" in pool.active("seg")
    pool.pause(["v1"])                       # a source changed → Drift pauses the arm
    assert "v1" not in pool.active("seg")
    pool.unblock(["v1"])                      # re-cleared → arm returns to the pool
    assert "v1" in pool.active("seg")


# --- P5 CISO: minimalist assurance shows the trust panel + drift watch ----------
def test_P5_assurance_panel_renders():
    t = c.get("/assurance").text
    assert "Trust score" in t and "Drift watch" in t and "100%" in t
    assert "Trap catch-rate" in t


# --- P6 Visitor: the public demo still renders ----------------------------------
def test_P6_demo_surfaces_render():
    assert c.get("/demo").status_code == 200
    assert c.get("/demo/monitor").status_code == 200


# --- INV1: provenance completeness (no shown fact without a source) -------------
def test_INV1_every_fact_has_a_source():
    for s in DS.SCENARIOS:
        for v in DS.gated_variants(s):
            assert v.data_used
            for d in v.data_used:
                assert d.source


# --- UI1: every navigable surface extends the shell -----------------------------
def test_UI1_pages_extend_shell():
    for name in SHELL_PAGES:
        body = (TPL / f"{name}.html").read_text()
        assert 'extends "shell.html"' in body, f"{name}.html must extend the shell"


# --- UI2: token discipline — shell pages use no off-system raw hex colors --------
def test_UI2_no_raw_hex_in_shell_pages():
    """All colour comes from the quiet.css token set (var(--…)); templates carry no raw hex."""
    hex_re = re.compile(r"#[0-9a-fA-F]{6}\b")
    offenders = {}
    for name in SHELL_PAGES + ["shell"]:
        found = hex_re.findall((TPL / f"{name}.html").read_text())
        if found:
            offenders[name] = sorted(set(found))
    assert not offenders, f"raw hex colours outside the token set: {offenders}"
