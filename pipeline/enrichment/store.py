"""ProfileStore — enrichment read model backed by unified ProfileStore.

Returns enrichment ``Profile`` shapes for Observatory and Helix demo paths while
persisting the canonical namespaced ``Profile`` aggregate (``profiles_v2`` table).
"""
from __future__ import annotations

from typing import Optional

from pipeline.common.config import PROFILES_DB_PATH
from pipeline.domain.models.profile import Profile as DomainProfile
from pipeline.domain.stores.profile_store import ProfileStore as UnifiedProfileStore
from pipeline.enrichment.schemas import Profile


class ProfileStore:
    def __init__(self, path=None):
        self.path = str(path or PROFILES_DB_PATH)
        self._unified = UnifiedProfileStore(path=self.path)

    def save(self, profile: Profile) -> None:
        existing = self._unified.get(profile.recipient_id)
        if existing:
            existing.merge_enrichment(profile)
            self._unified.upsert(existing)
        else:
            self._unified.upsert(DomainProfile.from_enrichment(profile))

    def get(self, recipient_id: str) -> Optional[Profile]:
        p = self._unified.get(recipient_id)
        return p.to_enrichment_profile() if p else None

    def all_facts(self) -> list[dict]:
        c = self._unified._conn()
        out: list[dict] = []
        try:
            rows = c.execute("SELECT payload FROM profiles_v2").fetchall()
            for row in rows:
                p = DomainProfile.model_validate_json(row["payload"])
                for f in p.enrichment_facts:
                    out.append({
                        "fact_id": f.fact_id,
                        "recipient_id": f.recipient_id or p.profile_id,
                        "key": f.key,
                        "value": f.value,
                        "source": f.source,
                        "source_kind": f.source_kind,
                        "basis": f.basis,
                        "verdict": f.verdict.value,
                        "reasons": f.reasons,
                    })
        finally:
            c.close()
        out.sort(key=lambda r: (r["recipient_id"], r["key"]))
        return out

    def summary(self) -> dict:
        c = self._unified._conn()
        try:
            n_prof = c.execute("SELECT COUNT(*) c FROM profiles_v2").fetchone()["c"]
            by_verdict: dict[str, int] = {}
            rows = c.execute("SELECT payload FROM profiles_v2").fetchall()
            for row in rows:
                p = DomainProfile.model_validate_json(row["payload"])
                for f in p.enrichment_facts:
                    v = f.verdict.value
                    by_verdict[v] = by_verdict.get(v, 0) + 1
        finally:
            c.close()
        return {"profiles": n_prof, "facts_by_verdict": by_verdict, "db_path": self.path}
