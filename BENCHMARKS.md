# BENCHMARKS — DukaBind

**Status:** Living — update only from measured `adtc-profiler` / `llama-bench` / soak output  
**Last updated:** 2026-08-10  
**Product:** Path A English offline ledger binder · Qwen2.5-1.5B Q4_K_M · participant laptop Intel i7-8650U  

**Schedule docs:** [`docs/ADTC-2026-Build-Kickoff.md`](docs/ADTC-2026-Build-Kickoff.md) · [`docs/ADTC-2026-ROADMAP.md`](docs/ADTC-2026-ROADMAP.md) · [`docs/PROGRESS.md`](docs/PROGRESS.md)

## How to reproduce

```bash
./download_model.sh
bash scripts/setup_llama.sh
bash scripts/run_profiler_smoke.sh
bash scripts/thread_matrix.sh
SOAK_MINUTES=10 bash scripts/thermal_soak.sh
THREADS=3 CTX=2048 bash scripts/ram_capped_proof.sh   # 8 GB-class proof; envs pin the 2026-08-06 recorded config
```

> Env-override note: the scripts read **uppercase** `THREADS` and `CTX` (e.g. `THREADS=2 CTX=1024 bash scripts/thermal_soak.sh`). The shipped default is `THREADS=2`/`CTX=1024`; the recorded 2026-08-06 runs below use the then-default `THREADS=3`/`CTX=2048` unless stated otherwise.

## Participant smoke (2026-08-06, `--full` — definitive run)

Source: `benchmarks/raw/submission.json` → see also `benchmarks/submission.summary.md`.

| Metric | Measured |
|---|---|
| Peak RSS | 1825.72 MB |
| Steady-state RSS | 1747.35 MB |
| Generation TPS | 16.44 tok/s |
| TTFT | 9026.84 ms |
| Core temp peak | 100.0 °C |
| Throttled | yes |
| Host | Intel i7-8650U · 23.3 GB RAM · Ubuntu 22.04 · no GPU |
| Accuracy block | `accuracy: []` — participant mode skips accuracy evals by design; ADTC audit mode scores the hidden subset |

**Accuracy note:** the profiler emits an empty `accuracy` block in participant mode. Forcing it by installing `lm-eval` fails upstream: the profiler calls `--model_args pretrained=<path>`, but every released lm-eval 0.4.x `gguf` model requires a llama-server `base_url` (installing it breaks `--full` with an AccuracyError). Official accuracy numbers come from the ADTC audit-mode run on the eval machine — never invented here.

## 8 GB-class memory-capped proof (2026-08-06, cgroup `MemoryMax=7.5G`)

`THREADS=3 CTX=2048 bash scripts/ram_capped_proof.sh` — re-execs itself inside a `systemd-run --user --scope` cgroup (`CAP_GB=7.5`), starts llama-server (envs pin the 2026-08-06 recorded config `THREADS=3`/`CTX=2048`, the then-default), runs three narrated asks, then reads `memory.max`/`memory.peak` (kernel 6.8, cgroup v2).

| Metric | Measured |
|---|---|
| Cap enforced (`memory.max`) | 7.50 GiB — no WARNING |
| Cgroup peak (`memory.peak`) | **0.77 GiB** (823853056 B) |
| Sampled `memory.current` max | 0.77 GiB (0.5 s interval) |
| llama-server peak VmRSS | **1.80 GiB** (1882692 KiB) |
| Headroom vs 7.5 GiB cap | 6.73 GiB |
| Headroom vs 7.0 GiB DQ ceiling | 6.23 GiB (incremental) · **~5.2 GiB** (whole-stack RSS per profiler 1825.72 MB) |
| Headroom vs 5.5 GiB self-limit | 4.73 GiB (incremental) · ~3.6 GiB (whole-stack RSS) |
| Asks under cap | 3/3 — credit **No** (8410 &gt; 8000, narrated), stock on_hand=14 (narrated), SOCA NULL refusal (model skipped) |

