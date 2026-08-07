# Profiler participant smoke — summary

**Run:** 2026-08-06T22:28:10Z UTC
**Command:** `bash scripts/run_profiler_smoke.sh` --full

> Auto-generated from the latest profiler run. The authoritative, curated benchmark story is [`BENCHMARKS.md`](../BENCHMARKS.md).
**Raw JSON:** `benchmarks/raw/submission.json` (gitignored)

## Measured (participant laptop)

| Field | Value |
|---|---|
| Peak RSS | **1825.72 MB** |
| Steady-state RSS | 1747.35 MB |
| Generation TPS | **16.44 tok/s** |
| First-token latency | 9026.84 ms |
| CPU p99 | 93.4% |
| Core temp peak | **100.0 °C** |
| Throttled | **True** |
| CPU | Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz |
| RAM | 23.3 GB |
| OS | Ubuntu 22.04.5 LTS |
| GPU | none |
| Architecture | qwen2 |

## Gate notes

- Peak RSS clears &lt;5.5 GB self-limit.
- Thermal **fails** contest soak target (&lt;85 °C / no throttle) on this run.
- Next: `bash scripts/thread_matrix.sh`, then the frozen-default soak `bash scripts/thermal_soak.sh`.
- Copy numbers into `REPORT.md` / `BENCHMARKS.md` only from this JSON — never invent.
