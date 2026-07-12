"""Online learning loop — the bandit that learns from REAL site traffic.

This bridges the deterministic demo (a synthetic CTA oracle over 1000 seeded recipients)
to genuine *online* reinforcement learning. Each real `/site` visit Thompson-samples a
Gate-cleared arm from posteriors that REAL clicks update, so the next visitor is served
what actually converted. It warm-starts from the demo's website posteriors, so it begins
with the simulated learning instead of cold.

The truth boundary holds for live traffic exactly as it does offline: the optimizer can
only ever pull arms in the Gate-cleared action pool, so the planted lie is unservable to a
real visitor — not by a filter here, but because it never enters the pool (Constitution II).

Reward model (online Bernoulli, so posteriors actually discriminate):
  - serve  -> record a PENDING impression (the arm pulled, and the policy that pulled it)
  - click  -> resolve that impression as reward 1 (and persist the posteriors)
  - no click after SETTLE_AFTER_SECONDS -> settle as reward 0

Two things layered on top:
  • Lift measurement — a `control` slice (holdout) is served a RANDOM cleared arm; comparing
    its CTR to the `bandit` (Thompson) slice's CTR is the honest measure of the bandit's lift.
  • Multi-tenant — posteriors and impressions are keyed by `tenant`, so tenants learn
    independently over their own Gate-cleared pools with no cross-contamination.
"""
from __future__ import annotations

import json
import random
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from pipeline.common.config import DB_PATH
from pipeline.common.db import connect, init_db
from pipeline.common.store import ActionPool, PosteriorStore
from pipeline.optimizer.bandit import ThompsonBandit

WARM_FROM_CAMPAIGN = "web"          # the deterministic demo's website campaign
SETTLE_AFTER_SECONDS = 1800         # 30 min with no click => a no-click (reward 0)
LIVE_HOLDOUT = 0.15                 # fraction of live traffic served a RANDOM arm (the control)

