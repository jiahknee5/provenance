"""Run manifest — the reproducibility header for every campaign/demo run.

Records the seed, inference profile, model ids/versions, and the library + rules
versions in force. Persisted next to the run trace so any number on stage can be
reproduced exactly.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from pipeline.common import config
from pipeline.common.config import RUNS_DIR


@dataclass
class RunManifest:
    seed: int = config.SEED
    profile: str = config.INFERENCE_PROFILE
    ollama_judges: list[str] = field(default_factory=lambda: list(config.OLLAMA_JUDGE_MODELS))
    claude_model: str = config.CLAUDE_JUDGE_MODEL
    deberta_model: str = config.DEBERTA_MODEL
    library_version: str = ""
    rules_version: str = ""
    notes: str = ""

    def save(self, name: str = "run_manifest") -> None:
        (RUNS_DIR / f"{name}.json").write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, name: str = "run_manifest") -> "RunManifest":
        return cls(**json.loads((RUNS_DIR / f"{name}.json").read_text()))
