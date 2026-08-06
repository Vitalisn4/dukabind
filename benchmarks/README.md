# Benchmarks

Official Gate 1 numbers come from **adtc-profiler** participant mode.

```bash
# once: GGUF on disk
./download_model.sh

# smoke (skips lm_eval accuracy — fast enough for M2 start)
bash scripts/run_profiler_smoke.sh

# optional full accuracy pass (slow)
bash scripts/run_profiler_smoke.sh --full
```

Raw JSON lands in `benchmarks/raw/` (gitignored). After a green run, copy measured Peak RSS / TPS / thermal into `REPORT.md` — never invent values.