PENDING, CLICKED, NOCLICK = 0, 1, 2


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(ts: str) -> datetime:
    try:
        dt = datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return _now()
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class LiveOptimizer:
    """Per-tenant, per-channel online bandit over the Gate-cleared pool, fed by real
    impressions/clicks, with a random control slice for lift measurement."""

    def __init__(self, pool: ActionPool, channel: str = "website", tenant: str = "helix",
                 posteriors: Optional[PosteriorStore] = None,
                 db_path: Optional[Path] = None,
                 rng: Optional[random.Random] = None):
        self.channel = channel
        self.tenant = tenant
        self.pool = pool
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.post = posteriors or self._load_or_warm_start(tenant, channel)
        self._rng = rng or random.Random()
        self._lock = threading.Lock()
        self.bandit = ThompsonBandit(self.pool, self.post, self._rng)
        init_db(self.db_path)

    # --- posterior lifecycle ------------------------------------------------
    @staticmethod
    def _load_or_warm_start(tenant: str, channel: str) -> PosteriorStore:
        """Resume this tenant's live posteriors if present; else seed from the demo website
        campaign (so the live bandit starts where the simulation left off); else cold Beta(1,1)."""
        campaign = f"live_{tenant}"
        try:
            return PosteriorStore.load(campaign, channel)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            ps = PosteriorStore(campaign, channel)
            try:
                ps.warm_start_from(PosteriorStore.load(WARM_FROM_CAMPAIGN, channel))
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                pass   # no demo posteriors yet — start cold
            return ps

    def save(self) -> None:
        self.post.save()

    # --- serving ------------------------------------------------------------
    def select(self, segment: str, rng: Optional[random.Random] = None) -> Optional[str]:
        """Thompson-sample a Gate-cleared variant_id for this segment (never the lie)."""
        if rng is not None:
            return ThompsonBandit(self.pool, self.post, rng).select(segment)
        return self.bandit.select(segment)

    def assign(self, segment: str, rng: Optional[random.Random] = None,
               holdout_frac: Optional[float] = None) -> tuple[Optional[str], str]:
        """Assign a visitor to an arm AND a policy. With prob `holdout_frac` the visitor is a
        `control` (served a uniformly RANDOM cleared arm); otherwise `bandit` (Thompson). The
        control slice is what makes the bandit's lift measurable rather than asserted."""
        r = rng or self._rng
        active = self.pool.active(segment)
        if not active:
            return None, "bandit"
        hf = LIVE_HOLDOUT if holdout_frac is None else holdout_frac
        if hf > 0 and r.random() < hf:
            return r.choice(active), "control"
        return self.select(segment, rng=r), "bandit"

    @staticmethod
    def arm_label(variant_id: str) -> str:
        return variant_id.split("__")[-1]

    def record_impression(self, recipient_id: str, segment: str, variant_id: str,
                          policy: str = "bandit", now: Optional[datetime] = None) -> None:
        conn = connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO impressions (tenant,recipient_id,segment,variant_id,policy,ts,resolved) "
                "VALUES (?,?,?,?,?,?,?)",
                (self.tenant, recipient_id, segment, variant_id, policy,
                 (now or _now()).isoformat(), PENDING))
            conn.commit()
        finally:
            conn.close()

    # --- reward -------------------------------------------------------------
    def reward_click(self, recipient_id: str) -> Optional[str]:
        """Resolve this recipient's most recent pending impression (for THIS tenant) as a
        click (reward 1). Returns the rewarded variant_id, or None if none was pending."""
        conn = connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT id, segment, variant_id FROM impressions "
                "WHERE tenant=? AND recipient_id=? AND resolved=? ORDER BY id DESC LIMIT 1",
                (self.tenant, recipient_id, PENDING)).fetchone()
            if not row:
                return None
            conn.execute("UPDATE impressions SET resolved=? WHERE id=?", (CLICKED, row["id"]))
            conn.commit()
        finally:
            conn.close()
        with self._lock:
            self.bandit.update(row["segment"], row["variant_id"], 1)
            self.save()
        return row["variant_id"]

    def settle(self, now: Optional[datetime] = None,
               max_age_seconds: int = SETTLE_AFTER_SECONDS) -> int:
        """Turn this tenant's pending impressions older than the window into no-clicks
        (reward 0). Returns how many were settled — the negative evidence the bandit needs."""
        cutoff = (now or _now()) - timedelta(seconds=max_age_seconds)
        conn = connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT id, segment, variant_id, ts FROM impressions WHERE tenant=? AND resolved=?",
                (self.tenant, PENDING)).fetchall()
            stale = [r for r in rows if _parse_ts(r["ts"]) <= cutoff]
            for r in stale:
                conn.execute("UPDATE impressions SET resolved=? WHERE id=?", (NOCLICK, r["id"]))
            conn.commit()
        finally:
            conn.close()
        if stale:
            with self._lock:
                for r in stale:
                    self.bandit.update(r["segment"], r["variant_id"], 0)
                self.save()
        return len(stale)

    # --- reporting ----------------------------------------------------------
    def posterior_mean(self, segment: str, variant_id: str) -> float:
        a, b = self.post.get(segment, variant_id)
        return a / (a + b)

    def snapshot(self) -> dict:
        """This tenant's per-segment live posteriors + real impression/click counts."""
        conn = connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT segment, variant_id, "
                "SUM(CASE WHEN resolved=1 THEN 1 ELSE 0 END) AS clicks, "
                "SUM(CASE WHEN resolved=2 THEN 1 ELSE 0 END) AS noclicks, "
                "SUM(CASE WHEN resolved=0 THEN 1 ELSE 0 END) AS pending, "
                "COUNT(*) AS impressions "
                "FROM impressions WHERE tenant=? GROUP BY segment, variant_id", (self.tenant,)).fetchall()
        finally:
            conn.close()
        stats: dict = {}
        for r in rows:
            stats.setdefault(r["segment"], {})[r["variant_id"]] = dict(
                clicks=r["clicks"], noclicks=r["noclicks"],
                pending=r["pending"], impressions=r["impressions"])
        out: dict = {}
        total_clicks = 0
        for seg in sorted(self.pool.segments):
            arms = {}
            for vid in self.pool.active(seg):
                a, b = self.post.get(seg, vid)
                s = stats.get(seg, {}).get(vid, {})
                total_clicks += s.get("clicks", 0)
                arms[self.arm_label(vid)] = {
                    "variant_id": vid,
                    "posterior_mean": round(a / (a + b), 4),
                    "alpha": round(a, 2), "beta": round(b, 2),
                    "impressions": s.get("impressions", 0),
                    "clicks": s.get("clicks", 0),
                    "pending": s.get("pending", 0)}
            if arms:
                out[seg] = {"arms": arms,
                            "winner": max(arms, key=lambda k: arms[k]["posterior_mean"])}
        return {"tenant": self.tenant, "channel": self.channel,
                "live_clicks": total_clicks, "segments": out}

    def lift_report(self) -> dict:
        """The honest measure of the bandit: CTR of the adaptive (`bandit`) slice vs the
        random (`control`) slice. lift = bandit_ctr - control_ctr; positive means adaptivity
        is converting better than serving a random cleared arm. Only RESOLVED impressions
        count toward CTR (pending excluded)."""
        conn = connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT policy, "
                "SUM(CASE WHEN resolved=1 THEN 1 ELSE 0 END) AS clicks, "
                "SUM(CASE WHEN resolved IN (1,2) THEN 1 ELSE 0 END) AS resolved_n, "
                "COUNT(*) AS impressions "
                "FROM impressions WHERE tenant=? GROUP BY policy", (self.tenant,)).fetchall()
        finally:
            conn.close()

        def _ctr(clicks: int, n: int) -> Optional[float]:
            return round(clicks / n, 4) if n else None

        by = {r["policy"]: {"clicks": r["clicks"], "resolved": r["resolved_n"],
                            "impressions": r["impressions"], "ctr": _ctr(r["clicks"], r["resolved_n"])}
              for r in rows}
        b_ctr = (by.get("bandit") or {}).get("ctr")
        c_ctr = (by.get("control") or {}).get("ctr")
        lift = round(b_ctr - c_ctr, 4) if (b_ctr is not None and c_ctr is not None) else None
        rel = round((lift / c_ctr) * 100, 1) if (lift is not None and c_ctr) else None
        return {"tenant": self.tenant, "channel": self.channel, "by_policy": by,
                "bandit_ctr": b_ctr, "control_ctr": c_ctr,
                "lift": lift, "relative_lift_pct": rel,
                "note": ("control is a random cleared arm; lift is the gain from adaptivity"
                         if lift is not None else
                         "need resolved impressions in BOTH the bandit and control slices to measure lift")}
