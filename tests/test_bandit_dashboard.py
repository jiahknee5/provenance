from __future__ import annotations

import re
import subprocess

from fastapi.testclient import TestClient

from app.main import app


def test_optimizer_bandit_dashboard_scripts_parse():
    response = TestClient(app).get("/optimizer/bandit-dashboard")
    assert response.status_code == 200

    scripts = re.findall(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>", response.text)
    assert scripts

    for idx, script in enumerate(scripts):
        subprocess.run(
            ["node", "--check", "-"],
            input=script,
            text=True,
            check=True,
            capture_output=True,
        ), f"inline script {idx} failed to parse"


def test_legacy_bandit_dashboard_redirects_to_optimizer_tab():
    response = TestClient(app).get("/bandit-dashboard", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/optimizer/bandit-dashboard"


def test_optimizer_sidebar_includes_bandit_subtabs():
    client = TestClient(app)

    dashboard = client.get("/optimizer/bandit-dashboard")
    assert dashboard.status_code == 200
    assert 'href="/optimizer/bandit-dashboard"' in dashboard.text
    assert 'href="/optimizer/bandit-dashboard/learn-more"' in dashboard.text
    assert ">Bandit dashboard</a>" in dashboard.text
    assert ">Bandit guide</a>" in dashboard.text
    assert 'href="/optimizer/bandit-dashboard" style="padding-left:30px;font-size:12.5px"' in dashboard.text

    guide = client.get("/optimizer/bandit-dashboard/learn-more")
    assert guide.status_code == 200
    assert 'href="/optimizer/bandit-dashboard/learn-more" style="padding-left:30px;font-size:12.5px"' in guide.text
