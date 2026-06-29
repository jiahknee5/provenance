"""Schema v1 → v2 migration tests."""
from __future__ import annotations

import json
import sqlite3

import pytest

from pipeline.common import config
from pipeline.common.config import SCHEMA_VERSION, SEED
from pipeline.customer import funnel
from pipeline.customer.schemas import Customer
from pipeline.domain.models.profile import ProfileClass
from pipeline.domain.stores.profile_store import ProfileStore
from pipeline.enrichment.schemas import Profile as EnrichProfile, ProfileFact, FactVerdict
from scripts import migrate_v1_to_v2 as mig


def _seed_v1_customer(db_path) -> Customer:
    c = funnel.new_visitor("vis_mig")
    funnel.web_signup(c, "Migr User", "mig@example.com", goal="learn AI", consent=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS customers ("
        "customer_id TEXT PRIMARY KEY, visitor_id TEXT, email TEXT, "
        "magic_token TEXT, stage TEXT, payload TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?)",
        (c.customer_id, c.visitor_id, c.email, c.magic_token, c.stage.value, c.model_dump_json()),
    )
    conn.commit()
    conn.close()
    return c


def _seed_v1_enrichment(db_path) -> EnrichProfile:
    ep = EnrichProfile(
        recipient_id="rec_mig_1",
        segment="clinops__mid__us",
        facts=[
            ProfileFact(
                fact_id="f1", recipient_id="rec_mig_1", key="intent_topic",
                value="analytics", source="synthetic", source_kind="enrich",
                basis="demo", verdict=FactVerdict.USABLE,
            ),
        ],
        signals={"intent_topic": "analytics"},
    )
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS profiles (
            recipient_id TEXT PRIMARY KEY, segment TEXT, signals TEXT,
            payload TEXT NOT NULL, synthesized_seq INTEGER);
    """)
    conn.execute(
        "INSERT OR REPLACE INTO profiles VALUES (?,?,?,?,?)",
        (ep.recipient_id, ep.segment, json.dumps(ep.signals), ep.model_dump_json(), 0),
    )
    conn.commit()
    conn.close()
    return ep


@pytest.fixture
def mig_paths(tmp_path, monkeypatch):
    cust_db = tmp_path / "customers.sqlite"
    prof_db = tmp_path / "profiles.sqlite"
    manifest = tmp_path / "manifest.json"
    monkeypatch.setattr(config, "CUSTOMERS_DB_PATH", cust_db)
    monkeypatch.setattr(config, "PROFILES_DB_PATH", prof_db)
    monkeypatch.setattr(config, "MANIFEST_PATH", manifest)
    return cust_db, prof_db, manifest


def test_migrate_v1_to_v2_profiles(mig_paths):
    cust_db, prof_db, manifest = mig_paths
    customer = _seed_v1_customer(cust_db)
    enrich = _seed_v1_enrichment(prof_db)
    result = mig.migrate(emit_events=False)
    assert result["schema_version"] == SCHEMA_VERSION
    assert result["migrated_customers"] == 1
    assert result["migrated_enrichment"] == 1

    store = ProfileStore(path=prof_db)
    p_cust = store.get(customer.customer_id)
    assert p_cust is not None
    assert p_cust.profile_class in (ProfileClass.LEAD, ProfileClass.CUSTOMER)
    assert p_cust.identity.email == "mig@example.com"

    p_enrich = store.get(enrich.recipient_id)
    assert p_enrich is not None
    assert p_enrich.segment == enrich.segment
    assert len(p_enrich.enrichment_facts) == 1

    manifest_data = json.loads(manifest.read_text())
    assert manifest_data["schema_version"] == SCHEMA_VERSION
    assert manifest_data["seed"] == SEED
