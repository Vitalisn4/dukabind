# Changelog

All notable changes to DukaBind are documented here, in
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
up to the Gate 1 freeze; pre-1.0 versions are milestone snapshots.

## [1.0.0-gate1] - 2026-08-11

**Freeze commit:** `fe5b506`, tagged `v1.0.0-gate1` (branch `feature/dukabind-m6-freeze`, 2026-08-11)

Code freeze for ADTC 2026 Gate 1 (M6). Packaging/demo only — no product features added.

### Added

- Demo assets for README and the submission: 5 numbered screenshots
  (`demo/screenshots/01…05`) and a 114 s demo video (`demo/demo.mp4`) rendered
  from real CLI output by `scripts/render_demo_assets.py`. The demo
  storyboard and video transcript (`demo/VIDEO.md`) are kept **local-only**
  (gitignored) by design — production notes, not submission artifacts.
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
  `docs/CODE_WALKTHROUGH.md` (renderer row). Local-only strategy docs
  (`docs/PROGRESS.md`, Kickoff, Roadmap, COMPLIANCE_CHECKLIST — gitignored
  by design) updated on disk: M6 done, thermal honesty carried through.

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
