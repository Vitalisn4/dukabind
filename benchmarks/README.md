# Benchmarks

Official Gate 1 numbers come from **adtc-profiler** participant mode.

```bash
# once: GGUF on disk
./download_model.sh

# smoke (skips lm_eval accuracy — fast, initial pass)
bash scripts/run_profiler_smoke.sh

# optional full accuracy pass (slow)
bash scripts/run_profiler_smoke.sh --full
```

Raw JSON lands in `benchmarks/raw/` (gitignored). After each completed run — green or failed — copy measured Peak RSS / TPS / thermal into `BENCHMARKS.md` / `REPORT.md` and record the PASS/FAIL verdict — never invent values.

At the code freeze (2026-08-11) the measured participant output was snapshotted into `benchmarks/submission.json` (committed, un-ignored) — the freeze-dated artifact referenced by `CHANGELOG.md`.
