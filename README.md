# DukaBind

**An offline shop assistant that cannot invent your money.**

DukaBind answers **credit**, **supplier payable**, and **stock** questions for African MSME counters. Staff ask in **English, French, or Swahili**. Answers come from a local SQLite ledger through allowlisted queries. A local GGUF model may polish the wording of those rows, but narration is **untrusted** and is not a source of figures. The binder `message` is the only financial answer. Missing data produces a hard refusal. Change a ledger row, and the answer must change.

> Domain: **Corporate / Enterprise** · Runtime: **llama.cpp + GGUF** · Offline at inference · Languages: English, French, Swahili (`language_scope: ["en", "fr", "sw"]`)

---

## Why this is not another chatbot

Most offline LLM demos answer from model memory. Asked for a customer's balance, they produce a plausible number. DukaBind cannot.

1. The model never sees the database. It receives a **JSON citation** of the rows an allowlisted query returned, and a rule that forbids amounts absent from that block.
2. The binder's deterministic `message` is **authoritative**. LLM narration is untrusted polish. Do not treat it as a source of figures. The model does not choose SQL or compute balances.
3. Every ask path is **read-only**: no cloud, no telemetry, no writes. Binder-only asks make no network call. Optional narration talks only to the local model on **127.0.0.1**.

Proof: edit one `credit_limit` row and ask the same question again. The answer follows the row. That is **binding, not recall**.

---

## Quick start

**Prerequisites:** Python 3.10+, `cmake`, a C compiler. No GPU required.

<details><summary><b>Ubuntu / Linux</b></summary>

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Binder tests (no model required): 128 passed
PYTHONPATH=. pytest tests/ -q

# Seed the ledger and ask (read-only, no model)
python -m app.db.connection
PYTHONPATH=. python -m app.cli "Can I give Marie-Claire three crates on credit?"

# Offline proof: answers track the ledger with no cloud dependency
bash scripts/offline_check.sh

# Held-out evaluation: EN/FR/SW, two shops, ledger-flip proofs
PYTHONPATH=. .venv/bin/python evals/run_heldout.py
```

</details>

<details><summary><b>macOS</b></summary>

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Binder tests (no model required): 128 passed
PYTHONPATH=. pytest tests/ -q

# Seed the ledger and ask (read-only, no model)
python -m app.db.connection
PYTHONPATH=. python -m app.cli "Can I give Marie-Claire three crates on credit?"

# Offline proof (no unshare; binder path still proven)
bash scripts/offline_check.sh

# Held-out evaluation
PYTHONPATH=. .venv/bin/python evals/run_heldout.py
```

</details>

<details><summary><b>Windows (PowerShell)</b></summary>

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Binder tests (no model required): 128 passed
$env:PYTHONPATH='.'; pytest tests/ -q

# Seed the ledger and ask (read-only, no model)
python -m app.db.connection
$env:PYTHONPATH='.'; python -m app.cli "Can I give Marie-Claire three crates on credit?"

