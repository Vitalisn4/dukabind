# Public documentation

These files ship with the GitHub submission. Keep them current when behaviour or Gate status changes.

## What DukaBind is (Gate 1)

Offline **English** shop assistant: allowlisted SQLite ledger bind + optional local llama.cpp narration for African MSME counters (Cameroon-designed; Douala / XAF). Fail closed on missing money fields.

## Docs map

| Doc | Purpose | Update when |
|---|---|---|
| [`README.md`](../README.md) | Product pitch, quick start, demo, measured numbers | Behaviour, numbers, or screenshots change |
| [`REPORT.md`](../REPORT.md) | Gate 1 technical writeup (template headings) | Benchmarks, constraints, or evidence change |
| [`MODEL_CARD.md`](../MODEL_CARD.md) | Qwen2.5-1.5B Q4_K_M: intended use, limits, honesty | Model or quant evidence changes |
| [`BENCHMARKS.md`](../BENCHMARKS.md) | Measured profiler / matrix / soak numbers (never invented) | Any measured run lands |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Reproduction runbook: fresh machine to verified binder | Commands, paths, or test counts change |
| [`CHANGELOG.md`](../CHANGELOG.md) | Keep-a-Changelog release history + freeze commit hash | A commit changes behaviour or packaging |
| [`SECURITY.md`](./SECURITY.md) | Threat model and control IDs (C1–C10) | A control ships, defers, or changes |
| [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md) | Research-backed product and runtime choices | A decision flips or evidence changes |
| [`CODE_WALKTHROUGH.md`](./CODE_WALKTHROUGH.md) | Module map, shop ledger, commands, security map | Modules, seed rows, envs, or milestones change |
| [`FREEZE_CHECKLIST.md`](./FREEZE_CHECKLIST.md) | Gate-freeze checklist (T1–T3, T5, T8–T9, T11, T13) | Gate status changes |

Committed evidence under `benchmarks/` and `evals/`:

- [`benchmarks/submission.json`](../benchmarks/submission.json), the freeze snapshot of the measured participant output
- [`benchmarks/submission.summary.md`](../benchmarks/submission.summary.md), the auto-regenerated summary of the latest profiler run
- [`benchmarks/README.md`](../benchmarks/README.md), how to re-run the profiler
- [`evals/heldout/REPORT.md`](../evals/heldout/REPORT.md), the held-out evaluation report (T11 28/28 = 100 %, flips 3/3, 31/31 checks)
- [`evals/run_heldout.py`](../evals/run_heldout.py), the offline held-out runner (28 EN prompts, two disjoint shop ledgers)
