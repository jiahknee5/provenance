"""Pytest wrapper for domain artifact sync governance."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_domain_artifact_sync_check_passes_or_no_catalog_change():
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts/check_domain_artifact_sync.py"
    result = subprocess.run([sys.executable, str(script)], cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
