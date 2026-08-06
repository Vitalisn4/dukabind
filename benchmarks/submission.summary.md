# Profiler participant smoke — summary

> **Status (2026-08-06):** the thermal story is now superseded by [`BENCHMARKS.md`](../BENCHMARKS.md) — thread matrix and thermal soak are complete (soak **FAIL**: mean 78 °C / peak 97 °C on the build laptop). This file documents the 2026-08-04 participant smoke only.

**Run:** 2026-08-04T21:10:02Z → 21:11:49Z UTC  
**Command:** `bash scripts/run_profiler_smoke.sh` (`--skip-accuracy`)  
**Raw JSON:** `benchmarks/raw/submission.json` (gitignored)

## Measured (participant laptop)

| Field | Value |
|---|---|
| Peak RSS | **1825.6 MB** |
| Steady-state RSS | 1750.63 MB |
| Generation TPS | **14.73** tok/s |
| First-token latency | 9865.49 ms |
| CPU p99 | 93.5% |
| Core temp peak | **100.0 °C** |
| Throttled | **true** |
| CPU | Intel Core i7-8650U @ 1.90GHz |
| RAM | 23.3 GB |
| OS | Ubuntu 22.04.5 LTS |
| GPU | none |
| Model | Qwen2.5-1.5B Q4_K_M (`qwen2`) |

## Gate notes

- Peak RSS ≪ 5.5 GB self-limit and ≪ 7 GB DQ — **memory OK for this smoke**.
- TPS ≈ Devpost provisional reference (15) — **acceptable for smoke**.
- Thermal **fails** contest soak target (&lt;85 °C, no throttle) on this host during `llama-bench`. Next: thread/ctx sweep + longer cool soak before claiming M2 complete.
- Accuracy block empty (`--skip-accuracy`). Re-run with `--full` before freeze if required.
