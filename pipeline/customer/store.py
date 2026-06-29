"""CustomerStore — backward-compatible facade over unified ProfileStore.

Deprecated: new code should use ``pipeline.domain.stores.profile_store.ProfileStore``
directly. Reads and writes map to the namespaced ``Profile`` aggregate in
``profiles_v2`` (same DB path as ``PROFILES_DB_PATH`` / ``CUSTOMERS_DB_PATH``).
"""
from __future__ import annotations

from typing import Optional

from pipeline.common.config import CUSTOMERS_DB_PATH
from pipeline.customer.schemas import Customer, SurfacePolicy
from pipeline.domain.models.profile import Profile
from pipeline.domain.stores.profile_store import ProfileStore


class CustomerStore:
    def __init__(self, path=None):
        self.path = str(path or CUSTOMERS_DB_PATH)
        self._profiles = ProfileStore(path=self.path)

    def save(self, cust: Customer) -> None:
        self._profiles.upsert(Profile.from_customer(cust))

    def get(self, customer_id: str) -> Optional[Customer]:
        profile = self._profiles.get(customer_id)
        return profile.to_customer() if profile else None

    def resolve(self, email: str = "", magic_token: str = "", visitor_id: str = "") -> Optional[str]:
        return self._profiles.resolve(email=email, magic_token=magic_token, visitor_id=visitor_id)

    def facts_for(self, customer_id: str) -> list[dict]:
        profile = self._profiles.get(customer_id)
        if not profile:
            return []
        return [f.model_dump() for f in profile.funnel_facts]

    def summary(self) -> dict:
        s = self._profiles.summary()
        by: dict[str, int] = {}
        c = self._profiles._conn()
        try:
            rows = c.execute("SELECT payload FROM profiles_v2").fetchall()
            for row in rows:
                p = Profile.model_validate_json(row["payload"])
                for f in p.funnel_facts:
                    key = f.surface_policy.value
                    by[key] = by.get(key, 0) + 1
        finally:
            c.close()
        return {
            "customers": s.get("profiles", 0),
            "facts_by_surface_policy": by,
            "db_path": self.path,
            "schema_version": s.get("schema_version"),
        }
