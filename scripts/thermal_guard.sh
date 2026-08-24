#!/usr/bin/env bash
# Adaptive thermal guard for DukaBind.
#
# Probes three thread/ctx/ubatch configurations and selects the first
# that stays below the temperature threshold for the full soak duration.
#
# Usage:
#   bash scripts/thermal_guard.sh              # default 10 minutes
#   THRESHOLD=80 SOAK_MINUTES=5 bash scripts/thermal_guard.sh
#
# Phases (degrade in order):
#   Phase 1: THREADS=2/CTX=1024/UBATCH=256 (baseline)
#   Phase 2: THREADS=1/CTX=1024/UBATCH=128 (if Phase 1 exceeds threshold)
#   Phase 3: THREADS=1/CTX=512/UBATCH=64   (if Phase 2 exceeds threshold)

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

THRESHOLD="${THRESHOLD:-85}"
PROBE_SECS="${PROBE_SECS:-180}"
SOAK_MINUTES="${SOAK_MINUTES:-10}"
SAMPLE_SECS="${SAMPLE_SECS:-5}"
PORT="${PORT:-8081}"

# Phase configurations: (threads, ctx, ubatch, label)
PHASES=(
  "2 1024 256  phase1-threads2-ctx1024-ubatch256"
  "1 1024 128  phase2-threads1-ctx1024-ubatch128"
  "1  512  64  phase3-threads1-ctx512-ubatch64"
)

stop_server() {
  kill "$(cat "$HERE/.llama_server.pid" 2>/dev/null)" 2>/dev/null || true
  rm -f "$HERE/.llama_server.pid"
}

start_server() {
  local threads="$1" ctx="$2" ubatch="$3"
  stop_server
  sleep 2
  THREADS="$threads" CTX="$ctx" UBATCH="$ubatch" PORT="$PORT" \
    bash scripts/start_llama_server.sh &>/dev/null &
  local pid=$!
  echo "$pid" > "$HERE/.llama_server.pid"
  # Wait for health (check HTTP 2xx)
  for _ in $(seq 1 30); do
    local status
    status=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/health" 2>/dev/null)
    if [[ "$status" =~ ^2[0-9][0-9]$ ]]; then
      return 0
    fi
    sleep 1
  done
  echo "Server failed to start (threads=$threads ctx=$ctx ubatch=$ubatch)" >&2
  return 1
}

send_request() {
  curl -s --max-time 10 "http://127.0.0.1:$PORT/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{"model":"qwen2.5","messages":[{"role":"user","content":"Can I give Marie-Claire three crates on credit?"}],"max_tokens":48}' \
    >/dev/null 2>&1
}

get_temp() {
  # Read CPU package temperature from thermal zone
  # Try to find the CPU package sensor first (thermal_zone0 or type contains x86/cpu)
  local temp_raw=""
  for zone in /sys/class/thermal/thermal_zone*; do
    local type_file="$zone/type"
    if [[ -f "$type_file" ]]; then
      local zone_type
      zone_type=$(cat "$type_file" 2>/dev/null)
      case "$zone_type" in
        *x86*|*cpu*|*CPU*|*core*|*Core*|*package*|*Package*)
          temp_raw=$(cat "$zone/temp" 2>/dev/null)
          if [[ -n "$temp_raw" && "$temp_raw" -gt 0 ]]; then
            echo "$((temp_raw / 1000))"
            return
          fi
          ;;
      esac
    fi
  done
  # No valid CPU sensor found — return high value to fail safe
  echo "999"
}

run_phase() {
  local threads="$1" ctx="$2" ubatch="$3" label="$4"
  local csv="benchmarks/raw/thermal_guard_${label}.csv"
  mkdir -p benchmarks/raw

  echo "── Phase: $label (threads=$threads ctx=$ctx ubatch=$ubatch) ──"

  if ! start_server "$threads" "$ctx" "$ubatch"; then
    return 1
  fi

  echo "time_s,temp_c,http_ok" > "$csv"
  local start=$SECONDS
  local peak=0
  local failures=0

  while (( SECONDS - start < PROBE_SECS )); do
    local t
    t=$(get_temp)
    local ok="true"
    send_request || { ok="false"; failures=$((failures + 1)); }
    echo "$((SECONDS - start)),$t,$ok" >> "$csv"
    (( t > peak )) && peak=$t
    sleep "$SAMPLE_SECS"
  done

  stop_server
  echo "  peak=${peak}°C failures=${failures}/${PROBE_SECS}"

  if (( peak >= THRESHOLD )); then
    echo "  VERDICT: FAIL (peak ${peak}°C >= threshold ${THRESHOLD}°C)"
    return 1
  fi
  echo "  VERDICT: PASS (peak ${peak}°C < threshold ${THRESHOLD}°C)"
  return 0
}

run_soak() {
  local threads="$1" ctx="$2" ubatch="$3"
  local csv="benchmarks/raw/thermal_soak_guard.csv"
  mkdir -p benchmarks/raw

  echo "── Full soak: ${SOAK_MINUTES} min (threads=$threads ctx=$ctx ubatch=$ubatch) ──"

  if ! start_server "$threads" "$ctx" "$ubatch"; then
    return 1
  fi

  echo "time_s,temp_c,http_ok" > "$csv"
  local start=$SECONDS
  local peak=0
  local failures=0
  local count=0

  while (( SECONDS - start < SOAK_MINUTES * 60 )); do
    local t
    t=$(get_temp)
    local ok="true"
    send_request || { ok="false"; failures=$((failures + 1)); }
    echo "$((SECONDS - start)),$t,$ok" >> "$csv"
    (( t > peak )) && peak=$t
    count=$((count + 1))
    sleep "$SAMPLE_SECS"
  done

  stop_server
  echo "  samples=$count peak=${peak}°C failures=${failures}"

  if (( peak >= THRESHOLD )); then
    echo "  SOAK VERDICT: FAIL"
    return 1
  fi
  echo "  SOAK VERDICT: PASS"
  return 0
}

echo "== DukaBind thermal guard =="
echo "  threshold: ${THRESHOLD}°C"
echo "  probe: ${PROBE_SECS}s | soak: ${SOAK_MINUTES} min"
echo ""

trap stop_server EXIT

selected=""
for phase in "${PHASES[@]}"; do
  read -r threads ctx ubatch label <<< "$phase"
  if run_phase "$threads" "$ctx" "$ubatch" "$label"; then
    echo ""
    echo "Selected: $label (threads=$threads ctx=$ctx ubatch=$ubatch)"
    selected="$threads $ctx $ubatch"
    break
  fi
  echo ""
done

if [[ -z "$selected" ]]; then
  echo "All phases failed. The eval machine may need a cooler environment."
  exit 1
fi

read -r t c u <<< "$selected"
run_soak "$t" "$c" "$u"
