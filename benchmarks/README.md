# Benchmarks

Official Gate 1 numbers come from **adtc-profiler** participant mode.

```bash
./download_model.sh
bash scripts/run_profiler_smoke.sh
bash scripts/run_profiler_smoke.sh --full   # optional; slow accuracy pass
```

Raw JSON lands in `benchmarks/raw/` (gitignored). After a completed run, copy measured Peak RSS, TPS, and thermal into `BENCHMARKS.md` and `REPORT.md`. Never invent values.

The freeze snapshot is `benchmarks/submission.json` (2026-08-11), the participant output for tag `v1.0.0-gate1`.
