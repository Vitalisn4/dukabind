# Design decisions

Each decision records **options** (when relevant), **choice**, **evidence**, and **how to reverse** if measurements fail.

---

## D1: Product, fail-closed ledger binder (not chat RAG)

| | |
|---|---|
| **Options** | Generic shop chatbot; vector RAG over SOPs; allowlisted SQL binder |
| **Choice** | Allowlisted SQL binder + optional LLM narration |
| **Evidence** | Differentiates from multilingual chat demos; 7 GB ceiling punishes large embedding indexes; judges reward products beyond demos |
| **Reverse if** | Reviewers require corpus RAG. Add FTS5 SOP search only after RSS headroom is proven |

---

## D2: Domain, `corporate_enterprise`

| | |
|---|---|
| **Choice** | `corporate_enterprise` in `metadata.json` |
| **Evidence** | Devpost frames knowledge-work for SMEs/operators; challenge narrative centres African small-business / corner-shop contexts |
| **Scope note** | Seeded ledger uses Douala (XAF). Product intent is African MSME counters with intermittent connectivity, not a Cameroon-only chatbot |

---

## D3: Model, Qwen2.5-1.5B-Instruct GGUF Q4_K_M (primary)

| | |
|---|---|
| **Options** | SmolLM2-135M (template demo); Qwen 1.5B; Tiny Aya ~3B; 7B-class |
| **Choice** | Qwen2.5-1.5B Q4_K_M primary |
| **Evidence** | Official quant guidance favours Q4_K_M; official Qwen GGUF ~1.12 GB; 7B risks Peak RSS DQ; SmolLM is weak for refuse/arithmetic accuracy |
| **URL** | `https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf` |
| **License** | Upstream Apache-2.0 for weights (confirm card at download); separate from repo GPL-3.0 |
| **Reverse if** | Peak RSS / refuse quality fail on contest laptop. Try Q3_K_M before any larger model |

---

## D4: Runtime, llama.cpp only

| | |
|---|---|
| **Choice** | Official `llama.cpp` + GGUF via local `llama-server` |
| **Evidence** | Template and FAQ require llama.cpp + GGUF only (no ONNX/MLC for this track) |
| **Reverse if** | Contest rules change (unlikely mid-challenge) |

---

## D5: Storage, SQLite + WAL

| | |
|---|---|
| **Options** | JSON files; DuckDB; Postgres; SQLite |
| **Choice** | SQLite3 with WAL and foreign keys |
| **Evidence** | Zero daemon; file-portable; parameterized queries; FTS5 available later; light for shop laptops |
| **Reverse if** | Write-heavy multi-process contention appears (unlikely at Gate 1 read path) |

---

## D6: Intent routing, rules first

| | |
|---|---|
| **Choice** | Keyword / lexicon English maps to a named allowlist query |
| **Evidence** | Deterministic; near-zero RAM; reduces intent hallucination |
| **Reverse if** | Coverage gaps after English held-out. Add constrained LLM JSON parse as fallback only |

---

## D6b: Product language, English, French, Swahili binder tracks (Gate 1)

| | |
|---|---|
| **Choice** | `language_scope: ["en","fr","sw"]`. Cashier asks and binder messages localized deterministically in English, French (Cameroon official language), and Swahili (pan-African) |
| **Evidence** | Language detection is keyword-based and deterministic; binder messages are templated per language with tests; narration was verified empirically on the frozen Qwen2.5-1.5B. English and French narrate reliably, **Swahili does not, so Swahili is binder-only** (narration skipped so money figures are never mis-stated) |
| **African claim** | `african_alpha_claim: true` covers the **offline Cameroon/Douala MSME ledger use-case** plus French/Swahili binder tracks |
| **Deferred** | Additional languages after Gate 1 |
| **Reverse if** | Held-out quality regresses in English, or a bigger model narrates Swahili reliably within the 8 GB envelope |

---

## D7: License posture

| | |
|---|---|
| **Repository** | **GNU GPL v3** (`LICENSE`), the governing license for this codebase |
| **Provenance** | Initialized from the ADTC submission template (GPL-3.0) |
| **Model weights** | Not in git; Qwen2.5 GGUF remains under upstream Apache-2.0 on Hugging Face |
| **Action** | Keep `NOTICE` and `LICENSE` aligned; do not claim Apache-2.0 for application code |

---

## D8: Seeded shop ledger

| | |
|---|---|
| **Choice** | Seeded SQLite shop (`marche_akwa` / Marché Akwa Viviane) with customers, suppliers, and SKUs |
| **Evidence** | Reproducible binder behaviour under Git; same pipeline loads any shop file offline |
| **Privacy** | Do not commit third-party personal data without explicit consent and redaction |
| **Reverse if** | Replacing the seed with an imported shop export (still offline, still allowlisted) |

---

## Related documents

- Threat model and control IDs: [`SECURITY.md`](./SECURITY.md)
