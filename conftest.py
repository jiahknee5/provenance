"""pytest bootstrap — puts the project root on sys.path and gives tests an isolated db.

The property tests are seed-locked; this also reseeds python/numpy RNG before each test
so a green suite reproduces the exact on-stage numbers.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.common import config, db  # noqa: E402


@pytest.fixture(autouse=True)
def _seed():
    random.seed(config.SEED)
    try:
        import numpy as np
        np.random.seed(config.SEED)
    except Exception:
        pass
    yield


@pytest.fixture()
def tmp_db(tmp_path):
    """An isolated sqlite db + initialized schema for a test."""
    path = tmp_path / "t.sqlite"
    db.init_db(path)
    conn = db.connect(path)
    yield conn
    conn.close()
