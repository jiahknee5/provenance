#!/usr/bin/env bash
# Deploy provenance demo to Railway (Dockerfile + railway.json).
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v railway >/dev/null 2>&1; then
  echo "railway CLI not found — install: npm i -g @railway/cli" >&2
  exit 1
fi

echo "Running test suite before deploy…"
PYTHONPATH=. uv run pytest tests/test_api_costs.py tests/test_brain_simulator.py tests/test_gauntlet_site.py tests/test_hero_image.py \
  tests/test_planet_site.py tests/test_planet_hero_image.py tests/test_planet_motion.py -q

echo "Deploying to Railway…"
railway up --detach

echo "Done. Check Railway dashboard for deploy URL."
