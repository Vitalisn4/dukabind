# DukaBind — Reproduction runbook

**Goal:** from a clean, offline-capable Ubuntu machine to a working, verified DukaBind in ~15 minutes of machine time **plus model download** (~1.1 GB — network-dependent), with every number traceable to a committed artifact.

> ✅ **Verified end-to-end 2026-08-12** from a clean clone of `main` (`e092c7c`): every step below (§2.1–§2.7) executed as written and passed — pytest 46/46, offline proof PASS, model sha256-verified + idempotent, llama.cpp build OK, server healthy, narrated asks correct. See [`CHANGELOG.md`](CHANGELOG.md) `[Unreleased]`.

This document is written for an **auditor or judge**, not for feature contributors. There are no contribution guidelines here because the product is frozen — see [`CHANGELOG.md`](CHANGELOG.md) for the freeze commit. If you want to verify DukaBind end to end, follow this runbook top to bottom.

**Quick facts**

| Item | Value |
|---|---|
| Product | Offline English fail-closed SQLite ledger binder + optional local llama.cpp narration |
| Domain / runtime | `corporate_enterprise` · llama.cpp + GGUF only |
| Model | Qwen2.5-1.5B-Instruct Q4_K_M (pinned GGUF + sha256 in `download_model.sh`) |
| Ship default | `THREADS=2` / `CTX=1024` (thermal-safety freeze) |
| Reference commit | [`CHANGELOG.md`](CHANGELOG.md) — `[1.0.0-gate1]`, tag `v1.0.0-gate1` |

---

## 1. Hardware assumptions

- Ubuntu 22.04 LTS (or close), x86-64 CPU (Intel i5 class / Ryzen 5 class — an i7-8650U participant laptop is sufficient)
- **≥ 8 GB RAM** (the contest target; measured full-stack peak RSS ~1.8 GB, see `BENCHMARKS.md`)
- ~20 GB free disk (llama.cpp build + 1.1 GB GGUF)
- Python 3.10+ and `cmake` + a C compiler (for the llama.cpp build)

No GPU required — `--n-gpu-layers 0` is the frozen flag.

## 2. Fresh-machine reproduction (from zero)

Everything below is run from a fresh clone. Network is needed for the repository clone, Python dependency installation, the llama.cpp source clone, and the model download; after these setup steps, the whole stack runs offline.

### 2.1 Clone + Python environment

