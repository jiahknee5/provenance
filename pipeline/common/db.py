"""SQLite layer — the durable store for recipients, channel events, and the caches.

Tables:
  recipients     — the form submissions (real form writes here; the 1000-generator seeds it)
  form_events    — every form submission (audit)
  cta_events     — every simulated/real CTA click, per channel (the bandit's reward feed)
  verdict_cache  — (claim_id, source_version, rules_version) -> ClaimVerdict json
  llm_cache      — sha256(input) -> model output json  (freezes non-deterministic calls)
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from pipeline.common.config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS recipients (
    recipient_id TEXT PRIMARY KEY,
    token        TEXT UNIQUE,
    payload      TEXT NOT NULL,           -- full Recipient json
    created_at   TEXT
);
CREATE TABLE IF NOT EXISTS form_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id TEXT,
    ts           TEXT,
    payload      TEXT
);
CREATE TABLE IF NOT EXISTS cta_events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_id TEXT,
    channel      TEXT,
    campaign     TEXT,
    variant_id   TEXT,
    clicked      INTEGER,                 -- 1 click, 0 no-click, -1 unsubscribe
    ts           TEXT
);
CREATE TABLE IF NOT EXISTS verdict_cache (
    cache_key    TEXT PRIMARY KEY,        -- claim_id|source_version|rules_version
    verdict_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS llm_cache (
    input_hash   TEXT PRIMARY KEY,
    output_json  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS app_kv (
    k            TEXT PRIMARY KEY,         -- editable app settings (e.g. policy overrides)
    v            TEXT NOT NULL
);
"""


def connect(path: Optional[Path] = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path or DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db(path: Optional[Path] = None) -> None:
    conn = connect(path)
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def reset_db(path: Optional[Path] = None) -> None:
    """Drop all rows — used by scripts to rebuild a deterministic run from scratch."""
    p = path or DB_PATH
    conn = connect(p)
    try:
        conn.executescript(_SCHEMA)
        for t in ("recipients", "form_events", "cta_events", "verdict_cache", "llm_cache"):
            conn.execute(f"DELETE FROM {t};")
        conn.commit()
    finally:
        conn.close()


# --- small helpers used across modules --------------------------------------
def kv_get(conn: sqlite3.Connection, table: str, key_col: str, key: str,
           val_col: str) -> Optional[Any]:
    row = conn.execute(
        f"SELECT {val_col} FROM {table} WHERE {key_col}=?", (key,)
    ).fetchone()
    return json.loads(row[val_col]) if row else None


def kv_put(conn: sqlite3.Connection, table: str, key_col: str, key: str,
           val_col: str, value: Any) -> None:
    conn.execute(
        f"INSERT INTO {table} ({key_col},{val_col}) VALUES (?,?) "
        f"ON CONFLICT({key_col}) DO UPDATE SET {val_col}=excluded.{val_col}",
        (key, json.dumps(value)),
    )
    conn.commit()
