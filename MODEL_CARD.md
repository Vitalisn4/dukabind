# Model card: Qwen2.5-1.5B-Instruct (GGUF Q4_K_M)

**Model used by:** DukaBind (ADTC 2026 Gate 1), an offline fail-closed SQLite ledger binder (English, French, and Swahili binder tracks) with optional local narration (English and French).

| Field | Value |
|---|---|
| Base model | Qwen2.5-1.5B-Instruct |
| Quantization | GGUF **Q4_K_M** (~1.12 GB file) |
| Runtime | llama.cpp (`llama-server`) only, no cloud, no API |
| Source | Hugging Face: `Qwen/Qwen2.5-1.5B-Instruct-GGUF`, file `qwen2.5-1.5b-instruct-q4_k_m.gguf` |
| Integrity | sha256-pinned in [`download_model.sh`](download_model.sh) (control C7) |
| Upstream license | Apache-2.0 (Qwen weights on Hugging Face), separate from this repo's GPL-3.0 application code (see [`NOTICE`](NOTICE)) |
| Lock status | **M3 model lock**, frozen as primary on measured evidence; see [`BENCHMARKS.md`](BENCHMARKS.md) |

## Intended use

- **Narrate cited ledger rows only.** DukaBind's deterministic binder (`app/binder/`) runs allowlisted SQL on a local SQLite shop ledger and produces an authoritative `message` plus `citation_json`. The model may **polish wording** of those rows. It never chooses SQL, never computes balances, and never sees or outputs amounts that are not already in the citation JSON.
- **Offline counter-staff Q&A** about credit, supplier payables, and stock on hand, on commodity 8 GB laptops with no connectivity.
- **Language scope:** `language_scope=["en","fr","sw"]`. Binder answers are localized deterministically (no LLM) in English, French (Cameroon official language), and Swahili (pan-African). The African use-case claim is the **Cameroon MSME offline ledger use-case** (`african_alpha_claim: true`).

## Out of scope (do not rely on it for)

- Inventing balances, limits, or stock figures that are not in the citation rows. The binder **refuses** (fail closed) when a required money field is `NULL`; refusals never call the model.
- Choosing or generating SQL, or any write path (owner-gated writes C6 are deferred past Gate 1).
- Narration languages: English and French (verified on the frozen Qwen2.5-1.5B). **Swahili is binder-only**. The 1.5B model does not narrate Swahili reliably (it can invent figures), so Swahili answers ship the authoritative deterministic binder message without model narration.
- Anything requiring a cloud API, telemetry, or network at inference time.

## Known limits

- **Multilingual binder track (en/fr/sw) shipped; narration is en/fr.** Additional languages remain a post–Gate 1 extension on the same binder.
- **Thermal on hot laptops:** on the build laptop (Intel i7-8650U) a 10-minute soak passed **&lt; 85 °C at `THREADS=2`/`ctx=1024`** on 2026-08-06 (peak 84.0 °C, 0/68 samples ≥ 85 °C), but that **PASS no longer reproduces**: the identical config re-run on 2026-08-10 from a cooler 60 °C idle **FAILED** (mean 78.6 °C, peak **89.0 °C**, several samples ≥ 85 °C). `THREADS=3`/`ctx=2048` and `THREADS=2`/`ctx=2048` also fail on that host (peaks 97 °C / 93 °C). Treat P_thermal on the build laptop as **unverified (FAIL on 2026-08-10 re-run)**; the authoritative P_thermal call is the official ADTC eval machine. Shipped default: `THREADS=2`/`ctx=1024` (documented in [`BENCHMARKS.md`](BENCHMARKS.md)).
- **Allowlist coverage:** the binder answers three intents (credit, supplier balance, stock) against the seeded ledgers. Unknown intents/entities refuse with `not_found`, by design, not a completeness claim.
- **Accuracy measurement:** official S_acc comes from ADTC audit mode on the eval machine. The profiler's participant mode can now emit a real self-benchmark (`arc_easy` 50-sample **74.0%** on 2026-08-12, toolchain evidence, not a S_acc claim). Held-out bind/refuse (T11) is measured separately by `evals/run_heldout.py`. See the [held-out report](evals/heldout/REPORT.md).

## Measured performance (build laptop, participant mode)

| Metric | Measured | Source |
|---|---|---|
| Peak RSS | 1825.72 MB | profiler `--full`, 2026-08-06 |
| Generation TPS | 16.44 tok/s (profiler); up to 17.94 (llama-bench `-t 3`) | `BENCHMARKS.md` |
| TTFT | 9026.84 ms | profiler `--full` |
| 7.5 GiB-capped stack | PASS, cgroup peak 0.77 GiB, headroom 6.73 GiB | `scripts/ram_capped_proof.sh` |
| Thermal soak (10 min) | PASS 2026-08-06 at `THREADS=2`/`ctx=1024` (mean 75.7 °C, peak 84.0 °C, 0/68 ≥ 85 °C); **FAIL 2026-08-10 re-run (peak 89.0 °C), no longer reproducible** | `BENCHMARKS.md` |

Full tables, methodology, and the thread/context matrix: [`BENCHMARKS.md`](BENCHMARKS.md).

## How to run

```bash
./download_model.sh                                   # downloads + sha256-verifies the GGUF once
bash scripts/setup_llama.sh                           # builds llama.cpp (third_party/, gitignored)
bash scripts/start_llama_server.sh                    # terminal A, llama-server on 127.0.0.1, CPU only
PYTHONPATH=. .venv/bin/python -m app.narrate_cli "Can I give Marie-Claire three crates on credit?"  # terminal B
```

Without the model, the binder still answers deterministically and refuses correctly:

```bash
PYTHONPATH=. .venv/bin/python -m app.cli "Can I give Marie-Claire three crates on credit?"
```

## Why Q4_K_M 1.5B (T15 quant lock)

- Q4_K_M is the ADTC-recommended quality/size trade-off; the 1.5B keeps Peak RSS far under the 5.5 GB self-limit while clearing the 3-intent bind/refuse held-out bar (T11 **28/28 = 100%**, target ≥ 90%).
- **T15 lock:** stays frozen unless T11 regresses against the held-out set with RSS margin; a 3B Q4 would only be considered if T1–T3 stay green.
- Tiny Aya (~3B) is **skipped** under the locked model scope; no Aya benchmark numbers are claimed or invented.

*See also:* [`BENCHMARKS.md`](BENCHMARKS.md) · [held-out report](evals/heldout/REPORT.md) · [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) · [`docs/SECURITY.md`](docs/SECURITY.md)
