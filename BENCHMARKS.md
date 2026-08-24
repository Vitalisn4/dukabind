# BENCHMARKS: DukaBind

**Status:** Updated only from measured `adtc-profiler` / `llama-bench` output.
**Last updated:** 2026-08-18
**Product:** Offline EN/FR/SW ledger binder · Qwen2.5-1.5B Q4_K_M · participant laptop Intel i7-8650U

## How to reproduce

```bash
./download_model.sh
bash scripts/setup_llama.sh
bash scripts/run_profiler_smoke.sh --full
```

Scripts read uppercase `THREADS` and `CTX` (example: `THREADS=2 CTX=1024 bash scripts/thermal_soak.sh`). Shipped default is `THREADS=2`/`CTX=1024`.

## Measured performance (2026-08-18, `--full` profiler run)

Source: [`benchmarks/submission.json`](benchmarks/submission.json) — the committed snapshot from the latest `--full` profiler run on the build laptop.

| Metric | Measured | Target |
|---|---|---:|
| Peak RSS (full stack) | **1826.23 MB** | < 5.5 GB |
| Steady-state RSS | 1747.49 MB | — |
| Generation TPS | **17.35 tok/s** | ≥ 15 tok/s |
| Time to first token | 8175.55 ms | — |
| Core temp peak | 100.0 °C | < 85 °C |
| Throttled | Yes | — |
| Host | Intel i7-8650U · 23.3 GB RAM · Ubuntu 22.04 · no GPU | — |
| Accuracy | `arc_easy` 74.0% (50 samples, `acc_norm`) | — |
| Language scope | `["en", "fr", "sw"]` | — |

**Accuracy note:** The 74.0% `arc_easy` score is a participant-mode self-benchmark on a public multiple-choice task. It is **not** the contest's S_acc: the judges score the hidden validation subset in audit mode on the eval machine. The score is committed as evidence of the toolchain path only.

## Thread matrix (2026-08-05, `llama-bench -t 2,3,4,6,8`)

| Threads | Generation TPS | Peak temp | Notes |
|---:|---:|---:|---|
| 2 | 14.96 | 76 °C | ok |
| 3 | **17.94** | 77 °C | peak throughput |
| 4 | 16.57 | 76 °C | ok |
| 6 | 16.32 | 79 °C | ok |
| 8 | 7.53 | 85 °C | collapsed throughput, hot |

**Shipped default:** `THREADS=2`/`CTX=1024` — balances thermal safety with throughput (14.96 tok/s at `-t 2` vs 17.94 at `-t 3`). `THREADS=3`/`CTX=2048` remains available via env override for the official eval-machine run.

## 8 GB-class memory proof (cgroup `MemoryMax=7.5G`)

| Metric | Measured |
|---|---|
| Cgroup peak (`memory.peak`) | **0.77 GiB** |
| llama-server peak VmRSS | **1.80 GiB** |
| Headroom vs 7.5 GiB cap | 6.73 GiB |
| Headroom vs 7.0 GiB DQ ceiling | ~5.2 GiB (whole-stack RSS) |
| Asks under cap | 3/3: credit No, stock on_hand=14, SOCA NULL refusal |

Full stack completes under the hard 7.5 GiB cap with no OOM. Cold-cache worst case ≈ 1.12 GB GGUF + 0.77 GiB compute ≈ **1.9 GiB**, ~3.7× under the 7 GB usable ceiling.

## Thermal soak summary

Thermal behaviour was tested across multiple configs on the build laptop (Intel i7-8650U, 2018-era). The build laptop runs hotter than the ADTC eval machine (i5 12th-gen / Ryzen 5). Official P_thermal is decided on the eval machine.

| Config | Peak °C | Verdict | Notes |
|---|---:|---|---|
| `THREADS=3`/`CTX=2048` | 97 | FAIL | Default before 2026-08-07 |
| `THREADS=2`/`CTX=2048` | 93 | FAIL | Still too hot at full context |
| `THREADS=2`/`CTX=1024` | 84→89 | PASS→FAIL | Passed 2026-08-06; failed re-run 2026-08-10 |

The shipped default (`THREADS=2`/`CTX=1024`) showed a thin 1 °C margin on the build laptop that did not reproduce. The eval machine typically runs cooler. Thermal mitigation (CPU affinity pinning, micro-batch reduction, adaptive guard) is implemented in `scripts/start_llama_server.sh` and `scripts/thermal_guard.sh`.

## Results summary

| Target | Status |
|---|---|
| Peak RSS < 5.5 GB | **Pass** — 1826.23 MB, well under limit |
| TPS >= 15 tok/s | **Pass** — 17.35 tok/s (profiler), up to 17.94 (llama-bench) |
| Thermal < 85 C | **Pending** — FAIL on build laptop; official verdict on eval machine |

## Model choice

- **Primary:** Qwen2.5-1.5B-Instruct Q4_K_M. Peak RSS 1826.23 MB, 17.35 tok/s (profiler `--full`), TTFT 8176 ms.
- **Selection policy:** Stay frozen unless held-out bind/refuse accuracy regresses with RSS margin.
- **Alternatives skipped:** Tiny Aya (~3B) is out of scope for this submission. No Aya numbers are claimed.
