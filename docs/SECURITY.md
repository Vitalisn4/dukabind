# Security model: DukaBind

This document maps controls C1-C10. Implementation comments currently cite C1-C5 and C7. C6 is deferred. C8-C10 are documented here without code-level ID comments.

---

## 1. Assets

| Asset | Sensitivity | Why it matters |
|---|---|---|
| Shop ledger (credit limits, balances, stock) | High | Wrong disclosure or mutation loses money and trust |
| Owner write capability | High | Unauthorized stock/payment writes corrupt ground truth |
| Model weights | Low (public GGUF) | Still require integrity checks (sha256) |
| Audit log | Medium | Evidence of queries and refusals |

---

## 2. Trust boundaries

```text
[Untrusted] Staff utterance / UI input
      │
      ▼
[Trusted] Intent router (rules) ──► Allowlisted SQL only
      │
      ▼
[Trusted] Citation JSON (rows from DB)
      │
      ▼
[Untrusted] LLM narration  (optional polish; not validated for figures)
      │
      ▼
[Trusted] Binder message remains authoritative; refuse skips the model
```

The language model is never trusted to choose SQL, invent balances, or execute writes.

---

## 3. Controls

| ID | Control | Basis | Status |
|---|---|---|---|
| **C1** | **Allowlisted queries only**: finite named SQL; no SQL built from user or model text | OWASP A03; deterministic ground truth | **Implemented** in `app/binder/allowlist.py` |
| **C2** | **Parameterized binds**: `?` via `sqlite3`; never f-string SQL | CWE-89; Python DB-API | **Implemented** in the same module |
| **C3** | **No LLM-generated SQL** | Hallucination + injection surface | **Implemented**. The model receives staff question + binder message + citation JSON; never receives SQL or chooses a query |
| **C4** | **Fail closed**: NULL/missing required fields refuse; never invent numbers | Financial safety | **Implemented** in `refuse.py` + tests |
| **C5** | **Loopback only**: `llama-server` and client use `127.0.0.1`; no redirects | Offline rule; reduce remote surface | **Implemented** in the start script + `assert_loopback_http` |
| **C6** | **Owner-gated writes**: mutating actions need local PIN/password; LLM cannot write | Separation of duties | **Deferred**, no write UI at this stage |
| **C7** | **Weight integrity**: `download_model.sh` verifies sha256 | Supply-chain hygiene | **Implemented**, pinned digest |
| **C8** | **No secrets in git**: no API keys; offline product | ADTC offline rule | **Implemented**, weights/env ignored |
| **C9** | **No third-party PII in git**: seeded shop rows only; do not commit customer files without consent | Privacy / eligibility honesty | **Implemented** in `seed.sql` + `fixture.py` |
| **C10** | **Injection / hallucination tests**: refuse and ledger-flip coverage; expand “invent amount” cases | Judge exposure questions | **Partial**, core refuse/flip tests; expand before Gate 3 |

---

## 4. Explicit non-goals (initial submission)

- Full-disk encryption (recommend OS-level for operators)
- SQLCipher (CPU cost on contest laptops)
- Multi-user network auth or multi-tenant hosting
- Cloud sync or telemetry

---

## 5. Reviewer FAQ

**What stops the model inventing a balance?**  
Architecture: the model only receives citation JSON from allowlisted SQL. Missing fields refuse before narration. Cashier-facing `message` is the only financial answer; optional `narration` is untrusted polish and is not validated for numbers. Tests cover NULL refuse and ledger flip.

**Where is the policy encoded?**  
Controls **C1-C5** and **C7** are cited in `app/binder/`, `app/llm/`, `scripts/start_llama_server.sh`, and `download_model.sh`. C8-C10 are repo and test practice described in this table, not ID comments in those paths. Design rationale: [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md).

---

## 6. References

- [ADTC submission template](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template), offline, llama.cpp, no weights in git  
- [Devpost overview](https://adtc-2026.devpost.com/), memory / OOM / thermal rules  
- OWASP Injection prevention cheat sheet  
- Python `sqlite3` parameterized queries  
- Architecture choices: [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md)
