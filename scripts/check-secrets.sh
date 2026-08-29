#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

SECRET_PATTERN='(GOCSPX-[A-Za-z0-9_-]+|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|ghp_[0-9A-Za-z]{20,}|xox[baprs]-[0-9A-Za-z-]+|AKIA[0-9A-Z]{16}|AQ\.Ab8RN6LFrZExOJXX[0-9A-Za-z_-]+|OPENAI_API_KEY="?sk-|GEMINI_API_KEY="?AQ\.|GOOGLE_CLIENT_SECRET="?GOCSPX-)'

fail() {
  echo "Secret check failed: $1" >&2
  exit 1
}

tracked_env_files="$(git ls-files '.env*' | grep -v '^.env.example$' || true)"
if [ -n "$tracked_env_files" ]; then
  echo "$tracked_env_files" >&2
  fail "environment files are tracked. Keep only .env.example in git."
fi

tracked_generated_files="$(
  git ls-files \
    'apps/storage/**' \
    'storage/**' \
    '*.db' \
    '*.pyc' \
    '*.tsbuildinfo' |
    grep -v '/.gitkeep$' || true
)"
if [ -n "$tracked_generated_files" ]; then
  echo "$tracked_generated_files" >&2
  fail "generated storage, database, cache, or build metadata files are tracked."
fi

if git grep -nI -E "$SECRET_PATTERN" -- . ':!apps/api/tests/**' ':!tests/**'; then
  fail "possible secret found in tracked files."
fi

if git diff --cached -U0 -- . ':!apps/api/tests/**' ':!tests/**' | grep -E "$SECRET_PATTERN"; then
  fail "possible secret found in staged diff."
fi

echo "Secret check passed: no tracked env/generated files or known key patterns found."
