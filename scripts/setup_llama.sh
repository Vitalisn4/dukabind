#!/usr/bin/env bash
# Clone + build upstream llama.cpp — the only inference runtime ADTC permits.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$HERE/third_party/llama.cpp"

mkdir -p "$HERE/third_party"

if [[ ! -d "$SRC/.git" ]]; then
  echo "cloning ggml-org/llama.cpp …"
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$SRC"
else
  echo "llama.cpp already present at $SRC"
fi

cmake -S "$SRC" -B "$SRC/build" -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON
cmake --build "$SRC/build" -j"$(nproc)"

echo "OK: $SRC/build/bin/llama-server"
echo "Next: ./download_model.sh && bash scripts/start_llama_server.sh"
