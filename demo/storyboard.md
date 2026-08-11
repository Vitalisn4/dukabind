# Demo video storyboard — DukaBind (M6 freeze)

**Path A (locked):** English only · no Swahili segment · Cameroon MSME offline use-case.
**Length:** ≤ 120 seconds · **Captions:** burned in (judges may watch muted).
**Asset:** [`demo/demo.mp4`](./demo.mp4) (114 s, H.264, 1280×720) rendered from **real CLI output**
by [`scripts/render_demo_assets.py`](../scripts/render_demo_assets.py) — every line of text on
screen is produced by actually running the binder / offline proof / profiler on this machine.

Frame the video as a concise pitch that contains proof — not a narrated screen recording.
Each segment establishes one claim.

| # | Time | Shot (what is on screen) | Caption (burned in) | Claim established |
|---|---|---|---|---|
| 1 | 0:00–0:06 | Title card: DukaBind — offline ledger binder · ADTC 2026 · Corporate/Enterprise · llama.cpp + GGUF · Qwen2.5-1.5B Q4_K_M | An offline shop assistant that cannot invent your money. | Positioning: fail-closed ledger binder, not a chatbot |
| 2 | 0:06–0:32 | Terminal: `python -m app.cli "Can I give Marie-Claire three crates on credit?"` → JSON answer: `No — 3×720=2160; 6250+2160=8410 exceeds limit 8000 by 410 XAF. Max qty within limit: 2.` with the citation block | It does not recall the shop's numbers — it reads the ledger and shows which rows it used. | The bind: answer = f(rows); arithmetic shown; citation visible |
| 3 | 0:32–0:56 | Terminal: `UPDATE customers SET credit_limit = 20000 …` then the **same question** → `Yes — projected outstanding 8410 ≤ limit 20000 XAF` | Change one ledger row → the same question gives a new answer. That is binding, not recall. | Single continuous proof: ledger flip (mutate → answer changes) |
| 4 | 0:56–1:16 | Terminal: `How much do we owe SOCA Distribution Douala?` → `refuse_reason: balance_owed_null` — "not on file — ask the owner". `Can I give Esther credit for 1 crate?` → `credit_limit_null` | Data missing? It says so and names the field. It will never invent a balance. | Fail-closed refusal (matches submission prompt `tp_001`) |
| 5 | 1:16–1:34 | Terminal: `bash scripts/offline_check.sh` → all asks OK + ledger flip OK + `PASS: offline_check — no cloud dependency` | Offline is not a mode — it is the operating assumption. | Airplane/offline proof (unshare note shown honestly) |
| 6 | 1:34–1:48 | Terminal: `benchmarks/submission.summary.md` — Peak RSS 1825.61 MB · TPS 15.9 tok/s · TTFT 11576 ms | Measured: peak RSS ≪ 5.5 GB limit · TPS above the 15 target · T11 100% (28/28). Thermal honesty: the 2026-08-06 PASS does not reproduce on 2026-08-10 re-run — authoritative P_thermal = eval machine. | Measured numbers + honesty about the thermal flag |
| 7 | 1:48–1:54 | Outro card: repo URL · English (Path A) · Cameroon MSME offline use-case | github.com/Vitalisn4/dukabind · English (Path A) · Cameroon MSME offline use-case | Credibility + honest claim boundary |

## Production notes

- **No fake UI, no Swahili, no invented numbers.** Every on-screen value comes from a real run
  on 2026-08-11 (see `demo/screenshots/` — same renderer, same runs).
- Segment 3 is the load-bearing shot: one row edited, same question, new answer.
- Raw terminal stills: [`demo/screenshots/`](./screenshots/) (numbered, captioned).
- Rendering is reproducible: `source .venv/bin/activate && PYTHONPATH=. python scripts/render_demo_assets.py`.
