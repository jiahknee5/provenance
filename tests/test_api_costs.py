"""API cost ledger — record, estimate, summarize, observatory routes."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from app.main import app
from pipeline.observability import api_costs as AC

c = TestClient(app)


@pytest.fixture()
def ledger(tmp_path, monkeypatch):
    path = tmp_path / "api_cost_ledger.jsonl"
    monkeypatch.setattr(AC, "LEDGER_PATH", path)
    return path


def test_estimate_cost_gemini_image():
    cost = AC.estimate_cost(
        service="gemini_image",
        model="gemini-2.5-flash-image",
        images_generated=2,
    )
    assert cost == pytest.approx(0.078, rel=1e-3)


def test_estimate_cost_anthropic_tokens():
    cost = AC.estimate_cost(
        service="anthropic",
        model="claude-haiku-4-5-20251001",
        input_tokens=1000,
        output_tokens=200,
    )
    assert cost > 0
    assert cost < 0.01


def test_record_and_read_ledger(ledger):
    row = AC.record_call(
        tenant="planet",
        service="gemini_image",
        model="gemini-2.5-flash-image",
        operation="generate_image",
        cache_key="abc123",
        images_generated=1,
        duration_ms=1200,
        status="success",
    )
    assert row["tenant"] == "planet"
    assert row["estimated_cost_usd"] > 0
    rows = AC.read_ledger(limit=10, tenant="planet")
    assert len(rows) == 1
    assert rows[0]["cache_key"] == "abc123"


def test_record_error_zero_cost(ledger):
    row = AC.record_call(
        tenant="gauntlet",
        service="gemini_image",
        model="gemini-2.5-flash-image",
        operation="generate_image",
        status="429",
        images_generated=0,
    )
    assert row["estimated_cost_usd"] == 0.0
    assert row["status"] == "429"


def test_summarize_by_tenant(ledger):
    AC.record_call(
        tenant="planet", service="gemini_image", model="gemini-2.5-flash-image",
        operation="generate_image", images_generated=1, status="success",
    )
    AC.record_call(
        tenant="gauntlet", service="gemini_image", model="gemini-2.5-flash-image",
        operation="generate_image", images_generated=1, status="success",
    )
    s = AC.summarize()
    assert s["call_count"] == 2
    assert "planet" in s["by_tenant"]
    assert "gauntlet" in s["by_tenant"]
    assert s["total_cost_usd"] > 0


def test_costs_for_cache_key(ledger):
    AC.record_call(
        tenant="planet", service="gemini_image", model="gemini-2.5-flash-image",
        operation="best_of_n_candidate", cache_key="key1", images_generated=1,
        status="success", extra={"candidate_index": 0},
    )
    AC.record_call(
        tenant="planet", service="gemini_image", model="gemini-2.5-flash-image",
        operation="best_of_n_candidate", cache_key="key1", images_generated=1,
        status="success", extra={"candidate_index": 1},
    )
    info = AC.costs_for_cache_key("key1", tenant="planet")
    assert info["estimated_cost_usd"] > 0
    assert len(info["by_candidate"]) == 2


def test_costs_page_200():
    r = c.get("/costs")
    assert r.status_code == 200
    assert "API cost ledger" in r.text or "LLM / API cost ledger" in r.text


def test_api_costs_json_200():
    r = c.get("/api/costs")
    assert r.status_code == 200
    data = r.json()
    assert "summary" in data
    assert "rows" in data
    assert "disclaimer" in data["summary"]


def test_thread_safe_append(ledger):
    import threading
    def worker(i):
        AC.record_call(
            tenant="planet", service="gemini_image", model="gemini-2.5-flash-image",
            operation="generate_image", cache_key=f"k{i}", images_generated=1,
            status="success",
        )
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    lines = [ln for ln in ledger.read_text().splitlines() if ln.strip()]
    assert len(lines) == 8
    for ln in lines:
        json.loads(ln)
