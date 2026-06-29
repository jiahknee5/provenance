#!/usr/bin/env python3
"""Rebuild projection stores from domain stream JSONL files."""
from __future__ import annotations

import argparse
import json

from pipeline.domain.projectors import replay_all
from pipeline.domain.stream_reader import GlobalSequence, StreamReader


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Rebuild global sequence index")
    args = parser.parse_args()
    reader = StreamReader()
    n = replay_all(reader)
    if args.verify:
        ids = GlobalSequence().rebuild(reader)
        print(json.dumps({"replayed": n, "global_sequence_len": len(ids)}, indent=2))
    else:
        print(json.dumps({"replayed": n}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
