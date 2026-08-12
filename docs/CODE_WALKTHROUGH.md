# Code walkthrough

**Status:** Living document — update when modules, commands, or Gate milestones change  
**Last updated:** 2026-08-12  
**Audience:** Contributors, Gate reviewers, and anyone reproducing DukaBind from a clean checkout

**What we are building:** offline shop assistant for African MSME counters in **English, French, and Swahili** — allowlisted SQL on Marché Akwa Viviane (Douala, XAF); hard refuse on missing money fields; optional local llama.cpp narration (en/fr; Swahili is binder-only by design); binder `message` authoritative.

This guide maps the shipped product: what each file does, how a staff question becomes an answer, which commands to run, and how the Marché Akwa Viviane ledger is structured.

---

## 1. What DukaBind is (read this first)

DukaBind is an **offline shop assistant** for commodity 8 GB laptops. Counter staff ask about:

1. **Credit** — “Can I give Marie-Claire three crates on credit?”  
2. **Supplier balances** — “How much do we owe SOCA?”  
3. **Stock** — “How many soda crates on hand?”

The system does **not** answer from the language model’s memory. It:

1. Detects intent with keyword rules (English / French / Swahili).  
2. Runs **one or more allowlisted SQL queries** with bound parameters (credit uses `customer_credit` then `sku_stock`).  
3. Computes credit math in Python (or **refuses** if a required money field is missing).  
4. Optionally asks a **local** `llama-server` to polish wording — the binder `message` stays authoritative.

**Product thesis:** change a ledger row → the answer must change. Delete a required field → the system refuses. The model is instructed not to invent amounts; it is never trusted to choose SQL.

**Shop in this repository:** Marché Akwa Viviane (Akwa, Douala, XAF). The same binder pipeline loads any shop SQLite file that matches the schema.

---

## 2. End-to-end data flow

