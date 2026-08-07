#!/usr/bin/env bash
# Start local llama-server bound to 127.0.0.1 only (control C5).
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
# Shipped default frozen at M5 (2026-08-07): THREADS=2/CTX=1024 is the only
# config with a measured 10-min thermal soak PASS (<85 °C) on the build laptop
# (peak 84.0 °C, 0/68 ≥85 °C, 2026-08-06). Risk gate: prefer thermal safety
# over TPS. THREADS=3/CTX=2048 (peak tg_tps 17.94) stays reachable via env
# override for eval-machine benchmarking.
CTX="${CTX:-1024}"
THREADS="${THREADS:-2}"

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
