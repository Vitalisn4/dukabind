#!/usr/bin/env bash
# Start local llama-server on 127.0.0.1 only (SECURITY C5 / Phase 5).
# Requires: built llama.cpp + downloaded GGUF via ./download_model.sh

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="$HERE/third_party/llama.cpp/build"
BIN=""
for candidate in \
  "$BUILD/bin/llama-server" \
  "$BUILD/llama-server"
do
  if [[ -x "$candidate" ]]; then
    BIN="$candidate"
    break
  fi
done

MODEL="$HERE/model/qwen2.5-1.5b-instruct-q4_k_m.gguf"
HOST="127.0.0.1"
PORT="${PORT:-8080}"
# Conservative context for 8 GB target machines (Phase 6).
CTX="${CTX:-2048}"
THREADS="${THREADS:-$(nproc)}"

if [[ -z "$BIN" ]]; then
  echo "error: llama-server binary not found. Build llama.cpp first." >&2
  echo "  cmake -S third_party/llama.cpp -B third_party/llama.cpp/build -DCMAKE_BUILD_TYPE=Release" >&2
  echo "  cmake --build third_party/llama.cpp/build -j\$(nproc)" >&2
  exit 1
fi

if [[ ! -f "$MODEL" ]]; then
  echo "error: model missing at $MODEL" >&2
  echo "  run: ./download_model.sh" >&2
  exit 1
fi

echo "starting llama-server"
echo "  bin:     $BIN"
echo "  model:   $MODEL"
echo "  bind:    $HOST:$PORT"
echo "  ctx:     $CTX"
echo "  threads: $THREADS"

exec "$BIN" \
  --model "$MODEL" \
  --host "$HOST" \
  --port "$PORT" \
  --ctx-size "$CTX" \
  --threads "$THREADS" \
  --n-gpu-layers 0
