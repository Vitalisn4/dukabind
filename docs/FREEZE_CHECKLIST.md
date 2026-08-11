# Gate-freeze checklist — DukaBind (M6)

**Status:** ✅ Complete at the M6 freeze commit (2026-08-11, branch `feature/dukabind-m6-freeze`).
**Scope:** packaging + demo only — no product features added after freeze.

Legend: ✅ pass · 🟡 measured on build laptop, authoritative run = ADTC eval machine · ⬜ not met

## Performance / anti-DQ gates (Phase 6 targets)

| Target | Criterion | Status | Evidence |
|---|---|---|---|
| **T1** Peak RSS (profiler / model) | ≤ 3500 MB | ✅ 1825.61 MB (2026-08-11 freeze re-run) | `benchmarks/submission.json` · `benchmarks/submission.summary.md` |
| **T2** Peak RSS (full stack ask) | ≤ 4500 MB | ✅ 0.77 GiB cgroup peak (full stack under hard 7.5 GiB cap) | `REPORT.md` · `scripts/ram_capped_proof.sh` (2026-08-06) |
| **T3** Peak RSS hard stop | < 5500 MB (red line) / < 7000 MB (DQ) | ✅ ~3× margin under the 7 GB usable ceiling | `BENCHMARKS.md` · `REPORT.md` |
| **T5** Generation TPS (warm) | ≥ 15 tok/s | ✅ 15.9 tok/s (2026-08-11); 16.44 tok/s (`--full` 2026-08-06); llama-bench up to 17.94 | `benchmarks/submission.summary.md` · `BENCHMARKS.md` |
| **T8** core temp (10–15 min soak) | < 85 °C | 🟡 **FAIL on 2026-08-10 re-run** at shipped default `THREADS=2`/`CTX=1024` (cold-start peak 89.0 °C); the 2026-08-06 PASS (peak 84.0 °C) no longer reproduces on the build laptop — authoritative P_thermal = official eval machine | `BENCHMARKS.md` · `benchmarks/raw/thermal_soak_20260810T093226Z.csv` |
| **T9** Throttle flag | false | 🟡 profiler smoke 2026-08-11 reported throttled on this laptop (peak 100.0 °C) — same honest caveat as T8; eval-machine run is the verdict | `benchmarks/submission.json` |
| **T11** Held-out EN bind/refuse | ≥ 90 % | ✅ **100.0 % (28/28)**, 31/31 checks, flips 3/3 | `evals/heldout/REPORT.md` |
| **T13** Submission prompts | disjoint from held-out | ✅ `tp_001` Esther Tchamba (NULL refuse) + `tp_002` Chidi Okafor × Sucre (grounded No); CI enforces ask-string disjointness | `metadata.json` · `tests/test_metadata.py` |
| **T15** Quant lock | Q4_K_M 1.5B | ✅ frozen (M3/M5); no change at freeze | `MODEL_CARD.md` · `REPORT.md` |

## Freeze packaging checklist

- [x] `metadata.json` unchanged and still T13-disjoint (verified by `tests/test_metadata.py`)
- [x] Ship defaults documented and unchanged: Qwen2.5-1.5B Q4_K_M · `THREADS=2` · `CTX=1024` (`scripts/start_llama_server.sh`)
- [x] `REPORT.md` freeze wording confirmed after thermal honesty (thread / `n_ctx` / quant flags)
- [x] Screenshots for README — `demo/screenshots/` (5 numbered stills, real output)
- [x] ≤ 2 min demo video — `demo/demo.mp4` (114 s) + `demo/storyboard.md` + `demo/VIDEO.md`
- [x] `CHANGELOG.md` created with Keep-a-Changelog format; freeze commit hash recorded
- [x] `benchmarks/submission.json` — measured participant output committed as the freeze snapshot
- [x] CI green: `pytest tests/` (46) + `evals/run_heldout.py` (31/31) + ruff
- [x] Docs aligned: `PROGRESS.md`, Kickoff Week 4 Days 3/5, Roadmap M6 → Done, `COMPLIANCE_CHECKLIST.md`
- [x] No new product features after freeze

## Remaining before submission (M7 — out of scope for M6)

- [ ] Official eval-machine P_thermal / profiler run (authoritative T8/T9 verdict)
- [ ] Devpost submission ≥ 24 h early (~Aug 22–23) with the freeze commit hash
- [ ] Fresh-machine reproduction day (`download_model.sh` sha256 check, server start, asks answer)
