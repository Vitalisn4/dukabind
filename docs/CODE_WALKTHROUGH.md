# Code walkthrough

**Status:** Living document — update when modules, commands, or Gate milestones change  
**Last updated:** 2026-08-04  
**Audience:** Contributors, Gate reviewers, and anyone reproducing DukaBind from a clean checkout

This guide maps the shipped product: what each file does, how a staff question becomes an answer, which commands to run, and how the Marché Akwa Viviane ledger is structured.

---

## 1. What DukaBind is (read this first)

DukaBind is an **offline shop assistant** for commodity 8 GB laptops. Counter staff ask about:

1. **Credit** — “Can I give Marie-Claire three crates on credit?”  
2. **Supplier balances** — “How much do we owe SOCA?”  
3. **Stock** — “How many soda crates on hand?”

The system does **not** answer from the language model’s memory. It:

1. Detects intent with English keyword rules.  
2. Runs **one allowlisted SQL query** with bound parameters.  
3. Computes credit math in Python (or **refuses** if a required money field is missing).  
4. Optionally asks a **local** `llama-server` to polish wording — the binder `message` stays authoritative.

**Product thesis:** change a ledger row → the answer must change. Delete a required field → the system refuses. The model is instructed not to invent amounts; it is never trusted to choose SQL.

**Shop in this repository:** Marché Akwa Viviane (Akwa, Douala, XAF). The same binder pipeline loads any shop SQLite file that matches the schema.

---

## 2. End-to-end data flow

```text
Staff question (English)
        │
        ▼
  app/binder/intents.py
        │  intent + slots (customer / supplier / sku / qty)
        ▼
  app/binder/allowlist.py
        │  ONE named SQL statement, ?-bound parameters
        ▼
  app/binder/refuse.py  (+ credit_decision arithmetic)
        │  NULL / missing → hard refuse
        │  else deterministic message + citation rows
        ▼
  app/llm/ask.py   (optional)
        │  refuse → return immediately (no LLM)
        │  else optional narration on 127.0.0.1 only
        ▼
  JSON to CLI / future UI
      message     = binder truth (always)
      narration   = model polish (optional)
      citation_json = ledger rows the model may see
```

| Field | Meaning |
|---|---|
| `ok` | `true` if an answer was produced; `false` on refuse |
| `intent` | `credit_check` · `supplier_balance` · `stock_check` · `unknown` |
| `lang` | `en` (Gate 1 Path A — English only) |
| `message` | **Authoritative** cashier string from the binder |
| `refuse_reason` | e.g. `balance_owed_null`, `credit_limit_null`, `not_found` |
| `citation_json` | Compact JSON of ledger rows |
| `narration` / `narrated` | Present only when LLM polish ran |
| `source` | `binder` or `binder+llm` |

---

## 3. Shop ledger — Marché Akwa Viviane

Seeded by `python -m app.db.connection` into `data/marche_akwa.sqlite`.

### Shop

| Field | Value |
|---|---|
| Name | Marché Akwa Viviane |
| Neighbourhood | Akwa, Douala |
| Currency | XAF |
| Fixture id | `marche_akwa` |

### Customers (credit)

| Display name | Nicknames staff may use | credit_limit | outstanding | Notes |
|---|---|---:|---:|---|
| Marie-Claire Fotso | Marie-Claire, Fotso, Marie | 8000 | 6250 | 3 crates @ 720 exceed limit |
| Ibrahim Njoya | Ibrahim, Njoya | 15000 | 2000 | Room left on credit |
| Esther Tchamba | Esther, Tchamba | **NULL** | 500 | Refuse — no limit on file |

### Suppliers (payables)

| Display name | Nicknames | balance_owed | Notes |
|---|---|---:|---|
| SOCA Distribution Douala | SOCA | **NULL** | Refuse — amount not confirmed |
| Grosserie Portuaire Bonaberi | Bonaberi, Portuaire | 42000 | Known payable |

### Stock (SKUs)

| Ledger name | Nicknames | unit_price | on_hand |
|---|---|---:|---:|
| Caisse boisson malt 300ml | soda, malt, boisson | 720 | 14 |
| Sac riz 25kg | rice, riz | 18500 | 6 |
| Bidon huile palme 5L | oil, huile | 4500 | 0 |

