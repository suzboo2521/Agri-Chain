#!/usr/bin/env bash
# Start AgriChain v2 (backend :8000 + frontend :5173)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"
if [ -x "$ROOT/.venv/bin/python" ]; then
  PY="$ROOT/.venv/bin/python"
else
  PY=python3
fi
echo "Backend → http://127.0.0.1:8000/docs"
"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
cd "$ROOT/frontend"
echo "Frontend → http://127.0.0.1:5173"
npm run dev
