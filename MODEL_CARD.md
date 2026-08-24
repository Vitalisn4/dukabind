# Model card: Qwen2.5-1.5B-Instruct (GGUF Q4_K_M)

DukaBind uses this model for optional local narration of English and French binder answers. The binder itself is deterministic (English, French, and Swahili).

| Field | Value |
|---|---|
| Base model | Qwen2.5-1.5B-Instruct |
| Quantization | GGUF **Q4_K_M** (~1.12 GB) |
| Runtime | llama.cpp (`llama-server`) only; no cloud API |
| Source | Hugging Face `Qwen/Qwen2.5-1.5B-Instruct-GGUF`, file `qwen2.5-1.5b-instruct-q4_k_m.gguf` |
| Integrity | sha256-pinned in [`download_model.sh`](download_model.sh) (control C7) |
| Upstream license | Apache-2.0 (weights). Application code is GPL-3.0. See [`NOTICE`](NOTICE). |
| Status | Primary model. See [`BENCHMARKS.md`](BENCHMARKS.md). |

## Intended use

- **Narrate cited ledger rows only.** The binder (`app/binder/`) runs allowlisted SQL on a local SQLite ledger and produces an authoritative `message` plus `citation_json`. Optional LLM narration is **untrusted**: it may polish wording of cited rows, but it is not validated for numeric claims. Treat `message` as the only financial answer. The model does not choose SQL or compute balances.
- **Offline counter Q&A** on credit, supplier payables, and stock, on 8 GB laptops without connectivity.
- **Language:** `language_scope=["en","fr","sw"]`. Binder answers are localized without the LLM. The African claim is the Cameroon MSME offline ledger use-case (`african_alpha_claim: true`).

## Out of scope

- Inventing balances, limits, or stock not present in citation rows. The binder refuses when a required money field is `NULL`. Refusals do not call the model.
- Choosing SQL, or any write path (owner-gated writes C6 are deferred).
- Swahili narration. **Swahili is binder-only.** The 1.5B model can invent figures in Swahili, so those answers ship the binder message only.
- Cloud APIs, telemetry, or network at inference time.

## Known limits

- Binder tracks: en/fr/sw. Narration: en/fr. Further languages are deferred.
- **Thermal.** On the build laptop (Intel i7-8650U), a 10-minute soak at `THREADS=2`/`ctx=1024` passed < 85 °C on 2026-08-06 (peak 84.0 °C, 0/68 samples ≥ 85 °C) and **failed** on 2026-08-10 from a cooler idle (mean 78.6 °C, peak **89.0 °C**). `THREADS=3`/`ctx=2048` and `THREADS=2`/`ctx=2048` also fail (peaks 97 °C / 93 °C). Treat P_thermal on this laptop as unverified. Official P_thermal is the ADTC eval machine. Shipped default: `THREADS=2`/`ctx=1024`. See [`BENCHMARKS.md`](BENCHMARKS.md).
- **Allowlist.** Seven answerable intents (credit check, credit headroom, supplier balance, stock on hand, total stock value, total outstanding debt, total supplier payables) plus refuse on unknown. Unknown entities refuse (`not_found`). That is by design, not a completeness claim.
- **Accuracy.** Official S_acc is ADTC audit mode on the eval machine. Participant self-benchmark: `arc_easy` 50-sample **74.0%** on 2026-08-18 (toolchain evidence, not S_acc). Held-out bind/refuse is **37/37 = 100.0%** on 37 prompts across EN/FR/SW. See [held-out report](evals/heldout/REPORT.md).

## Measured performance (build laptop, participant mode)

| Metric | Measured | Source |
|---|---|---|
| Peak RSS | 1826.23 MB | profiler `--full`, 2026-08-18 |
| Generation TPS | 17.35 tok/s (profiler); up to 17.94 (llama-bench `-t 3`) | `BENCHMARKS.md` |
| TTFT | 8175.55 ms | profiler `--full`, 2026-08-18 |
| 7.5 GiB-capped stack | PASS; cgroup peak 0.77 GiB; headroom 6.73 GiB | `scripts/ram_capped_proof.sh` |
| Thermal soak (10 min) | PASS 2026-08-06 at `THREADS=2`/`ctx=1024` (mean 75.7 °C, peak 84.0 °C); **FAIL 2026-08-10 re-run (peak 89.0 °C)** | `BENCHMARKS.md` |

Full tables: [`BENCHMARKS.md`](BENCHMARKS.md).

## How to run

```bash
./download_model.sh
bash scripts/setup_llama.sh
bash scripts/start_llama_server.sh
PYTHONPATH=. .venv/bin/python -m app.narrate_cli "Can I give Marie-Claire three crates on credit?"
```

Without the model, the binder still answers and refuses correctly:

```bash
PYTHONPATH=. .venv/bin/python -m app.cli "Can I give Marie-Claire three crates on credit?"
```

## Why Q4_K_M 1.5B

- Q4_K_M is the recommended quality/size trade. The 1.5B keeps Peak RSS far under 5.5 GB. The **binder** (not the model) achieves **37/37 = 100%** on EN/FR/SW held-out prompts (target >= 90%). Narration evidence is English and French only.
- The model is kept frozen unless held-out accuracy regresses with RSS margin. Alternatives (3B Q4, Tiny Aya) are out of scope for this submission.

See [`BENCHMARKS.md`](BENCHMARKS.md) · [held-out report](evals/heldout/REPORT.md) · [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) · [`docs/SECURITY.md`](docs/SECURITY.md).
