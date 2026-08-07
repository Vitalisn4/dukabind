# DukaBind — ADTC 2026

**An offline shop assistant that cannot invent your money.**

Domain: **Corporate / Enterprise** · Runtime: **llama.cpp + GGUF** · 100% offline at inference

Staff ask about credit, payables, or stock in **English**. DukaBind runs **allowlisted SQL** against a local SQLite ledger and lets a small GGUF model narrate *only* the returned rows. Missing data → hard refusal. Change a ledger row → the answer must change.

> Not another shop chatbot — a fail-closed ledger binder for African MSME counters.

**Builder:** Vitalis Ngam · Solo · [Vitalisn4](https://github.com/Vitalisn4) · Africa (ledger fixture: Cameroon / XAF)  
**Gate 1 path:** English only (Path A) · African claim = MSME offline use-case · Qwen2.5-1.5B Q4_K_M

## Start here

| Doc | Purpose |
|---|---|
| [`docs/CODE_WALKTHROUGH.md`](docs/CODE_WALKTHROUGH.md) | Understand every piece of shipped code |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Threat model and binder security rules |
| [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) | Research-backed design choices |
| [`BENCHMARKS.md`](BENCHMARKS.md) | Measured profiler / thermal numbers (never invent) |
| [`MODEL_CARD.md`](MODEL_CARD.md) | Model facts: Qwen2.5-1.5B Q4_K_M, intended use, limits |
| [`evals/heldout/REPORT.md`](evals/heldout/REPORT.md) | Held-out evidence report (T11, flips, both fixtures) |
| [`docs/README.md`](docs/README.md) | Public docs index |
| [`REPORT.md`](REPORT.md) | Gate 1 technical writeup |

Official ADTC template: [adtc-2026-submission-template](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template).

## Quick start (after Ubuntu + Python 3.10+)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Optional: download GGUF (~1.1 GB, needs network once)
# ./download_model.sh

# Binder unit tests (no model required)
PYTHONPATH=. pytest tests/ -q

# Init the shop ledger + try the binder yourself
python -m app.db.connection
PYTHONPATH=. python -m app.cli "Can I give Marie-Claire three crates on credit?"

# Binder offline proof (no model)
bash scripts/offline_check.sh

# Held-out eval: 28 EN prompts across two shop ledgers, cross-shop anti-memorization, ledger-flip proofs
PYTHONPATH=. .venv/bin/python evals/run_heldout.py
```

With local llama-server:

```bash
bash scripts/start_llama_server.sh   # terminal A
PYTHONPATH=. python -m app.narrate_cli "Can I give Marie-Claire three crates on credit?"  # terminal B
```

## Contest links

- [Devpost](https://adtc-2026.devpost.com/) · [Challenge site](https://africadeeptech.org/challenge-2026/)
- [Profiler](https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler) · [Template](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template)
