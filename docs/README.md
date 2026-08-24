# Public documentation

These files ship with the GitHub submission.

## Product

Offline shop assistant in **English, French, and Swahili**: allowlisted SQLite ledger bind plus optional local llama.cpp narration (en/fr; Swahili is binder-only) for African MSME counters (Cameroon-designed; Douala / XAF). Fail closed on missing money fields.

## Docs map

| Doc | Purpose |
|---|---|
| [`README.md`](../README.md) | Product pitch, quick start, demo, measured numbers |
| [`REPORT.md`](../REPORT.md) | Technical writeup (problem, design, benchmarks) |
| [`MODEL_CARD.md`](../MODEL_CARD.md) | Qwen2.5-1.5B Q4_K_M: intended use, limits, honesty |
| [`BENCHMARKS.md`](../BENCHMARKS.md) | Measured profiler, matrix, and soak numbers |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Reproduction runbook |
| [`SECURITY.md`](./SECURITY.md) | Threat model and control IDs (C1-C10) |
| [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md) | Product and runtime choices |

Evidence:

- [`benchmarks/submission.json`](../benchmarks/submission.json): freeze snapshot of participant output
- [`benchmarks/submission.summary.md`](../benchmarks/submission.summary.md): latest profiler summary
- [`benchmarks/README.md`](../benchmarks/README.md): how to re-run the profiler
- [`evals/heldout/REPORT.md`](../evals/heldout/REPORT.md): held-out report (37/37 bind/refuse, ledger-flip proofs, two shops, EN/FR/SW)
- [`evals/run_heldout.py`](../evals/run_heldout.py): offline held-out runner
