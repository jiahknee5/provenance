#!/usr/bin/env python3
"""CI check: event catalog CSV changes require coordinated diagram/field-model updates."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/domain-design/proposed/provenance_event_catalog"
REQUIRED_COMPANIONS = [
    ROOT / "docs/domain-design/proposed/01-context-map.md",
    ROOT / "docs/domain-design/proposed/02-aggregate-model.md",
    ROOT / "docs/domain-design/proposed/04-sequence-diagram.md",
    ROOT / "docs/domain-design/proposed/06-field-purpose-and-domain-data-model.md",
    ROOT / "docs/domain-design/implemented/runtime-mapping.md",
]


def _git_diff_paths() -> set[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        )
        staged = subprocess.check_output(
            ["git", "diff", "--name-only", "--cached"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        )
        untracked = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT, text=True, stderr=subprocess.DEVNULL,
        )
        return set(filter(None, (out + staged + untracked).splitlines()))
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def main() -> int:
    changed = _git_diff_paths()
    catalog_changed = any(
        p.startswith("docs/domain-design/proposed/provenance_event_catalog/")
        for p in changed
    )
    if not catalog_changed:
        print("OK: no event catalog changes")
        return 0

    missing = [str(p.relative_to(ROOT)) for p in REQUIRED_COMPANIONS if str(p.relative_to(ROOT)) not in changed]
    if missing:
        print("FAIL: event catalog changed but these companion artifacts were not updated:")
        for m in missing:
            print(f"  - {m}")
        return 1

    print("OK: event catalog change includes coordinated artifact updates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
