"""DecisionTraceStore — durable explainability persistence."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from pipeline.common.db import connect
from pipeline.common.schema_meta import set_schema_version
from pipeline.common.config import SCHEMA_VERSION
from pipeline.common.schemas import ClaimVerdict, MessageLedger
from pipeline.domain.emit import DomainContext, emit_domain
from pipeline.domain.envelope import StreamType, SubjectRef, TraceRef
from pipeline.domain.models.decision_trace import DecisionTrace

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decision_traces (
    decision_trace_id TEXT PRIMARY KEY,
    payload           TEXT NOT NULL,
    created_at        TEXT
);
"""


def init_traces_table(conn=None) -> None:
    conn = conn or connect()
    conn.executescript(_SCHEMA)
    set_schema_version(conn, SCHEMA_VERSION)


class DecisionTraceStore:
    def __init__(self, conn=None):
        self._conn = conn or connect()
        init_traces_table(self._conn)

    def _trace_id(self, decision_type: str, subject_id: str) -> str:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM decision_traces").fetchone()
        seq = row["n"] if row else 0
        raw = f"{decision_type}|{subject_id}|{seq}"
        return "dt_" + hashlib.sha256(raw.encode()).hexdigest()[:14]

    def upsert(self, trace: DecisionTrace) -> DecisionTrace:
        self._conn.execute(
            "INSERT OR REPLACE INTO decision_traces (decision_trace_id, payload, created_at) "
            "VALUES (?,?,?)",
            (trace.decision_trace_id, trace.model_dump_json(), trace.created_at),
        )
        self._conn.commit()
        return trace

    def record(
        self,
        decision_type: str,
        outcome: str,
        *,
        claim_refs: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        rule_refs: list[str] | None = None,
        asset_ref: str = "",
        explanation: str = "",
        confidence: float = 0.0,
        subject_id: str = "",
        ctx: Optional[DomainContext] = None,
        overridden: bool = False,
    ) -> DecisionTrace:
        tid = self._trace_id(decision_type, subject_id or asset_ref or "global")
        trace = DecisionTrace(
            decision_trace_id=tid,
            decision_type=decision_type,
            outcome=outcome,
            claim_refs=claim_refs or [],
            evidence_refs=evidence_refs or [],
            rule_refs=rule_refs or [],
            asset_ref=asset_ref,
            explanation=explanation,
            confidence=confidence,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO decision_traces (decision_trace_id, payload, created_at) "
            "VALUES (?,?,?)",
            (tid, trace.model_dump_json(), trace.created_at),
        )
        self._conn.commit()
        ename = "decision_overridden" if overridden else "decision_trace_recorded"
        emit_domain(
            ename,
            stream_id=f"decision_trace_{tid}",
            stream_type=StreamType.DECISION_TRACE,
            subject_ref=SubjectRef(type="decision_trace", id=tid),
            payload=trace.model_dump(),
            trace_ref=TraceRef(decision_trace_id=tid),
            ctx=ctx,
        )
        return trace

    def get(self, trace_id: str) -> Optional[DecisionTrace]:
        row = self._conn.execute(
            "SELECT payload FROM decision_traces WHERE decision_trace_id=?", (trace_id,)
        ).fetchone()
        return DecisionTrace.model_validate_json(row["payload"]) if row else None

    def all_traces(self) -> list[DecisionTrace]:
        rows = self._conn.execute("SELECT payload FROM decision_traces").fetchall()
        return [DecisionTrace.model_validate_json(r["payload"]) for r in rows]

    def from_message_ledger(self, ledger: MessageLedger, *, ctx: Optional[DomainContext] = None) -> DecisionTrace:
        claim_refs = [c.claim_id for c in ledger.claims]
        rule_refs = sorted({f for c in ledger.claims for f in c.rule_flags})
        outcome = "cleared" if ledger.cleared else "blocked"
        return self.record(
            "message_verify",
            outcome,
            claim_refs=claim_refs,
            rule_refs=rule_refs,
            asset_ref=ledger.variant_id,
            explanation="; ".join(f"{c.claim_id}:{c.verdict.value}" for c in ledger.claims),
            confidence=min((c.confidence for c in ledger.claims), default=1.0),
            subject_id=ledger.recipient_id,
            ctx=ctx,
        )

    def from_asset_selection(
        self,
        asset_id: str,
        verdicts: list[ClaimVerdict],
        *,
        subject_id: str = "",
        ctx: Optional[DomainContext] = None,
    ) -> DecisionTrace:
        return self.record(
            "asset_selection",
            "selected",
            claim_refs=[v.claim_id for v in verdicts],
            rule_refs=sorted({f for v in verdicts for f in v.rule_flags}),
            asset_ref=asset_id,
            explanation="bandit arm selection with gate-cleared claims",
            subject_id=subject_id,
            ctx=ctx,
        )


def explain_decision(trace_id: str, store: Optional[DecisionTraceStore] = None) -> dict[str, Any]:
    store = store or DecisionTraceStore()
    trace = store.get(trace_id)
    if not trace:
        return {"found": False, "trace_id": trace_id}
    return {"found": True, "trace": trace.model_dump()}
