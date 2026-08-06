#!/usr/bin/env bash
# Participant-mode adtc-profiler smoke (Gate 1 / M2).
#
# Requires:
#   - .venv311 with adtc-profiler installed
#   - GGUF at model/qwen2.5-1.5b-instruct-q4_k_m.gguf (./download_model.sh)
#   - local llama-bench on PATH (third_party/llama.cpp/build/bin)
#
# Writes:
#   - benchmarks/raw/submission.json   (gitignored raw dump)
#   - benchmarks/submission.summary.md (measured summary — committed)
#
# Usage:
#   bash scripts/run_profiler_smoke.sh
#   bash scripts/run_profiler_smoke.sh --full

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

PROFILER="${ADTC_PROFILER:-$HERE/.venv311/bin/adtc-profiler}"
if [[ ! -x "$PROFILER" ]]; then
  echo "error: adtc-profiler not found at $PROFILER" >&2
  echo "Install into .venv311 (Python ≥3.11)." >&2
  exit 1
fi

MODEL="$HERE/model/qwen2.5-1.5b-instruct-q4_k_m.gguf"
if [[ ! -f "$MODEL" ]]; then
  echo "error: missing $MODEL — run ./download_model.sh first" >&2
  exit 1
fi

mkdir -p benchmarks/raw
OUT="$HERE/benchmarks/raw/submission.json"
SKIP=(--skip-accuracy)
if [[ "${1:-}" == "--full" ]]; then
  SKIP=()
fi

LLAMA_BIN="$HERE/third_party/llama.cpp/build/bin"
if [[ -x "$LLAMA_BIN/llama-bench" ]]; then
  export PATH="$LLAMA_BIN:$PATH"
else
  echo "error: $LLAMA_BIN/llama-bench missing — run bash scripts/setup_llama.sh" >&2
  exit 1
fi

echo "== adtc-profiler participant smoke =="
echo "submission: $HERE"
echo "output:     $OUT"
echo "profiler:   $PROFILER"
echo "flags:      ${SKIP[*]:-(none)}"
echo "started:    $(date -u +%Y-%m-%dT%H:%M:%SZ)"

"$PROFILER" run \
  --submission "$HERE" \
  --mode participant \
  --output "$OUT" \
  "${SKIP[@]}"

echo "finished:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "wrote:      $OUT"

FLAG_DESC=""
if [[ "${1:-}" == "--full" ]]; then
  FLAG_DESC=" --full"
fi

python - "$OUT" "$FLAG_DESC" <<'PY'
import json, sys
from pathlib import Path
from datetime import datetime, timezone

path = Path(sys.argv[1])
flag_desc = sys.argv[2] if len(sys.argv) > 2 else ""
data = json.loads(path.read_text(encoding="utf-8"))
mem = data.get("memory") or {}
thr = data.get("throughput") or {}
therm = data.get("cpu_thermal") or {}
env = data.get("environment") or {}
model = data.get("model_info") or {}

def fmt(v, suffix=""):
    if v is None:
        return "_not present_"
    return f"{v}{suffix}"

peak = mem.get("peak_rss_mb")
tps = thr.get("tokens_per_second_generation")
ttft = thr.get("first_token_latency_ms")
temp = therm.get("core_temp_c_peak")
throttled = therm.get("throttled")
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

lines = [
    "# Profiler participant smoke — summary",
    "",
    f    "**Run:** {now} UTC",
    "**Command:** `bash scripts/run_profiler_smoke.sh`{flag_desc}",
    "",
    "> Auto-generated from the latest profiler run. The authoritative, curated benchmark story is [`BENCHMARKS.md`](../BENCHMARKS.md).",
    "**Raw JSON:** `benchmarks/raw/submission.json` (gitignored)",
    "",
    "## Measured (participant laptop)",
    "",
    "| Field | Value |",
    "|---|---|",
    f"| Peak RSS | **{fmt(peak, ' MB')}** |",
    f"| Steady-state RSS | {fmt(mem.get('steady_state_rss_mb'), ' MB')} |",
    f"| Generation TPS | **{fmt(tps, ' tok/s')}** |",
    f"| First-token latency | {fmt(ttft, ' ms')} |",
    f"| CPU p99 | {fmt(therm.get('cpu_percent_p99'), '%')} |",
    f"| Core temp peak | **{fmt(temp, ' °C')}** |",
    f"| Throttled | **{throttled}** |",
    f"| CPU | {env.get('cpu_model', '_')} |",
    f"| RAM | {env.get('ram_gb', '_')} GB |",
    f"| OS | {env.get('os', '_')} |",
    f"| GPU | {env.get('gpu', '_')} |",
    f"| Architecture | {model.get('architecture', '_')} |",
    "",
    "## Gate notes",
    "",
]
if isinstance(peak, (int, float)) and peak < 5500:
    lines.append("- Peak RSS clears &lt;5.5 GB self-limit.")
else:
    lines.append("- Peak RSS check inconclusive or above self-limit — inspect JSON.")
if (isinstance(temp, (int, float)) and temp >= 85) or throttled is True:
    lines.append("- Thermal **fails** contest soak target (&lt;85 °C / no throttle) on this run.")
    lines.append("- Next: `bash scripts/thread_matrix.sh`, then the frozen-default soak `bash scripts/thermal_soak.sh`.")
else:
    lines.append("- Thermal looks within &lt;85 °C / no-throttle for this smoke.")
lines.append("- Copy numbers into `REPORT.md` / `BENCHMARKS.md` only from this JSON — never invent.")
lines.append("")

Path("benchmarks/submission.summary.md").write_text("\n".join(lines), encoding="utf-8")
print("top-level keys:", sorted(data.keys()))
print("updated benchmarks/submission.summary.md")
PY

echo "PASS: profiler smoke finished"
