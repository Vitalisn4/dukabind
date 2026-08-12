#!/usr/bin/env bash
# 8 GB-class proof: run llama-server + narrated asks under a cgroup memory cap
# (default 7.5 GB) and report the measured peak + headroom. Requires systemd
# user session + cgroup v2 (memory.max/memory.peak).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CAP_GB="${CAP_GB:-7.5}"

if [[ ! "$CAP_GB" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "error: CAP_GB must be a number (e.g. 7.5)" >&2
  exit 1
fi

if [[ "${DUKABIND_CAPPED:-}" != "1" ]]; then
  CAP_BYTES="$(python3 -c "print(int($CAP_GB * 1024**3))")"
  exec systemd-run --user --scope -p "MemoryMax=$CAP_BYTES" \
    --setenv=DUKABIND_CAPPED=1 bash "$0" "$@"
fi

# ---- inside the capped scope ----
BUILD="$HERE/third_party/llama.cpp/build"
BIN=""
for candidate in "$BUILD/bin/llama-server" "$BUILD/llama-server"; do
  if [[ -x "$candidate" ]]; then
    BIN="$candidate"
    break
  fi
done
MODEL="$HERE/model/qwen2.5-1.5b-instruct-q4_k_m.gguf"
PORT="${PORT:-8080}"
CTX="${CTX:-1024}"
THREADS="${THREADS:-2}"

if [[ -z "$BIN" || ! -f "$MODEL" ]]; then
  echo "error: llama-server build or model missing" >&2
  exit 1
fi

CG="$(cut -d: -f3 /proc/self/cgroup)"
CGPATH="/sys/fs/cgroup$CG"
if [[ ! -r "$CGPATH/memory.max" ]]; then
  echo "error: cgroup v2 memory.max not readable" >&2
  exit 1
fi

LOG="$(mktemp /tmp/ram_capped_server.XXXXXX.log)"
SAMP="$(mktemp /tmp/ram_capped_samp.XXXXXX)"
cleanup() {
  kill "${SPID:-}" 2>/dev/null || true
  wait "${SPID:-}" 2>/dev/null || true
  rm -f "$LOG" "$SAMP"
}
trap cleanup EXIT

"$BIN" --model "$MODEL" --host 127.0.0.1 --port "$PORT" \
  --ctx-size "$CTX" --threads "$THREADS" --n-gpu-layers 0 >"$LOG" 2>&1 &
SPID=$!

for _ in $(seq 1 120); do
  if curl -sf -m 1 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$SPID" 2>/dev/null; then
    echo "error: llama-server died at startup:" >&2
    tail -30 "$LOG" >&2
    exit 1
  fi
  sleep 1
done
if ! curl -sf -m 1 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
  echo "error: server never became healthy" >&2
  exit 1
fi

# Sample cgroup current + llama-server VmRSS every 0.5 s (memory.peak is the
# authoritative cgroup max; the sampler is the VmRSS cross-check).
(
  while kill -0 "$SPID" 2>/dev/null; do
    cat "$CGPATH/memory.current" 2>/dev/null || echo 0
    awk '/VmRSS/ {print $2}' "/proc/$SPID/status" 2>/dev/null || echo 0
    sleep 0.5
  done
) >"$SAMP" &
SAMPPID=$!

cd "$HERE"
export PYTHONPATH="$HERE"
echo "== narrated asks =="
ask_fail=0
run_ask() {
  local q="$1" validator="$2" out
  out="$("$HERE/.venv/bin/python" -m app.narrate_cli "$q" 2>&1)" || {
    echo "  error: app.narrate_cli failed for: $q" >&2
    printf '%s\n' "$out" | head -20 >&2
    ask_fail=1
    return
  }
  if ! printf '%s' "$out" | python3 -c "$validator"; then
    echo "  error: unexpected binder result for: $q" >&2
    printf '%s\n' "$out" | head -20 >&2
    ask_fail=1
    return
  fi
  printf '%s' "$out" | python3 -c '
import json, sys
d = json.load(sys.stdin)
print("  approved=%s narrated=%s source=%s | %s" % (
    d.get("approved"), d.get("narrated"), d.get("source"), d.get("message")))'
}

run_ask "Can I give Marie-Claire three crates on credit?" '
import json, sys
d = json.load(sys.stdin)
sys.exit(0 if d.get("ok") is True and d.get("approved") is False and "No" in d.get("message", "") else 1)'
run_ask "How many soda crates on hand?" '
import json, sys
d = json.load(sys.stdin)
sys.exit(0 if d.get("ok") is True and "on_hand=14" in d.get("message", "") else 1)'
run_ask "How much do we owe SOCA Distribution Douala?" '
import json, sys
d = json.load(sys.stdin)
sys.exit(0 if d.get("ok") is False and d.get("refuse_reason") == "balance_owed_null" else 1)'

if [[ "$ask_fail" -ne 0 ]]; then
  echo "error: narrated-ask validation failed; proof invalid" >&2
  exit 1
fi

kill "$SPID" 2>/dev/null || true
wait "$SPID" 2>/dev/null || true
wait "$SAMPPID" 2>/dev/null || true

echo "== memory report =="
python3 - "$CGPATH" "$SAMP" "$CAP_GB" <<'PY'
import sys

cg, samp_path, cap_gb = sys.argv[1], sys.argv[2], float(sys.argv[3])
cap = int(cap_gb * 1024**3)


def gi(b: int) -> str:
    return f"{b / 1024**3:.2f} GiB"


with open(f"{cg}/memory.max") as f:
    max_b = int(f.read().strip())
peak_b = None
try:
    with open(f"{cg}/memory.peak") as f:
        peak_b = int(f.read().strip())
except OSError:
    pass

rows = [int(l) for l in open(samp_path) if l.strip()]
samp_max = max(rows[0::2]) if len(rows) > 1 else 0
rss_max = max(rows[1::2]) if len(rows) > 1 else 0
if peak_b is None:
    peak_b = samp_max

print(f"Cap (memory.max)          : {gi(max_b)} ({max_b} B)")
if max_b != cap:
    print("  WARNING: memory.max != requested cap")
print(f"Cgroup peak (memory.peak) : {gi(peak_b)} ({peak_b} B)")
if peak_b == samp_max and peak_b:
    print("  (memory.peak missing; used sampled memory.current max)")
print(f"  sampled memory.current  : {gi(samp_max)} (0.5 s interval)")
print(f"llama-server peak VmRSS   : {gi(rss_max * 1024)} ({rss_max} KiB)")
print(f"Headroom vs {gi(cap)} cap     : {gi(cap - peak_b)}")
print(f"Headroom vs 7.0 GiB DQ    : {gi(7 * 1024**3 - peak_b)}")
print(f"Headroom vs 5.5 GiB self  : {gi(int(5.5 * 1024**3) - peak_b)}")
PY
