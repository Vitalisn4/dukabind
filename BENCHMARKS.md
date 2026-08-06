# BENCHMARKS — DukaBind

**Status:** Living — update only from measured `adtc-profiler` / `llama-bench` / soak output  
**Last updated:** 2026-08-06

## How to reproduce

```bash
./download_model.sh
bash scripts/setup_llama.sh
bash scripts/run_profiler_smoke.sh
bash scripts/thread_matrix.sh
SOAK_MINUTES=10 bash scripts/thermal_soak.sh
```

## Participant smoke (2026-08-04, `--skip-accuracy`)

Source: `benchmarks/raw/submission.json` → see also `benchmarks/submission.summary.md`.

| Metric | Measured |
|---|---|
| Peak RSS | 1825.6 MB |
| Steady-state RSS | 1750.63 MB |
| Generation TPS | 14.73 tok/s |
| TTFT | 9865.49 ms |
| Core temp peak | 100.0 °C |
| Throttled | yes |
| Host | Intel i7-8650U · 23.3 GB RAM · Ubuntu 22.04 · no GPU |

## Thread matrix (2026-08-05, `llama-bench -t 2,3,4,6,8`)

Source: `benchmarks/raw/thread_matrix_20260805T204347Z.md` (+ raw JSONL). `-t 3` is the sweet spot; `-t 8` collapses throughput **and** reaches 85 °C.

| threads | tg_tps | pp_tps | temp_c_after | notes |
|---:|---:|---:|---:|---|
| 2 | 14.96 | 45.79 | 76.0 | ok |
| 3 | **17.94** | 63.73 | 77.0 | ok — frozen default |
| 4 | 16.57 | 62.52 | 76.0 | ok |
| 6 | 16.32 | 62.20 | 79.0 | ok |
| 8 | 7.53 | 59.74 | 85.0 | hot — collapsed TPS |

**Action taken:** `scripts/start_llama_server.sh` freezes `THREADS=3` (override via `THREADS=…` for experiments).

## Thermal soak (2026-08-06, `THREADS=3` `ctx=2048`, single server)

Source: `benchmarks/raw/thermal_soak_20260806T071704Z.csv` — `bash scripts/thermal_soak.sh` (default 10 min, sample 5 s). All 75 completions succeeded.

| Metric | Measured |
|---|---:|
| Samples | 75 over ~10 min |
| HTTP success | 100 % |
| Temp mean | 78.1 °C |
| Temp peak | 97.0 °C (at +297 s) |
| Samples ≥ 85 °C | 9 / 75 (12 %) |
| Verdict | **FAIL** — peak ≥ 85 °C (P_thermal risk) |

**Interpretation:** steady state is comfortable (mean 78 °C, last samples 70–81 °C, no runaway), but this 2018-era 8-thread laptop intermittently spikes ≥ 85 °C under sustained generation — the same burst pattern as the 100 °C profiler-smoke. Mitigations: (a) re-soak at `THREADS=2` (thread matrix measured 76 °C and 14.96 tg_tps there); (b) P_thermal is decided on the **official eval laptop** (i5 12th-gen / Ryzen 5 3000–5000), which cools differently from this host.

### Other soak attempts (kept for provenance — NOT authoritative)

| Run | threads | peak °C | mean °C | http ok | Why excluded |
|---:|---:|---:|---:|---:|---|
| `thermal_soak_20260806T070010Z` | 3 | 92.0 | 82.6 | 100% | contaminated — ran concurrently with another llama-server (~7 min) |
| `thermal_soak_20260806T070257Z` | 2 | 91.0 | 84.0 | 100% | contaminated — ran concurrently with another llama-server |
| `thermal_soak_20260806T065836Z` | 3 | 91.0 | 75.7 | 27% | interrupted — server died mid-run |
| `thermal_soak_20260806T065633Z` | 3 | 77.0 | 70.0 | 0% | crashed at launch — script had a transient syntax error (2 samples) |

A short 1-min positive run (`thermal_soak_20260806T073357Z`, after the single-server guard landed) returned **PASS** (peak 79 °C, http 100%) — it verifies the script mechanics only, not the 10-min soak.

## Gate interpretation

| Target | Status |
|---|---|
| Peak RSS &lt; 5.5 GB | **Pass** |
| TPS near 15 | **Pass / near** on smoke + matrix |
| Thermal &lt; 85 °C / no throttle | **Pending on this participant laptop** under sustained generate |

**M2 tooling: complete.** The measurement toolkit (profiler smoke, thread matrix, thermal soak) is shipped and reproducible.

**P_thermal: pending.** Thermal closure needs a soak that stays &lt;85 °C (cooler room, shorter `max_tokens`, `CTX=1024`, `THREADS=2`, or measure on a quieter machine closer to the contest profile). Official Gate 1 scores use the ADTC eval machine — record that separately.

## Still to run

- [ ] Clean re-soak at `THREADS=2` (mitigation for the FAIL above)  
- [ ] Optional `bash scripts/run_profiler_smoke.sh --full` (accuracy)  
- [ ] Official eval-machine numbers (Gate 1 scoring machine ≠ this laptop)
