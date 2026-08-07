#!/usr/bin/env bash
# Sustained generation thermal soak (Phase 6 §2.4 / M2 Day 3).
#
# Starts llama-server with frozen THREADS/CTX defaults, runs repeated
# completions, samples package/core temp every SAMPLE_SECS, writes a CSV log.
#
# Usage:
#   bash scripts/thermal_soak.sh              # default 10 minutes
#   SOAK_MINUTES=3 bash scripts/thermal_soak.sh

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

SOAK_MINUTES="${SOAK_MINUTES:-10}"
SAMPLE_SECS="${SAMPLE_SECS:-5}"
PORT="${PORT:-8080}"
BASE_URL="http://127.0.0.1:${PORT}"
export THREADS="${THREADS:-2}"
export CTX="${CTX:-1024}"
export PORT

if [[ ! -x "$HERE/third_party/llama.cpp/build/bin/llama-server" ]]; then
  echo "error: llama-server missing — run bash scripts/setup_llama.sh" >&2
  exit 1
fi
if [[ ! -f "$HERE/model/qwen2.5-1.5b-instruct-q4_k_m.gguf" ]]; then
  echo "error: GGUF missing — run ./download_model.sh" >&2
  exit 1
fi

# Measurement integrity: the soak must be a single-server run. Refuse to start
# if another llama-server is alive or the port is already bound — a concurrent
# server skews temps and makes the verdict meaningless.
if pgrep -f 'llama-serve[r] --model' >/dev/null 2>&1; then
  echo "error: another llama-server is already running — stop it first (soak must be single-server)" >&2
  exit 1
fi
if command -v ss >/dev/null 2>&1 && ss -tln 2>/dev/null | grep -q ":$PORT "; then
  echo "error: port $PORT is already in use — free it first" >&2
  exit 1
fi

mkdir -p benchmarks/raw
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="benchmarks/raw/thermal_soak_${STAMP}.csv"
SERVER_LOG="$(mktemp "${TMPDIR:-/tmp}/dukabind-soak-server.XXXXXX.log")"
REQ_JSON="$(mktemp "${TMPDIR:-/tmp}/dukabind-soak-req.XXXXXX.json")"

python - "$REQ_JSON" <<'PY'
import json, sys
path = sys.argv[1]
payload = {
    "model": "local",
    "messages": [
        {
            "role": "user",
            "content": (
                "LEDGER_JSON is authoritative. Customer Marie-Claire Fotso has "
                "credit_limit=8000 XAF and outstanding=6250 XAF. unit_price=720. "
                "Staff ask: Can I give Marie-Claire three crates on credit? "
                "Answer using only these numbers."
            ),
        }
    ],
    "max_tokens": 48,
    "temperature": 0,
}
with open(path, "w", encoding="utf-8") as fh:
    json.dump(payload, fh)
PY

read_package_temp() {
  python - <<'PY'
import sys
from pathlib import Path
best = None
for p in Path("/sys/class/hwmon").glob("*/temp*_input"):
    try:
        label = (p.parent / (p.name.replace("_input", "_label"))).read_text(encoding="utf-8").strip().lower()
    except OSError:
        label = ""
    try:
        val = int(p.read_text(encoding="utf-8").strip()) / 1000.0
    except (OSError, ValueError):
        continue
    if "package" in label or label in {"tctl", "tdie"}:
        best = val if best is None else max(best, val)
    elif "core" in label:
        best = val if best is None else max(best, val)
if best is None:
    vals = []
    for p in Path("/sys/class/hwmon").glob("*/temp*_input"):
        try:
            vals.append(int(p.read_text(encoding="utf-8").strip()) / 1000.0)
        except (OSError, ValueError):
            pass
    best = max(vals) if vals else None
if best is None:
    print("error: no usable temperature sensor under /sys/class/hwmon", file=sys.stderr)
    raise SystemExit(3)
print(f"{best:.1f}")
PY
}

# A soak without a usable temperature reading cannot produce a verdict.
if ! read_package_temp >/dev/null 2>&1; then
  echo "error: no usable temperature sensor under /sys/class/hwmon — cannot run thermal soak" >&2
  exit 1
fi

