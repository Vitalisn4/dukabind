#!/usr/bin/env bash
# One-shot narration smoke (starts llama-server, asks, stops).
# Prefer keeping the server up in your own terminal for development:
#   bash scripts/start_llama_server.sh

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

# shellcheck disable=SC1091
source .venv/bin/activate

LOG_FILE="$(mktemp "${TMPDIR:-/tmp}/dukabind-llama-server.XXXXXX.log")"
bash scripts/start_llama_server.sh > "$LOG_FILE" 2>&1 &
SPID=$!
cleanup() { kill "$SPID" 2>/dev/null || true; rm -f "$LOG_FILE"; }
trap cleanup EXIT

ready=0
for i in $(seq 1 90); do
  if curl -sf -m 1 http://127.0.0.1:8080/health >/dev/null; then
    echo "server ready (${i}s)"
    ready=1
    break
  fi
  sleep 1
  if ! kill -0 "$SPID" 2>/dev/null; then
    echo "server died"
    tail -40 "$LOG_FILE" || true
    exit 1
  fi
done

if [[ "$ready" -ne 1 ]]; then
  echo "error: llama-server did not become healthy within 90s"
  tail -40 "$LOG_FILE" || true
  exit 1
fi

QUESTION="${*:-Can I give Amina three crates on credit?}"
PYTHONPATH=. python -m app.narrate_cli "$QUESTION"
