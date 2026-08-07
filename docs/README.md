# Public documentation

These files ship with the GitHub submission. Keep them current when behaviour or Gate status changes.

## What DukaBind is (Gate 1)

Offline **English** shop assistant: allowlisted SQLite ledger bind + optional local llama.cpp narration for African MSME counters (Cameroon-designed; Douala / XAF). Fail closed on missing money fields. Path A — no Swahili claim.

## Docs map

| Doc | Purpose | Update when |
|---|---|---|
| [SECURITY.md](./SECURITY.md) | Threat model and control IDs (C1–C10) | A control ships, defers, or changes |
| [DESIGN_DECISIONS.md](./DESIGN_DECISIONS.md) | Research-backed product and runtime choices | A decision flips or evidence changes |
| [CODE_WALKTHROUGH.md](./CODE_WALKTHROUGH.md) | Module map, shop ledger, commands, security map | Modules, seed rows, envs, or milestones change |

Root also ships [`BENCHMARKS.md`](../BENCHMARKS.md) (measured profiler / matrix / soak numbers), [`MODEL_CARD.md`](../MODEL_CARD.md) (Qwen2.5-1.5B Q4_K_M — intended use, limits, Path A honesty), `benchmarks/submission.summary.md`, and the held-out evaluation set + offline runner under `evals/` (28 EN prompts, two disjoint shop ledgers, committed evidence report at [`evals/heldout/REPORT.md`](../evals/heldout/REPORT.md) — see [`CODE_WALKTHROUGH.md`](./CODE_WALKTHROUGH.md) §5.7).

## Local-only build guides (gitignored — open on disk)

Use these for **implementation steps**, not for the public judge repo:

| Doc | Role |
|---|---|
| `docs/ADTC-2026-Build-Kickoff.md` | Day-by-day checklist |
| `docs/ADTC-2026-ROADMAP.md` | Milestone DoD M0–M7 + Path A status |
| `docs/PROGRESS.md` | Lived status / what is open next |
| `docs/COMPLIANCE_CHECKLIST.md` | Contest rules map |

Strategy phase packs stay local (see `.gitignore`) so the public repo remains submission-focused.
