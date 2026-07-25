# Design decisions — research-backed

Each decision lists **options**, **choice**, **evidence**, and **how to reverse** if measurements fail.

---

## D1 — Product: fail-closed ledger binder (not chat RAG)

| | |
|---|---|
| **Options** | Generic shop chatbot; vector RAG over SOPs; allowlisted SQL binder |
| **Choice** | Allowlisted SQL binder + LLM narration |
| **Evidence** | Devpost field is steered toward multilingual chat (Resources #7 Aya, #8 Masakhane). Structural binding differentiates. Judge Oji Udezue session emphasized products beyond demos. 7 GB ceiling punishes embedding indexes. |
| **Reverse if** | Judges require corpus RAG — add FTS5 SOP search only after RSS headroom proven |

## D2 — Domain: `corporate_enterprise`

| | |
|---|---|
| **Evidence** | Official blurb: knowledge-work for SMEs/operators ([Devpost](https://adtc-2026.devpost.com/)). Challenge intro names Dakar small-business owner / corner shops. Phase 2–4 scoring. |
| **metadata.json** | `"domain": "corporate_enterprise"` |

## D3 — Model: Qwen2.5-1.5B-Instruct GGUF Q4_K_M (primary)

| | |
|---|---|
| **Options** | SmolLM2-135M (template demo); Qwen 1.5B; Tiny Aya 3.35B; 7B-class |
| **Choice** | Qwen2.5-1.5B Q4_K_M primary; Aya bake-off Week 2 |
| **Evidence** | Official quant guide: Q4_K_M sweet spot. Official Qwen GGUF publishes `qwen2.5-1.5b-instruct-q4_k_m.gguf` (~1.12 GB) on Hugging Face. 7B risks Peak RSS DQ. Template SmolLM is too weak for refuse/arithmetic S_acc. |
| **URL** | `https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf` |
| **License** | Apache-2.0 (confirm card at download) |
| **Reverse if** | SW held-out fails and Aya clears RSS/thermal/TPS gates (Phase 5 bake-off criteria) |

## D4 — Runtime: llama.cpp only

| | |
|---|---|
| **Evidence** | Template + FAQ: **llama.cpp + GGUF only**. No ONNX/MLC. |

## D5 — Storage: SQLite + WAL

| | |
|---|---|
| **Options** | JSON files; DuckDB; Postgres; SQLite |
| **Choice** | SQLite3 WAL |
| **Evidence** | Zero daemon; file-portable; parameterized queries; FTS5 available later; public domain. DuckDB/Postgres heavier for shop laptop. |

## D6 — Intent routing: rules first, not LLM-first

| | |
|---|---|
| **Choice** | Keyword/lexicon EN+SW → named allowlist query |
| **Evidence** | Reduces hallucination of intent; deterministic; near-zero RAM. LLM JSON parse only as fallback after M1. |

## D7 — License posture

| | |
|---|---|
| **Repository** | **GNU GPL v3** (`LICENSE`) — governing license for this codebase |
| **Provenance** | Initialized from the ADTC submission template (also GPL-3.0) |
| **Model weights** | Not in git; Qwen2.5 GGUF remains under its upstream Apache-2.0 terms on Hugging Face (separate from repo code license) |
| **Action** | Keep `NOTICE` + `LICENSE` consistent; do not claim Apache-2.0 for application code while `LICENSE` is GPL-3.0 |

## D8 — Demo data: synthetic only

| | |
|---|---|
| **Evidence** | Privacy; reproducibility; Phase 7 fixtures `duka_a` / `duka_b`. No real shop PII without consent. |

---

## Change log

| Date | Change |
|---|---|
| 2026-07-25 | Initial decisions locked for Week 0–1 implementation |
