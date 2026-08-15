# Technical Report: DukaBind

**Team ID:** vitalisn4  
**Submitter:** Vitalis Ngam · ngamvitailisyuh@gmail.com · [Vitalisn4](https://github.com/Vitalisn4)  
**Domain:** `corporate_enterprise`  
**Model:** Qwen2.5-1.5B-Instruct-Q4_K_M  
**Team size:** Solo

---

## Problem

When a shop owner is away from the counter, staff cannot reliably answer credit, payables, or stock questions. Cloud POS and chatbots fail without connectivity, or invent balances.

**DukaBind** is an offline llama.cpp/GGUF assistant that answers only from a local SQLite ledger and fails closed when data is missing. Primary users are counter staff; secondary users are shop owners. Context: commodity 8 GB laptops, intermittent connectivity, owner-absent shifts. The seeded ledger is a Cameroon MSME shop (Douala, XAF).

Rationale and alternatives: [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md).

---

## Design Decisions

- **Base model:** Qwen2.5-1.5B-Instruct (Apache-2.0 upstream).
- **Quantization:** GGUF Q4_K_M (~1.12 GB), per contest quant guidance.
- **Integration:** Allowlisted SQL binder, not vector RAG. Fits the 7 GB usable budget and prevents financial hallucination.
- **Language:** English, French, and Swahili (`language_scope: ["en","fr","sw"]`). Binder messages are deterministic in all three. Narration is English and French only. Swahili is binder-only because the 1.5B model does not narrate Swahili reliably. The African claim is the Cameroon MSME offline ledger use-case.
- **Runtime:** llama.cpp and GGUF only.
- **Model lock:** Qwen2.5-1.5B Q4_K_M is primary. Peak RSS 1825.72 MB, 16.44 tok/s (profiler `--full`; llama-bench up to 17.94), TTFT ~9.0 s. T15: stay on Q4_K_M 1.5B unless held-out T11 regresses with RSS margin. Tiny Aya is not downloaded. No Aya numbers are claimed.
- **Rejected:** 7B-class (RSS risk); embeddings/FAISS (RAM); LLM-generated SQL (injection and hallucination).

Detail: [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md), [`docs/SECURITY.md`](docs/SECURITY.md).

---

## Constraints

- ADTC Standard Laptop: 8 GB RAM, integrated GPU, Ubuntu 22.04, Intel i5 or AMD Ryzen 5.
- 100% offline during evaluation; no API fees.
- Peak RSS self-limit < 5.5 GB; thermal soak < 85 °C (else −10).
- OOM or crash is disqualification (S_total = 0).
- Optional ≤5 Udutech GPU hours for training only; final benches on CPU.

---

## Tools used (and why)

| Tool | Why |
|---|---|
| Official submission template | Required repo shape and metadata |
| adtc-profiler | Official latency, TPS, Peak RSS, thermal |
| llama.cpp + GGUF | Required runtime |
| SQLite3 | Local ledger, parameterized SQL, no daemon |
| pytest | Fail-closed regression tests |

---

## Benchmarks

Participant measurements on the build laptop. Definitive `--full` run: 2026-08-06. Freeze re-run 2026-08-11 (`--skip-accuracy`): Peak RSS 1821.11 MB, TPS 15.67 tok/s, TTFT 10548.82 ms, core temp peak 100.0 °C / throttled (FAIL on this laptop, consistent with the 2026-08-10 soak). Snapshot: `benchmarks/submission.json`. Accuracy self-benchmark 2026-08-12: `arc_easy` 50-sample **74.0%** (`acc_norm`) in [`BENCHMARKS.md`](BENCHMARKS.md) as toolchain evidence only. Official S_acc is ADTC audit mode on the eval machine.

| Metric | Measured (participant, `--full`, 2026-08-06) |
|---|---|
| Machine | Intel i7-8650U · 23.3 GB RAM · Ubuntu 22.04 · no GPU |
| Peak RSS | **1825.72 MB** |
| Generation speed | **16.44 tok/s** |
| Time to first token | 9026.84 ms |
| Thermal | 10-min soak PASS 2026-08-06 at `THREADS=2`/`ctx=1024` (mean 75.7 °C, peak 84.0 °C, 0/68 ≥ 85 °C). FAIL on 2026-08-10 re-run (peak 89.0 °C). The PASS does not reproduce on this laptop. |
| 7.5 GB-capped proof | Full stack under a 7.5 GiB cgroup cap: peak 0.77 GiB, llama-server VmRSS 1.80 GiB, headroom 6.73 GiB (2026-08-06, `scripts/ram_capped_proof.sh`) |

Peak RSS is under the 5.5 GB self-limit. The stack (llama-server plus three narrated asks) ran under a 7.5 GiB `MemoryMax` cap with 6.73 GiB headroom. Process footprint (~1.80 GiB) leaves roughly 3× margin under the 7 GB usable ceiling.

Thermal on this laptop: `THREADS=3` (peak 97 °C) and `THREADS=2` at `ctx=2048` (peak 93 °C) fail < 85 °C. `THREADS=2`/`ctx=1024` passed on 2026-08-06 and failed on 2026-08-10 from a cooler idle. **Ship default:** `THREADS=2`/`CTX=1024` in `scripts/start_llama_server.sh`. Official P_thermal is the eval-machine run.

Tables and method: [`BENCHMARKS.md`](BENCHMARKS.md). Model limits: [`MODEL_CARD.md`](MODEL_CARD.md).

---

## Evaluation (held-out, offline)

37 prompts (28 English, 5 French, 4 Swahili) in `evals/heldout/prompts.json` (`language_scope: ["en","fr","sw"]`) against two disjoint ledgers: Marché Akwa Viviane (Douala) and Marché Nkolmébé (`duka_b`, Yaoundé). Coverage: credit, payables, stock, NULL refusals, adversarial asks, cross-shop non-leak, and ledger-flip proofs.

**40/40 checks pass** (`PYTHONPATH=. .venv/bin/python evals/run_heldout.py`; `pytest tests/ -q` = 78 passed). T11 bind/refuse: **37/37 = 100.0%** (target ≥ 90%). Report: [`evals/heldout/REPORT.md`](evals/heldout/REPORT.md).

**T13.** The two prompts in `metadata.json` are disjoint from the held-out set. `tp_001` (Esther Tchamba, NULL credit limit) uses an entity absent from held-out. `tp_002` (Chidi Okafor × Sucre 25kg) is a novel entity×product ask. Chidi Okafor appears in held-out only as a different scenario (`cb_02`, one bag of flour). The projected total 31000 is not in any held-out binder message. `tests/test_metadata.py` fails CI if a staff-ask string appears in the held-out file.

---

## African use case claim

`african_alpha_claim: true` is the **use-case** claim: an offline MSME shop ledger assistant for commodity laptops, designed from Cameroon (Douala / XAF) reality. Product languages are English, French, and Swahili binder tracks. Narration is limited to English and French, the languages the frozen model handles reliably.