```bash
git clone https://github.com/Vitalisn4/dukabind.git
cd dukabind
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2.2 Binder tests — no model required (2 min)

```bash
PYTHONPATH=. pytest tests/ -q        # expect 46 passed
```

This exercises the binder (credit check, supplier balance, stock), the fail-closed refusal rules (NULL limit / NULL outstanding / NULL balance), injection battery, the second ledger fixture `duka_b`, and the T13 metadata guard.

### 2.3 Offline proof — no model required (30 s)

```bash
bash scripts/offline_check.sh        # expect: PASS — binder answers track the ledger
```

Proves the binder answers from the SQLite ledger with no cloud dependency: credit over-limit refusal, supplier NULL-balance refusal, stock answer, and the **ledger-flip** (edit a `credit_limit` row → same question, new answer → rollback → original answer).

### 2.4 Model download — network once, sha256-verified, idempotent

```bash
./download_model.sh                  # ~1.1 GB from HF; pinned sha256 checked
./download_model.sh                  # run twice: second run skips + re-verifies (idempotent)
```

`model/qwen2.5-1.5b-instruct-q4_k_m.gguf` is created. The expected sha256 is pinned in the script (`EXPECTED_SHA256`); a mismatch fails the run.

### 2.5 Build llama.cpp (5–10 min, one-time)

```bash
bash scripts/setup_llama.sh         # clone + CMake Release build into third_party/llama.cpp
```

Requires `cmake`, a C compiler, and `nproc` cores.

### 2.6 Start the server + narrated asks

```bash
bash scripts/start_llama_server.sh   # terminal A — llama-server on 127.0.0.1:8080 (ship default THREADS=2/CTX=1024)
```

Then, in a second terminal:

```bash
source .venv/bin/activate
export PYTHONPATH=.
python -m app.narrate_cli "Can I give Marie-Claire three crates on credit?"   # over-limit → No, arithmetic shown
python -m app.narrate_cli "How much do we owe SOCA?"                         # NULL balance → refusal naming the field
```

The binder `message` is authoritative; the local model only narrates the cited rows (see `docs/CODE_WALKTHROUGH.md`).

### 2.7 Held-out evaluation (5 min)

```bash
PYTHONPATH=. .venv/bin/python evals/run_heldout.py
# expect: 31/31 checks, 0 failures (T11 28/28 = 100.0%, ledger-flip proofs 3/3)
```

28 EN prompts against **two disjoint shop ledgers** (`marche_akwa` + `duka_b`) — credit, payables, stock, NULL-field refusals, adversarial/jailbreak asks, and cross-shop non-leak.

### 2.8 (Optional) Profiler — `benchmarks/` regeneration

The committed `benchmarks/submission.json` is the freeze snapshot; only regenerate it if you are re-measuring on a new host. Requirements are documented in the script header: a Python ≥ 3.11 venv with `adtc-profiler` installed (the repo convention is `.venv311`, created with `uv` or `python3.11 -m venv`), the GGUF from §2.4, and `llama-bench` from the §2.5 build on `PATH`:

```bash
# Python 3.11 venv for adtc-profiler only (uv or python3.11 -m venv both work)
python3.11 -m venv .venv311 && source .venv311/bin/activate
# install adtc-profiler per its README (https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler)
bash scripts/run_profiler_smoke.sh        # writes benchmarks/raw + regenerates the summary
```

See [`benchmarks/README.md`](benchmarks/README.md) and [`BENCHMARKS.md`](BENCHMARKS.md) for methodology. Raw dumps stay gitignored (`benchmarks/raw/`); only the summary and the freeze snapshot are committed.

## 3. Verifying the claims (auditor checklist)

| Claim | How to verify | Expected |
|---|---|---|
| Offline | `bash scripts/offline_check.sh` (incl. `unshare -n` when available) | PASS |
| Binding, not recall | Ledger flip in §2.3 / [`demo/screenshots/02-ledger-flip.png`](demo/screenshots/02-ledger-flip.png) | answer changes when the row changes |
| Fail-closed refusals | `python -m app.cli "How much do we owe SOCA?"` | `ok:false`, named missing field, no invented amount |
| Two shop ledgers, no memorization | `evals/run_heldout.py` + `evals/heldout/REPORT.md` | 31/31; T11 28/28 = 100.0 %; flips 3/3 |
| Measured RSS/TPS/thermal | `BENCHMARKS.md` + `benchmarks/submission.json` (freeze snapshot) | Peak RSS 1821.11 MB · 15.67 tok/s · thermal record honest (2026-08-06 PASS does not reproduce on 2026-08-10 re-run; authoritative P_thermal = official eval machine) |
| Model provenance | `download_model.sh` sha256 + `MODEL_CARD.md` | pinned Qwen Q4_K_M |
| Submission prompts T13-disjoint | `metadata.json` + `tests/test_metadata.py` | exactly 2 prompts; CI enforces disjointness from held-out |

## 4. Frozen configuration (do not change for judging)

| Flag | Frozen value | Where |
|---|---|---|
| Threads | `THREADS=2` (env-overridable for eval-machine runs) | `scripts/start_llama_server.sh` |
| Context | `CTX=1024` | `scripts/start_llama_server.sh` |
| GPU layers | `--n-gpu-layers 0` | `scripts/start_llama_server.sh` |
| Model / quant | Qwen2.5-1.5B-Instruct Q4_K_M | `download_model.sh`, `MODEL_CARD.md` |

Any change to these flags after the freeze is a re-freeze and must be recorded in `CHANGELOG.md`.

## 5. Common failure modes

| Symptom | Cause / fix |
|---|---|
| `llama-server binary not found` | Skip §2.5 or rebuild: `bash scripts/setup_llama.sh` |
| `model missing at model/qwen2.5-…gguf` | Run `./download_model.sh` first (§2.4) |
| sha256 mismatch on download | Network-corrupted download; delete `model/qwen2.5-1.5b-instruct-q4_k_m.gguf` and re-run (idempotent) |
| `pytest` fails on a fresh clone | `.venv` not active / `PYTHONPATH=.` missing — see §2.1–2.2 |
| Held-out eval fails on a fresh clone | `.venv` not active / `PYTHONPATH=.` missing (see §2.1–2.2). No seeding is needed — `evals/run_heldout.py` creates and seeds its temporary SQLite fixtures automatically. |
| Thermal on a hot laptop | This is the documented, honest risk: see `BENCHMARKS.md`. The authoritative P_thermal verdict is the official ADTC eval machine. |
