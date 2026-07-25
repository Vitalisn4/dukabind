# Security model — DukaBind

**Status:** Active Gate 1 design  
**Last reviewed:** 2026-07-25  
**Audience:** Builders + Gate 2 auditors

This document is the authoritative threat model for the binder. Every security-sensitive code path must cite a control ID from here.

---

## 1. Assets

| Asset | Sensitivity | Why it matters |
|---|---|---|
| Shop ledger (credit limits, balances, stock) | High | Wrong disclosure or mutation loses money/trust |
| Owner write capability | High | Unauthorized stock/payment writes corrupt truth |
| Model weights | Low (public) | Public GGUF; integrity still required (sha256) |
| Audit log | Medium | Evidence of refuses and queries |

## 2. Trust boundaries

```
[Untrusted] Staff utterance / UI input
      │
      ▼
[Trusted] Intent router (rules) ──► Allowlisted SQL only
      │
      ▼
[Trusted] Citation JSON (rows from DB)
      │
      ▼
[Semi-trusted] LLM narration  (may hallucinate prose; MUST NOT invent amounts)
      │
      ▼
[Trusted] Post-check / refuse path if citation empty or policy fail
```

The language model is **never** trusted to choose SQL, invent balances, or execute writes.

## 3. Controls (must implement)

| ID | Control | Research basis |
|---|---|---|
| **C1** | **Allowlisted queries only** — finite named SQL statements; no string-built SQL from user or LLM text | OWASP A03 Injection; ADTC load-bearing integration requires deterministic ground truth |
| **C2** | **Parameterized binds** — `?` placeholders via `sqlite3`; never f-string SQL | Python sqlite3 docs; CWE-89 |
| **C3** | **No LLM-generated SQL** | Hallucination + injection surface; Phase 5 architecture decision |
| **C4** | **Fail closed** — empty/null required fields → refuse; never invent numbers | Competition differentiator + financial safety |
| **C5** | **Loopback bind** — `llama-server` and app listen on `127.0.0.1` only | Offline contest rule; reduce remote attack surface |
| **C6** | **Owner-gated writes** — mutating forms require local password/PIN (hashed); LLM cannot write | Separation of duties |
| **C7** | **Weight integrity** — `download_model.sh` verifies sha256 when known | Supply-chain hygiene for public HF downloads |
| **C8** | **No secrets in git** — `.env` ignored; no API keys (offline product) | ADTC offline rule |
| **C9** | **Synthetic demo data** — Gate 1 fixtures are fictional; no real PII without consent | Privacy / eligibility honesty |
| **C10** | **Injection tests** — pytest covers “ignore ledger / invent 5000” style prompts | Phase 7 / Phase 8 exposing questions |

## 4. Explicit non-goals (Gate 1)

- Full disk encryption (recommend OS-level; document for operators)
- SQLCipher (defer unless calendar slack — CPU cost)
- Multi-user auth / network multi-tenant (single shop laptop)
- Cloud sync or telemetry

## 5. Incident posture for judges

If asked “what stops the model inventing a balance?”:  
**Architectural:** the model only sees citation JSON from allowlisted SQL; missing fields trigger refuse before narration; tests assert no numeric hallucination path when rows are empty.

## 6. References

- [ADTC submission template rules](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template) — offline, llama.cpp, no weights in git  
- [Devpost overview](https://adtc-2026.devpost.com/) — 7 GB / OOM DQ, thermal −10  
- OWASP Injection prevention cheat sheet  
- Python `sqlite3` — DB-API parameter substitution  
- Phase 5 architecture (`docs/ADTC-2026-Phase5-Technical-Architecture.md`)
