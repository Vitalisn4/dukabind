# Code walkthrough — understand every piece

**Audience:** Vitalis (solo builder)  
**Goal:** You should be able to explain any file to a Gate 3 judge in plain language.

Read this top-to-bottom once. Then re-run the commands. Then change one seed number and watch the answer flip — that is the product thesis.

---

## 1. Big picture (30 seconds)

```text
Staff question (EN/SW)
        │
        ▼
  intents.py     →  which task? (credit / supplier / stock)
        │
        ▼
  allowlist.py   →  run ONE pre-approved SQL with ? binds
        │
        ▼
  refuse.py      →  if field NULL → hard refuse
                 →  if credit math over limit → say No + numbers
        │
        ▼
  (later) LLM    →  only narrates citation JSON — never invents balances
```

**Why this wins vs a chatbot:** the money numbers come from SQLite + Python arithmetic, not from model imagination. Judges care about African MSME reality + anti-hallucination.

---

## 2. Contest-required files (must ship)

| File | What it does | Rule it satisfies |
|---|---|---|
| `metadata.json` | Team, domain, model, 2 prompts | Template + evaluator |
| `download_model.sh` | Downloads GGUF to `model/` | No weights in git; public URL |
| `REPORT.md` | Technical writeup | Devpost “what to submit” |
| `.gitignore` | Blocks `*.gguf` | Template rule |
| `LICENSE` / `NOTICE` | Template GPL + provenance | Cite OSS |

Your identity is already filled:

- Name: **Vitalis Ngam**
- Email: **ngamvitailisyuh@gmail.com**
- GitHub: **[Vitalisn4](https://github.com/Vitalisn4)** (verified)
- `team_id`: provisional **`vitalisn4`** (no portal ID yet)
- Solo · domain `corporate_enterprise` · `african_alpha_claim: true`

---

## 3. Application code (the product)

### `app/db/schema.sql`
Creates tables: `customers`, `suppliers`, `skus`, `audit_log`, `shop_meta`.  
`credit_limit` and `balance_owed` may be **NULL** — that NULL is intentional so we can demo **refuse**.

### `app/db/seed_demo.sql`
Fake Douala shop (“Boutique Demo Douala”). Not real people. Currency **XAF**.  
Amina has limit 8000 / outstanding 6250 → 3 soda crates (3×720) exceeds limit.  
Bidco has `balance_owed = NULL` → must refuse.

### `app/db/connection.py`
Opens SQLite, turns on **WAL** + foreign keys, loads schema/seed.  
Run: `python -m app.db.connection`

### `app/binder/allowlist.py`  ← security heart
A **dict of named queries only**. Unknown name → `ValueError`.  
Uses `?` placeholders (control **C1/C2** in `SECURITY.md`).  
**The LLM never writes SQL.**

### `app/binder/intents.py`
Regex/keyword router for English + Swahili. Finds customer/supplier/sku names from the known demo list. Parses qty (`3` or `three`).

### `app/binder/refuse.py`
Fail-closed messages. Credit decision does **integer math in Python** so the model cannot botch arithmetic.

### `app/binder/citations.py`
Packs DB rows into compact JSON for (future) LLM context.

### `app/binder/pipeline.py`
`handle_ask(conn, text)` — full path without needing a model.  
This is what you demo before llama.cpp is wired.

### `tests/test_binder.py`
Eight tests: allowlist rejection, over-limit No, NULL refuse, Nest 42000, stock 14, Swahili path, **ledger flip → answer flips**.

---

## 4. Commands you should memorize

```bash
# From the repository root (wherever you cloned dukabind)
source .venv/bin/activate

# Re-run truth tests (no internet, no GGUF)
PYTHONPATH=. pytest tests/ -v

# Rebuild demo DB
python -m app.db.connection

# Ask the binder yourself
PYTHONPATH=. python -m app.cli "Can I give Amina three crates on credit?"
PYTHONPATH=. python -m app.cli "How much do we owe Bidco Distributors?"
```

---

## 5. What is NOT built yet (so you are not confused)

| Missing | Why it waits |
|---|---|
| FastAPI / HTMX UI | After RSS headroom proven |
| Frozen held-out eval set | After bilingual smoke; `metadata.json` currently has provisional domain prompts |
| Profiler numbers in REPORT | Never invent — measure with adtc-profiler |
| Public GitHub repo | In progress under Vitalisn4/dukabind |

## 5b. What THIS stage added (llama + narration)

See also [`docs/SECURITY.md`](./SECURITY.md) (C4/C5) and [`docs/DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md) (runtime choices).

| New piece | Role |
|---|---|
| `third_party/llama.cpp` | Official runtime (gitignored clone) |
| `scripts/setup_llama.sh` | Clone + build |
| `scripts/start_llama_server.sh` | Loopback CPU server |
| `app/prompts/narrate.py` | System/user prompts (no SQL) |
| `app/llm/client.py` | HTTP to 127.0.0.1:8080 only |
| `app/llm/ask.py` | Binder first; optional `narration` field; `message` stays binder |
| `app/narrate_cli.py` | End-to-end CLI |
| `.venv311` + `adtc-profiler` | Official metrics (Python 3.11+) |

```bash
# After ./download_model.sh finishes:
bash scripts/start_llama_server.sh   # terminal A
source .venv/bin/activate
PYTHONPATH=. python -m app.narrate_cli "Can I give Amina three crates on credit?"  # terminal B
```

---

## 6. How to explain DukaBind to a judge (elevator)

> “DukaBind is an offline shop assistant for 8 GB laptops. Staff ask about credit, payables, or stock. We run allowlisted SQL against a local ledger and refuse if data is missing. The GGUF model only narrates rows — it cannot invent a balance. Change the ledger, the answer changes. Built for Cameroon MSME shops that lose connectivity.”

---

## 7. Learning loop (do this weekly)

1. Read one module + its matching test.  
2. Break a seed value; predict the new answer; run CLI; check.  
3. Re-read `docs/SECURITY.md` and `docs/DESIGN_DECISIONS.md` — confirm controls still match the code.  
4. Ask in Discord only the open dual-source questions (bonus math, Gate 1 TZ).