**Default credit SKU:** if staff say “crates on credit” without naming a product, the binder prices **Caisse boisson malt 300ml** (`DEFAULT_CREDIT_SKU` in `fixture.py`).

**Keep in sync:** `app/db/fixture.py` (nicknames + normalize helpers) ↔ `app/db/seed.sql` (rows).

---

## 4. Contest-required files

| File | Role |
|---|---|
| `metadata.json` | Team, domain `corporate_enterprise`, model, exactly two `test_prompts`, claims |
| `download_model.sh` | Idempotent GGUF download + sha256 check (weights never in git) |
| `REPORT.md` | Gate 1 technical writeup |
| `LICENSE` / `NOTICE` | GPL-3.0 application code; model weights stay upstream |
| `.gitignore` | Ignores `*.gguf`, local strategy docs, venvs, live `*.sqlite` |

**Submitter (public):** Vitalis Ngam · [Vitalisn4](https://github.com/Vitalisn4) · provisional `team_id`: `vitalisn4`  
Contact email lives in `metadata.json` / Devpost only — not in this walkthrough.

---

## 5. Application modules (file-by-file)

### 5.1 Database — `app/db/`

| Path | What it does |
|---|---|
| `schema.sql` | Tables: `shop_meta`, `customers`, `suppliers`, `skus`, `audit_log`. **NULL** `credit_limit` / `balance_owed` means “not on file” → refuse (control **C4**). |
| `seed.sql` | Loads Marché Akwa Viviane rows. |
| `fixture.py` | Display names, nicknames, and `normalize_*` helpers used by the intent router. |
| `connection.py` | Opens SQLite (WAL + foreign keys). Ask CLIs use **`readonly=True`**. `python -m app.db.connection` creates/seeds `data/marche_akwa.sqlite`. |

### 5.2 Binder — `app/binder/` (load-bearing)

| Path | What it does |
|---|---|
| `intents.py` | Rule-based English detection; extracts slots; caps ask length at 500 chars; word-boundary name match (so `rice` does not match inside `price`). |
| `allowlist.py` | Finite map of named SQL; unknown name or missing params → `ValueError`; never concatenates user text into SQL (**C1/C2**). |
| `refuse.py` | Refuse strings + `credit_decision` arithmetic in Python (**C4**). |
| `citations.py` | Rows → compact JSON for narration prompts. |
| `pipeline.py` | `handle_ask(conn, text)` — full answer path **without** a model. |

**Allowlisted query names today:** `customer_credit`, `supplier_balance`, `sku_stock`.

### 5.3 Narration — `app/llm/` + `app/prompts/`

| Path | What it does |
|---|---|
| `prompts/narrate.py` | System + user messages: copy binder numbers; do not invent figures. |
| `llm/client.py` | HTTP to **`http://127.0.0.1` only**; rejects redirects; wraps transport errors (**C5**). |
| `llm/ask.py` | Binder first; refusals never call the model; `message` stays binder; polish in `narration`. |

### 5.4 CLIs

| Command | Behaviour |
|---|---|
| `python -m app.cli "…"` | Binder only (no LLM). Read-only DB. |
| `python -m app.narrate_cli "…"` | Binder + optional local llama-server. `--no-llm` forces binder-only. `--base-url` must stay loopback. |

### 5.5 Scripts

| Script | Behaviour |
|---|---|
| `scripts/setup_llama.sh` | Clone/build official `llama.cpp` under `third_party/` (gitignored). |
| `scripts/start_llama_server.sh` | Starts `llama-server` on `127.0.0.1`, CPU only, ctx 2048. |
| `scripts/smoke_narrate.sh` | Starts server, waits for `/health`, one narrate ask, cleans up. |
| `download_model.sh` | Downloads pinned Qwen2.5-1.5B Q4_K_M GGUF + sha256 (**C7**). |

### 5.6 Tests — `tests/`

| File | Covers |
|---|---|
| `test_binder.py` | Allowlist reject; Fotso over-limit 8410; Esther NULL limit; SOCA NULL balance; Bonaberi 42000; stock; SW ask unknown; substring safety; overlong ask; zero qty; rice price; ledger flip |
| `test_ask.py` | Refuse skips LLM; binder `message` authority; loopback reject; non-loopback `base_url` does not narrate |

Run: `PYTHONPATH=. pytest tests/ -q` (expect **18 passed**).

---

## 6. Environments and setup (explicit)

### Two virtualenvs

| Env | Python | Use |
|---|---|---|
| `.venv` | 3.10+ | App, pytest, `app.cli`, `app.narrate_cli` |
| `.venv311` | ≥3.11 | **`adtc-profiler` only** (official tool requirement) |

Do **not** activate `.venv311` to run narration — use `.venv`.

### First-time setup (from repo root)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m app.db.connection
PYTHONPATH=. pytest tests/ -q
```

### Optional: model + narration

```bash
./download_model.sh                          # once; needs network
bash scripts/setup_llama.sh                  # once; builds llama-server
bash scripts/start_llama_server.sh           # terminal A — stays running
source .venv/bin/activate                    # terminal B
PYTHONPATH=. python -m app.narrate_cli "Can I give Marie-Claire three crates on credit?"
```

### Binder-only smoke phrases (no model)

```bash
source .venv/bin/activate
PYTHONPATH=. python -m app.cli "Can I give Marie-Claire three crates on credit?"
# → No … 8410 … Max qty within limit: 2.

PYTHONPATH=. python -m app.cli "How much do we owe SOCA?"
# → refuse: balance_owed_null

PYTHONPATH=. python -m app.cli "How much do we owe Bonaberi?"
# → Amount owed … 42000

PYTHONPATH=. python -m app.cli "What stock of soda do we have on hand?"
# → Caisse boisson malt 300ml … on_hand=14

PYTHONPATH=. python -m app.cli "Can I give Esther credit for 1 crate?"
# → refuse: credit_limit_null
```

---

## 7. Security controls (map to code)

Full threat model: [`SECURITY.md`](./SECURITY.md).

| ID | Rule | Where |
|---|---|---|
| C1/C2 | Allowlisted + parameterized SQL only | `allowlist.py` |
| C3 | No LLM-generated SQL | `ask.py` / prompts see citations only |
| C4 | Fail closed on NULL money fields | `refuse.py`, seed NULLs, tests |
| C5 | Loopback-only LLM HTTP | `client.py`, `start_llama_server.sh` |
| C6 | Owner-gated writes | Deferred (read path only) |
| C7 | GGUF sha256 pin | `download_model.sh` |
| C8 | No secrets / weights in git | `.gitignore` |
| C9 | No third-party PII committed without consent | `seed.sql`, `fixture.py` |

Design rationale: [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md).

---

## 8. Current scope and next work

| Shipped | Not yet (by design) |
|---|---|
| Fail-closed binder + 3 intents | FastAPI / HTMX staff UI |
| Marché Akwa Viviane ledger + tests | Profiler Peak RSS / TPS / thermal numbers in `REPORT.md` |
| Optional local narration | Airplane-mode proof checklist artifact |
| Loopback + readonly ask path | Owner-gated writes (C6) |
| Public SECURITY / DESIGN / this guide | Frozen ≥25 held-out eval set |

---

## 9. Elevator pitch (reviewers)

> DukaBind is an offline shop assistant for 8 GB commodity laptops used across African MSMEs. Counter staff ask about credit, payables, or stock. Allowlisted SQL reads a local ledger; missing fields produce a hard refusal. The GGUF model may narrate cited rows and is instructed not to invent balances — the binder’s deterministic `message` stays authoritative. Change the ledger, and the answer must change. This repository ships Marché Akwa Viviane (Douala, XAF); the product target is African shops with intermittent connectivity.

---

## 10. Maintenance checklist

When you change behaviour, update this file in the **same** change set:

1. Module tables if paths or responsibilities moved.  
2. Shop tables if customers / suppliers / SKUs changed (`fixture.py` + `seed.sql`).  
3. Commands if entrypoints or env names changed.  
4. “Current scope” when a deferred item ships.  
5. Re-run `PYTHONPATH=. pytest tests/ -q` and confirm [`SECURITY.md`](./SECURITY.md) status still matches code.

---

## Change log

| Date | Change |
|---|---|
| 2026-08-04 | Present shop as Marché Akwa Viviane; rename `seed.sql`; English-only Path A |
| 2026-07-26 | Qualify narration wording; binder message authoritative |
| 2026-07-26 | Professional public rewrite; Africa-wide framing; dual-venv clarity |
| 2026-07-25 | Initial Gate 1 walkthrough |
