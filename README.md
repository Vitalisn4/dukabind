# DukaBind — ADTC 2026

**An offline shop assistant that cannot invent your money.**

Domain: **Corporate / Enterprise** · Runtime: **llama.cpp + GGUF** · 100% offline at inference

Staff ask about credit, payables, or stock (English or Swahili). DukaBind runs **allowlisted SQL** against a local SQLite ledger and lets a small GGUF model narrate *only* the returned rows. Missing data → hard refusal. Change a ledger row → the answer must change.

> Not another multilingual shop chatbot — a fail-closed ledger binder.

**Builder:** Vitalis Ngam · Solo · [Vitalisn4](https://github.com/Vitalisn4) · Cameroon

## Start here

| Doc | Purpose |
|---|---|
| [`docs/CODE_WALKTHROUGH.md`](docs/CODE_WALKTHROUGH.md) | **Understand every piece of code** |
| [`docs/COMPLIANCE_CHECKLIST.md`](docs/COMPLIANCE_CHECKLIST.md) | Devpost / Rules / Template compliance |
| [`docs/ADTC-2026-INDEX.md`](docs/ADTC-2026-INDEX.md) | Full strategy document map |
| [`docs/ADTC-2026-ROADMAP.md`](docs/ADTC-2026-ROADMAP.md) | Milestones to Gate 1 / Gate 3 |
| [`docs/ADTC-2026-Build-Kickoff.md`](docs/ADTC-2026-Build-Kickoff.md) | Tools + Day 1–5 |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Threat model and binder security rules |
| [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) | Research-backed design choices |

Official template requirements: see [`TEMPLATE_README.md`](TEMPLATE_README.md) (from [adtc-2026-submission-template](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template)).

## Quick start (after Ubuntu + Python 3.10+)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Optional for Day 2 smoke: download GGUF (~1.1 GB, needs network once)
# ./download_model.sh

# Binder unit tests (no model required)
PYTHONPATH=. pytest tests/ -q

# Init demo ledger + try the binder yourself
python -m app.db.connection
PYTHONPATH=. python -m app.cli "Can I give Amina three crates on credit?"
```

## Contest links

- [Devpost](https://adtc-2026.devpost.com/) · [Challenge site](https://africadeeptech.org/challenge-2026/)
- [Profiler](https://github.com/Africa-Deep-Tech-Foundation/adtc-profiler) · [Template](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template)
