# Demo video — DukaBind (M6 freeze)

| | |
|---|---|
| **Video file** | [`demo/demo.mp4`](./demo.mp4) |
| **Duration** | 114 s (≤ 120 s gate) |
| **Format** | H.264 MP4 · 1280×720 · ~0.56 MB |
| **Captions** | Burned in (watchable muted) |
| **Storyboard** | [`demo/storyboard.md`](./storyboard.md) |
| **Renderer** | [`scripts/render_demo_assets.py`](../scripts/render_demo_assets.py) — frames every on-screen line from real CLI output (no hand-typed text) |
| **Rendered on** | Build laptop, 2026-08-11 (branch `feature/dukabind-m6-freeze`) |

## Transcript (captions, with timestamps)

- **0:00** DukaBind — an offline shop assistant that cannot invent your money. ADTC 2026 · Corporate/Enterprise · llama.cpp + GGUF · Qwen2.5-1.5B Q4_K_M.
- **0:06** *Credit ask:* "Can I give Marie-Claire three crates on credit?" → **No — 3×720=2160; 6250+2160=8410 exceeds limit 8000 by 410 XAF. Max qty within limit: 2.** Citation block shown.
- **0:32** *Ledger flip:* `UPDATE customers SET credit_limit = 20000` → same question → **Yes — projected outstanding 8410 ≤ limit 20000 XAF.** Answer follows the row.
- **0:56** *Fail-closed refusal:* SOCA → `balance_owed_null` ("ask the owner"); Esther → `credit_limit_null`. Missing field named; no invented figure.
- **1:16** *Offline proof:* `bash scripts/offline_check.sh` → all asks OK, ledger flip OK, `PASS: offline_check — binder answers track the ledger with no cloud dependency`.
- **1:34** *Measured:* Peak RSS 1825.61 MB (≪ 5.5 GB self-limit) · Generation TPS 15.9 tok/s · TTFT 11576 ms · T11 100% (28/28). Honest thermal note: 2026-08-06 soak PASS does not reproduce on the 2026-08-10 re-run (peak 89.0 °C) — authoritative P_thermal = official eval machine.
- **1:48** github.com/Vitalisn4/dukabind · English (Path A) · Cameroon MSME offline use-case.

## Honesty notes

- English only (Path A) — deliberately **no** Swahili segment.
- No fake UI: the demo shows the real CLI binder and scripts.
- The measured-numbers segment prints the committed `benchmarks/submission.summary.md` (2026-08-11 freeze re-run) and states the thermal FAIL-on-re-run instead of a green claim.
- Still frames: [`demo/screenshots/`](./screenshots/) (same runs, captioned in this repo's docs).
