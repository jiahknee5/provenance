"""The observability spine — an append-only, monotonic-seq event ledger for a pipeline run.

This adapts the /observe contract (one JSONL line per event; a `seq` that only increases;
honest empty state when nothing has run) to Provenance's deterministic *runtime* pipeline.
Each node emits, as it runs, the four things the operator asked to see:

    INPUT   — what the node received
    TOOL    — the model / engine / data structure it used
    DECISION— the call it made (verdict, vote, arm, pause…) and why
    OUTPUT  — what it produced

Per decision R5 ("live = deterministic seeded replay"), the dashboard replays this ledger
rather than driving live inference.

Three properties make the watching trustworthy, not theatrical (the /observe thesis):

1. **Mechanical, not voluntary.** The decision points are instrumented *inside* the nodes
   (every Gate sub-step, the bandit, drift, assurance) — so a claim cannot be verified
   without its trace being written. `emit()` is a no-op unless a Recorder is active, so a
   normal run or the test suite (no recorder) is byte-for-byte unchanged and pays no cost.
2. **Append-only + monotonic.** One JSON line per event; `seq` is read-then-incremented so
   the merged stream has a total order across lanes; files are never truncated mid-run.
3. **Deterministic.** `seq` restarts at 0 each run and `t` is a *logical* clock
   (BASE_EPOCH + seq seconds), so re-running the trace yields byte-identical JSONL — the
   demo's reproducibility guarantee extends to the observability ledger itself.

The vocabulary is closed (no node invents an event type):

    RUN_START · PHASE · NODE_START · INPUT · TOOL · DECISION · OUTPUT · NODE_END
    · CACHE_HIT · DRIFT · ESCALATE · ERROR · RUN_END
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from pipeline.common.config import OBSERVE_DIR

# logical clock base — keeps `t` deterministic across re-runs (no wall clock in the ledger)
BASE_EPOCH = datetime(2025, 1, 1, tzinfo=timezone.utc)

VOCAB = {
    "RUN_START", "PHASE", "NODE_START", "INPUT", "TOOL", "DECISION", "OUTPUT",
    "NODE_END", "CACHE_HIT", "DRIFT", "ESCALATE", "ERROR", "RUN_END",
}


class Recorder:
    """Owns the run's seq counter and the per-lane append-only files."""

    def __init__(self, run_id: str, out_dir: Path = OBSERVE_DIR):
        self.run_id = run_id
        self.out_dir = out_dir
        self.seq = 0
        self._fh: dict[str, Any] = {}
        out_dir.mkdir(parents=True, exist_ok=True)
        # fresh run -> reproducible files: clear the prior ledger, reset seq
        for p in out_dir.glob("*.jsonl"):
            p.unlink()
        (out_dir / "seq.txt").write_text("0")

    def _file(self, lane: str):
        if lane not in self._fh:
            self._fh[lane] = open(self.out_dir / f"{lane}.jsonl", "a", encoding="utf-8")
        return self._fh[lane]

    def emit(self, lane: str, event: str, node: str = "", detail: str = "",
             tool: str = "", input: Any = None, decision: Any = None,
             output: Any = None, phase: str = "", **extra) -> int:
        if event not in VOCAB:
            raise ValueError(f"unknown observe event {event!r} (vocabulary is closed)")
        self.seq += 1
        rec = {
            "t": (BASE_EPOCH + timedelta(seconds=self.seq)).isoformat(),
            "seq": self.seq, "run_id": self.run_id, "lane": lane, "node": node or lane,
            "event": event, "phase": phase, "detail": detail,
        }
        if tool:
            rec["tool"] = tool
        if input is not None:
            rec["input"] = input
        if decision is not None:
            rec["decision"] = decision
        if output is not None:
            rec["output"] = output
        rec.update(extra)
        fh = self._file(lane)
        fh.write(json.dumps(rec, default=str) + "\n")
        fh.flush()
        (self.out_dir / "seq.txt").write_text(str(self.seq))
        return self.seq

    def close(self) -> None:
        for fh in self._fh.values():
            fh.close()
        self._fh.clear()


# --------------------------------------------------------------------------- #
# Module-global active recorder — emit() is a no-op unless one is attached.
# --------------------------------------------------------------------------- #
_REC: Optional[Recorder] = None
_PHASE: str = ""


def active() -> bool:
    return _REC is not None


def start_run(run_id: str, phases: Optional[list[str]] = None,
              out_dir: Path = OBSERVE_DIR) -> Recorder:
    global _REC, _PHASE
    _REC = Recorder(run_id, out_dir)
    _PHASE = ""
    _REC.emit("run", "RUN_START", node="run", detail=run_id,
              output={"phases": phases or []})
    return _REC


def end_run(summary: Optional[dict] = None) -> None:
    global _REC, _PHASE
    if _REC is None:
        return
    _REC.emit("run", "RUN_END", node="run", detail="run complete", output=summary or {})
    _REC.close()
    _REC = None
    _PHASE = ""


def set_phase(name: str) -> None:
    global _PHASE
    _PHASE = name
    if _REC is not None:
        _REC.emit("run", "PHASE", node="run", detail=name, phase=name)


def emit(lane: str, event: str, node: str = "", detail: str = "", tool: str = "",
         input: Any = None, decision: Any = None, output: Any = None, **extra) -> int:
    """No-op unless a Recorder is active (so tests / plain runs are untouched)."""
    if _REC is None:
        return 0
    return _REC.emit(lane, event, node=node, detail=detail, tool=tool, input=input,
                     decision=decision, output=output, phase=_PHASE, **extra)
