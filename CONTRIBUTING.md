# DukaBind: Reproduction runbook

From a clean machine to a verified DukaBind. Setup needs network (clone, Python packages, llama.cpp source, model download). After that, the stack runs offline. Numbers below cite committed artifacts in [`REPORT.md`](REPORT.md) and [`BENCHMARKS.md`](BENCHMARKS.md).

This is an **auditor runbook**, not a contributor guide. The product is frozen. Follow the sections in order.

**Quick facts**

| Item | Value |
|---|---|
| Product | Offline EN/FR/SW fail-closed SQLite ledger binder; optional local llama.cpp narration (en/fr) |
| Domain / runtime | `corporate_enterprise` . llama.cpp + GGUF only |
| Model | Qwen2.5-1.5B-Instruct Q4_K_M (GGUF + sha256 in `download_model.sh`) |
| Defaults | `THREADS=2` / `CTX=1024` |
| Source | Detached checkout of the commit that last changed this file. |

---

## 1. Hardware

- **Ubuntu 22.04+**, **macOS 12+**, or **Windows 10+** (x86-64)
- Intel i5 / Ryzen 5 class or better (an i7-8650U is sufficient)
- **8 GB RAM or more** (measured full-stack peak RSS ~1.8 GB; see `BENCHMARKS.md`)
- ~20 GB free disk (llama.cpp build + 1.1 GB GGUF)
- Python 3.10+, `cmake`, and a C compiler

No GPU. `--n-gpu-layers 0` is the frozen flag.

### Platform-specific prerequisites

<details><summary><b>Ubuntu / Linux</b></summary>

```bash
sudo apt update && sudo apt install -y python3 python3-venv cmake build-essential
```

</details>

<details><summary><b>macOS</b></summary>

```bash
xcode-select --install   # installs C compiler and make
brew install cmake        # if Homebrew is available
```

</details>

<details><summary><b>Windows</b></summary>