**Interpretation:** the full stack completes under the hard 7.5 GiB cap with no OOM (independent re-run: peak 0.76 GiB, headroom 6.74 GiB — run-to-run variance &lt; 0.02 GiB). The cgroup charge (0.77 GiB) is the *incremental* cost on this host — the 1.12 GB GGUF was already resident in global page cache from earlier uncapped runs, so the scope paid only compute/token memory. The process-level footprint is the safe planning number: llama-server VmRSS 1.80 GiB ≈ profiler Peak RSS 1825.72 MB. Cold-cache worst case ≈ 1.12 GB GGUF + 0.77 GiB compute ≈ **1.9 GiB** → still ~3.7× under the 7 GB usable DQ ceiling.

## Thread matrix (2026-08-05, `llama-bench -t 2,3,4,6,8`)

Source: `benchmarks/raw/thread_matrix_20260805T204347Z.md` (+ raw JSONL). `-t 3` is the sweet spot; `-t 8` collapses throughput **and** reaches 85 °C.

| threads | tg_tps | pp_tps | temp_c_after | notes |
|---:|---:|---:|---:|---|
| 2 | 14.96 | 45.79 | 76.0 | ok |
| 3 | **17.94** | 63.73 | 77.0 | ok — frozen default |
| 4 | 16.57 | 62.52 | 76.0 | ok |
| 6 | 16.32 | 62.20 | 79.0 | ok |
| 8 | 7.53 | 59.74 | 85.0 | hot — collapsed TPS |

**Action taken (2026-08-05):** `THREADS=3`/`CTX=2048` was frozen as the default after this matrix (peak tg_tps 17.94). **Superseded 2026-08-07 (M5):** the shipped default is now `THREADS=2`/`CTX=1024` — the measured thermal-PASS config as of 2026-08-06 (FAIL on 2026-08-10 re-run — see soak sections below) — with `THREADS=3`/`CTX=2048` reachable via env override for eval-machine runs. This matrix remains the TPS evidence for both choices.

## Thermal soak (2026-08-06, `THREADS=3` `ctx=2048`, single server)

**Scope of verdicts:** every soak verdict on this page is **temperature-only** — `thermal_soak.sh` samples package temperature + HTTP success, never CPU frequency or throttle states, so no claim of throttle-free operation is made on this host.

Source: `benchmarks/raw/thermal_soak_20260806T071704Z.csv` — `bash scripts/thermal_soak.sh` (default 10 min, sample 5 s). All 75 completions succeeded.

| Metric | Measured |
|---|---:|
| Samples | 75 over ~10 min |
| HTTP success | 100 % |
| Temp mean | 78.1 °C |
| Temp peak | 97.0 °C (at +297 s) |
| Samples ≥ 85 °C | 9 / 75 (12 %) |
| Verdict | **FAIL** — peak ≥ 85 °C (P_thermal risk) |

**Interpretation:** steady state is comfortable (mean 78 °C, last samples 70–81 °C, no runaway), but this 2018-era 8-thread laptop intermittently spikes ≥ 85 °C under sustained generation — the same burst pattern as the 100 °C profiler-smoke. Mitigations: (a) `THREADS=2` re-soak — **measured FAIL** at `ctx=2048`, see below; (b) `CTX=1024` re-soak — **measured PASS**, see below; (c) P_thermal is decided on the **official eval laptop** (i5 12th-gen / Ryzen 5 3000–5000), which cools differently from this host.

## Thermal soak (2026-08-06, `THREADS=2` `ctx=2048`, single server)

Source: `benchmarks/raw/thermal_soak_20260806T133807Z.csv` — `THREADS=2 SOAK_MINUTES=10 bash scripts/thermal_soak.sh`. 69 completions, http 100%.

