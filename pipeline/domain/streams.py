"""Append-only domain stream writers — one JSONL per aggregate stream."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from pipeline.common.config import DATA_DIR, SEED
from pipeline.domain.envelope import EventEnvelope, StreamType

STREAMS_DIR = DATA_DIR / "streams"
BASE_EPOCH = datetime(2025, 1, 1, tzinfo=timezone.utc)


class DomainRecorder:
    """Owns stream positions and writes canonical envelopes to disk."""

    def __init__(self, run_id: str, out_dir: Optional[Path] = None):
        self.run_id = run_id
        self.out_dir = out_dir if out_dir is not None else STREAMS_DIR
        self._positions: dict[str, int] = {}
        self._logical_seq = 0
        self._event_counter = 0
        self.out_dir.mkdir(parents=True, exist_ok=True)
        for st in StreamType:
            (self.out_dir / st.value).mkdir(parents=True, exist_ok=True)

    def _stream_path(self, stream_type: StreamType, stream_id: str) -> Path:
        safe_id = stream_id.replace("/", "_")
        return self.out_dir / stream_type.value / f"{safe_id}.jsonl"

    def next_position(self, stream_id: str) -> int:
        self._positions[stream_id] = self._positions.get(stream_id, 0) + 1
        return self._positions[stream_id]

    def logical_time(self) -> str:
        self._logical_seq += 1
        return (BASE_EPOCH + timedelta(seconds=self._logical_seq)).isoformat()

    def next_event_id(self, event_name: str, stream_id: str) -> str:
        self._event_counter += 1
        import hashlib
        raw = f"{SEED}|{self.run_id}|{event_name}|{stream_id}|{self._event_counter}"
        return "ev_" + hashlib.sha256(raw.encode()).hexdigest()[:16]

    def append(self, envelope: EventEnvelope) -> int:
        path = self._stream_path(envelope.stream_type, envelope.stream_id)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(envelope.model_dump_json() + "\n")
        return envelope.stream_position

    def read_stream(self, stream_type: StreamType, stream_id: str) -> list[EventEnvelope]:
        path = self._stream_path(stream_type, stream_id)
        if not path.exists():
            return []
        out: list[EventEnvelope] = []
        for line in path.read_text().splitlines():
            if line.strip():
                out.append(EventEnvelope.model_validate_json(line))
        return out


_REC: Optional[DomainRecorder] = None


def active_recorder() -> Optional[DomainRecorder]:
    return _REC
