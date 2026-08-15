# DukaBind: Reproduction runbook

From a clean Ubuntu machine to a verified DukaBind. Setup needs network (clone, Python packages, llama.cpp source, model download). After that, the stack runs offline. Numbers below cite committed artifacts in [`REPORT.md`](REPORT.md) and [`BENCHMARKS.md`](BENCHMARKS.md).

This is an **auditor runbook**, not a contributor guide. The product is frozen. Follow the sections in order.

**Quick facts**

| Item | Value |
|---|---|
| Product | Offline EN/FR/SW fail-closed SQLite ledger binder; optional local llama.cpp narration (en/fr) |
| Domain / runtime | `corporate_enterprise` · llama.cpp + GGUF only |
| Model | Qwen2.5-1.5B-Instruct Q4_K_M (GGUF + sha256 in `download_model.sh`) |
| Defaults | `THREADS=2` / `CTX=1024` |
| Source | Clone **`main`**. Tag `v1.0.0-gate1` is a packaging snapshot. |

---

## 1. Hardware

- Ubuntu 22.04 LTS (or close), x86-64 (Intel i5 / Ryzen 5 class; an i7-8650U is sufficient)
- **≥ 8 GB RAM** (measured full-stack peak RSS ~1.8 GB; see `BENCHMARKS.md`)
- ~20 GB free disk (llama.cpp build + 1.1 GB GGUF)
- Python 3.10+, `cmake`, and a C compiler

No GPU. `--n-gpu-layers 0` is the frozen flag.

## 2. Fresh-machine reproduction

### 2.1 Clone and Python environment

```bash
git clone https://github.com/Vitalisn4/dukabind.git
cd dukabind
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expect: pytest **78 passed**, held-out **40/40** (T11 **37/37**, flips 3/3), `offline_check.sh` **PASS**.

### 2.2 Binder tests (no model, ~2 min)

```bash
PYTHONPATH=. pytest tests/ -q        # expect 78 passed
```

Covers credit, supplier balance, stock, NULL-field refusals, injection cases, the second ledger `duka_b`, French and Swahili tracks, and the T13 metadata guard.

### 2.3 Offline proof (no model, ~30 s)

```bash
bash scripts/offline_check.sh        # expect PASS
```

Confirms ledger-backed answers with no cloud: credit over-limit, supplier NULL-balance refusal, stock, and a **ledger flip** (edit `credit_limit`, same question, new answer, rollback).

### 2.4 Model download (network once)

```bash
./download_model.sh                  # ~1.1 GB; sha256 checked
./download_model.sh                  # second run skips and re-verifies
```

Writes `model/qwen2.5-1.5b-instruct-q4_k_m.gguf`. Expected hash is `EXPECTED_SHA256` in the script.

### 2.5 Build llama.cpp (~5-10 min, once)

```bash
bash scripts/setup_llama.sh          # CMake Release build in third_party/llama.cpp
```

Needs `cmake`, a C compiler, and CPU cores from `nproc`.

### 2.6 Local server and narrated asks

Terminal A:

```bash
bash scripts/start_llama_server.sh   # 127.0.0.1:8080, THREADS=2, CTX=1024
```

Terminal B:

```bash
source .venv/bin/activate
export PYTHONPATH=.
python -m app.narrate_cli "Can I give Marie-Claire three crates on credit?"
python -m app.narrate_cli "How much do we owe SOCA?"
```

The binder `message` is authoritative. The model narrates cited rows only.

### 2.7 Held-out evaluation (~5 min)

```bash
PYTHONPATH=. .venv/bin/python evals/run_heldout.py
# expect: 40/40, T11 37/37 = 100.0%, flips 3/3
```

**37 prompts** (28 English, 5 French, 4 Swahili) on two disjoint ledgers (`marche_akwa`, `duka_b`): credit, payables, stock, NULL refusals, adversarial asks, and cross-shop non-leak. See `evals/heldout/prompts.json` and `tests/test_languages.py`.

### 2.8 Optional: French, Swahili, and bare GGUF

```bash
PYTHONPATH=. python -m app.cli "Puis-je donner trois caisses de crédit à Marie-Claire ?"
PYTHONPATH=. python -m app.cli "Tunadaiwa kiasi gani na SOCA?"
```

English and French may be narrated. Swahili is binder-only (`MODEL_CARD.md`). The GGUF is a standard Qwen2.5 file and loads in LM Studio or Ollama; that is compatibility, not a shipped runtime. llama.cpp is the only runtime this repo builds. Binder-only `python -m app.cli` never needs the model.

### 2.9 Optional: profiler regeneration

`benchmarks/submission.json` is the freeze snapshot. Regenerate only when measuring a new host. Needs Python ≥ 3.11, `adtc-profiler`, the GGUF from §2.4, and `llama-bench` from §2.5:

```bash
python3.11 -m venv .venv311 && source .venv311/bin/activate
# install adtc-profiler: https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler
bash scripts/run_profiler_smoke.sh
```

See [`benchmarks/README.md`](benchmarks/README.md) and [`BENCHMARKS.md`](BENCHMARKS.md). Raw dumps stay in gitignored `benchmarks/raw/`.

## 3. Claim checklist

| Claim | How to verify | Expected |
|---|---|---|
| Offline | `bash scripts/offline_check.sh` (`unshare -n` when available) | PASS |
| Binding, not recall | Ledger flip in §2.3; [`demo/screenshots/02-ledger-flip.png`](demo/screenshots/02-ledger-flip.png) | Answer changes with the row |
| Fail-closed refusals | `python -m app.cli "How much do we owe SOCA?"` | `ok: false`, named missing field, no invented amount |
| Two ledgers | `evals/run_heldout.py` and `evals/heldout/REPORT.md` | 40/40; T11 37/37; flips 3/3 |
| RSS / TPS / thermal | `BENCHMARKS.md` and `benchmarks/submission.json` | Peak RSS 1821.11 MB · 15.67 tok/s. Thermal: 2026-08-06 PASS does not reproduce on 2026-08-10; official P_thermal is the eval machine |
| Model provenance | `download_model.sh` sha256 and `MODEL_CARD.md` | Pinned Qwen Q4_K_M |
| T13 prompts | `metadata.json` and `tests/test_metadata.py` | Exactly two prompts, disjoint from held-out |

## 4. Frozen configuration

| Flag | Value | Where |
|---|---|---|
| Threads | `THREADS=2` (overridable for eval-machine runs) | `scripts/start_llama_server.sh` |
| Context | `CTX=1024` | `scripts/start_llama_server.sh` |
| GPU layers | `--n-gpu-layers 0` | `scripts/start_llama_server.sh` |
| Model / quant | Qwen2.5-1.5B-Instruct Q4_K_M | `download_model.sh`, `MODEL_CARD.md` |

Record any later change in `REPORT.md` and `BENCHMARKS.md`.

## 5. Common failures

| Symptom | Cause / fix |
|---|---|
| `llama-server binary not found` | Run `bash scripts/setup_llama.sh` |
| Model missing at `model/qwen2.5-…gguf` | Run `./download_model.sh` first (§2.4) |
| sha256 mismatch | Delete the GGUF and re-run `download_model.sh` |
| `pytest` fails on a fresh clone | Activate `.venv` and set `PYTHONPATH=.` (§2.1-2.2) |
| Held-out eval fails on a fresh clone | Same as above. The runner seeds temporary SQLite fixtures itself |
| Thermal on a hot laptop | Documented in `BENCHMARKS.md`. Official P_thermal is the ADTC eval machine |
