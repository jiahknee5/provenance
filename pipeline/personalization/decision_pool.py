"""Per-decision cleared pool — the ONE object binding Gate + bandit + drift + provenance
for a single page element (S4/R34; pinned contract: 04-spec/contracts/decision-pool.md).

Pool id = ``tenant:section_id:target_id`` (the registry grain, sections.py). Keying is
pinned by the contract ``[PANEL — locked]``:
  • posterior-store identity = (tenant, channel) — exactly LiveOptimizer's
    ``_load_or_warm_start`` (optimizer/live.py:77-89): one store per tenant+channel,
    arms namespaced by pool id so pools never collide inside the shared store;
  • segment cell = ``audience_route`` (b2b_hire | b2b_upskill | individual | neutral);
  • a route cell with <30 RESOLVED impressions serves from the pooled ``_all`` cell
    (hierarchical fallback), so posteriors visibly move within one demo session.

The truth boundary is structural (Art II), never a filter: ``cleared_pool()`` Gates every
candidate's claims (``gate.verify_variant``) AND its message hygiene
(``creative.verify_message``), and only the doubly-cleared are CONSTRUCTED into the
ActionPool — build_action_pool's pattern (generation/variants.py:81). ``pick()``
Thompson-samples that pool, so a blocked / held / red / spammy candidate is unreachable.

Drift (S4.3): ``on_claims_invalidated()`` pauses exactly the variants asserting an
affected claim — across every built pool, atomically (they leave ``pool.active()``
before the call returns). No over- or under-invalidation.

Provenance (S4.1): every cleared variant gets a receipt at construction time; since only
cleared variants are pickable, every ``pick()`` result has a receipt by construction.

Lift (S4.2): a deterministic hash slice of visit keys is served a RANDOM cleared arm
(``control``); ``lift_report()`` compares its CTR to the Thompson slice — measured, not
asserted (live.py pattern).

NOT wired into serving this wave — T-04/T-05 consume this module.
"""
from __future__ import annotations

import hashlib
import itertools
import random
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

from pipeline.common.config import DB_PATH
from pipeline.common.db import connect, init_db
from pipeline.common.schemas import Variant, Verdict
from pipeline.common.store import PosteriorStore, ActionPool
from pipeline.optimizer.bandit import ThompsonBandit
from pipeline.optimizer.live import (CLICKED, LIVE_HOLDOUT, NOCLICK, PENDING,
                                     SETTLE_AFTER_SECONDS, LiveOptimizer)
from pipeline.personalization import creative as CR
from pipeline.personalization import sections

# [PANEL — locked] the segment vocabulary (gauntlet_site._audience_route) + pooled cell.
ROUTES = ("b2b_hire", "b2b_upskill", "individual", "neutral")
ALL_CELL = "_all"
FALLBACK_MIN_RESOLVED = 30       # a route cell below this serves from the pooled _all cell

_SEV = {Verdict.GREEN: 1, Verdict.AMBER: 2, Verdict.RED: 3}

