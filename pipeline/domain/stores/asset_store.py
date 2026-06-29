"""AssetStore — canonical Asset persistence."""
from __future__ import annotations

import sqlite3
from typing import Optional

from pipeline.common.config import DB_PATH, SCHEMA_VERSION
from pipeline.common.schema_meta import set_schema_version
from pipeline.domain.models.asset import Asset

_SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
    asset_id   TEXT PRIMARY KEY,
    segment    TEXT,
    channel    TEXT,
    status     TEXT,
    payload    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_assets_segment ON assets(segment);
"""


class AssetStore:
    def __init__(self, path=None):
        self.path = str(path or DB_PATH)
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

    def save(self, asset: Asset) -> Asset:
        c = self._conn()
        try:
            c.execute(
                "INSERT OR REPLACE INTO assets (asset_id, segment, channel, status, payload) "
                "VALUES (?,?,?,?,?)",
                (asset.asset_id, asset.segment, asset.channel, asset.status.value, asset.model_dump_json()),
            )
            c.commit()
        finally:
            c.close()
        return asset

    def get(self, asset_id: str) -> Optional[Asset]:
        c = self._conn()
        try:
            row = c.execute("SELECT payload FROM assets WHERE asset_id=?", (asset_id,)).fetchone()
        finally:
            c.close()
        return Asset.model_validate_json(row["payload"]) if row else None

    def list_by_segment(self, segment: str, channel: str = "") -> list[Asset]:
        c = self._conn()
        try:
            if channel:
                rows = c.execute(
                    "SELECT payload FROM assets WHERE segment=? AND channel=?", (segment, channel)
                ).fetchall()
            else:
                rows = c.execute("SELECT payload FROM assets WHERE segment=?", (segment,)).fetchall()
        finally:
            c.close()
        return [Asset.model_validate_json(r["payload"]) for r in rows]
