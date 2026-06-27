"""DecisionTrace — re-exports canonical store."""
from __future__ import annotations

from typing import Any, Optional

from pipeline.common.schemas import ClaimVerdict, MessageLedger
from pipeline.domain.emit import DomainContext
from pipeline.domain.models.decision_trace import DecisionTrace
from pipeline.domain.stores.decision_trace_store import DecisionTraceStore, explain_decision

_store: Optional[DecisionTraceStore] = None


def _get_store() -> DecisionTraceStore:
    global _store
    if _store is None:
        _store = DecisionTraceStore()
    return _store


def record_trace(*args, **kwargs) -> DecisionTrace:
    return _get_store().record(*args, **kwargs)


def from_message_ledger(ledger: MessageLedger, *, ctx: Optional[DomainContext] = None) -> DecisionTrace:
    return _get_store().from_message_ledger(ledger, ctx=ctx)


def from_claim_verdicts(
    variant_id: str,
    verdicts: list[ClaimVerdict],
    *,
    decision_type: str = "asset_selection",
    subject_id: str = "",
    ctx: Optional[DomainContext] = None,
) -> DecisionTrace:
    return _get_store().from_asset_selection(
        variant_id, verdicts, subject_id=subject_id, ctx=ctx,
    )


def get_trace(trace_id: str) -> Optional[DecisionTrace]:
    return _get_store().get(trace_id)


def all_traces() -> list[DecisionTrace]:
    return _get_store().all_traces()


__all__ = [
    "DecisionTrace",
    "DecisionTraceStore",
    "all_traces",
    "explain_decision",
    "from_claim_verdicts",
    "from_message_ledger",
    "get_trace",
    "record_trace",
]
