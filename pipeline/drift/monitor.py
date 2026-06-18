"""The Drift Monitor — treats truth as temporal.

On a source change it walks the claim->source dependency graph; on a legal-hold flip it
targets the held claim. Either way it re-Gates ONLY the affected claims (surgical), then
mutates every action pool: a claim that went red pauses the variants that assert it; a
claim that recovered unblocks them. Capitalise newly-cleared claims; never ship a stale
one.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from pipeline.common import observe
from pipeline.common.config import RUNS_DIR
from pipeline.common.schemas import ClaimVerdict, Verdict
from pipeline.common.store import ActionPool
from pipeline.generation.variants import build_variants


@dataclass
class DriftReport:
    event: str
    change: str
    affected_claims: list[str] = field(default_factory=list)
    recomputed_ids: list[str] = field(default_factory=list)
    before: dict = field(default_factory=dict)        # claim_id -> verdict
    after: dict = field(default_factory=dict)
    paused_variants: list[str] = field(default_factory=list)
    unblocked_variants: list[str] = field(default_factory=list)
    ts: str = ""

    def save(self, name: str) -> None:
        (RUNS_DIR / f"drift_{name}.json").write_text(json.dumps(asdict(self), indent=2))


class DriftMonitor:
    def __init__(self, gate, library, rules):
        self.gate = gate
        self.library = library
        self.rules = rules

    def _verify(self, claim_id: str) -> ClaimVerdict:
        c = self.library.claim(claim_id)
        return self.gate.verify_claim(c.text, c)

    def _mutate_pools(self, pools: list[ActionPool], affected: list[str],
                      before: dict, after: dict) -> tuple[list[str], list[str]]:
        paused, unblocked = [], []
        for pool in pools:
            variants = {v.variant_id: v for vs in build_variants(pool.channel).values() for v in vs}
            for vid in sorted(pool.all_variant_ids()):   # sorted -> deterministic output
                v = variants.get(vid)
                if not v:
                    continue
                for cid in affected:
                    if cid not in v.claim_ids:
                        continue
                    if after[cid] == Verdict.RED.value and vid not in pool.paused:
                        pool.pause([vid]); paused.append(vid)
                    elif before[cid] == Verdict.RED.value and after[cid] != Verdict.RED.value:
                        pool.unblock([vid]); unblocked.append(vid)
            pool.save()
        return paused, unblocked

    def _run(self, event: str, change: str, affected: list[str],
             apply_change, pools: list[ActionPool], name: str) -> DriftReport:
        observe.emit("drift", "INPUT", node="drift", tool="claim→source dependency graph",
                     detail=f"{event}: {change}", input={"event": event, "change": change,
                                                         "affected_claims": affected})
        before = {cid: self._verify(cid).verdict.value for cid in affected}  # pre-change (cached)
        calls0 = self.gate.compute_calls
        apply_change()                                                       # source/rule diff
        after = {cid: self._verify(cid).verdict.value for cid in affected}   # surgical re-Gate
        recomputed = self.gate.compute_calls - calls0
        recomputed_ids = [k[0] for k in self.gate.verified_keys[-recomputed:]]
        observe.emit("drift", "DRIFT", node="drift", tool="surgical re-Gate (cache-miss only)",
                     detail=f"re-verified {recomputed}/{len(affected)} affected claim(s) — "
                            + ", ".join(f"{c} {before[c]}→{after[c]}" for c in affected),
                     decision={"recomputed_count": recomputed, "recomputed_ids": recomputed_ids,
                               "before": before, "after": after})
        paused, unblocked = self._mutate_pools(pools, affected, before, after)
        observe.emit("drift", "OUTPUT", node="drift", detail=f"paused {len(paused)} · unblocked {len(unblocked)}",
                     output={"paused_variants": paused, "unblocked_variants": unblocked})
        rep = DriftReport(event=event, change=change, affected_claims=affected,
                          recomputed_ids=recomputed_ids,
                          before=before, after=after, paused_variants=paused,
                          unblocked_variants=unblocked,
                          ts=datetime.now(timezone.utc).isoformat())
        rep.save(name)
        return rep

    # ---- triggers ----------------------------------------------------------
    def fire_source_change(self, source_id: str, new_text: str,
                           pools: list[ActionPool], name: str = "source") -> DriftReport:
        affected = sorted(self.library.claims_for_source(source_id))
        return self._run("source_change", f"{source_id} edited", affected,
                         lambda: self.library.apply_source_change(source_id, new_text),
                         pools, name)

    def fire_legal_hold(self, hold_id: str, active: bool,
                        pools: list[ActionPool], name: str = "hold") -> DriftReport:
        claim_id = next(h["claim_id"] for h in self.rules.cfg["holds"] if h["id"] == hold_id)
        return self._run("legal_hold", f"{hold_id} -> {'ON' if active else 'OFF'}", [claim_id],
                         lambda: self.rules.set_hold(hold_id, active), pools, name)
