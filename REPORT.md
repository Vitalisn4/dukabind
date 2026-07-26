# Technical Report — DukaBind

**Team ID:** vitalisn4 (provisional solo ID — GitHub handle; replace if ADTF issues an official ID)  
**Submitter:** Vitalis Ngam · ngamvitailisyuh@gmail.com · [Vitalisn4](https://github.com/Vitalisn4)  
**Domain:** corporate_enterprise  
**Model:** Qwen2.5-1.5B-Instruct-Q4_K_M  
**Team size:** Solo

---

## Problem

When a micro/small shop owner is away from the counter, semi-trained staff cannot reliably answer credit, payables, or stock questions. Cloud POS and messaging bots fail without connectivity; general chatbots invent balances.

**DukaBind** is an offline llama.cpp/GGUF assistant that answers only from a local SQLite ledger bind and fails closed when data is missing. Target users: counter staff (primary), shop owners (secondary). African context: commodity 8 GB laptops, intermittent mobile data, owner-absent shifts — designed from Cameroon MSME shop reality (demo fixture: Douala, XAF).

See [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) for selection rationale and alternatives considered.

---

## Design Decisions

- **Base model:** Qwen2.5-1.5B-Instruct (Apache-2.0 upstream); Tiny Aya ~3B reserved as bake-off challenger for Swahili quality.
- **Quantization:** GGUF Q4_K_M — quality/size trade per Devpost quant guidance; official Qwen GGUF file ~1.12 GB.
- **Integration (load-bearing):** Allowlisted SQL binder — not vector RAG. Protects S_eff under the 7 GB usable budget and prevents financial hallucination.
- **Runtime:** llama.cpp only (template + FAQ requirement).
- **Alternatives rejected:** 7B-class (RSS DQ risk); embeddings/FAISS (RAM); LLM-generated SQL (injection + hallucination).

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

| Metric | Value |
|---|---|
| Machine | _to measure on build laptop_ |
| RAM at peak | _adtc-profiler only — never invent_ |
| Time to first token | _to measure_ |
| Generation speed | _target ≥15 tok/s warm (Devpost TPS_REFERENCE provisional)_ |
| Thermal throttling | _must remain none under soak_ |

Official scores are measured by the ADTC profiler on the standard evaluation machine.

---

## African use case claim

`african_alpha_claim: true` — product is an offline MSME shop ledger assistant for African commodity laptops (Cameroon-designed demo), not a generic cloud chatbot. Swahili is a designed track with kill switch if RSS/quality fail bake-off.
