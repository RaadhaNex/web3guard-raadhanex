#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Starting Web3Guard AI by RAADHANEX local stack"
(
  cd "$ROOT/backend"
  [ -f .env ] || cp .env.example .env
  [ -d .venv ] || python3.12 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!
(
  cd "$ROOT/frontend"
  [ -f .env.local ] || cp .env.local.example .env.local
  npm install
  npm run dev
) &
FRONTEND_PID=$!
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT
wait
