#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/apps/api"
WEB_DIR="$ROOT_DIR/apps/web"
API_PORT="${API_PORT:-8050}"
WEB_PORT="${WEB_PORT:-3050}"
API_HOST="${API_HOST:-127.0.0.1}"

if [[ ! -x "$API_DIR/venv/bin/uvicorn" ]]; then
  echo "Missing API dependency: $API_DIR/venv/bin/uvicorn"
  echo "Run: cd apps/api && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

if [[ ! -d "$WEB_DIR/node_modules" ]]; then
  echo "Missing web dependencies: $WEB_DIR/node_modules"
  echo "Run: cd apps/web && npm install"
  exit 1
fi

api_port_owner="$(lsof -nP -iTCP:"$API_PORT" -sTCP:LISTEN 2>/dev/null || true)"
web_port_owner="$(lsof -nP -iTCP:"$WEB_PORT" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$api_port_owner" || -n "$web_port_owner" ]]; then
  if [[ -n "$api_port_owner" ]]; then
    echo "API port $API_PORT is already in use:"
    echo "$api_port_owner"
  fi
  if [[ -n "$web_port_owner" ]]; then
    echo "Web port $WEB_PORT is already in use:"
    echo "$web_port_owner"
  fi
  if [[ -n "$api_port_owner" && -n "$web_port_owner" ]]; then
    echo "Both local ports are already occupied. If this is AI Report Studio, open http://localhost:$WEB_PORT or run: bash scripts/smoke-local.sh"
    exit 0
  fi
  echo "Stop the process using the occupied port, or set API_PORT/WEB_PORT before running this script."
  exit 1
fi

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "$API_PID" 2>/dev/null || true
  fi

  if [[ -n "${WEB_PID:-}" ]]; then
    kill "$WEB_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting API: http://$API_HOST:$API_PORT"
(
  cd "$API_DIR"
  if [[ "${API_RELOAD:-0}" == "1" ]]; then
    venv/bin/uvicorn app.main:app --host "$API_HOST" --port "$API_PORT" --reload
  else
    venv/bin/uvicorn app.main:app --host "$API_HOST" --port "$API_PORT"
  fi
) &
API_PID=$!

echo "Starting web: http://localhost:$WEB_PORT"
(
  cd "$WEB_DIR"
  NEXT_PUBLIC_API_URL="http://$API_HOST:$API_PORT/api/v1" ./node_modules/.bin/next dev -p "$WEB_PORT"
) &
WEB_PID=$!

echo
echo "AI Report Studio local dev is starting."
echo "Web:  http://localhost:$WEB_PORT"
echo "API:  http://$API_HOST:$API_PORT/docs"
echo "Stop: Ctrl+C"
echo

while kill -0 "$API_PID" 2>/dev/null && kill -0 "$WEB_PID" 2>/dev/null; do
  sleep 1
done