cleanup() {
  local code=$?
  if [[ -n "${SPID:-}" ]]; then
    kill "$SPID" 2>/dev/null || true
    wait "$SPID" 2>/dev/null || true
  fi
  # Keep server log on failure for diagnosis; always drop the request json.
  if [[ "$code" -eq 0 ]]; then
    rm -f "$SERVER_LOG"
  else
    echo "server log kept: $SERVER_LOG" >&2
  fi
  rm -f "$REQ_JSON"
}
trap cleanup EXIT

echo "== DukaBind thermal_soak =="
echo "minutes: $SOAK_MINUTES  sample: ${SAMPLE_SECS}s  threads: $THREADS  ctx: $CTX"
echo "log: $LOG"
echo "started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Line-buffered logs so a crash mid-load still leaves a usable trail.
stdbuf -oL -eL bash scripts/start_llama_server.sh >"$SERVER_LOG" 2>&1 &
SPID=$!

ready=0
for i in $(seq 1 180); do
  if curl -sf -m 1 "$BASE_URL/health" >/dev/null 2>&1; then
    echo "server ready (${i}s)"
    ready=1
    break
  fi
  # Give the shell a moment to exec into llama-server before declaring death.
  if (( i > 3 )) && ! kill -0 "$SPID" 2>/dev/null; then
    echo "error: llama-server died during startup (pid=$SPID)" >&2
    tail -80 "$SERVER_LOG" >&2 || true
    exit 1
  fi
  sleep 1
done
if [[ "$ready" -ne 1 ]]; then
  echo "error: llama-server not healthy within 180s" >&2
  tail -80 "$SERVER_LOG" >&2 || true
  exit 1
fi

echo "ts_utc,elapsed_s,temp_c,http_ok" >"$LOG"
END=$((SECONDS + SOAK_MINUTES * 60))
fail_hot=0
contaminated=0

while (( SECONDS < END )); do
  elapsed=$SECONDS
  http_ok=0
  if curl -sf -m 120 "$BASE_URL/v1/chat/completions" \
    -H 'Content-Type: application/json' \
    --data-binary @"$REQ_JSON" >/dev/null; then
    http_ok=1
  fi
  temp="$(read_package_temp)"
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "$ts,$elapsed,$temp,$http_ok" >>"$LOG"
  echo "sample +${elapsed}s  temp=${temp}C  http_ok=${http_ok}"
  if python -c "import sys; sys.exit(0 if float('$temp') >= 85 else 1)"; then
    fail_hot=1
  fi
  # Flag concurrent servers so the verdict is never claimed on a dirty run.
  if (( $(pgrep -fc 'llama-serve[r] --model' 2>/dev/null || echo 0) > 1 )); then
    contaminated=1
    echo "WARNING: another llama-server detected — this run is contaminated" >&2
  fi
  sleep "$SAMPLE_SECS"
done

python - "$LOG" "$fail_hot" "$contaminated" <<'PY'
import csv, math, sys
from pathlib import Path

path = Path(sys.argv[1])
fail_hot = len(sys.argv) > 2 and sys.argv[2] == "1"
contaminated = len(sys.argv) > 3 and sys.argv[3] == "1"
rows = list(csv.DictReader(path.open(encoding="utf-8")))
temps = [float(r["temp_c"]) for r in rows if r.get("temp_c")]
https = [int(r["http_ok"]) for r in rows if r.get("http_ok") != ""]
peak = max(temps) if temps else float("nan")
mean = sum(temps) / len(temps) if temps else float("nan")
ok_rate = (sum(https) / len(https) * 100) if https else 0.0
if any(not math.isfinite(t) for t in temps):
    print("RESULT: FAIL — non-finite temperature values in log (sensor unavailable?).")
    raise SystemExit(2)
print()
print(f"samples: {len(rows)}")
print(f"temp peak: {peak:.1f} C")
print(f"temp mean: {mean:.1f} C")
print(f"http ok: {ok_rate:.0f}%")
print(f"log: {path}")
if contaminated:
    print("RESULT: FAIL — another llama-server ran concurrently; not a single-server measurement.")
    raise SystemExit(2)
if ok_rate < 100.0:
    print("RESULT: FAIL — server health degraded (http_ok < 100%). Inspect the server log and re-soak.")
    raise SystemExit(2)
if peak >= 85 or fail_hot:
    print("RESULT: FAIL — peak ≥85°C (P_thermal risk). Lower THREADS or ctx and re-soak.")
    raise SystemExit(2)
print("RESULT: PASS — single-server, http_ok 100%, peak <85°C on this soak")
PY
