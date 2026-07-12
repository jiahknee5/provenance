"""CustomerStore — the per-customer system of record (customers.sqlite).

Persists the whole customer (identity + timeline + facts) and a flattened, queryable facts
table (so "collect all info by customer" is one query). `resolve()` stitches identity across
sessions: an anonymous visitor_id, then an email, then a magic-link token all map to one
customer_id. Separate DB, gitignored, env-overridable for a deploy volume.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Optional

from pipeline.common.config import CUSTOMERS_DB_PATH
from pipeline.customer.schemas import Customer

_SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
  customer_id TEXT PRIMARY KEY,
  visitor_id  TEXT,
  email       TEXT,
  magic_token TEXT,
  stage       TEXT,
  payload     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS facts (
  fact_id        TEXT PRIMARY KEY,
  customer_id    TEXT,
  key            TEXT,
  value          TEXT,
  source         TEXT,
  surface_policy TEXT,
  sensitive      INTEGER,
  observed_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_facts_customer ON facts(customer_id);
"""


class CustomerStore:
    def __init__(self, path=None):
        self.path = str(path or CUSTOMERS_DB_PATH)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def _init(self) -> None:
        c = self._conn()
        try:
            c.executescript(_SCHEMA)
            c.commit()
        finally:
            c.close()

    def save(self, cust: Customer) -> None:
        c = self._conn()
        try:
            c.execute("INSERT OR REPLACE INTO customers "
                      "(customer_id, visitor_id, email, magic_token, stage, payload) VALUES (?,?,?,?,?,?)",
                      (cust.customer_id, cust.visitor_id, cust.email, cust.magic_token,
                       cust.stage.value, cust.model_dump_json()))
            c.execute("DELETE FROM facts WHERE customer_id=?", (cust.customer_id,))
            for f in cust.facts:
                c.execute("INSERT OR REPLACE INTO facts "
                          "(fact_id, customer_id, key, value, source, surface_policy, sensitive, observed_at) "
                          "VALUES (?,?,?,?,?,?,?,?)",
                          (f.fact_id, cust.customer_id, f.key, f.value, f.source,
                           f.surface_policy.value, int(f.sensitive), f.observed_at))
            c.commit()
        finally:
            c.close()

    def get(self, customer_id: str) -> Optional[Customer]:
        c = self._conn()
        try:
            row = c.execute("SELECT payload FROM customers WHERE customer_id=?",
                            (customer_id,)).fetchone()
        finally:
            c.close()
        return Customer.model_validate_json(row["payload"]) if row else None

    def resolve(self, email: str = "", magic_token: str = "", visitor_id: str = "") -> Optional[str]:
        """Stitch identity → the customer_id, trying the strongest signal first."""
        c = self._conn()
        try:
            for col, val in (("magic_token", magic_token), ("email", email), ("visitor_id", visitor_id)):
                if not val:
                    continue
                row = c.execute(f"SELECT customer_id FROM customers WHERE {col}=?", (val,)).fetchone()
                if row:
                    return row["customer_id"]
        finally:
            c.close()
        return None

    def facts_for(self, customer_id: str) -> list[dict]:
        c = self._conn()
        try:
            rows = c.execute("SELECT * FROM facts WHERE customer_id=? ORDER BY observed_at",
                             (customer_id,)).fetchall()
        finally:
            c.close()
        return [dict(r) for r in rows]

    def summary(self) -> dict:
        c = self._conn()
        try:
            n = c.execute("SELECT COUNT(*) AS n FROM customers").fetchone()["n"]
            by = {r["surface_policy"]: r["n"] for r in c.execute(
                "SELECT surface_policy, COUNT(*) AS n FROM facts GROUP BY surface_policy").fetchall()}
        finally:
            c.close()
        return {"customers": n, "facts_by_surface_policy": by, "db_path": self.path}
