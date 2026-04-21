#!/bin/bash
set -e

echo "[pwm-explorer] Starting indexer..."
cd /app
python -m indexer.main &
INDEXER_PID=$!

echo "[pwm-explorer] Starting API on :8000..."
uvicorn api.main:app --host 127.0.0.1 --port 8000 --log-level warning &
API_PID=$!

# Wait for API to be ready before starting frontend
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
        echo "[pwm-explorer] API ready."
        break
    fi
    sleep 1
done

echo "[pwm-explorer] Starting frontend on :${PORT:-3000}..."
cd /app/frontend
exec node server.js
