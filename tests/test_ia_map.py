"""IA contract tests — derived from docs/04-workflow/IA-MAP.md (W9, R40–R45).

The map is LOCKED v1. These tests keep the built IA aligned with it:
  - sidebar = stage-ordered PRODUCT plane (R40, R44)
  - channel items land on setup pages, never galleries/landing URLs (R42)
  - stage pages serve for every tenant; Home carries the J1 checklist (R43)
  - PRODUCT-plane crawler: no broken links, no orphan jumps (R44)
Wired into the deploy gate via deploy/railway.sh.
"""
from __future__ import annotations

import html
import re

from starlette.testclient import TestClient

from app.main import app
from pipeline.personalization import demo_nav as NAV

c = TestClient(app)
TENANTS = NAV.TENANTS

STAGE_KEYS = ["home", "live", "channels", "consoles", "preview", "launch", "measure"]
CHANNELS = ("direct", "search", "ads", "email")


# --------------------------------------------------------------------------- #
# Sidebar: stage order + PRODUCT-plane destinations
# --------------------------------------------------------------------------- #
def test_sidebar_groups_are_stage_ordered():
    for t in TENANTS:
        ctx = NAV.console_shell_ctx(t, "home")
        assert [g["key"] for g in ctx["nav_tree"]] == STAGE_KEYS, t


def test_sidebar_channel_items_land_on_setup_pages_not_galleries():
    # R42: the "search goes straight to a landing page" class of bug.
    for t in TENANTS:
        ctx = NAV.console_shell_ctx(t, "channels")
        grp = next(g for g in ctx["nav_tree"] if g["key"] == "channels")
        hrefs = [i["href"] for i in grp["items"]]
        assert hrefs == [f"/apt/channel/{ch}?site={t}" for ch in CHANNELS], t
        for h in hrefs:
            assert "gallery" not in h and "utm_" not in h and "ref=" not in h


def test_sidebar_live_plane_is_marked():
    # R44: the only LIVE-plane sidebar item is the replica, and it carries ↗.
    for t in TENANTS:
        ctx = NAV.console_shell_ctx(t, "home")
        live = next(g for g in ctx["nav_tree"] if g["key"] == "live")
        replica = next(i for i in live["items"] if i["id"] == "replica")
        assert "↗" in replica["label"]
        others = [i for g in ctx["nav_tree"] for i in g["items"] if i["id"] != "replica"]
        for i in others:
            assert i["href"].startswith(("/apt/", "/observatory", "/costs")) or "/dev/business" in i["href"], i


# --------------------------------------------------------------------------- #
# Stage pages serve per tenant
# --------------------------------------------------------------------------- #
def test_channel_setup_pages_serve_for_every_tenant():
    for t in TENANTS:
        for ch in CHANNELS:
            r = c.get(f"/apt/channel/{ch}?site={t}")
            assert r.status_code == 200, (t, ch)
            assert "Guardrails on this channel" in r.text
            assert "What arrives with this click" in r.text
            assert "Preview arrival →" in r.text, (t, ch)


def test_channel_decisions_links_target_marketer_console():
    for t in TENANTS:
        r = c.get(f"/apt/channel/direct?site={t}").text
        biz = NAV._mounts_for(t)["dev_business"]
        assert f'href="{biz}' in r, t
        # never deep-link the engineer console from a PRODUCT page
        dev = NAV._mounts_for(t)["dev"]
        assert not re.search(rf'href="{re.escape(dev)}\?', r), t


def test_home_carries_the_j1_checklist():
    for t in TENANTS:
        r = c.get(f"/apt/demo?site={t}")
        assert r.status_code == 200
        for step_href in (f"/apt/connect?site={t}", f"/apt/channel/direct?site={t}",
                          f"/apt/launch?site={t}", f"/observatory?site={t}"):
            assert step_href in r.text, (t, step_href)
        assert "Launch personalization on" in r.text


def test_connect_and_launch_pages_serve():
    for t in TENANTS:
        rc = c.get(f"/apt/connect?site={t}")
        assert rc.status_code == 200 and "Installed · verified" in rc.text
        rl = c.get(f"/apt/launch?site={t}")
        assert rl.status_code == 200 and "Staged changes" in rl.text
        assert "simulated" in rl.text  # R41: apply is honestly labeled


def test_unknown_channel_redirects_home():
    r = c.get("/apt/channel/bogus?site=skyfi", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].startswith("/apt/demo")


# --------------------------------------------------------------------------- #
# PRODUCT-plane crawler (R44): every link on a PRODUCT page resolves
# --------------------------------------------------------------------------- #
_HREF_RE = re.compile(r'href="(/[^"#]*)')

def _is_product(path: str) -> bool:
    return (path.startswith(("/apt/", "/observatory", "/costs"))
            or "/dev/business" in path)


def test_product_plane_crawler_no_broken_links():
    seen_pages: set[str] = set()
    checked: set[str] = set()
    queue = [f"/apt/demo?site={t}" for t in TENANTS]
    broken: list[tuple[str, str, int | str]] = []
    while queue:
        page = queue.pop()
        if page in seen_pages:
            continue
        seen_pages.add(page)
        assert len(seen_pages) < 500, "crawl runaway — link space is snowballing"
        r = c.get(page)
        assert r.status_code == 200, page
        # hrefs are HTML-escaped in markup; browsers decode entities before
        # requesting — the crawler must too, or &amp; params snowball.
        for href in {html.unescape(h) for h in _HREF_RE.findall(r.text)}:
            if href in checked:
                continue
            checked.add(href)
            if len(href) > 600:
                broken.append((page, href[:120], "url-snowball"))
                continue
            resp = c.get(href)
            if resp.status_code >= 400:
                broken.append((page, href, resp.status_code))
            if _is_product(href) and href not in seen_pages:
                queue.append(href)
    assert not broken, broken
    # sanity: the crawl actually covered the workspace, not a corner of it
    assert len(seen_pages) >= 3 * 6, len(seen_pages)
