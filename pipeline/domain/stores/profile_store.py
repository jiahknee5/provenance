"""Unified ProfileStore — single source for namespaced Profile aggregates."""
from __future__ import annotations

import json
import sqlite3
from typing import Optional

from pipeline.common.config import PROFILES_DB_PATH, SCHEMA_VERSION
from pipeline.common.schema_meta import set_schema_version
from pipeline.domain.models.profile import Profile

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles_v2 (
    profile_id    TEXT PRIMARY KEY,
    profile_class TEXT,
    visitor_id    TEXT,
    email         TEXT,
    magic_token   TEXT,
    recipient_id  TEXT,
    payload       TEXT NOT NULL,
    updated_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_profiles_v2_email ON profiles_v2(email);
CREATE INDEX IF NOT EXISTS idx_profiles_v2_visitor ON profiles_v2(visitor_id);
CREATE INDEX IF NOT EXISTS idx_profiles_v2_token ON profiles_v2(magic_token);
CREATE INDEX IF NOT EXISTS idx_profiles_v2_recipient ON profiles_v2(recipient_id);
"""


class ProfileStore:
    def __init__(self, path=None):
        self.path = str(path or PROFILES_DB_PATH)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _init(self) -> None:
        c = self._conn()
        try:
            c.executescript(_SCHEMA)
            set_schema_version(c, SCHEMA_VERSION)
            c.commit()
        finally:
            c.close()

    def upsert(self, profile: Profile) -> Profile:
        profile.reconcile_refs()
        c = self._conn()
        try:
            c.execute(
                "INSERT OR REPLACE INTO profiles_v2 "
                "(profile_id, profile_class, visitor_id, email, magic_token, recipient_id, payload, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    profile.profile_id,
                    profile.profile_class.value,
                    profile.identity.visitor_id,
                    profile.identity.email,
                    profile.identity.magic_token,
                    profile.identity.recipient_id,
                    profile.model_dump_json(),
                    profile.last_reconciled_at or profile.created_at,
                ),
            )
            c.commit()
        finally:
            c.close()
        return profile

    def get(self, profile_id: str) -> Optional[Profile]:
        c = self._conn()
        try:
            row = c.execute("SELECT payload FROM profiles_v2 WHERE profile_id=?", (profile_id,)).fetchone()
        finally:
            c.close()
        return Profile.model_validate_json(row["payload"]) if row else None

    def resolve(self, email: str = "", magic_token: str = "", visitor_id: str = "",
                recipient_id: str = "") -> Optional[str]:
        c = self._conn()
        try:
            for col, val in (
                ("magic_token", magic_token),
                ("email", email),
                ("visitor_id", visitor_id),
                ("recipient_id", recipient_id),
            ):
                if not val:
                    continue
                row = c.execute(f"SELECT profile_id FROM profiles_v2 WHERE {col}=?", (val,)).fetchone()
                if row:
                    return row["profile_id"]
        finally:
            c.close()
        return None

    def summary(self) -> dict:
        c = self._conn()
        try:
            n = c.execute("SELECT COUNT(*) AS n FROM profiles_v2").fetchone()["n"]
        finally:
            c.close()
        return {"profiles": n, "schema_version": SCHEMA_VERSION, "db_path": self.path}

    # backward compat alias
    save = upsert
