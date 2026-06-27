"""Schema version stamping for SQLite databases and migration checks."""
from __future__ import annotations

import sqlite3
from typing import Optional

from pipeline.common.config import SCHEMA_VERSION

_META_DDL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL
);
"""


def ensure_schema_meta(conn: sqlite3.Connection) -> None:
    conn.executescript(_META_DDL)


def get_schema_version(conn: sqlite3.Connection) -> int:
    ensure_schema_meta(conn)
    row = conn.execute("SELECT v FROM schema_meta WHERE k='schema_version'").fetchone()
    if not row:
        return 1
    return int(row["v"])


def set_schema_version(conn: sqlite3.Connection, version: Optional[int] = None) -> None:
    ensure_schema_meta(conn)
    v = version if version is not None else SCHEMA_VERSION
    conn.execute(
        "INSERT INTO schema_meta (k, v) VALUES ('schema_version', ?) "
        "ON CONFLICT(k) DO UPDATE SET v=excluded.v",
        (str(v),),
    )
    conn.commit()
