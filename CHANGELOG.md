# Changelog

All notable changes to DukaBind are documented here, in
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
up to the Gate 1 freeze; pre-1.0 versions are milestone snapshots.

## [Unreleased] - post-freeze (M7, submission readiness)

Docs, CI, and benchmark tooling only, **plus the single deliberate post-freeze
product change: the French + Swahili binder tracks** (owner-approved to claim
the ADTC African-language bonus before submission).

### Added

- `CONTRIBUTING.md` — fresh-machine reproduction runbook written for an auditor/judge.
- `.github/workflows/link-health.yml` — weekly + manual GGUF URL-rot guard (HEAD probe
  + content-length ≥ 1 GB; fails loudly on a dead or non-200 final response). Hardened
  after review: exact `MODEL_URL=` extraction (awk, count == 1), URL passed via step
  `env` (no shell interpolation), and `^[0-9]+$` content-length validation.
- Accuracy self-benchmark evidence: with the current `adtc-profiler` (in-process
  llama-cpp-python path), `bash scripts/run_profiler_smoke.sh --full` emits a real
  participant score — `arc_easy` 50-sample **74.0 %** (`acc_norm`, 2026-08-12),
  recorded in `BENCHMARKS.md` as toolchain evidence only (official S_acc = audit mode).
- French + Swahili binder tracks (`language_scope: ["en","fr","sw"]`):
  language detection (marker-scored, word-boundary safe, ties fall back to
  English), localized deterministic binder messages (credit / supplier / stock /
  all refusals, with internal identifiers localized too), localized narration
  prompts, Swahili product aliases (`sukari`, `unga`, and others), and 31 tests
  (30 in `tests/test_languages.py` plus the narration-gate test in
  `tests/test_ask.py`). Narration ships for English and French (verified on the
  frozen Qwen2.5-1.5B); Swahili is **binder-only** by design because the 1.5B
  model does not narrate Swahili reliably, so the authoritative deterministic
  message is never overridden with a mangled figure.
- Fresh-machine reproduction evidence (M7 Day 1, 2026-08-12): the full
  `CONTRIBUTING.md` runbook was executed from a clean clone of `main`
  (`e092c7c`). Every step passed as documented: venv and `pip install`,
  pytest (46 passed at the time), `offline_check.sh` PASS (including the ledger
  flip and rollback), `download_model.sh` sha256-verified and idempotent,
  llama.cpp Release build OK, server healthy at the ship default
  (`THREADS=2`/`CTX=1024`), and the narrated asks correct (credit No because
  8410 exceeds 8000, and the NULL-balance refusal).

### Changed

- `README.md` — professional judge-facing rewrite: pitch, “why not a chatbot”
  (binding not recall), quick start, intents table (EN/FR/SW examples), demo
  screenshot grid, measured performance table (incl. the accuracy
  self-benchmark), docs index.
- `scripts/run_profiler_smoke.sh` — `--full` runs now emit an “Accuracy self-benchmark”
  section in `benchmarks/submission.summary.md`.
- Docs honesty: `BENCHMARKS.md` / `REPORT.md` / `MODEL_CARD.md` corrected the
  now-false claim that participant-mode accuracy is impossible; the 74.0 %
  self-benchmark is recorded with the audit-mode caveat.

## [1.0.0-gate1] - 2026-08-11

**Freeze commit:** `fe5b506`, tagged `v1.0.0-gate1` (branch `feature/dukabind-m6-freeze`, 2026-08-11)

Code freeze for ADTC 2026 Gate 1 (M6). Packaging/demo only — no product features added.

### Added

- Demo assets for README and the submission: 5 numbered screenshots
  (`demo/screenshots/01…05`) and a 114 s demo video (`demo/demo.mp4`) rendered
  from real CLI output by `scripts/render_demo_assets.py`.
- `CHANGELOG.md` (this file) — freeze commit hash recorded above.
- `docs/FREEZE_CHECKLIST.md` — gate-freeze checklist (T1–T3, T5, T8–T9, T11, T13).
- `benchmarks/submission.json` — freeze snapshot of the measured adtc-profiler
  participant output (2026-08-11, `--skip-accuracy`; raw dumps stay gitignored).

### Changed

- `benchmarks/submission.summary.md` — regenerated from the 2026-08-11 freeze
  re-run: Peak RSS 1821.11 MB, Generation TPS 15.67 tok/s, TTFT 10548.82 ms,
  core temp peak 100.0 °C / throttled (honest FAIL on this laptop).
- `benchmarks/.gitignore` — explicit `!submission.json` exception for the
  committed freeze snapshot.
- Docs: `README.md` (Demo section), `REPORT.md` (freeze re-run line),
  `docs/CODE_WALKTHROUGH.md` (renderer row).

### Fixed

- None (product code frozen since PR #5; fail-closed NULL-outstanding handling
  already landed on `main`).

## [0.5.0] - 2026-08-10

### Added

- Fail-closed refusal when a customer row has `outstanding IS NULL`
  (`refuse_reason: "outstanding_null"`) — previously `int(None)` crashed.
  Unit + end-to-end pipeline tests (suite 44 → 46). (PR #5.)

### Changed

- `BENCHMARKS.md` / `MODEL_CARD.md` / `REPORT.md` / `docs/CODE_WALKTHROUGH.md`:
  thermal honesty — the 2026-08-06 `THREADS=2`/`CTX=1024` soak PASS (peak
  84.0 °C) **no longer reproduces**; the identical 2026-08-10 re-run FAILED
  (cold-start peak 89.0 °C, hot-start 98.0 °C). Authoritative P_thermal stays
  with the official ADTC eval machine.

## [0.4.0] - 2026-08-07

### Added

- M5 evidence pack (PR #4): `MODEL_CARD.md`, committed held-out report
  (`evals/heldout/REPORT.md`, T11 28/28 = 100 %, flips 3/3), T13-disjoint
  submission prompts in `metadata.json` (`tp_001` Esther Tchamba NULL-refuse,
  `tp_002` Chidi Okafor × Sucre grounded No), CI held-out report freshness gate.
- Ship default frozen: `THREADS=2` / `CTX=1024` in `scripts/start_llama_server.sh`.

## [0.3.0] - 2026-08-06

### Added

- M2 measurement toolkit (PR #2): `offline_check.sh`, profiler smoke, thread
  matrix, thermal soak scripts; measured tables in `BENCHMARKS.md`.
- EN held-out set (28 prompts) + second ledger fixture `duka_b` (PR #3);
  `evals/run_heldout.py` — 31/31 checks; T11 scored 100.0 %.

## [0.2.0] - 2026-08-01

### Added

- M1 binder vertical slice: three allowlisted intents (credit, supplier
  balance, stock), fail-closed refusals, ledger-flip proof, offline proof.

## [0.1.0] - 2026-07-25

### Added

- M0 setup: repo scaffold from the official ADTC template, `metadata.json`,
  `download_model.sh`, SECURITY / DESIGN docs, initial binder tests.