| Metric | Measured |
|---|---:|
| Samples | 69 over ~10 min |
| HTTP success | 100 % |
| Temp mean | 79.4 °C |
| Temp peak | 93.0 °C (at +333 s) |
| Samples ≥ 85 °C | 8 / 69 (12 %) |
| Verdict | **FAIL** — peak ≥ 85 °C (P_thermal risk) |

Same burst pattern as `THREADS=3`: the thread-matrix “76 °C after a single bench” reading did not survive sustained load. **`THREADS=2` at the default `ctx=2048` is measured and ruled out on this host** — but the `CTX=1024` re-soak below **passes**. The authoritative P_thermal decision still stays on the official eval laptop.

## Thermal soak (2026-08-06, `THREADS=2` `ctx=1024`, single server) — **PASS (superseded 2026-08-10)**

Source: `benchmarks/raw/thermal_soak_20260806T213423Z.csv` — `THREADS=2 CTX=1024 SOAK_MINUTES=10 bash scripts/thermal_soak.sh`. 68 completions, http 100%, idle baseline 73 °C.

| Metric | Measured |
|---|---:|
| Samples | 68 over ~10 min |
| HTTP success | 100 % |
| Temp mean | 75.7 °C |
| Temp peak | 84.0 °C (at +139 s) |
| Samples ≥ 85 °C | 0 / 68 |
| Verdict | **PASS** — peak &lt; 85 °C |

**Interpretation:** halving the context (`ctx=2048 → 1024`) removed the intermittent ≥ 85 °C bursts that failed both `THREADS=3` and `THREADS=2` at full context — the **first 10-min soak to pass on temperature alone on this laptop**. Note the margin is thin (peak 84.0 °C, 1 °C below the −10 threshold) and the burst appears early (peak at +139 s, then settles to 73 °C by the end). The former default (`THREADS=3`/`CTX=2048`) still fails on this host; the authoritative run stays on the official eval laptop.

**⚠ Superseded (2026-08-10):** this PASS **no longer reproduces** — re-running the identical config (`THREADS=2`/`CTX=1024`, 10 min, single server) on the same laptop, even from a *cooler* 60 °C idle baseline, **FAILED**: mean **78.6 °C**, peak **89.0 °C** at +356 s, several samples ≥ 85 °C, http 100 % (see next section). The thin margin that produced the 2026-08-06 PASS is gone on this host today — treat P_thermal on the build laptop as **unverified (FAIL on re-run)** and rely on the official eval machine for the Gate verdict.

## Thermal soak (2026-08-10, `THREADS=2` `ctx=1024`, re-run) — **FAIL — PASS no longer reproduces**

Re-validation of the shipped default config (`THREADS=2`/`CTX=1024`, `SOAK_MINUTES=10`, single server) after the 2026-08-06 PASS. Run 1 started immediately after the thread matrix (hot baseline); Run 2 started from a cool 60 °C idle baseline.

| Run | Source | Samples | Idle baseline | Temp mean | Temp peak | Samples ≥ 85 °C | HTTP | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 (hot start) | `thermal_soak_20260810T091737Z.csv` | 70 | ~81 °C (post-bench) | 80.3 °C | 98.0 °C (at +524 s) | many | 100 % | FAIL (skewed by residual heat) |
| 2 (cold start) | `thermal_soak_20260810T093226Z.csv` | 69 | 60 °C | 78.6 °C | 89.0 °C (at +356 s) | several | 100 % | **FAIL** |

**Interpretation:** the 2026-08-06 PASS (peak 84.0 °C, 0/68 ≥ 85 °C) **does not reproduce on this laptop as of 2026-08-10**. Even from a *cooler* idle baseline (60 °C vs 73 °C on the PASS run), the same config burst ≥ 85 °C repeatedly and peaked 89.0 °C — roughly a 5 °C upward shift in this host's thermal behaviour (ambient / machine-state change). The documented "thin margin" caveat was correct: the shipped default is now **FAIL on this host**. The authoritative P_thermal decision remains the official ADTC eval machine — run the soak there before Gate.

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
| Thermal &lt; 85 °C (temperature-only — soak samples no throttle signal) | **PASS 2026-08-06 but FAIL on 2026-08-10 re-run** at shipped default `THREADS=2`/`CTX=1024` on this laptop (cold-start peak 89.0 °C, hot-start 98.0 °C — no longer reproducible); `THREADS=3`/`CTX=2048` (peak 97 °C) and `THREADS=2`/`CTX=2048` (peak 93 °C) documented FAIL — the official eval laptop is the authoritative P_thermal run |

