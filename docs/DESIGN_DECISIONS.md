# Design decisions

**Status:** Living document — lock choices early; revise only with measurement or rule changes  
**Last updated:** 2026-07-26  
**Audience:** Contributors and Gate reviewers

Each decision records **options** (when relevant), **choice**, **evidence**, and **how to reverse** if measurements fail. Update the change log when a decision flips.

---

## D1 — Product: fail-closed ledger binder (not chat RAG)

| | |
|---|---|
| **Options** | Generic shop chatbot; vector RAG over SOPs; allowlisted SQL binder |
| **Choice** | Allowlisted SQL binder + optional LLM narration |
| **Evidence** | Differentiates from multilingual chat demos; 7 GB ceiling punishes large embedding indexes; judges reward products beyond demos |
| **Reverse if** | Reviewers require corpus RAG — add FTS5 SOP search only after RSS headroom is proven |

---

## D2 — Domain: `corporate_enterprise`

| | |
|---|---|
| **Choice** | `corporate_enterprise` in `metadata.json` |
| **Evidence** | Devpost frames knowledge-work for SMEs/operators; challenge narrative centres African small-business / corner-shop contexts |
| **Scope note** | Demo fixture uses Douala (XAF). Product intent is African MSME counters with intermittent connectivity — not a Cameroon-only chatbot |

---

## D3 — Model: Qwen2.5-1.5B-Instruct GGUF Q4_K_M (primary)

| | |
|---|---|
| **Options** | SmolLM2-135M (template demo); Qwen 1.5B; Tiny Aya ~3B; 7B-class |
| **Choice** | Qwen2.5-1.5B Q4_K_M primary; Tiny Aya reserved as Swahili bake-off challenger |
| **Evidence** | Official quant guidance favours Q4_K_M; official Qwen GGUF ~1.12 GB; 7B risks Peak RSS DQ; SmolLM is weak for refuse/arithmetic accuracy |
| **URL** | `https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf` |
| **License** | Upstream Apache-2.0 for weights (confirm card at download); separate from repo GPL-3.0 |
| **Reverse if** | Swahili held-out fails and Aya clears RSS / thermal / TPS gates |

---

## D4 — Runtime: llama.cpp only

| | |
|---|---|
| **Choice** | Official `llama.cpp` + GGUF via local `llama-server` |
| **Evidence** | Template and FAQ require llama.cpp + GGUF only (no ONNX/MLC for this track) |
| **Reverse if** | Contest rules change (unlikely mid-challenge) |

---

## D5 — Storage: SQLite + WAL

| | |
|---|---|
| **Options** | JSON files; DuckDB; Postgres; SQLite |
| **Choice** | SQLite3 with WAL and foreign keys |
| **Evidence** | Zero daemon; file-portable; parameterized queries; FTS5 available later; light for shop laptops |
| **Reverse if** | Write-heavy multi-process contention appears (unlikely at Gate 1 read path) |

---

## D6 — Intent routing: rules first

| | |
|---|---|
| **Choice** | Keyword / lexicon EN+SW → named allowlist query |
| **Evidence** | Deterministic; near-zero RAM; reduces intent hallucination |
| **Reverse if** | Coverage gaps after bilingual eval — add constrained LLM JSON parse as fallback only |

---

## D7 — License posture

| | |
|---|---|
| **Repository** | **GNU GPL v3** (`LICENSE`) — governing license for this codebase |
| **Provenance** | Initialized from the ADTC submission template (GPL-3.0) |
| **Model weights** | Not in git; Qwen2.5 GGUF remains under upstream Apache-2.0 on Hugging Face |
| **Action** | Keep `NOTICE` and `LICENSE` aligned; do not claim Apache-2.0 for application code |

---

## D8 — Demo data: synthetic only

| | |
|---|---|
| **Choice** | Fictional shop fixtures (`duka_a` seed; further fixtures as needed) |
| **Evidence** | Privacy, reproducibility, eligibility honesty — no real customer PII without consent |
| **Reverse if** | Never reverse into committing real shop data without explicit consent and redaction policy |

---

## Related documents

- Threat model and control IDs: [`SECURITY.md`](./SECURITY.md)  
- Module map and commands: [`CODE_WALKTHROUGH.md`](./CODE_WALKTHROUGH.md)

---

## Change log

| Date | Change |
|---|---|
| 2026-07-26 | Structured headers; Africa-wide product scope note; linked SECURITY / walkthrough |
| 2026-07-25 | Initial decisions locked for Week 0–1 implementation |
