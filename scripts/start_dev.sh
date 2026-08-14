#!/bin/bash
# Запуск локального dev-окружения: redis + backend + frontend.
# PID процессов сохраняются в /tmp/stroyzakup_dev.pids
set -euo pipefail

PIDS_FILE=/tmp/stroyzakup_dev.pids
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

> "$PIDS_FILE"

echo "=== Stroyzakup dev starter ==="

# Redis
if redis-cli ping >/dev/null 2>&1; then
    echo "Redis:      already running"
else
    redis-server --daemonize yes
    sleep 1
    echo "Redis:      started (daemon)"
fi

# Backend
if curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/ 2>/dev/null | grep -qE '401|200'; then
    echo "Backend:    already running on :8000"
else
    if [ ! -x "$BACKEND_DIR/.venv/bin/python" ]; then
        echo "Backend:    ERROR - .venv/bin/python not found at $BACKEND_DIR/.venv" >&2
        exit 1
    fi
    (cd "$BACKEND_DIR" && .venv/bin/python manage.py runserver 0.0.0.0:8000) &
    echo $! >> "$PIDS_FILE"
    echo "Backend:    started on :8000"
fi

# Frontend
if curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/ 2>/dev/null | grep -q '200'; then
    echo "Frontend:   already running on :3000"
else
    if [ ! -x "$FRONTEND_DIR/node_modules/.bin/next" ]; then
        echo "Frontend:   ERROR - next not found in $FRONTEND_DIR/node_modules/.bin" >&2
        exit 1
    fi
    (cd "$FRONTEND_DIR" && node node_modules/.bin/next start -p 3000 -H 0.0.0.0) &
    echo $! >> "$PIDS_FILE"
    echo "Frontend:   started on :3000"
fi

echo ""
echo "URLs:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000/api/"
echo "  Admin:     http://localhost:8000/admin/"
echo "PIDs saved to: $PIDS_FILE"