**M2 tooling: complete.** The measurement toolkit (profiler smoke, thread matrix, thermal soak) is shipped and reproducible.

**Ship default (M5 decision, 2026-08-07):** `scripts/start_llama_server.sh` now ships **`THREADS=2`/`CTX=1024`** — the only config with a measured 10-min thermal soak **PASS** on this laptop (peak 84.0 °C, mean 75.7 °C, 0/68 samples ≥ 85 °C, http 100 %). Risk gate applied: *prefer thermal safety over TPS* (TPS 14.96 at `-t 2` vs 17.94 at `-t 3`). `THREADS=3`/`CTX=2048` remains available via env override for the official eval-machine run, which is still the authoritative P_thermal decision. **Re-validation 2026-08-10: the PASS config no longer reproduces on this laptop (peak 89.0 °C, FAIL) — the thermal decision must come from the official eval machine.**

**P_thermal (temperature-only): FAIL on 2026-08-10 re-run at the shipped default `THREADS=2`/`CTX=1024` on this laptop** — cold-start peak **89.0 °C** (mean 78.6 °C); the 2026-08-06 PASS (peak 84.0 °C, 0/68 ≥ 85 °C) **no longer reproduces on this host**. The former default `THREADS=3`/`CTX=2048` (peak 97 °C) and `THREADS=2` at `CTX=2048` (peak 93 °C) also FAIL at full context (documented above). Official Gate 1 scores use the ADTC eval machine — record that separately.

## Model lock (M3 — Path A)

- **Primary (locked):** Qwen2.5-1.5B-Instruct Q4_K_M (`model/qwen2.5-1.5b-instruct-q4_k_m.gguf`, sha256-pinned in `download_model.sh`). Evidence above: Peak RSS 1825.72 MB, 16.44 tok/s (profiler `--full`; llama-bench up to 17.94), TTFT ~9.0 s — clears the 5.5 GB self-limit with margin.
- **T15 quant lock:** Q4_K_M 1.5B stays frozen unless T11 (answer accuracy) regresses against the held-out set with RSS margin; 3B Q4 only if T1–T3 stay green.
- **Tiny Aya — skipped (Path A):** no Swahili track, so the Aya bake-off is out of scope for Gate 1. No Aya benchmark numbers are claimed or invented.

## Still to run

- [x] Re-soak at `THREADS=2` — **measured FAIL** at `ctx=2048` (peak 93 °C, 2026-08-06)  
- [x] Re-soak at `CTX=1024` — **measured PASS** 2026-08-06 (peak 84.0 °C) but **FAIL on 2026-08-10 re-run** (peak 89.0 °C) — no longer a thermally-safe config on this laptop  
- [x] **Decide ship default** — **done 2026-08-07 (M5):** freeze `THREADS=2`/`CTX=1024` in `scripts/start_llama_server.sh`; documented above (thermal safety over TPS; `THREADS=3`/`CTX=2048` reachable via env override for eval-machine runs)  
- [x] `bash scripts/run_profiler_smoke.sh --full` — done 2026-08-06; `accuracy` block is `[]` in participant mode by design (see note above)  
- [x] 8 GB-class memory-capped proof — done 2026-08-06, `bash scripts/ram_capped_proof.sh` (cgroup peak 0.77 GiB under 7.5 GiB cap; see section above)  
- [ ] Official eval-machine numbers (Gate 1 scoring machine ≠ this laptop)
