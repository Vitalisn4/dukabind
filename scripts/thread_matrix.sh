#!/usr/bin/env bash
# Thread bake-off for Gate 1 / M2 (Phase 6 §1.1).
#
# Runs llama-bench at -t 2,3,4,6,8 and samples package/core temp after each setting.
# Writes JSONL + markdown under benchmarks/raw/ (gitignored).
#
# Usage:
#   bash scripts/thread_matrix.sh
#   REPS=2 DELAY=20 bash scripts/thread_matrix.sh

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

LLAMA_BIN="$HERE/third_party/llama.cpp/build/bin"
BENCH="$LLAMA_BIN/llama-bench"
MODEL="$HERE/model/qwen2.5-1.5b-instruct-q4_k_m.gguf"
REPS="${REPS:-3}"
DELAY="${DELAY:-15}"
N_PROMPT="${N_PROMPT:-256}"
N_GEN="${N_GEN:-64}"
THREADS_LIST="${THREADS_LIST:-2,3,4,6,8}"

if [[ ! -x "$BENCH" ]]; then
  echo "error: missing $BENCH — run bash scripts/setup_llama.sh" >&2
  exit 1
fi
if [[ ! -f "$MODEL" ]]; then
  echo "error: missing $MODEL — run ./download_model.sh" >&2
  exit 1
fi

# Temp readings are only comparable without a concurrent server.
if pgrep -f 'llama-serve[r] --model' >/dev/null 2>&1; then
  echo "warning: a llama-server is already running — temp readings will be skewed" >&2
fi

mkdir -p benchmarks/raw
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_JSONL="benchmarks/raw/thread_matrix_${STAMP}.jsonl"
OUT_MD="benchmarks/raw/thread_matrix_${STAMP}.md"
: >"$OUT_JSONL"

read_package_temp() {
  python - <<'PY'
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
    best = max(vals) if vals else float("nan")
print(f"{best:.1f}")
PY
}

echo "== DukaBind thread_matrix =="
echo "model: $MODEL"
echo "reps: $REPS  delay: ${DELAY}s  prompt: $N_PROMPT  gen: $N_GEN"
echo "threads: $THREADS_LIST"
echo "started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo

{
  echo "# Thread matrix — $STAMP"
  echo
  echo "| threads | tg_tps | pp_tps | temp_c_after | notes |"
  echo "|---:|---:|---:|---:|---|"
} >"$OUT_MD"

IFS=',' read -r -a THREADS <<<"$THREADS_LIST"
first=1
for t in "${THREADS[@]}"; do
  t="$(echo "$t" | tr -d '[:space:]')"
  [[ -n "$t" ]] || continue
  echo "-- llama-bench -t $t --"
  if [[ "$first" -eq 0 ]]; then
    sleep "$DELAY"
  fi
  first=0

  tmp_json="$(mktemp "${TMPDIR:-/tmp}/dukabind-bench.XXXXXX.json")"
  "$BENCH" \
    -m "$MODEL" \
    -t "$t" \
    -ngl 0 \
    -p "$N_PROMPT" \
    -n "$N_GEN" \
    -r "$REPS" \
    --delay "$DELAY" \
    -o json >"$tmp_json"

  temp_after="$(read_package_temp)"
  python - "$t" "$temp_after" "$OUT_JSONL" "$OUT_MD" "$tmp_json" <<'PY'
import json, sys
from pathlib import Path

threads = int(sys.argv[1])
temp = float(sys.argv[2])
jsonl_path = Path(sys.argv[3])
md_path = Path(sys.argv[4])
raw_path = Path(sys.argv[5])
data = json.loads(raw_path.read_text(encoding="utf-8"))
rows = [data] if isinstance(data, dict) else list(data)

tg = [r for r in rows if int(r.get("n_gen", 0) or 0) > 0]
pp = [r for r in rows if int(r.get("n_prompt", 0) or 0) > 0 and int(r.get("n_gen", 0) or 0) == 0]


def avg_tps(items):
    vals = []
    for item in items:
        for k in ("avg_ts", "tokens_per_second", "ts"):
            if item.get(k) is not None:
                vals.append(float(item[k]))
                break
    return sum(vals) / len(vals) if vals else float("nan")


tg_tps = avg_tps(tg) if tg else avg_tps(rows)
pp_tps = avg_tps(pp) if pp else float("nan")
record = {
    "threads": threads,
    "tg_tps": tg_tps,
    "pp_tps": pp_tps,
    "temp_c_after": temp,
    "raw": rows,
}
with jsonl_path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(record) + "\n")
note = "hot" if temp >= 85 else ("warm" if temp >= 80 else "ok")
line = f"| {threads} | {tg_tps:.2f} | {pp_tps:.2f} | {temp:.1f} | {note} |"
with md_path.open("a", encoding="utf-8") as fh:
    fh.write(line + "\n")
print(line)
PY
  rm -f "$tmp_json"
done

echo
echo "wrote: $OUT_JSONL"
echo "wrote: $OUT_MD"
echo "Pick lowest -t within ~5% of peak tg_tps with manageable temp; freeze THREADS in start_llama_server.sh."
echo "PASS: thread_matrix finished"
