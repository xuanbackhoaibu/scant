#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8050/api/v1/health}"
WEB_URL="${WEB_URL:-http://localhost:3050}"

echo "Checking API: $API_URL"
api_body="$(curl -fsS "$API_URL")"
if [[ "$api_body" != *'"status":"healthy"'* ]]; then
  echo "API health response did not contain status=healthy"
  echo "$api_body"
  exit 1
fi
echo "API healthy"

echo "Checking web: $WEB_URL"
web_status="$(curl -fsS -o /dev/null -w "%{http_code}" "$WEB_URL")"
if [[ "$web_status" != "200" && "$web_status" != "307" && "$web_status" != "308" ]]; then
  echo "Web returned unexpected HTTP status: $web_status"
  exit 1
fi
echo "Web reachable: HTTP $web_status"
