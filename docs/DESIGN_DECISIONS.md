# Design decisions

This document records the key technical choices behind DukaBind, the alternatives considered, and the evidence behind each decision.

---

## D1: Allowlisted SQL binder (not chat RAG)

| | |
|---|---|
| **Choice** | Allowlisted SQL binder with optional LLM narration |
| **Alternatives considered** | Generic shop chatbot, vector RAG over SOPs |
| **Why this choice** | A 7 GB RAM ceiling makes large embedding indexes impractical. Allowlisted SQL gives deterministic answers with near-zero memory overhead. The model narrates wording, not numbers, so financial accuracy is guaranteed by the database, not the LLM. |

---

## D2: Domain, `corporate_enterprise`

| | |
|---|---|
| **Choice** | `corporate_enterprise` in metadata.json |
| **Why this choice** | The challenge frames knowledge-work for SMEs and operators. DukaBind serves African MSME shop counters with credit, payables, and stock questions. The seeded ledger uses Douala (XAF), but the product design applies to any MSME with intermittent connectivity. |

---

## D3: Model, Qwen2.5-1.5B-Instruct GGUF Q4_K_M

| | |
|---|---|
| **Choice** | Qwen2.5-1.5B Q4_K_M (~1.12 GB) |
| **Alternatives considered** | SmolLM2-135M (too weak for credit arithmetic), Tiny Aya ~3B (RSS risk), 7B-class (would exceed 5.5 GB self-limit) |
| **Why this choice** | The official quant guidance recommends Q4_K_M. The 1.5B parameter count keeps Peak RSS at 1826 MB, well under the 5.5 GB self-limit. The model handles credit arithmetic and refusal correctly in testing. |
| **Model source** | Hugging Face: `Qwen/Qwen2.5-1.5B-Instruct-GGUF`, file `qwen2.5-1.5b-instruct-q4_k_m.gguf` |
| **License** | Upstream Apache-2.0 for weights; application code is GPL-3.0 |

---

## D4: Runtime, llama.cpp only

| | |
|---|---|
| **Choice** | llama.cpp + GGUF via local llama-server |
| **Why this choice** | Required by the contest rules. No ONNX, MLC, or other runtimes are accepted for this track. |

---

## D5: SQLite with WAL (not JSON, DuckDB, or Postgres)

| | |
|---|---|
| **Choice** | SQLite3 with WAL mode and foreign keys |
| **Alternatives considered** | JSON files, DuckDB, Postgres |
| **Why this choice** | SQLite requires no daemon, is file-portable, supports parameterized queries (preventing SQL injection), and is lightweight enough for shop laptops. FTS5 is available if full-text search is needed later. |

---

## D6: Keyword-based intent routing (not LLM-generated SQL)

| | |
|---|---|
| **Choice** | Keyword and lexicon maps (English, French, Swahili) that map to named allowlisted SQL queries |
| **Why this choice** | Deterministic, near-zero RAM, and eliminates intent hallucination. The model never sees the database schema or chooses which query to run. |

---

## D7: Three languages: English, French, Swahili

| | |
|---|---|
| **Choice** | `language_scope: ["en","fr","sw"]` |
| **Why this choice** | English is the primary language. French is an official language of Cameroon. Swahili is a major pan-African language. Binder messages are deterministic in all three. |
| **Narration note** | English and French narration works reliably on the frozen Qwen2.5-1.5B. Swahili narration does not, so Swahili answers use the binder message directly (no model involved). This ensures money figures are never mis-stated. |
| **African claim** | `african_alpha_claim: true` covers the offline Cameroon/Douala MSME ledger use-case with French and Swahili binder tracks. |

---

## D8: License posture

| | |
|---|---|
| **Application code** | GNU GPL v3 (see `LICENSE`) |
| **Model weights** | Not committed to git. Qwen2.5 GGUF stays under upstream Apache-2.0 on Hugging Face |
| **Provenance** | Repository initialized from the ADTC submission template (GPL-3.0) |

---

## D9: Seeded shop ledger

| | |
|---|---|
| **Choice** | Seeded SQLite shop (Marche Akwa Viviane, Douala) with customers, suppliers, and SKUs |
| **Why this choice** | Reproducible binder behaviour under Git. The same pipeline loads any shop file offline. A second ledger (duka_b, Yaounde) is used for held-out testing to prove the system does not overfit to one shop. |
| **Privacy** | No third-party personal data is committed without consent. The seed data is fictional. |

---

## Related documents

- Threat model and controls: [`SECURITY.md`](./SECURITY.md)
- Benchmarks and measurements: [`../BENCHMARKS.md`](../BENCHMARKS.md)
- Model details: [`../MODEL_CARD.md`](../MODEL_CARD.md)
