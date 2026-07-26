# Security model — DukaBind

**Status:** Active — Gate 1  
**Last reviewed:** 2026-07-26  
**Audience:** Contributors and Gate auditors  
**Authority:** Security-sensitive code paths should cite a control ID from this document.

This is the threat model for the ledger binder. Update the **Status** column when a control ships, is deferred, or changes.

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
[Semi-trusted] LLM narration  (may polish prose; MUST NOT invent amounts)
      │
      ▼
[Trusted] Binder message remains authoritative; refuse skips the model
```

The language model is never trusted to choose SQL, invent balances, or execute writes.

---

## 3. Controls

| ID | Control | Basis | Gate 1 status |
|---|---|---|---|
| **C1** | **Allowlisted queries only** — finite named SQL; no SQL built from user or model text | OWASP A03; deterministic ground truth | **Implemented** — `app/binder/allowlist.py` |
| **C2** | **Parameterized binds** — `?` via `sqlite3`; never f-string SQL | CWE-89; Python DB-API | **Implemented** — same module |
| **C3** | **No LLM-generated SQL** | Hallucination + injection surface | **Implemented** — model sees citation JSON only |
| **C4** | **Fail closed** — NULL/missing required fields → refuse; never invent numbers | Financial safety | **Implemented** — `refuse.py` + tests |
| **C5** | **Loopback only** — `llama-server` and client use `127.0.0.1`; no redirects | Offline rule; reduce remote surface | **Implemented** — start script + `assert_loopback_http` |
| **C6** | **Owner-gated writes** — mutating actions need local PIN/password; LLM cannot write | Separation of duties | **Deferred** — no write UI at Gate 1 |
| **C7** | **Weight integrity** — `download_model.sh` verifies sha256 | Supply-chain hygiene | **Implemented** — pinned digest |
| **C8** | **No secrets in git** — no API keys; offline product | ADTC offline rule | **Implemented** — weights/env ignored |
| **C9** | **Synthetic demo data** — fictional fixtures; no real PII without consent | Privacy / eligibility honesty | **Implemented** — `seed_demo.sql` |
| **C10** | **Injection / hallucination tests** — refuse and ledger-flip coverage; expand “invent amount” cases | Judge exposure questions | **Partial** — core refuse/flip tests; expand before Gate 3 |

---

## 4. Explicit non-goals (Gate 1)

- Full-disk encryption (recommend OS-level for operators)
- SQLCipher (CPU cost on contest laptops)
- Multi-user network auth or multi-tenant hosting
- Cloud sync or telemetry

---

## 5. Reviewer FAQ

**What stops the model inventing a balance?**  
Architecture: the model only receives citation JSON from allowlisted SQL. Missing fields refuse before narration. Cashier-facing `message` stays the binder decision; optional polish is stored in `narration`. Tests cover NULL refuse and ledger flip.

**Where is the policy encoded?**  
Controls **C1–C5** and **C7–C9** in code under `app/binder/` and `app/llm/`. Design rationale: [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md).

---

## 6. References

- [ADTC submission template](https://github.com/Africa-Deep-Tech-Foundation/adtc-2026-submission-template) — offline, llama.cpp, no weights in git  
- [Devpost overview](https://adtc-2026.devpost.com/) — memory / OOM / thermal rules  
- OWASP Injection prevention cheat sheet  
- Python `sqlite3` parameterized queries  
- Architecture choices: [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md)

---

## Change log

| Date | Change |
|---|---|
| 2026-07-26 | Added Gate 1 implementation status per control; clarified binder-authoritative message |
| 2026-07-25 | Initial threat model |
