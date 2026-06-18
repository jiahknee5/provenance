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
