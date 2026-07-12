"""Shared fixtures for the eval harness — a fresh Gate over an isolated db.

All tests run under the deterministic inference profile (the default), so a green suite
reproduces the exact on-stage numbers. These fixtures hit the REAL Gate (no mocks of the
decision logic) per Constitution Article VII.
"""
from __future__ import annotations

import pytest

from pipeline.common.cache import LLMCache, VerdictCache
from pipeline.gate.gate import Gate
from pipeline.gate.rules import RulesEngine
from pipeline.library.library import ClaimsLibrary
from pipeline.observability import api_costs as _AC


@pytest.fixture(autouse=True)
def _isolated_cost_ledger(tmp_path, monkeypatch):
    """Tests never write the production api-cost ledger. R35a cost-logs EVERY image
    call — including test-faked ones — so an unisolated suite inflates the real
    'today spend' and trips the S3.3 realtime ceiling (root cause of the P6-exit
    brain_simulator failure). Tests that assert ledger behavior monkeypatch their
    own path on top of this."""
    monkeypatch.setattr(_AC, "LEDGER_PATH", tmp_path / "test_api_cost_ledger.jsonl")
    yield


@pytest.fixture()
def library() -> ClaimsLibrary:
    return ClaimsLibrary.from_seed()


@pytest.fixture()
def rules() -> RulesEngine:
    return RulesEngine.load()


@pytest.fixture()
def gate(library, rules, tmp_db) -> Gate:
    return Gate(library, rules,
                verdict_cache=VerdictCache(tmp_db), llm_cache=LLMCache(tmp_db))
