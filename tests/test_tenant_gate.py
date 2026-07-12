"""Per-tenant Gate — each tenant gates with its OWN compliance rules.

A hold/block in one tenant's rules changes only that tenant's verdicts and action pool;
another tenant over the same claims is unaffected. The structural truth boundary (NLI +
message hygiene) holds for every tenant regardless of how permissive its rules are — so no
tenant, however lax, can ship the planted lie.
"""
from __future__ import annotations

from pipeline.common.cache import LLMCache, VerdictCache
from pipeline.common.config import RULES_DIR
from pipeline.gate.gate import Gate
from pipeline.gate.rules import RulesEngine
from pipeline.generation.variants import build_action_pool

CFO_A = "cfo__core__website__A"          # uses c_tco


def _gate(library, tmp_db, rules):
    return Gate(library, rules, verdict_cache=VerdictCache(tmp_db), llm_cache=LLMCache(tmp_db))


def test_per_tenant_gate_isolates_compliance(library, tmp_db):
    held, free = RulesEngine.load(), RulesEngine.load()
    held.set_hold("mlr_hold_tco", True)                       # only THIS tenant holds c_tco
    pool_held, _ = build_action_pool(_gate(library, tmp_db, held), "website", "ten_held")
    pool_free, _ = build_action_pool(_gate(library, tmp_db, free), "website", "ten_free")
    assert CFO_A not in pool_held.active("cfo__core")          # held -> dropped for this tenant
    assert CFO_A in pool_free.active("cfo__core")              # unaffected for the other tenant
    # neither tenant can ship the lie — the boundary is structural, not rule-dependent
    assert not any(v.endswith("__LIE")
                   for v in pool_held.all_variant_ids() | pool_free.all_variant_ids())


def test_tenant_rules_are_genuinely_different():
    helix = RulesEngine.load(RULES_DIR / "helix_tenant.yaml")
    academy = RulesEngine.load(RULES_DIR / "academy_tenant.yaml")
    assert helix.cfg.get("tenant") == "helix_analytics"
    assert academy.cfg.get("tenant") == "academy"
    assert helix.rules_version() != academy.rules_version()    # different compliance fingerprints


def test_context_gate_and_live_are_per_tenant():
    from app.context import Ctx
    c = Ctx()
    assert c.gate_for("helix") is c.gate                       # helix gate carries demo_state
    academy_gate = c.gate_for("academy")
    assert academy_gate is not c.gate and c.gate_for("academy") is academy_gate   # distinct + cached
    # the academy live optimizer is built from the academy gate and is still lie-free
    la = c.live_for("academy")
    assert la.tenant == "academy"
    assert not any(v.endswith("__LIE") for v in la.pool.all_variant_ids())
