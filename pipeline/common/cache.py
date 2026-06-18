"""The two caches that make the demo cheap, surgical, and reproducible.

VerdictCache — keyed (claim_id, source_version, rules_version). This is the structural
guarantee that the Gate runs **once per unique claim**, never per user. Drift re-Gates
only the affected (claim, source_version) pairs; the website reads the same cache the
email channel wrote.

LLMCache — keyed by a hash of the exact model input. Freezes non-deterministic model
calls (Ollama/Claude) into reproducible artifacts so a "live" re-Gate on stage returns
exactly what rehearsal did.
"""
from __future__ import annotations

import hashlib
import sqlite3
from typing import Callable, Optional

from pipeline.common import db
from pipeline.common.schemas import ClaimVerdict


def verdict_key(claim_id: str, source_version: str, rules_version: str) -> str:
    return f"{claim_id}|{source_version}|{rules_version}"


class VerdictCache:
    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self._own = conn is None
        self.conn = conn or db.connect()
        db.init_db()

    def get(self, claim_id: str, source_version: str, rules_version: str) -> Optional[ClaimVerdict]:
        raw = db.kv_get(self.conn, "verdict_cache", "cache_key",
                        verdict_key(claim_id, source_version, rules_version), "verdict_json")
        return ClaimVerdict.model_validate(raw) if raw else None

    def put(self, cv: ClaimVerdict) -> None:
        db.kv_put(self.conn, "verdict_cache", "cache_key",
                  verdict_key(cv.claim_id, cv.source_version, cv.rules_version),
                  "verdict_json", cv.model_dump(mode="json"))

    def close(self) -> None:
        if self._own:
            self.conn.close()


class LLMCache:
    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self._own = conn is None
        self.conn = conn or db.connect()
        db.init_db()

    @staticmethod
    def hash_input(*parts: str) -> str:
        h = hashlib.sha256()
        for p in parts:
            h.update(p.encode("utf-8"))
            h.update(b"\x00")
        return h.hexdigest()

    def get_or_compute(self, key: str, compute: Callable[[], dict]) -> dict:
        raw = db.kv_get(self.conn, "llm_cache", "input_hash", key, "output_json")
        if raw is not None:
            return raw
        out = compute()
        db.kv_put(self.conn, "llm_cache", "input_hash", key, "output_json", out)
        return out

    def close(self) -> None:
        if self._own:
            self.conn.close()
