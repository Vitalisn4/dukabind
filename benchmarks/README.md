# Benchmarks

**adtc-profiler** participant mode records Peak RSS, generation TPS, TTFT, and on-laptop thermal / accuracy self-checks. Official Gate 1 `S_acc` and `P_thermal` come from an ADTC audit-mode run on the evaluation machine, not from this snapshot.

```bash
./download_model.sh
bash scripts/run_profiler_smoke.sh
bash scripts/run_profiler_smoke.sh --full   # optional; slow accuracy pass
```

Raw JSON lands in `benchmarks/raw/` (gitignored). After a completed run, copy measured Peak RSS, TPS, and thermal into `BENCHMARKS.md` and `REPORT.md`. Never invent values.

The latest snapshot is `benchmarks/submission.json` (2026-08-18, `--full` profiler run).
