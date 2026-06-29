from __future__ import annotations

import re
import subprocess

from fastapi.testclient import TestClient

from app.main import app


def test_optimizer_bandit_dashboard_scripts_parse():
    response = TestClient(app).get("/optimizer/bandit-dashboard")
    assert response.status_code == 200
    assert 'id="run-btn-live"' not in response.text
    assert 'id="run-btn-demo"' not in response.text
    assert "Fast-forward 1,000 sends" in response.text
    assert "/api/optimizer/demo/fast-forward" in response.text
    assert 'id="sim-speed" min="100" max="2500" value="300"' in response.text
    assert "Cost sensitive Engineer" in response.text
    assert "Reward Driven Engineer" in response.text
    assert "AI Displacement Fear Engineer" in response.text
    assert "Low personalization: Flexible ROI" in response.text
    assert "High personalization: Stack-to-AI plan" in response.text
    assert "Creepy personalization: Financial surveillance" in response.text
    assert "hospital Total Cost of Ownership" not in response.text

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


def test_demo_fast_forward_processes_exactly_1000_sends():
    payload = {
        "segment_ids": ["cfo__core"],
        "gate_active": True,
        "seed": 7,
        "arms": {
            "cfo": [
                {"id": "A", "latentCTR": 0.24, "unsubRate": 0.004},
                {"id": "B", "latentCTR": 0.11, "unsubRate": 0.003},
                {"id": "LIE", "latentCTR": 0.44, "unsubRate": 0.09},
            ]
        },
        "posteriors": {
            "cfo__core": {
                arm: {"alpha": 1, "beta": 1, "sends": 0, "clicks": 0,
                      "unsubs": 0, "status": "active"}
                for arm in ("A", "B", "LIE")
            }
        },
        "global_stats": {
            "sends": 0, "clicks": 0, "unsubs": 0, "blockedLies": 0,
            "exploitCount": 0, "exploreCount": 0, "cumulativeRegret": 0,
        },
    }

    response = TestClient(app).post("/api/optimizer/demo/fast-forward", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sends_processed"] == 1000
    assert data["global_stats"]["sends"] == 1000
    assert sum(arm["sends"] for arm in data["posteriors"]["cfo__core"].values()) == 1000
    assert data["posteriors"]["cfo__core"]["LIE"]["sends"] == 0


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


def test_optimizer_sidebar_includes_bandit_subtabs():
    client = TestClient(app)

    dashboard = client.get("/optimizer/bandit-dashboard")
    assert dashboard.status_code == 200
    assert 'href="/optimizer/bandit-dashboard"' in dashboard.text
    assert 'href="/optimizer/bandit-dashboard/learn-more"' in dashboard.text
    assert ">Bandit dashboard</a>" in dashboard.text
    assert ">Bandit guide</a>" in dashboard.text

    guide = client.get("/optimizer/bandit-dashboard/learn-more")
    assert guide.status_code == 200
    assert 'href="/optimizer/bandit-dashboard/learn-more"' in guide.text
