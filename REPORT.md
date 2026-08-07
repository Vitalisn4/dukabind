# Technical Report — DukaBind

**Team ID:** vitalisn4 (provisional solo ID — GitHub handle; replace if ADTF issues an official ID)  
**Submitter:** Vitalis Ngam · ngamvitailisyuh@gmail.com · [Vitalisn4](https://github.com/Vitalisn4)  
**Domain:** corporate_enterprise  
**Model:** Qwen2.5-1.5B-Instruct-Q4_K_M  
**Team size:** Solo

---

## Problem

When a micro/small shop owner is away from the counter, semi-trained staff cannot reliably answer credit, payables, or stock questions. Cloud POS and messaging bots fail without connectivity; general chatbots invent balances.

**DukaBind** is an offline llama.cpp/GGUF assistant that answers only from a local SQLite ledger bind and fails closed when data is missing. Target users: counter staff (primary), shop owners (secondary). African context: commodity 8 GB laptops, intermittent mobile data, owner-absent shifts — designed from Cameroon MSME shop reality (ledger: Douala, XAF).

See [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) for selection rationale and alternatives considered.

---

## Design Decisions

- **Base model:** Qwen2.5-1.5B-Instruct (Apache-2.0 upstream).
- **Quantization:** GGUF Q4_K_M — quality/size trade per Devpost quant guidance; official Qwen GGUF file ~1.12 GB.
- **Integration (load-bearing):** Allowlisted SQL binder — not vector RAG. Protects S_eff under the 7 GB usable budget and prevents financial hallucination.
- **Language:** English cashier asks and binder messages (`language_scope: ["en"]`). African use-case claim is Cameroon MSME offline ledger context, not an African-language claim.
- **Runtime:** llama.cpp only (template + FAQ requirement).
- **Model lock (M3):** Qwen2.5-1.5B Q4_K_M is frozen as primary on measured evidence — Peak RSS 1825.72 MB (≪ 5.5 GB limit), 16.44 tok/s (profiler `--full` run; llama-bench up to 17.94), TTFT ~9.0 s. **T15 quant lock:** Q4_K_M 1.5B stays frozen unless accuracy regresses with RSS margin; 3B Q4 only if T1–T3 stay green. Tiny Aya is explicitly **not** downloaded (no Swahili track under Path A) — no Aya benchmark is claimed.
- **Alternatives rejected:** 7B-class (RSS DQ risk); embeddings/FAISS (RAM); LLM-generated SQL (injection + hallucination); shallow Swahili without a native reviewer.

Authoritative writeups: `docs/DESIGN_DECISIONS.md`, `docs/SECURITY.md`.

---

## Constraints

- Target: ADTC Standard Laptop — 8 GB RAM, integrated GPU, Ubuntu 22.04; Intel i5 **or** AMD Ryzen 5 (Devpost hardware table).
- 100% offline during evaluation; no API fees.
- Peak RSS self-limit &lt; 5.5 GB; thermal soak &lt; 85 °C (else −10).
- OOM / crash → disqualification (S_total = 0).
- Optional ≤5 Udutech GPU hours for training only; final benches on CPU.

---

## Tools used (and why)

| Tool | Why |
|---|---|
| Official submission template | Required repo shape / metadata |
| adtc-profiler | Official latency, TPS, Peak RSS, thermal |
| llama.cpp + GGUF | Only accepted runtime |
| SQLite3 | Zero-daemon local ledger; parameterized SQL |
| pytest | Fail-closed regression tests |

---

## Benchmarks

Participant smoke on build laptop (`bash scripts/run_profiler_smoke.sh --full`, definitive run 2026-08-06; earlier smoke 2026-08-04). The profiler's `accuracy` block is `[]` in participant mode by design — official accuracy comes from ADTC audit mode on the eval machine. Full tables: [`BENCHMARKS.md`](BENCHMARKS.md). Official Gate 1 scores come from the ADTC eval machine.

| Metric | Measured (participant, definitive `--full` run) |
|---|---|
| Machine | Intel i7-8650U · 23.3 GB RAM · Ubuntu 22.04 · no GPU |
| Peak RSS | **1825.72 MB** |
| Generation speed | **16.44 tok/s** |
| Time to first token | 9026.84 ms |
| Thermal | 10-min soak **PASS** on build laptop at `THREADS=2`/`ctx=1024`: mean **75.7 °C**, peak **84.0 °C** (0/68 ≥ 85 °C), 100 % HTTP ok |
| 7.5 GB-capped proof | Full stack (server + asks) ran under a hard **7.5 GiB** cgroup cap — cgroup peak 0.77 GiB, llama-server VmRSS 1.80 GiB, headroom **6.73 GiB** (2026-08-06, `bash scripts/ram_capped_proof.sh`) |

Memory envelope clears the &lt;5.5 GB self-limit. **8 GB-class proof:** the whole stack (llama-server + three narrated asks) ran under a hard 7.5 GiB cgroup `MemoryMax` cap with 6.73 GiB headroom; even the process-level footprint (llama-server VmRSS 1.80 GiB ≈ profiler Peak RSS 1825.72 MB) leaves ~3× margin under the 7 GB usable DQ ceiling. Thermal on the build laptop: `THREADS=3` (peak **97 °C**) and `THREADS=2` at `ctx=2048` (peak **93 °C**) 10-min soaks FAIL the &lt;85 °C criterion — the 2018-era cooling bursts under sustained full-context generation. Halving context (`THREADS=2`/`ctx=1024`) **passes**: mean **75.7 °C**, peak **84.0 °C**, 0/68 samples ≥ 85 °C, http 100 %. **Ship default (M5, 2026-08-07):** `scripts/start_llama_server.sh` ships `THREADS=2`/`CTX=1024` — the measured thermally-safe config (risk gate: thermal safety over TPS). The authoritative P_thermal call stays with the official eval-machine run.

Full measured tables and methodology: [`BENCHMARKS.md`](BENCHMARKS.md). Model facts, limits, and intended use: [`MODEL_CARD.md`](MODEL_CARD.md).

---

## Evaluation (held-out, offline)


28 EN prompts (`evals/heldout/prompts.json`) run against **two disjoint shop ledgers** — Marché Akwa Viviane (Douala) and Marché Nkolmébé (`duka_b`, Yaoundé) — covering credit, payables, stock, NULL-field refusals, adversarial / jailbreak asks, and cross-shop prompts that must refuse without leaking the other shop's numbers, plus ledger-flip proofs. **31/31 checks pass** offline (`PYTHONPATH=. .venv/bin/python evals/run_heldout.py`; `pytest tests/ -q` = 44 passed). Measured T11 bind/refuse: **28/28 = 100.0 %** (target ≥ 90 %). Committed evidence report: [`evals/heldout/REPORT.md`](evals/heldout/REPORT.md) (regenerated from measured runs via `--write-report`).

**T13 — submission prompts:** the 2 prompts in `metadata.json` are **disjoint** from the held-out set. `tp_001` (Esther Tchamba, NULL credit limit → refuse) uses an entity absent from every held-out prompt. `tp_002` (Chidi Okafor × Sucre 25kg) is a novel entity×product ask — Chidi Okafor appears in the held-out set only in a different scenario (one bag of flour, `cb_02`), and the projected total **31000** appears in no held-out binder message; the shared sub-total 27000 (2×13500) is unavoidable across sugar credit asks. `tests/test_metadata.py` fails CI if any staff-ask string drifts into the held-out file, which is the hard T13 gate.

---

## African use case claim

`african_alpha_claim: true` — African **use-case** claim: offline MSME shop ledger assistant for commodity laptops, designed from Cameroon (Douala / XAF) reality. Product language is **English only** (`language_scope: ["en"]`); no African-language bonus is claimed without a native reviewer.
