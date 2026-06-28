#!/usr/bin/env bash
set -euo pipefail

HOST="${VPS_HOST:?VPS_HOST must be set}"
USER="${VPS_USER:?VPS_USER must be set}"
PORT="${VPS_PORT:-22}"
APP_ROOT="${APP_ROOT:-/opt/provenance-pm}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-provenance-pm}"
ARCHIVE_DIR="$(mktemp -d)"
ARCHIVE="$ARCHIVE_DIR/provenance-pm-source.tar.gz"

cleanup() {
  rm -rf "$ARCHIVE_DIR"
}
trap cleanup EXIT

tar \
  --exclude='./.git' \
  --exclude='./.agents' \
  --exclude='./.claude' \
  --exclude='./.codex' \
  --exclude='./.env' \
  --exclude='./.env.local' \
  --exclude='./.env.production' \
  --exclude='./.venv' \
  --exclude='./.pytest_cache' \
  --exclude='./__pycache__' \
  --exclude='./*/__pycache__' \
  --exclude='./*/*/__pycache__' \
  --exclude='./data' \
  -czf "$ARCHIVE" .

scp -P "$PORT" "$ARCHIVE" "$USER@$HOST:/tmp/provenance-pm-source.tar.gz"

ssh -p "$PORT" "$USER@$HOST" "APP_DIR='$APP_ROOT' COMPOSE_PROJECT_NAME='$COMPOSE_PROJECT_NAME' bash -s" <<'REMOTE'
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/provenance-pm}"
APP_SOURCE="$APP_DIR/app"
RELEASE_DIR="$APP_DIR/app.release"
PREVIOUS_DIR="$APP_DIR/app.previous"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-provenance-pm}"
COMPOSE=(docker compose --project-name "$COMPOSE_PROJECT_NAME" --env-file "$APP_DIR/.env" -f docker-compose.production.yml)

test -f "$APP_DIR/.env"
mkdir -p "$APP_DIR/backups" "$APP_DIR/data"

rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"
tar -xzf /tmp/provenance-pm-source.tar.gz -C "$RELEASE_DIR"
rm -f /tmp/provenance-pm-source.tar.gz

rm -rf "$PREVIOUS_DIR"
if [ -d "$APP_SOURCE" ]; then
  mv "$APP_SOURCE" "$PREVIOUS_DIR"
fi
mv "$RELEASE_DIR" "$APP_SOURCE"

cd "$APP_SOURCE"
"${COMPOSE[@]}" build web
"${COMPOSE[@]}" rm -sf web
"${COMPOSE[@]}" up -d web

web_container="$("${COMPOSE[@]}" ps -q web)"
if [ -z "$web_container" ]; then
  echo "Could not find the web container after compose up."
  "${COMPOSE[@]}" ps
  exit 1
fi

web_health=""
for attempt in $(seq 1 60); do
  web_health="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$web_container" 2>/dev/null || true)"

  if [ "$web_health" = "healthy" ] || [ "$web_health" = "running" ]; then
    break
  fi

  if [ "$web_health" = "unhealthy" ] || [ "$web_health" = "exited" ] || [ "$web_health" = "dead" ]; then
    echo "Web container entered bad state: $web_health"
    "${COMPOSE[@]}" logs --tail=160 web
    exit 1
  fi

  sleep 2
done

if [ "$web_health" != "healthy" ] && [ "$web_health" != "running" ]; then
  echo "Web container did not become healthy. Last state: ${web_health:-unknown}"
  "${COMPOSE[@]}" ps
  "${COMPOSE[@]}" logs --tail=160 web
  exit 1
fi

docker exec "$web_container" python -c "import os, urllib.request; port=os.environ.get('PORT','8000'); print(urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=5).read().decode())"
"${COMPOSE[@]}" ps
REMOTE
