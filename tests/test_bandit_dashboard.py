from __future__ import annotations

import re
import subprocess

from fastapi.testclient import TestClient

from app.main import app


def test_optimizer_bandit_dashboard_scripts_parse():
    response = TestClient(app).get("/optimizer/bandit-dashboard")
    assert response.status_code == 200
    assert "/api/optimizer/dashboard" in response.text
    assert "Live optimizer" in response.text
    assert "Run demo" in response.text
    assert "runMode = new URLSearchParams" in response.text

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


def test_optimizer_dashboard_api_combines_live_snapshot_and_lift():
    response = TestClient(app).get("/api/optimizer/dashboard")
    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "live"
    assert isinstance(data["settled"], int)
    assert data["snapshot"]["tenant"] == "helix"
    assert data["snapshot"]["channel"] == "website"
    assert "segments" in data["snapshot"]
    assert data["lift"]["tenant"] == "helix"
    assert data["lift"]["channel"] == "website"
    assert "by_policy" in data["lift"]
