"""Generative text mode (T-05 / S2 / R31) — the opt-in lane for a registry text target
with ``mode: generative``.

The shape is creative.py's thesis at the pool grain: **the agent proposes, the Gate
disposes.** For a generative target this module PROPOSES candidates; the per-decision
DecisionPool (T-02) is the only thing that decides servability — every candidate runs
through the real Gate (claims + message hygiene + the per-line copy Gate) and only the
cleared are constructed into the pool (Art II, structural, never a filter).

Candidates come in three layers:
  1. **Deterministic seeded synthesis (the offline default — $0, no key needed).**
     A pure function of the registry target (tenant | section | slot | prompt) over
     creative.ANGLES via angle_copy: same registry bytes -> same candidates, byte for
     byte, forever. This is what ships when ANTHROPIC_API_KEY is absent.
  2. **LLM upgrades (key only UPGRADES, never replaces).** With a key, one batched
     Claude call proposes extra drafts on top of layer 1. Every call is cost-logged via
     api_costs.record_anthropic_usage and cached in LLMCache, so a repeat build is a $0
     byte-identical replay. A failed/keyless call degrades to layer 1 silently.
  3. **Adversarial probes — always proposed, never servable.** A planted lie, a
     superlative, a competitor recite, and a hold-fact candidate ride along on every
     build so the clearance report PROVES the boundary working on live state (the lie /
     superlative / competitor are 0-servable in every state; the hold-fact flips to
     0-servable the moment its legal hold activates — the drift story).

Workflows (registry ``workflow`` field):
  * ``prebuilt``  — scripts/warm_copy_cache.py bakes the FULL candidate set (layers
    1+2+3) to data/demo/copy_cache/<tenant>__<section>__<slot>.json offline; at run
    time candidates_for() replays those bytes ($0, 0 ms, deterministic) and the pool
    still re-Gates them against CURRENT rules state — a baked candidate whose claim
    goes on hold is structurally unservable on the next pool build.
  * ``realtime``  — candidates synthesize in-process (cached by LLMCache when keyed);
    serve() memoizes the pick by visit key, so a returning key is <100 ms, adds no
    duplicate impression, and always replays the same variant (Art IV).
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path
from typing import Optional

from pipeline.common import config
from pipeline.common.cache import LLMCache
from pipeline.common.schemas import Variant
from pipeline.observability import api_costs as AC
from pipeline.personalization import creative as CR
from pipeline.personalization import decision_pool as DP
from pipeline.personalization import sections

COPY_CACHE_DIR = config.DATA_DIR / "copy_cache"          # ships in the image, like image_cache
CACHE_SCHEMA = 1
LLM_MODEL = "claude-haiku-4-5-20251001"
LLM_CANDIDATES = 3                                       # drafts per keyed upgrade call

# deterministic layer: the creative angles that carry full copy templates
_ANGLE_KEYS = ("peer", "roi", "loss", "local", "scale", "speed")
_SYNTH_K = 4                                             # angles per target (seed-picked)
# tenant -> creative/scene industry flavor for the deterministic templates
_TENANT_INDUSTRY = {"gauntlet": "technology", "planet": "agriculture", "skyfi": "general"}


# --------------------------------------------------------------------------- #
# Registry lookup
# --------------------------------------------------------------------------- #
def _target(tenant: str, section_id: str, target_id: str) -> dict:
    sec = sections.get_section(tenant, section_id)
    for t in sec.get("text_targets") or []:
        if t.get("slot_id") == target_id:
            return t
    raise KeyError(f"generative_text [{tenant}]: no text target {target_id!r} "
                   f"in section {section_id!r}")


def _seed(tenant: str, section_id: str, target_id: str, prompt: str) -> int:
    h = hashlib.sha256(f"{tenant}|{section_id}|{target_id}|{prompt}".encode()).hexdigest()
    return int(h[:16], 16)


def _prompt_sha(prompt: str) -> str:
    return hashlib.sha256((prompt or "").encode()).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# Layer 1 — deterministic seeded synthesis (offline default, $0)
# --------------------------------------------------------------------------- #
def _synth_candidates(tenant: str, section_id: str, target_id: str, prompt: str) -> list[Variant]:
    """A pure function of the registry target: seed-picked creative angles filled by
    angle_copy. No I/O, no key, no cost — the offline default AND the replay baseline."""
    rng = random.Random(_seed(tenant, section_id, target_id, prompt))
    industry = _TENANT_INDUSTRY.get(tenant, "general")
    out: list[Variant] = []
    for angle in rng.sample(_ANGLE_KEYS, k=min(_SYNTH_K, len(_ANGLE_KEYS))):
        ac = CR.angle_copy(industry, angle, region=None)
        out.append(Variant(
            variant_id=f"gen_{angle}", segment="pool", channel="website",
            arm_label=angle, template=f"{ac['headline']}\n{ac['sub']}",
            claim_ids=[], planted_lie=False, headline=ac["headline"]))
    return out


# --------------------------------------------------------------------------- #
# Layer 2 — keyed LLM upgrades (cost-logged, LLM-cached; absent key => [])
# --------------------------------------------------------------------------- #
def _get_llm_cache() -> LLMCache:
    """Seam for tests (isolated db); production uses the shared LLM cache."""
    return LLMCache()


def _llm_candidates(tenant: str, section_id: str, target_id: str, prompt: str) -> list[Variant]:
    """One batched Claude call -> up to LLM_CANDIDATES extra drafts. Cost-logged via
    record_anthropic_usage on every real call; cached by (target, prompt) so a repeat
    build replays byte-identical at $0. Any failure returns [] — the deterministic
    layer already covers the target (key only upgrades)."""
    if not config.ANTHROPIC_API_KEY:
        return []
    ask = (f"{prompt}\n"
           f"Propose {LLM_CANDIDATES} distinct hero copy candidates.\n"
           "Rules: no superlatives (#1/best/leading/guaranteed), no comparatives\n"
           "('better/faster/cheaper than', 'vs'), never name any company, no invented\n"
           "numbers or stats, at most one em-dash per candidate.\n"
           'Return JSON only: {"candidates": [{"headline": "...", "sub": "..."}]} '
           "— each headline <= 9 words.")
    ck = LLMCache.hash_input("copy_candidates_v1", tenant, section_id, target_id, ask)

    def compute() -> dict:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        r = client.messages.create(model=LLM_MODEL, max_tokens=600,
                                   messages=[{"role": "user", "content": ask}])
        AC.record_anthropic_usage(tenant=tenant, model=LLM_MODEL,
                                  operation="copy_candidates", response=r, cache_key=ck)
        txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        m = re.search(r"\{.*\}", txt, re.S)
        d = json.loads(m.group(0)) if m else {}
        cands = [{"headline": c["headline"].strip(), "sub": c["sub"].strip()}
                 for c in (d.get("candidates") or [])
                 if isinstance(c, dict) and c.get("headline") and c.get("sub")]
        if cands:
            return {"candidates": cands[:LLM_CANDIDATES]}
        raise ValueError("no candidates")      # raise -> not cached -> retried next build

    try:
        drafts = (_get_llm_cache().get_or_compute(ck, compute) or {}).get("candidates") or []
    except Exception:
        return []
    return [Variant(variant_id=f"gen_ai_{i + 1}", segment="pool", channel="website",
                    arm_label=f"ai_{i + 1}", template=f"{d['headline']}\n{d['sub']}",
                    claim_ids=[], planted_lie=False, headline=d["headline"])
            for i, d in enumerate(drafts)]


# --------------------------------------------------------------------------- #
# Layer 3 — adversarial probes (always proposed; the Gate keeps them 0-servable)
# --------------------------------------------------------------------------- #
def _probes() -> list[Variant]:
    """The four trap candidates every pool build proposes. lie / superlative /
    competitor recite are unservable in EVERY state; the hold-fact probe is honest
    approved copy that becomes 0-servable the moment its legal hold flips (S4.3)."""
    def v(vid, headline, claim_ids, lie=False):
        return Variant(variant_id=vid, segment="pool", channel="website",
                       arm_label=vid, template=headline, claim_ids=claim_ids,
                       planted_lie=lie, headline=headline)
    return [
        v("trap_lie", "Guaranteed outcomes for every team, risk-free", ["c_deployed"], lie=True),
        v("trap_superlative", "The #1 platform, best-in-class for modern teams", []),
        v("trap_competitor", "Everyone at Clay is already routing their pipeline here", []),
        v("trap_hold", "A verified cut in total cost of ownership", ["c_tco"]),
    ]


# --------------------------------------------------------------------------- #
# Prebuilt copy cache (parallel to data/demo/image_cache)
# --------------------------------------------------------------------------- #
def _cache_path(tenant: str, section_id: str, target_id: str) -> Path:
    return COPY_CACHE_DIR / f"{tenant}__{section_id}__{target_id}.json"


def _variant_payload(v: Variant) -> dict:
    return {"variant_id": v.variant_id, "arm_label": v.arm_label, "headline": v.headline,
            "template": v.template, "claim_ids": list(v.claim_ids),
            "planted_lie": v.planted_lie}


def write_cache(tenant: str, section_id: str, target_id: str,
                candidates: list[Variant], prompt: str) -> Path:
    """Bake the FULL candidate set (probes included — the pool re-Gates on load) with
    stable bytes: same candidates -> the same file, byte for byte."""
    payload = {"schema": CACHE_SCHEMA, "tenant": tenant, "section_id": section_id,
               "slot_id": target_id, "prompt_sha": _prompt_sha(prompt),
               "candidates": [_variant_payload(v) for v in candidates]}
    path = _cache_path(tenant, section_id, target_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_cache(tenant: str, section_id: str, target_id: str,
               prompt: str) -> Optional[list[Variant]]:
    """The baked candidates, or None when absent/stale (prompt changed since the warm —
    then the deterministic synthesis is the honest state until the next warm run)."""
    path = _cache_path(tenant, section_id, target_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("schema") != CACHE_SCHEMA or data.get("prompt_sha") != _prompt_sha(prompt):
        return None
    return [Variant(variant_id=c["variant_id"], segment="pool", channel="website",
                    arm_label=c.get("arm_label", c["variant_id"]),
                    template=c["template"], claim_ids=list(c.get("claim_ids") or []),
                    planted_lie=bool(c.get("planted_lie")),
                    headline=c.get("headline", ""))
            for c in data.get("candidates") or []]


# --------------------------------------------------------------------------- #
# The CandidateProvider (decision_pool.CandidateProvider signature)
# --------------------------------------------------------------------------- #
def build_candidates(tenant: str, section_id: str, target_id: str, *,
                     use_cache: bool = True) -> list[Variant]:
    """The UN-gated proposal set for one generative target. The DecisionPool decides
    what is servable — this function only proposes (Art II)."""
    meta = _target(tenant, section_id, target_id)
    if meta.get("mode") != "generative":
        raise ValueError(f"generative_text [{tenant}]: target {target_id!r} is "
                         f"mode={meta.get('mode')!r} — the generative provider only "
                         "proposes for mode: generative (deterministic slots ship via "
                         "the slot-fill path, $0)")
    prompt = meta.get("prompt") or ""
    if use_cache and meta.get("workflow") == "prebuilt":
        cached = load_cache(tenant, section_id, target_id, prompt)
        if cached is not None:
            return cached                       # byte-identical replay, $0
    cands = _synth_candidates(tenant, section_id, target_id, prompt)
    cands += _llm_candidates(tenant, section_id, target_id, prompt)
    cands += _probes()
    return cands


def candidates_for(tenant: str, section_id: str, target_id: str) -> list[Variant]:
    """decision_pool.CandidateProvider — injected into DecisionPool (T-02)."""
    return build_candidates(tenant, section_id, target_id)


# --------------------------------------------------------------------------- #
# Shared pools (one per Gate rule set) + realtime serve, cached by visit key
# --------------------------------------------------------------------------- #
_POOLS: dict[str, DP.DecisionPool] = {}
_SERVE_MEMO: dict[tuple, Variant] = {}


def _build_gate(rule_set: str):
    """The Gate bounding a pool: the registry target's named rule set when the file
    exists (rules/<name>.yaml), else the default tenant rules — exactly the fallback
    app.context.gate_for applies today."""
    from pipeline.gate.gate import Gate
    from pipeline.gate.rules import RulesEngine
    from pipeline.library.library import ClaimsLibrary
    path = sections.RULES_DIR / f"{rule_set}.yaml"
    rules = RulesEngine.load(path) if path.exists() else RulesEngine.load()
    return Gate(ClaimsLibrary.from_seed(), rules)


def pool_for(tenant: str, section_id: str, target_id: str) -> DP.DecisionPool:
    """The shared DecisionPool for this target's Gate rule set (registry ``gate:``
    field). One pool object per rule set; pool ids namespace the targets inside it."""
    meta = _target(tenant, section_id, target_id)
    rule_set = (meta.get("gate") or "").strip() or "helix_tenant"
    pool = _POOLS.get(rule_set)
    if pool is None:
        pool = DP.DecisionPool(_build_gate(rule_set), candidates_for)
        _POOLS[rule_set] = pool
    return pool


def serve(tenant: str, section_id: str, target_id: str, *, route: str,
          visit_key: str, pool: Optional[DP.DecisionPool] = None) -> Optional[dict]:
    """The realtime workflow: pick from the cleared pool, cached by visit key. A
    returning key replays the SAME variant with no re-sample and no duplicate
    impression (<100 ms, $0). Returns {variant_id, headline, template, receipt,
    cached} or None on an empty pool."""
    dp = pool if pool is not None else pool_for(tenant, section_id, target_id)
    memo_key = (id(dp), DP.DecisionPool.pool_id(tenant, section_id, target_id),
                route, visit_key)
    v = _SERVE_MEMO.get(memo_key)
    cached = v is not None
    if v is None:
        v = dp.pick(tenant, section_id, target_id, route, visit_key=visit_key)
        if v is None:
            return None
        _SERVE_MEMO[memo_key] = v
    return {"variant_id": v.variant_id, "headline": v.headline, "template": v.template,
            "receipt": dp.receipt(v.variant_id), "cached": cached}


def reset_state() -> None:
    """Drop shared pools + the serve memo (tests / registry reload)."""
    _POOLS.clear()
    _SERVE_MEMO.clear()
