"""Stream replay and projection infrastructure."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

from pipeline.common.config import DATA_DIR
from pipeline.domain.envelope import EventEnvelope, StreamType
from pipeline.domain.streams import STREAMS_DIR


class StreamReader:
    def __init__(self, root: Path = STREAMS_DIR):
        self.root = root

    def replay(self, stream_type: StreamType, stream_id: str) -> Iterator[EventEnvelope]:
        safe_id = stream_id.replace("/", "_")
        path = self.root / stream_type.value / f"{safe_id}.jsonl"
        if not path.exists():
            return iter(())
        events = []
        for line in path.read_text().splitlines():
            if line.strip():
                events.append(EventEnvelope.model_validate_json(line))
        events.sort(key=lambda e: e.stream_position)
        return iter(events)

    def all_streams(self) -> list[tuple[StreamType, str]]:
        out = []
        if not self.root.exists():
            return out
        for st in StreamType:
            d = self.root / st.value
            if not d.exists():
                continue
            for p in d.glob("*.jsonl"):
                stream_id = p.stem
                out.append((st, stream_id))
        return out

    def global_sequence(self) -> list[EventEnvelope]:
        all_events: list[EventEnvelope] = []
        for st, sid in self.all_streams():
            all_events.extend(self.replay(st, sid))
        all_events.sort(key=lambda e: (e.recorded_at, e.stream_position))
        return all_events


class GlobalSequence:
    """Sidecar index for cross-stream ordering."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or (DATA_DIR / "streams" / "global_sequence.json")

    def rebuild(self, reader: Optional[StreamReader] = None) -> list[str]:
        reader = reader or StreamReader()
        events = reader.global_sequence()
        ids = [e.event_id for e in events]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(ids, indent=2))
        return ids

    def load(self) -> list[str]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text())
