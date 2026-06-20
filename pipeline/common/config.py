"""Global configuration, paths, and the inference profile.

One seed governs all randomness (synthetic records, segment assignment, bandit RNG,
response oracle). The inference profile decides whether the Gate runs on deterministic
offline components (default — fast, reproducible, no key) or upgrades to real models
(DeBERTa / Ollama / Claude). Model outputs are always cached, so even the rich profile
replays deterministically.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---- paths -----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "demo"
SOURCES_DIR = DATA_DIR / "sources"
CLAIMS_DIR = DATA_DIR / "claims"
LEDGERS_DIR = DATA_DIR / "ledgers"
RUNS_DIR = DATA_DIR / "runs"
CACHE_DIR = DATA_DIR / "cache"
OBSERVE_DIR = DATA_DIR / "observe"      # the observability ledger (one JSONL per role lane)
RULES_DIR = PROJECT_ROOT / "rules"
# DB paths are env-overridable so a deploy can put the writable SQLite on a persistent
# volume (form submissions survive redeploys) while the baked, read-only demo artifacts
# (runs/observe/claims) stay in the image. Defaults keep everything local under data/demo.
DB_PATH = Path(os.environ.get("PROVENANCE_DB_PATH", str(DATA_DIR / "provenance.sqlite")))
PROFILES_DB_PATH = Path(os.environ.get("PROVENANCE_PROFILES_DB_PATH",
                                       str(DATA_DIR / "profiles.sqlite")))  # profiles + fact receipts
CUSTOMERS_DB_PATH = Path(os.environ.get("PROVENANCE_CUSTOMERS_DB_PATH",
                                        str(DATA_DIR / "customers.sqlite")))  # funnel timeline + facts
USERS_PATH = DATA_DIR / "users.jsonl"

for _d in (DATA_DIR, SOURCES_DIR, CLAIMS_DIR, LEDGERS_DIR, RUNS_DIR, CACHE_DIR, OBSERVE_DIR, RULES_DIR,
           DB_PATH.parent, PROFILES_DB_PATH.parent, CUSTOMERS_DB_PATH.parent):
    _d.mkdir(parents=True, exist_ok=True)

# ---- global seed -----------------------------------------------------------
SEED = int(os.environ.get("PROVENANCE_SEED", "1729"))

# ---- inference profile -----------------------------------------------------
# "deterministic" (default): lexical/numeric NLI + heuristic judge + rules. Offline,
#   reproducible, no key — what the test suite and a $0 demo run on.
# "rich": adds DeBERTa NLI and live Ollama/Claude judges (cached). For a credibility
#   pass that populates the cache; the demo then replays from cache.
INFERENCE_PROFILE = os.environ.get("PROVENANCE_PROFILE", "deterministic").lower()

# Ollama (local, free) — used as cross-family judges in the rich profile.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
# two genuinely different families for ensemble diversity (small + fast):
OLLAMA_JUDGE_MODELS = os.environ.get(
    "OLLAMA_JUDGE_MODELS", "qwen3.5:4b,nemotron-3-nano:4b"
).split(",")

# Claude API — auto-enabled only when a key is present AND profile is rich.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_JUDGE_MODEL = os.environ.get("CLAUDE_JUDGE_MODEL", "claude-haiku-4-5-20251001")

# DeBERTa NLI — auto-enabled only when transformers+torch+model are importable AND rich.
DEBERTA_MODEL = os.environ.get("DEBERTA_MODEL", "microsoft/deberta-v3-large-mnli")


def use_rich() -> bool:
    return INFERENCE_PROFILE == "rich"


def claude_available() -> bool:
    return use_rich() and bool(ANTHROPIC_API_KEY)


# ---- enrichment mode -------------------------------------------------------
# "synthetic" (default): all connectors are simulated + deterministic — offline, $0,
#   byte-identical. "live": the one free real connector set (DNS/MX on the email domain +
#   public news RSS) is used; responses are cached so replays stay deterministic. Real
#   connectors send only the company domain/name (no PII to third parties) and cost $0.
ENRICH_MODE = os.environ.get("PROVENANCE_ENRICH", "synthetic").lower()


def enrich_live() -> bool:
    return ENRICH_MODE == "live"


# ---- Google OAuth (the /google demo) ---------------------------------------
# When both are set (a Google Cloud OAuth client + redirect to <base>/google/callback),
# the page does a REAL "Sign in with Google" and fills the top tier with the actual profile.
# Otherwise it runs in demo mode (synthetic, clearly labeled) — offline + safe.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")


def google_oauth_ready() -> bool:
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