# candidates(tenant, section_id, target_id) -> list[Variant] — the UN-gated candidate set;
# this object decides what is servable, the provider only proposes.
CandidateProvider = Callable[[str, str, str], list[Variant]]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(ts: str) -> datetime:            # mirrors optimizer/live.py
    try:
        dt = datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return _now()
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class DecisionPool:
    """Gate-cleared pool + Thompson bandit + surgical drift pause + receipt, per element."""

    def __init__(self, gate, candidates: CandidateProvider, *,
                 channel: str = "website",
                 db_path: Optional[Path] = None,
                 posteriors: Optional[dict[str, PosteriorStore]] = None,
                 holdout_frac: float = LIVE_HOLDOUT,
                 persist: bool = True,
                 rng: Optional[random.Random] = None,
                 routes: tuple[str, ...] = ROUTES):
        self.gate = gate
        self.candidates = candidates
        self.channel = channel
        # the tenant's audience_route vocabulary — defaults to the pinned gauntlet set;
        # a tenant whose _audience_route speaks differently (planet: enterprise/selfserve/
        # research/neutral) injects its own. Same pinned semantics: segment = audience_route.
        self.routes = tuple(routes)
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.holdout_frac = holdout_frac
        self.persist = persist
        self._rng = rng or random.Random()
        self._lock = threading.Lock()
        self._anon = itertools.count()
        # (tenant, channel) posterior-store identity — injected for tests, warm-started
        # via the exact live.py path otherwise.
        self._posteriors: dict[str, PosteriorStore] = dict(posteriors or {})
        self._pools: dict[str, ActionPool] = {}          # pool_id -> cleared ActionPool
        self._cleared: dict[str, list[str]] = {}         # pool_id -> cleared vids, in order
        self._variants: dict[str, Variant] = {}          # canonical vid -> Variant (cleared only)
        self._receipts: dict[str, dict] = {}             # canonical vid -> provenance receipt
        self._reports: dict[str, list[dict]] = {}        # pool_id -> clearance report rows
        init_db(self.db_path)

    # --- keying ---------------------------------------------------------------
    @staticmethod
    def pool_id(tenant: str, section_id: str, target_id: str) -> str:
        return f"{tenant}:{section_id}:{target_id}"

    def _posteriors_for(self, tenant: str) -> PosteriorStore:
        ps = self._posteriors.get(tenant)
        if ps is None:                                   # live.py:77-89, verbatim reuse
            ps = LiveOptimizer._load_or_warm_start(tenant, self.channel)
            self._posteriors[tenant] = ps
        return ps

    @staticmethod
    def _target_meta(tenant: str, section_id: str, target_id: str) -> dict:
        """The registry entry this pool decides for — fail loud on an unregistered target."""
        sec = sections.get_section(tenant, section_id)
        for t in sec.get("text_targets") or []:
            if t.get("slot_id") == target_id:
                return {**t, "kind": "text"}
        for t in sec.get("image_targets") or []:
            if t.get("surface_id") == target_id:
                return {**t, "kind": "image"}
        raise KeyError(f"decision pool [{tenant}]: no target {target_id!r} "
                       f"in section {section_id!r}")

    # --- pool construction (Art II: structural, never a filter) ----------------
    def cleared_pool(self, tenant: str, section_id: str, target_id: str) -> list[Variant]:
        """ONLY Gate-cleared variants exist in the pool. A blocked/held/red candidate is
        never constructed into it (build_action_pool pattern). Idempotent per pool id —
        the built pool (and its pause state) is reused; drift mutates it via
        on_claims_invalidated, not by rebuild."""
        pid = self.pool_id(tenant, section_id, target_id)
        if pid in self._pools:
            return [self._variants[vid] for vid in self._cleared[pid]]

        meta = self._target_meta(tenant, section_id, target_id)
        rules_version = self.gate.rules.rules_version()
        registry_version = sections.registry_version(tenant)
        pool = ActionPool(pid, self.channel)
        cleared_ids: list[str] = []
        report: list[dict] = []

        for cand in self.candidates(tenant, section_id, target_id):
            vid = (cand.variant_id if cand.variant_id.startswith(f"{pid}__")
                   else f"{pid}__{cand.variant_id}")
            v = cand.model_copy(update={"variant_id": vid, "segment": pid,
                                        "channel": self.channel})
            # unknown claim ids are unverifiable -> structurally blocked, never skipped
            unknown = [cid for cid in v.claim_ids if self.gate.library.claim(cid) is None]
            verdicts = self.gate.verify_variant(v) if not unknown else []
            claims_cleared = not unknown and all(cv.verdict != Verdict.RED for cv in verdicts)
            msg = CR.verify_message(v.template, channel=self.channel, stage="cold")
            cleared = claims_cleared and msg["ok"]
            report.append({
                "pool_id": pid, "variant_id": vid, "arm": v.arm_label,
                "planted_lie": v.planted_lie, "cleared": cleared,
                "claims_cleared": claims_cleared, "unknown_claim_ids": unknown,
                "message_ok": msg["ok"], "message_vetoes": msg["vetoes"],
                "message_warnings": msg["warnings"], "in_pool": cleared,
                "verdicts": [{"claim_id": cv.claim_id, "verdict": cv.verdict.value,
                              "flags": cv.rule_flags} for cv in verdicts],
            })
            if not cleared:
                continue                                  # never constructed into the pool
            for cell in self.routes + (ALL_CELL,):
                pool.add(cell, vid)
            self._variants[vid] = v
            self._receipts[vid] = self._build_receipt(
                v, verdicts, meta, tenant, section_id, target_id,
                rules_version, registry_version)
            cleared_ids.append(vid)

        self._pools[pid] = pool
        self._cleared[pid] = cleared_ids
        self._reports[pid] = report
        return [self._variants[vid] for vid in cleared_ids]

    def clearance_report(self, tenant: str, section_id: str, target_id: str) -> list[dict]:
        """Every candidate's clearance row (incl. the blocked ones) — the designer/obs feed."""
        self.cleared_pool(tenant, section_id, target_id)
        return self._reports[self.pool_id(tenant, section_id, target_id)]

    # --- serving (S4.2/S4.4) ----------------------------------------------------
    def serving_cell(self, tenant: str, section_id: str, target_id: str, route: str) -> str:
        """The posterior cell pick() samples: the route once it has >=30 resolved
        impressions, else the pooled _all cell (hierarchical fallback)."""
        pid = self.pool_id(tenant, section_id, target_id)
        conn = connect(self.db_path)
        try:
            n = conn.execute(
                "SELECT COUNT(*) AS n FROM impressions "
                "WHERE tenant=? AND segment=? AND resolved IN (?,?)",
                (pid, route, CLICKED, NOCLICK)).fetchone()["n"]
        finally:
            conn.close()
        return route if n >= FALLBACK_MIN_RESOLVED else ALL_CELL

    def assign_control(self, visit_key: str) -> bool:
        """Deterministic holdout slice: the same visit key always lands on the same side,
        so lift measurement never reshuffles a visitor between policies on replay."""
        h = int(hashlib.sha256(f"holdout|{visit_key}".encode()).hexdigest()[:8], 16)
        return (h / 0xFFFFFFFF) < self.holdout_frac

    @staticmethod
    def _replay_rng(pid: str, route: str, cell: str, visit_key: str) -> random.Random:
        seed = int(hashlib.sha256(f"{pid}|{route}|{cell}|{visit_key}".encode())
                   .hexdigest()[:16], 16)
        return random.Random(seed)

    def pick(self, tenant: str, section_id: str, target_id: str, route: str, *,
             visit_key: Optional[str] = None, policy: Optional[str] = None,
             now: Optional[datetime] = None) -> Optional[Variant]:
        """Thompson-sample the cleared pool for this route (pooled _all cell below 30
        resolved). With a visit_key the draw is a pure function of (pool, route, cell,
        visit_key) + posterior state — same key replays the same variant (Art IV) — and
        the control/bandit split is the deterministic assign_control slice. Records a
        PENDING impression (live.py reward model). Returns None only on an empty pool."""
        if route not in self.routes:
            raise ValueError(f"route {route!r} not in {self.routes}")
        self.cleared_pool(tenant, section_id, target_id)
        pid = self.pool_id(tenant, section_id, target_id)
        pool = self._pools[pid]
        cell = self.serving_cell(tenant, section_id, target_id, route)
        arms = pool.active(cell)
        if not arms:
            return None
        if policy is None:
            policy = ("control" if visit_key is not None and self.assign_control(visit_key)
                      else "bandit")
        rng = (self._replay_rng(pid, route, cell, visit_key)
               if visit_key is not None else self._rng)
        if policy == "control":
            vid = rng.choice(arms)                       # a uniformly random CLEARED arm
        else:
            vid = ThompsonBandit(pool, self._posteriors_for(tenant), rng).select(cell)
        key = visit_key if visit_key is not None else f"anon_{next(self._anon)}"
        conn = connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO impressions (tenant,recipient_id,segment,variant_id,policy,ts,resolved) "
                "VALUES (?,?,?,?,?,?,?)",
                (pid, key, route, vid, policy, (now or _now()).isoformat(), PENDING))
            conn.commit()
        finally:
            conn.close()
        return self._variants[vid]

    # --- reward (online posterior updates, live.py pattern) ---------------------
    def _update_posteriors(self, pool_id: str, route: str, variant_id: str, reward: int) -> None:
        tenant = pool_id.split(":", 1)[0]
        post = self._posteriors_for(tenant)
        with self._lock:
            bandit = ThompsonBandit(self._pools[pool_id], post, self._rng)
            for cell in (route, ALL_CELL):               # hierarchical: route + pooled cell
                bandit.update(cell, variant_id, reward)
            if self.persist:
                post.save()

    def reward_click(self, pool_id: str, variant_id: str, route: str) -> Optional[str]:
        """Resolve this pool's most recent pending impression of (variant, route) as a
        click (reward 1) and move the posteriors. Returns the variant_id, or None if no
        impression was pending — posteriors only ever move on real events."""
        conn = connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT id FROM impressions WHERE tenant=? AND variant_id=? AND segment=? "
                "AND resolved=? ORDER BY id DESC LIMIT 1",
                (pool_id, variant_id, route, PENDING)).fetchone()
            if not row:
                return None
            conn.execute("UPDATE impressions SET resolved=? WHERE id=?", (CLICKED, row["id"]))
            conn.commit()
        finally:
            conn.close()
        self._update_posteriors(pool_id, route, variant_id, 1)
        return variant_id

    def settle(self, pool_id: str, now: Optional[datetime] = None,
               max_age_seconds: int = SETTLE_AFTER_SECONDS) -> int:
        """Turn this pool's pending impressions older than the window into no-clicks
        (reward 0) — the negative evidence that separates the posteriors."""
        cutoff = (now or _now()) - timedelta(seconds=max_age_seconds)
        conn = connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT id, segment, variant_id, ts FROM impressions "
                "WHERE tenant=? AND resolved=?", (pool_id, PENDING)).fetchall()
            stale = [r for r in rows if _parse_ts(r["ts"]) <= cutoff]
            for r in stale:
                conn.execute("UPDATE impressions SET resolved=? WHERE id=?", (NOCLICK, r["id"]))
            conn.commit()
        finally:
            conn.close()
        for r in stale:
            self._update_posteriors(pool_id, r["segment"], r["variant_id"], 0)
        return len(stale)

    def lift_report(self, pool_id: str) -> dict:
        """The honest measure of the bandit for THIS pool: Thompson-slice CTR vs the
        random-control slice's, over resolved impressions only (live.py pattern)."""
        conn = connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT policy, "
                "SUM(CASE WHEN resolved=1 THEN 1 ELSE 0 END) AS clicks, "
                "SUM(CASE WHEN resolved IN (1,2) THEN 1 ELSE 0 END) AS resolved_n, "
                "COUNT(*) AS impressions "
                "FROM impressions WHERE tenant=? GROUP BY policy", (pool_id,)).fetchall()
        finally:
            conn.close()

        def _ctr(clicks: int, n: int) -> Optional[float]:
            return round(clicks / n, 4) if n else None

        by = {r["policy"]: {"clicks": r["clicks"], "resolved": r["resolved_n"],
                            "impressions": r["impressions"],
                            "ctr": _ctr(r["clicks"], r["resolved_n"])}
              for r in rows}
        b_ctr = (by.get("bandit") or {}).get("ctr")
        c_ctr = (by.get("control") or {}).get("ctr")
        lift = round(b_ctr - c_ctr, 4) if (b_ctr is not None and c_ctr is not None) else None
        return {"pool_id": pool_id, "channel": self.channel, "by_policy": by,
                "bandit_ctr": b_ctr, "control_ctr": c_ctr, "lift": lift,
                "note": ("control is a random cleared arm; lift is the gain from adaptivity"
                         if lift is not None else
                         "need resolved impressions in BOTH slices to measure lift")}

    def posterior_mean(self, tenant: str, cell: str, variant_id: str) -> float:
        a, b = self._posteriors_for(tenant).get(cell, variant_id)
        return a / (a + b)

    def active(self, tenant: str, section_id: str, target_id: str, cell: str) -> list[str]:
        """The arms pick() may pull right now (paused excluded) for one cell."""
        self.cleared_pool(tenant, section_id, target_id)
        return self._pools[self.pool_id(tenant, section_id, target_id)].active(cell)

    # --- drift (S4.3) ------------------------------------------------------------
    def on_claims_invalidated(self, claim_ids: Iterable[str]) -> list[str]:
        """Pause ONLY the variants asserting an affected claim, across every built pool,
        atomically (under the lock, out of pool.active() before this returns). Variants
        with no affected claim keep serving; receipts survive the pause (provenance)."""
        affected = set(claim_ids)
        paused: list[str] = []
        with self._lock:
            for pid in sorted(self._pools):              # sorted -> deterministic output
                pool = self._pools[pid]
                for vid in sorted(pool.all_variant_ids()):
                    if vid in pool.paused:
                        continue
                    if affected & set(self._variants[vid].claim_ids):
                        pool.pause([vid])
                        paused.append(vid)
                if self.persist:
                    pool.save()
        return sorted(paused)

    # --- provenance (S4.1) ---------------------------------------------------------
    def _build_receipt(self, v: Variant, verdicts: list, meta: dict, tenant: str,
                       section_id: str, target_id: str, rules_version: str,
                       registry_version: str) -> dict:
        pid = self.pool_id(tenant, section_id, target_id)
        claim_sources: list[str] = []
        for cid in v.claim_ids:
            sid = self.gate.library.claim(cid).source_id
            if sid not in claim_sources:
                claim_sources.append(sid)
        worst = (max(verdicts, key=lambda cv: _SEV[cv.verdict]).verdict
                 if verdicts else Verdict.GREEN)
        key_parts = [pid, v.variant_id, rules_version, registry_version] + [
            f"{cid}:{self.gate.library.source_version(self.gate.library.claim(cid).source_id)}"
            for cid in v.claim_ids]
        return {
            # the 9 pinned fields (contract S4.1)
            "source_id": claim_sources[0] if claim_sources else (meta.get("source") or "none"),
            "lawful_basis": "first_party_content",       # approved claims/catalog copy — no
                                                         # visitor-level data at this grain
            "policy": meta.get("policy") or "allude",
            "gate_verdict": worst.value,
            "claim_ids": list(v.claim_ids),
            "cache_key": hashlib.sha256("|".join(key_parts).encode()).hexdigest()[:16],
            "mode": meta.get("mode") or ("image" if meta.get("kind") == "image"
                                         else "deterministic"),
            "workflow": meta.get("workflow") or "realtime",
            "rules_version": rules_version,
            # attribution extras
            "variant_id": v.variant_id, "pool_id": pid, "tenant": tenant,
            "section_id": section_id, "target_id": target_id,
            "registry_version": registry_version, "claim_sources": claim_sources,
            "cleared_at": _now().isoformat(),
        }

    def receipt(self, variant_id: str) -> dict:
        """The provenance receipt minted when this variant cleared the Gate. Every
        pick() result has one by construction; KeyError for anything never cleared."""
        return self._receipts[variant_id]
