"""v1 → v2 migration — bootstrap domain streams and unified Profile projections."""
from __future__ import annotations

import json
import sqlite3

from pipeline.common.config import (
    CUSTOMERS_DB_PATH,
    DATA_DIR,
    MANIFEST_PATH,
    PROFILES_DB_PATH,
    SCHEMA_VERSION,
    SEED,
)
from pipeline.common.db import connect, init_db
from pipeline.common.schema_meta import set_schema_version
from pipeline.customer.schemas import Customer
from pipeline.domain.emit import end_domain_run, start_domain_run
from pipeline.domain.models.profile import Profile
from pipeline.domain.stores.profile_store import ProfileStore
from pipeline.enrichment.schemas import Profile as EnrichProfile


from pipeline.common import config


def _has_table(c: sqlite3.Connection, name: str) -> bool:
    return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                     (name,)).fetchone() is not None


def _migrate_customers(store: ProfileStore) -> int:
    if not config.CUSTOMERS_DB_PATH.exists():
        return 0
    c = sqlite3.connect(str(config.CUSTOMERS_DB_PATH))
    c.row_factory = sqlite3.Row
    try:
        if not _has_table(c, "customers"):   # already v2 / fresh-v2: no legacy table → no-op
            return 0
        rows = c.execute("SELECT payload FROM customers").fetchall()
    finally:
        c.close()
    n = 0
    for row in rows:
        cust = Customer.model_validate_json(row["payload"])
        store.upsert(Profile.from_customer(cust))
        n += 1
    return n


def _migrate_enrichment(store: ProfileStore) -> int:
    if not config.PROFILES_DB_PATH.exists():
        return 0
    c = sqlite3.connect(str(config.PROFILES_DB_PATH))
    c.row_factory = sqlite3.Row
    try:
        if not _has_table(c, "profiles"):   # no legacy enrichment table → no-op
            return 0
        rows = c.execute("SELECT payload FROM profiles").fetchall()
    finally:
        c.close()
    n = 0
    for row in rows:
        ep = EnrichProfile.model_validate_json(row["payload"])
        pid = store.resolve(recipient_id=ep.recipient_id) or ep.recipient_id
        existing = store.get(pid)
        if existing:
            existing.merge_enrichment(ep)
            store.upsert(existing)
        else:
            store.upsert(Profile.from_enrichment(ep, profile_id=pid))
        n += 1
    return n


def migrate(*, emit_events: bool = True) -> dict:
    """Migrate v1 Customer + enrichment Profile rows into v2 unified ProfileStore."""
    store = ProfileStore(path=config.PROFILES_DB_PATH)
    rec = None
    if emit_events:
        rec = start_domain_run("migrate-v1-v2")
    n_cust = _migrate_customers(store)
    n_enrich = _migrate_enrichment(store)
    init_db()
    set_schema_version(connect(), SCHEMA_VERSION)
    config.MANIFEST_PATH.write_text(json.dumps({
        "schema_version": SCHEMA_VERSION,
        "seed": SEED,
        "migrated_customers": n_cust,
        "migrated_enrichment": n_enrich,
    }, indent=2))
    if emit_events:
        end_domain_run()
    return {
        "schema_version": SCHEMA_VERSION,
        "migrated_customers": n_cust,
        "migrated_enrichment": n_enrich,
        "profiles_db": str(config.PROFILES_DB_PATH),
    }


def main() -> None:
    result = migrate(emit_events=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
