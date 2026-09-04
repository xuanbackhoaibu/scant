#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_BASE="${API_BASE:-http://127.0.0.1:8050/api/v1}"
DEMO_EMAIL="${DEMO_EMAIL:-demo@aireportstudio.pro}"
DEMO_PASSWORD="${DEMO_PASSWORD:-DemoVIP123!}"
DEMO_PROJECT_NAME="${DEMO_PROJECT_NAME:-Xây dựng Website Thương mại Điện tử ASP.NET Core MVC}"
DEMO_REPORT_TITLE="${DEMO_REPORT_TITLE:-Báo cáo Đồ án: Xây dựng Website Thương mại Điện tử ASP.NET Core MVC}"

json_value() {
  python3 -c "import json, sys; print(json.load(sys.stdin)$1)"
}

json_any_equals() {
  python3 -c "import json, sys; items=json.load(sys.stdin); key=sys.argv[1]; expected=sys.argv[2]; print(any(item.get(key) == expected for item in items))" "$1" "$2"
}

echo "Checking API health: $API_BASE/health"
health_body="$(curl -fsS "$API_BASE/health")"
health_status="$(printf '%s' "$health_body" | json_value "['status']")"
if [[ "$health_status" != "healthy" ]]; then
  echo "API health is not healthy: $health_body"
  exit 1
fi
echo "API healthy"

if [[ "${SKIP_SEED:-0}" != "1" ]]; then
  echo "Seeding demo data"
  PYTHONPATH="$ROOT_DIR/apps/api" "$ROOT_DIR/apps/api/venv/bin/python" "$ROOT_DIR/apps/api/app/seed_sample.py" >/dev/null
fi

echo "Logging in demo user: $DEMO_EMAIL"
login_body="$(
  curl -fsS -X POST "$API_BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$DEMO_EMAIL\",\"password\":\"$DEMO_PASSWORD\"}"
)"
token="$(printf '%s' "$login_body" | json_value "['access_token']")"
user_email="$(printf '%s' "$login_body" | json_value "['user']['email']")"
if [[ -z "$token" || "$user_email" != "$DEMO_EMAIL" ]]; then
  echo "Demo login failed: $login_body"
  exit 1
fi
echo "Demo login OK"

echo "Checking demo project"
projects_body="$(curl -fsS "$API_BASE/projects" -H "Authorization: Bearer $token")"
has_project="$(printf '%s' "$projects_body" | json_any_equals "name" "$DEMO_PROJECT_NAME")"
if [[ "$has_project" != "True" ]]; then
  echo "Demo project not found in API response"
  echo "$projects_body"
  exit 1
fi
echo "Demo project OK"

echo "Checking demo report"
reports_body="$(curl -fsS "$API_BASE/reports" -H "Authorization: Bearer $token")"
has_report="$(printf '%s' "$reports_body" | json_any_equals "title" "$DEMO_REPORT_TITLE")"
if [[ "$has_report" != "True" ]]; then
  echo "Demo report not found in API response"
  echo "$reports_body"
  exit 1
fi
echo "Demo report OK"

echo "Demo flow healthy"