Install [Python 3.10+](https://www.python.org/downloads/) (check "Add to PATH").
Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) with "Desktop development with C++" workload.
Install [CMake](https://cmake.org/download/) or use `pip install cmake`.

</details>

---

## 2. Fresh-machine reproduction

### 2.1 Clone and Python environment

<details><summary><b>Ubuntu / Linux / macOS</b></summary>

```bash
git clone https://github.com/Vitalisn4/dukabind.git
cd dukabind
git checkout --detach "$(git log -1 --format=%H -- CONTRIBUTING.md)"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

</details>

<details><summary><b>Windows (PowerShell)</b></summary>

```powershell
git clone https://github.com/Vitalisn4/dukabind.git
cd dukabind
git checkout --detach "$(git log -1 --format=%H -- CONTRIBUTING.md)"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

</details>

That checkout pins the runbook you are reading, so a later push to `main` cannot change the commands or expected counts. On that revision, expect pytest **128 passed**, held-out **40/40** (bind/refuse **37/37**, flips 3/3).

### 2.2 Binder tests (no model, ~2 min)

<details><summary><b>Ubuntu / Linux / macOS</b></summary>

```bash
PYTHONPATH=. pytest tests/ -q        # expect 128 passed
```

</details>

<details><summary><b>Windows (PowerShell)</b></summary>

```powershell
$env:PYTHONPATH='.'; pytest tests/ -q        # expect 128 passed
```

</details>

Covers credit, supplier balance, stock, NULL-field refusals, injection cases, the second ledger `duka_b`, French and Swahili tracks, and submission-prompt independence.

### 2.3 Offline proof (no model, ~30 s)

<details><summary><b>Ubuntu / Linux / macOS</b></summary>

```bash
bash scripts/offline_check.sh        # expect PASS
```

Note: On macOS, `unshare` is not available. The binder path is still proven via `pytest` and the held-out eval.

</details>

<details><summary><b>Windows</b></summary>

The offline proof script uses Linux-specific `unshare`. On Windows, the binder path is proven via:

```powershell
$env:PYTHONPATH='.'; pytest tests/ -q
$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe evals\run_heldout.py
```

</details>

Confirms ledger-backed answers with no cloud: credit over-limit, supplier NULL-balance refusal, stock, and a **ledger flip** (edit `credit_limit`, same question, new answer, rollback).

### 2.4 Model download (network once)

<details><summary><b>Ubuntu / Linux / macOS</b></summary>

```bash
./download_model.sh                  # ~1.1 GB; sha256 checked
./download_model.sh                  # second run skips and re-verifies
```

</details>

<details><summary><b>Windows (PowerShell)</b></summary>

```powershell
.\download_model.ps1                 # or: bash download_model.sh (if Git Bash is installed)
```

If you do not have bash on Windows, download the file manually:
URL: `https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf`
Save to: `model\qwen2.5-1.5b-instruct-q4_k_m.gguf`

</details>

Writes `model/qwen2.5-1.5b-instruct-q4_k_m.gguf`. Expected hash is `EXPECTED_SHA256` in the script.

### 2.5 Build llama.cpp (~5-10 min, once)

<details><summary><b>Ubuntu / Linux / macOS</b></summary>

```bash
bash scripts/setup_llama.sh          # CMake Release build in third_party/llama.cpp
```

</details>

<details><summary><b>Windows</b></summary>

```powershell
# If you have bash (Git Bash or WSL):
bash scripts\setup_llama.sh

# Otherwise, build manually:
cd third_party\llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j
```

</details>

Needs `cmake` and a C compiler.

### 2.6 Local server and narrated asks

<details><summary><b>Ubuntu / Linux / macOS</b></summary>

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

</details>

<details><summary><b>Windows (PowerShell)</b></summary>

Terminal A:

```powershell
.\scripts\start_llama_server.ps1     # or: bash scripts\start_llama_server.sh
```

Terminal B:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH='.'
python -m app.narrate_cli "Can I give Marie-Claire three crates on credit?"
python -m app.narrate_cli "How much do we owe SOCA?"
```

</details>

The binder `message` is the only financial answer. Optional LLM narration is untrusted polish of cited rows; it is not validated for figures.

### 2.7 Held-out evaluation (~5 min)

<details><summary><b>Ubuntu / Linux / macOS</b></summary>

```bash
PYTHONPATH=. .venv/bin/python evals/run_heldout.py
# expect: 40/40, bind/refuse 37/37 = 100.0%, flips 3/3
```

</details>

<details><summary><b>Windows (PowerShell)</b></summary>

```powershell
$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe evals\run_heldout.py
# expect: 40/40, bind/refuse 37/37 = 100.0%, flips 3/3
```

</details>

**37 prompts** (28 English, 5 French, 4 Swahili) on two disjoint ledgers (`marche_akwa`, `duka_b`): credit, payables, stock, NULL refusals, adversarial asks, and cross-shop non-leak.

### 2.8 Optional: French, Swahili, and bare GGUF

<details><summary><b>Ubuntu / Linux / macOS</b></summary>

```bash
PYTHONPATH=. python -m app.cli "Puis-je donner trois caisses de crédit à Marie-Claire ?"
PYTHONPATH=. python -m app.cli "Tunadaiwa kiasi gani na SOCA?"
```

</details>

<details><summary><b>Windows (PowerShell)</b></summary>

```powershell
$env:PYTHONPATH='.'; python -m app.cli "Puis-je donner trois caisses de crédit à Marie-Claire ?"
$env:PYTHONPATH='.'; python -m app.cli "Tunadaiwa kiasi gani na SOCA?"
```

</details>

English and French may be narrated; that polish is untrusted. Swahili is binder-only (`MODEL_CARD.md`). The GGUF is a standard Qwen2.5 file and loads in LM Studio or Ollama; that is compatibility, not a shipped runtime. llama.cpp is the only runtime this repo builds. Binder-only `python -m app.cli` never needs the model.

### 2.9 Optional: profiler regeneration

`benchmarks/submission.json` is the freeze snapshot. Regenerate only when measuring a new host. Needs Python 3.11+, `adtc-profiler`, the GGUF from section 2.4, and `llama-bench` from section 2.5:

<details><summary><b>Ubuntu / Linux / macOS</b></summary>

```bash
python3.11 -m venv .venv311 && source .venv311/bin/activate
# install adtc-profiler: https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler
bash scripts/run_profiler_smoke.sh
```

</details>

<details><summary><b>Windows (PowerShell)</b></summary>

```powershell
python -m venv .venv311; .\.venv311\Scripts\Activate.ps1
pip install "git+https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler.git"
adtc-profiler run --submission . --mode participant --output submission.json --skip-accuracy
```

</details>

See [`benchmarks/README.md`](benchmarks/README.md) and [`BENCHMARKS.md`](BENCHMARKS.md). Raw dumps stay in gitignored `benchmarks/raw/`.

---

## 3. Claim checklist

| Claim | How to verify | Expected |
|---|---|---|
| Offline | `bash scripts/offline_check.sh` (Linux/macOS); `pytest` + held-out eval (Windows) | PASS |
| Binding, not recall | Ledger flip in section 2.3 | Answer changes with the row |
| Fail-closed refusals | `python -m app.cli "How much do we owe SOCA?"` | `ok: false`, named missing field, no invented amount |
| Two ledgers | `evals/run_heldout.py` and `evals/heldout/REPORT.md` | 40/40; bind/refuse 37/37; flips 3/3 |
| RSS / TPS / thermal | `BENCHMARKS.md` and `benchmarks/submission.json` | Peak RSS 1826.23 MB, 17.35 tok/s |
| Model provenance | `download_model.sh` sha256 and `MODEL_CARD.md` | Pinned Qwen Q4_K_M |
| Submission prompt independence | `metadata.json` and `tests/test_metadata.py` | CI fails if either ask string is in held-out |

---

## 4. Frozen configuration

| Flag | Value | Where |
|---|---|---|
| Threads | `THREADS=2` (overridable for eval-machine runs) | `scripts/start_llama_server.sh` |
| Context | `CTX=1024` | `scripts/start_llama_server.sh` |
| GPU layers | `--n-gpu-layers 0` | `scripts/start_llama_server.sh` |
| Model / quant | Qwen2.5-1.5B-Instruct Q4_K_M | `download_model.sh`, `MODEL_CARD.md` |

Record any later change in `REPORT.md` and `BENCHMARKS.md`.

---

## 5. Common failures

| Symptom | Cause / fix |
|---|---|
| `llama-server binary not found` | Run `bash scripts/setup_llama.sh` (Linux/macOS) or build manually (Windows) |
| Model missing at `model/qwen2.5-...gguf` | Run `./download_model.sh` first (section 2.4) |
| sha256 mismatch | Delete the GGUF and re-run `download_model.sh` |
| `pytest` fails on a fresh clone | Activate `.venv` and set `PYTHONPATH=.` (section 2.1-2.2) |
| Held-out eval fails on a fresh clone | Same as above. The runner seeds temporary SQLite fixtures itself |
| Thermal on a hot laptop | Documented in `BENCHMARKS.md`. Official P_thermal is the ADTC eval machine |
| Windows: `bash` not found | Install Git for Windows (includes Git Bash) or use WSL |