```text
Staff question (EN / FR / SW)
        │
        ▼
  app/binder/intents.py
        │  intent + slots (customer / supplier / sku / qty)
        ▼
  app/binder/allowlist.py
        │  named allowlisted SQL (credit: customer + SKU), ?-bound parameters
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
| `ok` | `true` when the binder returned a grounded answer (including credit Yes/No); `false` on refuse |
| `approved` | Credit only: `true` within limit, `false` over limit; `null` for non-credit / refuse |
| `intent` | `credit_check` · `supplier_balance` · `stock_check` · `unknown` |
| `lang` | `en` / `fr` / `sw` (ask language; binder message localized deterministically) |
| `message` | **Authoritative** cashier string from the binder |
| `refuse_reason` | e.g. `balance_owed_null`, `credit_limit_null`, `not_found` |
| `citation_json` | Compact JSON of ledger rows |
| `narration` / `narrated` | Always present on the `ask()` response; `narrated=false` and `narration=null` when LLM polish does not run |
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

### Second shop fixture — Marché Nkolmébé (`duka_b`)

A second, **fully disjoint** shop (Yaoundé, XAF) proves answers bind to the live ledger instead of being memorized from the first shop. Seeded via `seed_file=SEED_DUKA_B` (see `connection.init_db`); the held-out eval runs both shops.

| Display name | credit_limit | outstanding | Notes |
|---|---|---:|---|
| Amina Bello | 25000 | 9800 | 2 bags of sugar @ 13500 exceed limit |
| Chidi Okafor | 12000 | 4000 | 1 bag of flour @ 22000 exceed limit |
| Maman Rachel | **NULL** | 0 | Refuse — no limit on file |

| Supplier | balance_owed | Notes |
|---|---:|---|
| Sanaga Épicerie | 15500 | Known payable |
| Ciment du Cameroun | **NULL** | Refuse — amount not confirmed |

| SKU | unit_price | on_hand |
|---|---:|---:|
| Sucre 25kg (sugar, sucre) | 13500 | 4 |
| Savon carton 24 (soap, savon) | 9800 | 0 |
| Farine 50kg (flour, farine) | 22000 | 9 |

**Anti-memorization rule:** asking about `duka_b` entities against the Akwa ledger (or vice versa) must **refuse** (`not_found`) and never leak the other shop's numbers — enforced by `evals/run_heldout.py` cross-shop prompts.

---

## 4. Contest-required files

| File | Role |
|---|---|
| `metadata.json` | Team, domain `corporate_enterprise`, model, exactly two `test_prompts`, claims |
| `download_model.sh` | Idempotent GGUF download + sha256 check (weights never in git) |
| `REPORT.md` | Gate 1 technical writeup |
| `MODEL_CARD.md` | Qwen2.5-1.5B Q4_K_M — intended use, limits, language honesty, run instructions |
| `evals/heldout/REPORT.md` | Committed held-out evidence report (T11, flips, both fixtures; regenerated via `--write-report`) |
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
| `seed.sql` | Loads Marché Akwa Viviane rows (primary demo shop). |
| `seed_duka_b.sql` | Loads Marché Nkolmébé (`duka_b`) rows — second shop for the held-out eval. |
| `fixture.py` | Display names, nicknames, and `normalize_*` helpers for **both** shops (disjoint aliases), used by the intent router. |
| `connection.py` | Opens SQLite (WAL + foreign keys). Ask CLIs use **`readonly=True`**. `python -m app.db.connection` creates/seeds `data/marche_akwa.sqlite`; `init_db(seed_file=SEED_DUKA_B)` seeds the second shop. |

### 5.2 Binder — `app/binder/` (load-bearing)

| Path | What it does |
|---|---|
| `intents.py` | Rule-based EN/FR/SW detection (marker scoring); extracts slots; caps ask length at 500 chars; word-boundary name match (so `rice` does not match inside `price`). |
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
| `scripts/start_llama_server.sh` | Starts `llama-server` on `127.0.0.1`, CPU only. **Shipped default (M5, 2026-08-07): `CTX=1024`, `THREADS=2`** — the measured 10-min thermal-soak PASS config of 2026-08-06 (peak 84.0 °C), **superseded 2026-08-10: the PASS no longer reproduces on the build laptop (re-run peak 89.0 °C, FAIL)**; `THREADS=3`/`CTX=2048` reachable via env override for eval-machine runs, which stays the authoritative P_thermal decision. |
| `scripts/smoke_narrate.sh` | Starts server, waits for `/health`, one narrate ask, cleans up. |
| `scripts/offline_check.sh` | Binder offline proof: credit / SOCA refuse / stock; optional `unshare -n`. |
| `scripts/run_profiler_smoke.sh` | `adtc-profiler` participant mode → `benchmarks/raw/submission.json`; optional `--full`. |
| `scripts/ram_capped_proof.sh` | 8 GB-class proof: full stack under a cgroup `MemoryMax` cap (default 7.5 GB), reports `memory.peak` headroom. |
| `scripts/thread_matrix.sh` | `llama-bench` thread bake-off (`-t 2,3,4,6,8`) + temp sampling → `benchmarks/raw/`. |
| `scripts/thermal_soak.sh` | Sustained generation soak (default 10 min) sampling package temp every 5 s → CSV + PASS/FAIL. |
| `scripts/render_demo_assets.py` | M6 packaging tool: renders `demo/screenshots/*.png` + `demo/demo.mp4` (≤2 min, captioned) from **real CLI / offline-check / profiler output** — nothing hand-typed. Requires Pillow + ffmpeg (dev-only). |
| `scripts/static_analysis.sh` | One-pass gate: `ruff` + `bandit` (skip `B101` in tests) + `shellcheck`; exit 0 only when all clean. |
| `download_model.sh` | Downloads pinned Qwen2.5-1.5B Q4_K_M GGUF + sha256 (**C7**). |

### 5.6 Tests — `tests/`

| File | Covers |
|---|---|
| `test_binder.py` | Allowlist reject; Fotso over-limit 8410; Esther NULL limit; SOCA NULL balance; Bonaberi 42000; stock; non-English ask unknown; substring safety; overlong ask; zero qty; rice price; ledger flip; qty-vs-amount parsing; SQL-injection battery; narration prompt-injection invariant |
| `test_ask.py` | Refuse skips LLM; binder `message` authority; loopback reject; non-loopback `base_url` does not narrate |
| `test_duka_b.py` | Second-shop generalization; NULL refusal; accent-insensitive asks; cross-shop non-leak; flip on `duka_b`; full held-out suite stays green |
| `test_languages.py` | French + Swahili tracks: detection, localized credit/supplier/stock/refuse messages, word-boundary markers, noun-before-digit quantities, localized `not_found` identifiers, narration gate |
| `test_metadata.py` | Contest-claims guard: domain, `language_scope: ["en","fr","sw"]`, honest claims, exactly 2 ledger-grounded `test_prompts`, llama.cpp runtime |

Run: `PYTHONPATH=. pytest tests/ -q` (expect **77 passed**).

### Binder offline proof (no model)

```bash
bash scripts/offline_check.sh
```

### 5.7 Held-out eval (no model, no network)

```bash
PYTHONPATH=. .venv/bin/python evals/run_heldout.py
```

Runs **28 EN prompts** (`evals/heldout/prompts.json`) against both disjoint shop ledgers — credit, supplier, stock, NULL-field refusals, adversarial/jailbreak prompts, and cross-shop prompts that must refuse without leaking the other shop's numbers — plus ledger-flip proofs (change a limit/stock row → the answer must change). Exit 0 = all 31 checks pass. The runner prints the **T11 bind/refuse score** (measured **100.0%, 28/28**, 2026-08-06; target ≥90%).

`PYTHONPATH=. .venv/bin/python evals/run_heldout.py --write-report` also regenerates the committed evidence report [`evals/heldout/REPORT.md`](../evals/heldout/REPORT.md) (T11, per-category + per-fixture tables, flip proofs, T13 note) — numbers are recomputed from the measured run, never hand-edited. The 2 submission prompts in `metadata.json` are picked from a pool **disjoint** from this set (T13); `tests/test_metadata.py` fails CI on any overlap.

### Benchmarks (`BENCHMARKS.md` + `benchmarks/`)

```bash
bash scripts/thread_matrix.sh   # llama-bench thread bake-off → benchmarks/raw/thread_matrix_*.{jsonl,md}
bash scripts/thermal_soak.sh    # 10-min sustained soak → benchmarks/raw/thermal_soak_*.csv + PASS/FAIL
bash scripts/run_profiler_smoke.sh  # raw JSON → benchmarks/raw/submission.json (gitignored)
bash scripts/ram_capped_proof.sh    # 8 GB-class proof: full stack under cgroup MemoryMax cap → headroom report
```

Only measured numbers are committed: the summary tables in `BENCHMARKS.md`, `REPORT.md`, and `benchmarks/submission.summary.md`. Raw dumps stay gitignored under `benchmarks/raw/`.

### 5.8 Continuous integration — `.github/workflows/ci.yml`

Runs on every push/PR: `pip install -r requirements.txt` → `pytest` (77 tests) → `ruff` → `static_analysis.sh` gate (ruff + bandit + shellcheck) → held-out eval (31 checks) → **held-out report freshness gate** (regenerates `evals/heldout/REPORT.md` via `--write-report` and fails if it drifts from the committed artifact; the daily `Generated:` date is excluded from the comparison) → offline binder proof. Contest-claims drift is caught by `tests/test_metadata.py`.

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
| C3 | No LLM-generated SQL | `ask.py` / prompts get staff question + binder message + citation JSON; model never receives SQL or chooses a query |
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
| Marché Akwa Viviane + Marché Nkolmébé (`duka_b`) ledgers + tests | Owner-gated writes (C6) |
| Optional local narration + profiler accuracy self-benchmark (74.0 % `arc_easy`, 2026-08-12) | |
| Loopback + readonly ask path | |
| `scripts/offline_check.sh` binder proof | Thermal soak green &lt;85 °C on **official eval machine** — build laptop: shipped default `THREADS=2`/`CTX=1024` **PASS 2026-08-06** (peak 84.0 °C, temperature-only) but **FAIL on 2026-08-10 re-run** (peak 89.0 °C — no longer reproducible); `THREADS=3`/`ctx=2048` (97 °C) and `THREADS=2`/`ctx=2048` (93 °C) documented FAIL |
| Profiler smoke Peak RSS ~1.8 GB | |
| Thread/ctx matrix + thermal soak logged in `BENCHMARKS.md` | |
| Held-out eval: 28 EN prompts, cross-shop non-leak, flip proofs (`evals/`) | |
| Held-out evidence report + `MODEL_CARD.md` (M5, 2026-08-07) | |
| T13 submission prompts frozen in `metadata.json` (disjoint from held-out) | |
| Ship default `THREADS=2`/`CTX=1024` (2026-08-06 thermal PASS config, M5 decision — no longer thermally safe on the build laptop after the 2026-08-10 re-run) | |
| Model lock (M3): Qwen2.5-1.5B Q4_K_M; T15 quant lock; Aya skipped | |

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
| 2026-08-10 | Thermal re-validation: shipped default `THREADS=2`/`CTX=1024` 10-min soak **FAIL** on build laptop (cold-start peak 89.0 °C, hot-start 98.0 °C) — the 2026-08-06 PASS no longer reproduces; authoritative P_thermal stays on the official eval machine |
| 2026-08-07 | M5 evidence pack: `MODEL_CARD.md`; committed held-out report (`evals/heldout/REPORT.md` via `--write-report`); T13-disjoint `tp_001`/`tp_002` in metadata.json; ship default frozen `THREADS=2`/`CTX=1024` in `start_llama_server.sh` (+ soak/proof scripts); REPORT/BENCHMARKS aligned to measured reality |
| 2026-08-12 | Accuracy self-benchmark: `--full` profiler run with the current in-process llama-cpp-python accuracy path → `arc_easy` 50-sample **74.0 %** (`acc_norm`) recorded in `BENCHMARKS.md` (toolchain evidence; official S_acc = audit mode); `run_profiler_smoke.sh` now emits the score in `benchmarks/submission.summary.md` |
| 2026-08-06 | 8 GB-class proof: `scripts/ram_capped_proof.sh` (cgroup peak 0.77 GiB under 7.5 GiB cap, headroom 6.73 GiB); definitive `--full` profiler run (Peak RSS 1825.72 MB, 16.44 tok/s, TTFT 9026.84 ms; the then-default toolchain emitted `accuracy: []` in participant mode) |
| 2026-08-06 | Thermal: `THREADS=2`/`ctx=1024` 10-min soak **PASS** on build laptop (mean 75.7 °C / peak 84.0 °C / 0 ≥ 85 °C); `THREADS=3` and `THREADS=2`@`ctx=2048` documented FAIL; eval laptop still decides P_thermal |
| 2026-08-06 | CI: `.github/workflows/ci.yml` — pytest + ruff + static-analysis gate + held-out eval + offline binder proof + metadata validation on every push/PR |
| 2026-08-06 | Security hardening: qty-vs-amount parsing, accent-insensitive aliases, injection-battery tests; `scripts/static_analysis.sh` gate (ruff + bandit + shellcheck) |
| 2026-08-06 | EN held-out + `duka_b`: second shop fixture, 28-prompt offline eval (`evals/run_heldout.py`), cross-shop non-leak + flip proofs; M3 Qwen lock note |
| 2026-08-06 | M2 bench completion: thread matrix + thermal soak scripts, `THREADS=3` freeze, `BENCHMARKS.md` measured tables (soak **FAIL**: mean 78 °C / peak 97 °C on build laptop) |
| 2026-08-06 | English-only framing; M2 thermal honesty |
| 2026-07-26 | Qualify narration wording; binder message authoritative |
| 2026-07-26 | Professional public rewrite; Africa-wide framing; dual-venv clarity |
| 2026-07-25 | Initial Gate 1 walkthrough |