# Held-out evaluation
$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe evals\run_heldout.py
```

Note: `offline_check.sh` uses Linux-specific `unshare`. On Windows, the binder path is still proven via `pytest` and `evals/run_heldout.py`.

</details>

**Optional local narration** (GGUF + llama.cpp):

```bash
./download_model.sh                 # once; ~1.1 GB, sha256-verified
bash scripts/setup_llama.sh         # builds llama-server
bash scripts/start_llama_server.sh  # terminal A, 127.0.0.1:8080
PYTHONPATH=. python -m app.narrate_cli "Can I give Marie-Claire three crates on credit?"  # terminal B
```

Full reproduction runbook: [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## What it answers

| Intent | Example (EN / FR / SW) | Behaviour |
|---|---|---|
| Credit check | "Can I give Marie-Claire three crates on credit?" / "Puis-je donner trois caisses de crédit à Marie-Claire ?" / "Ninaweza kumpa Marie-Claire kreti ya makreti matatu?" | Arithmetic against the ledger limit; Yes / No with the math, in the ask language |
| Credit headroom | "How much credit does Fotso have left?" / "Combien de crédit reste-t-il pour Fotso ?" / "Fotso ana mkopo uliobaki kiasi gani?" | Shows limit − outstanding = available credit |
| Supplier balance | "How much do we owe SOCA?" / "Combien devons-nous à SOCA ?" / "Tunadaiwa kiasi gani na SOCA?" | Reads `balance_owed`, localized |
| Stock on hand | "How many soda crates on hand?" / "Combien de sodas en stock ?" / "Tuna hifadhi ngapi ya soda?" | Reads `on_hand`, localized |
| Total stock value | "What is the total value of all stock?" / "Quelle est la valeur totale du stock ?" / "Thamani ya jumla ya bidhaa ni ngapi?" | Sums on_hand × unit_price across all SKUs |
| Total outstanding debt | "What is the total outstanding debt?" / "Quelle est la dette totale ?" / "Deni la jumla ni lipi?" | Sums outstanding across all active customers |
| Total supplier payables | "How much do we owe all suppliers?" / "Combien devons-nous à tous les fournisseurs ?" / "Tunadaiwa jumla kiasi gani na wauzaji wote?" | Sums balance_owed across all suppliers |
| Anything else | "Who owns this shop?", jailbreaks | Refusal: `unknown_intent` or `not_found`, in the ask language |

**Narration.** English and French may be polished by the local Qwen2.5-1.5B Q4_K_M model. That polish is untrusted and is not a source of figures. Swahili is **binder-only**: the 1.5B model does not narrate Swahili reliably, so money figures stay on the deterministic message.

**Fail-closed.** A required money field that is `NULL` produces a refusal that names the field. No balance, limit, or amount is invented. Applies to `credit_limit`, `outstanding`, and `balance_owed`.

**Two shop ledgers.** Marché Akwa Viviane (Douala) and Marché Nkolmébé (`duka_b`, Yaoundé) use disjoint names and numbers. Held-out flip checks (3/3) show that answers follow the live ledger.

---

## Demo

[Watch the 108-second demo](https://vitalisn4.github.io/dukabind/demo/) (credit bind, ledger flip, fail-closed refusal, French and Swahili asks, offline proof, measured numbers). Frames are rendered from real CLI output. The product interface is the CLI; there is no staff GUI.

[![DukaBind demo](demo/demo-poster.png)](https://vitalisn4.github.io/dukabind/demo/)

<video controls muted preload="metadata" width="100%" poster="https://vitalisn4.github.io/dukabind/demo/demo-poster.png" src="https://vitalisn4.github.io/dukabind/demo/demo.mp4"></video>

File: [`demo/demo.mp4`](demo/demo.mp4) (108 s, 1280×720, H.264 Baseline + AAC).

| | |
|---|---|
| ![Credit bind answer](demo/screenshots/01-credit-answer.png) | ![Ledger flip](demo/screenshots/02-ledger-flip.png) |
| Credit ask answered from the ledger rows it read, with arithmetic shown. | One `credit_limit` row changes in a rolled-back transaction; the same question returns a new answer. |
| ![Fail-closed refusal](demo/screenshots/03-refuse-null-field.png) | ![Offline proof](demo/screenshots/04-offline-proof.png) |
| A missing field produces a named refusal. Never an invented balance. | `offline_check.sh` shows answers track the ledger with no cloud dependency. |
| ![Measured numbers](demo/screenshots/05-measured-numbers.png) | ![French and Swahili](demo/screenshots/06-multilingual.png) |
| Peak RSS 1826.23 MB, 17.35 tok/s. Thermal record in [`BENCHMARKS.md`](BENCHMARKS.md). | French and Swahili asks answered in-language from the binder, with no model required. |

---

## Measured performance

| Metric | Result | Target |
|---|---:|---:|
| Peak RSS (full stack) | **1826.23 MB** | < 5.5 GB self-limit |
| Generation speed | **17.35 tok/s** | ≥ 15 tok/s |
| Time to first token | 8175.55 ms | n/a |
| Accuracy self-benchmark | **74.0%** on `arc_easy` (50 samples, `acc_norm`); toolchain evidence only. Official S_acc is audit mode. | n/a |
| Held-out bind/refuse | **37/37 = 100.0%** | ≥ 90% |
| Held-out checks | **40/40**, flip proofs 3/3 | n/a |
| Thermal soak (10 min) | Documented in [`BENCHMARKS.md`](BENCHMARKS.md). A 2026-08-06 PASS on the build laptop does not reproduce on 2026-08-10. The official verdict is the ADTC eval machine. | < 85 °C |

Source: freeze snapshot `benchmarks/submission.json` (2026-08-18). Thread matrix and thermal soak history in [`BENCHMARKS.md`](BENCHMARKS.md). Evidence: [`BENCHMARKS.md`](BENCHMARKS.md) · [`benchmarks/submission.summary.md`](benchmarks/submission.summary.md) · [`MODEL_CARD.md`](MODEL_CARD.md) · [`evals/heldout/REPORT.md`](evals/heldout/REPORT.md).

---

## Documentation

| Doc | Purpose |
|---|---|
| [`docs/SECURITY.md`](docs/SECURITY.md) | Threat model and binder controls (C1-C10) |
| [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) | Design choices and rejected alternatives |
| [`docs/README.md`](docs/README.md) | Public documentation index |
| [`REPORT.md`](REPORT.md) | Technical writeup (problem, design, benchmarks) |
| [`MODEL_CARD.md`](MODEL_CARD.md) | Qwen2.5-1.5B Q4_K_M: intended use, limits, honesty |
| [`BENCHMARKS.md`](BENCHMARKS.md) | Measured profiler and thermal numbers |
| [`evals/heldout/REPORT.md`](evals/heldout/REPORT.md) | Held-out evidence: 37/37 bind/refuse, ledger-flip proofs, two shops |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Reproduction runbook |

---

## Model and license

- **Model:** Qwen2.5-1.5B-Instruct, GGUF **Q4_K_M** (~1.12 GB), sha256-pinned in [`download_model.sh`](download_model.sh). See [`MODEL_CARD.md`](MODEL_CARD.md).
- **License:** GPL-3.0 for application code. Model weights are upstream Apache-2.0. See [`NOTICE`](NOTICE).

---

## Contest

ADTC 2026 · [Devpost](https://adtc-2026.devpost.com/) · [Challenge site](https://africadeeptech.org/challenge-2026/) · [adtc-profiler](https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler) · [Submission template](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template)

**Builder:** Vitalis Ngam · Solo · [Vitalisn4](https://github.com/Vitalisn4) · Cameroon (ledger fixture: Douala / XAF)
