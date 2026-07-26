# Code walkthrough

**Status:** Living document — update when modules, commands, or Gate milestones change  
**Last updated:** 2026-07-26  
**Audience:** Contributors, Gate reviewers, and auditors reading a clean checkout

This guide explains the shipped codebase: what each module does, how data flows, and which commands verify behaviour. Prefer short updates here over adding one-off scratch notes to the public tree.

---

## 1. Architecture (30 seconds)

```text
Staff question (EN/SW)
        │
        ▼
  intents.py     →  intent + slots (credit / supplier / stock)
        │
        ▼
  allowlist.py   →  one named SQL statement with bound parameters
        │
        ▼
  refuse.py      →  NULL / missing fields → hard refuse
                 →  credit arithmetic in Python (not in the model)
        │
        ▼
  LLM (optional) →  narrates citation JSON only; never invents balances
```

Ledger numbers come from SQLite and deterministic Python math. The GGUF model may polish wording; it does not choose SQL or invent amounts. That separation is the product thesis for African MSME counters on offline commodity laptops.

---

## 2. Contest-required files

| File | Role | Requirement |
|---|---|---|
| `metadata.json` | Team, domain, model, held-out prompts | Template + evaluator |
| `download_model.sh` | Fetches GGUF into `model/` with sha256 check | No weights in git; public URL |
| `REPORT.md` | Technical writeup | Devpost submission |
| `.gitignore` | Ignores `*.gguf`, local strategy notes, venvs | Template + hygiene |
| `LICENSE` / `NOTICE` | GPL-3.0 code license + provenance | Cite OSS |

**Submitter (public attribution)**

- Name: Vitalis Ngam  
- GitHub: [Vitalisn4](https://github.com/Vitalisn4)  
- `team_id`: provisional `vitalisn4` (replace if ADTF issues an official ID)  
- Solo · domain `corporate_enterprise` · `african_alpha_claim: true`

Contact email for submission lives in `metadata.json` / Devpost only — not duplicated in this walkthrough.

---

## 3. Application modules

### Database

| Path | Role |
|---|---|
| `app/db/schema.sql` | Tables: `customers`, `suppliers`, `skus`, `audit_log`, `shop_meta`. Nullable `credit_limit` / `balance_owed` enable fail-closed refusals. |
| `app/db/seed_demo.sql` | Synthetic Douala demo shop (XAF). Not real PII. Amina over-limit and Bidco NULL balance are intentional fixtures. |
| `app/db/connection.py` | Opens SQLite with WAL + foreign keys; loads schema/seed. Run: `python -m app.db.connection` |

### Binder (load-bearing path)

| Path | Role |
|---|---|
| `app/binder/allowlist.py` | Finite named queries; unknown name → `ValueError`; `?` binds (controls **C1/C2**). |
| `app/binder/intents.py` | Rule-based EN/SW routing; extracts customer, supplier, SKU, quantity. |
| `app/binder/refuse.py` | Fail-closed messages; credit math in Python (control **C4**). |
| `app/binder/citations.py` | Compact ledger JSON for narration prompts. |
| `app/binder/pipeline.py` | `handle_ask` — full answer path without a model. |

### Local narration

| Path | Role |
|---|---|
| `app/prompts/narrate.py` | System/user prompts; model must copy binder numbers. |
| `app/llm/client.py` | HTTP to `127.0.0.1` only; rejects redirects (control **C5**). |
| `app/llm/ask.py` | Binder first; `message` stays binder; optional text in `narration`. |
| `app/cli.py` / `app/narrate_cli.py` | Binder-only and binder+LLM CLIs. |

### Tests

| Path | Coverage |
|---|---|
| `tests/test_binder.py` | Allowlist reject, over-limit, NULL refuse, stock, Swahili, ledger flip |
| `tests/test_ask.py` | Refuse skips LLM; binder `message` authority; loopback URL reject |

---

## 4. Essential commands

```bash
# From the repository root
source .venv/bin/activate

PYTHONPATH=. pytest tests/ -q
python -m app.db.connection
PYTHONPATH=. python -m app.cli "Can I give Amina three crates on credit?"
PYTHONPATH=. python -m app.cli "How much do we owe Bidco Distributors?"
```

### Virtual environments

| Env | Purpose |
|---|---|
| `.venv` | Application, pytest, narration CLI (Python 3.10+) |
| `.venv311` | `adtc-profiler` only (requires Python ≥3.11) |

```bash
# Narration (app env)
bash scripts/start_llama_server.sh          # terminal A
source .venv/bin/activate                   # terminal B — not .venv311
PYTHONPATH=. python -m app.narrate_cli "Can I give Amina three crates on credit?"

# Metrics (profiler env)
# source .venv311/bin/activate && adtc-profiler --help
```

Security and design context: [`SECURITY.md`](./SECURITY.md), [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md).

---

## 5. Current scope and next work

| Not yet shipped | Why it waits |
|---|---|
| FastAPI / HTMX UI | After RSS headroom is measured |
| Frozen held-out eval set beyond `metadata.json` prompts | After bilingual smoke + profiler |
| Profiler numbers in `REPORT.md` | Measure with `adtc-profiler`; never invent |
| Owner-gated writes (control **C6**) | Gate 1 non-goal; binder is read-path only |
| Number post-check on narration | Hardening after smoke quality baseline |

**Shipped this stage:** llama.cpp build/start scripts, loopback client, binder-authoritative `ask()`, dual-env docs, EN/SW binder tests.

---

## 6. Elevator pitch (for reviewers)

> DukaBind is an offline shop assistant for 8 GB commodity laptops used across African MSMEs. Counter staff ask about credit, payables, or stock in English or Swahili. Allowlisted SQL reads a local ledger; missing fields produce a hard refusal. The GGUF model only narrates citation rows — it cannot invent a balance. Change the ledger, and the answer must change. The demo fixture is a Douala boutique (XAF); the product target is African shops with intermittent connectivity, not a single-country chatbot.

---

## 7. Maintenance checklist

When you change behaviour, update this file in the same PR:

1. Module table rows if paths or responsibilities moved.  
2. Commands if entrypoints or env names changed.  
3. “Current scope” when a deferred item ships.  
4. Re-run `PYTHONPATH=. pytest tests/ -q` and confirm [`SECURITY.md`](./SECURITY.md) control status still matches code.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-26 | Professional public rewrite; Africa-wide framing; dual-venv clarity; no personal email |
| 2026-07-25 | Initial Gate 1 walkthrough |
