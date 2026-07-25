#!/usr/bin/env bash
# One-shot narration smoke (starts llama-server, asks, stops).
# Prefer keeping the server up in your own terminal for development:
#   bash scripts/start_llama_server.sh

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

# shellcheck disable=SC1091
source .venv/bin/activate

bash scripts/start_llama_server.sh > /tmp/dukabind-llama-server.log 2>&1 &
SPID=$!
cleanup() { kill "$SPID" 2>/dev/null || true; }
trap cleanup EXIT

for i in $(seq 1 90); do
  if curl -sf -m 1 http://127.0.0.1:8080/health >/dev/null; then
    echo "server ready (${i}s)"
    break
  fi
  sleep 1
  if ! kill -0 "$SPID" 2>/dev/null; then
    echo "server died"; tail -40 /tmp/dukabind-llama-server.log; exit 1
  fi
done

QUESTION="${*:-Can I give Amina three crates on credit?}"
PYTHONPATH=. python -m app.narrate_cli "$QUESTION"
