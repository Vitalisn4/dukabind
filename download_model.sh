#!/usr/bin/env bash
# Download DukaBind GGUF weights from the official Qwen repo. Idempotent.
# Model choice is justified in docs/DESIGN_DECISIONS.md (D3).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$HERE/model"
MODEL_FILE="$MODEL_DIR/qwen2.5-1.5b-instruct-q4_k_m.gguf"

MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"

# Pinned on 2026-07-25 for supply-chain integrity (control C7); override to re-pin.
EXPECTED_SHA256="${EXPECTED_SHA256:-6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e}"

mkdir -p "$MODEL_DIR"

if [[ -f "$MODEL_FILE" ]]; then
  echo "model already present at $MODEL_FILE — skipping download"
  if [[ -n "$EXPECTED_SHA256" ]]; then
    echo "$EXPECTED_SHA256  $MODEL_FILE" | sha256sum -c -
  fi
  exit 0
fi

echo "downloading $MODEL_URL → $MODEL_FILE (~1.1 GB)…"

if command -v curl > /dev/null 2>&1; then
  curl -L --fail --progress-bar -o "$MODEL_FILE.partial" "$MODEL_URL"
elif command -v wget > /dev/null 2>&1; then
  wget --show-progress -O "$MODEL_FILE.partial" "$MODEL_URL"
else
  echo "error: neither curl nor wget found" >&2
  exit 1
fi

mv "$MODEL_FILE.partial" "$MODEL_FILE"

if [[ -n "$EXPECTED_SHA256" ]]; then
  echo "$EXPECTED_SHA256  $MODEL_FILE" | sha256sum -c -
fi

echo "done: $MODEL_FILE"
echo "tip: compute digest with: sha256sum \"$MODEL_FILE\""
echo "     then set EXPECTED_SHA256=... for supply-chain checks"
