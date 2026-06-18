"""ProfileStore — the synthesized profiles + their fact receipts, in profiles.sqlite.

A separate DB from provenance.sqlite, so the location is obvious (and shown in the
Observatory + the architecture diagram). Local, synthetic, gitignored. Every fact row is a
receipt: value + source + basis + verdict, queryable for the observability "Profiles" view.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Optional

from pipeline.common.config import PROFILES_DB_PATH
from pipeline.enrichment.schemas import Profile, ProfileFact

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    recipient_id    TEXT PRIMARY KEY,
    segment         TEXT,
    signals         TEXT,
    payload         TEXT NOT NULL,
    synthesized_seq INTEGER
);
CREATE TABLE IF NOT EXISTS profile_facts (
    fact_id      TEXT PRIMARY KEY,
    recipient_id TEXT,
    key          TEXT,
    value        TEXT,
    source       TEXT,
    source_kind  TEXT,
    basis        TEXT,
    verdict      TEXT,
    reasons      TEXT
);
"""


class ProfileStore:
    def __init__(self, path=None):
        self.path = str(path or PROFILES_DB_PATH)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        conn = self._conn()
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def save(self, profile: Profile) -> None:
        conn = self._conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO profiles (recipient_id, segment, signals, payload, synthesized_seq) "
                "VALUES (?,?,?,?,?)",
                (profile.recipient_id, profile.segment, json.dumps(profile.signals),
                 profile.model_dump_json(), profile.synthesized_seq))
            for f in profile.facts:
                conn.execute(
                    "INSERT OR REPLACE INTO profile_facts "
                    "(fact_id, recipient_id, key, value, source, source_kind, basis, verdict, reasons) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (f.fact_id, f.recipient_id, f.key, f.value, f.source, f.source_kind,
                     f.basis, f.verdict.value, json.dumps(f.reasons)))
            conn.commit()
        finally:
            conn.close()

    def get(self, recipient_id: str) -> Optional[Profile]:
        conn = self._conn()
        try:
            row = conn.execute("SELECT payload FROM profiles WHERE recipient_id=?",
                               (recipient_id,)).fetchone()
        finally:
            conn.close()
        return Profile.model_validate_json(row["payload"]) if row else None

    def all_facts(self) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM profile_facts ORDER BY recipient_id, key").fetchall()
        finally:
            conn.close()
        return [dict(r) for r in rows]

    def summary(self) -> dict:
        conn = self._conn()
        try:
            n_prof = conn.execute("SELECT COUNT(*) c FROM profiles").fetchone()["c"]
            by_verdict = {r["verdict"]: r["c"] for r in conn.execute(
                "SELECT verdict, COUNT(*) c FROM profile_facts GROUP BY verdict").fetchall()}
        finally:
            conn.close()
        return {"profiles": n_prof, "facts_by_verdict": by_verdict, "db_path": self.path}
