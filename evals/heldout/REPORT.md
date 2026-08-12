# Held-out evaluation report: DukaBind

**Generated:** 2026-08-12 by `evals/run_heldout.py --write-report` (measured run; numbers recomputed, never hand-edited)  
**Set:** `evals/heldout/prompts.json`, frozen 2026-08-12, English + French + Swahili  
**Command:** `PYTHONPATH=. .venv/bin/python evals/run_heldout.py`  
**Fixtures:** Marché Akwa Viviane (`marche_akwa`) and Marché Nkolmébé (`duka_b`), two disjoint ledgers

## Summary

| Metric | Result |
|---|---|
| T11 held-out bind/refuse | 37/37 (**100.0%**); target ≥ 90 % |
| Ledger-flip proofs | 3/3 |
| Total checks | 40, **0 failures** |

## Per category / fixture

| adversarial          | 5/5 |
| credit               | 11/11 |
| cross_shop           | 4/4 |
| refuse               | 6/6 |
| stock                | 8/8 |
| supplier             | 3/3 |
| **All prompts**      | 37/37 |
|                      |  |
| fixture: duka_b      | 11/11 |
| fixture: marche_akwa | 26/26 |

## Cross-shop non-leak

4/4 cross-shop prompts passed; entities of one shop
asked against the other ledger refuse with `not_found` and never leak the other
shop's numbers (no memorization between fixtures).

## Ledger flips (answers track ledger rows)

- `marche_akwa`: PASS (token `Yes` in the flipped answer)
- `marche_akwa`: PASS (token `on_hand=30` in the flipped answer)
- `duka_b`: PASS (token `Yes` in the flipped answer)

## T13: submission prompts stay disjoint

The 2 submission prompts in `metadata.json` are chosen from a pool **disjoint**
from this held-out set (T13). `tests/test_metadata.py` fails CI if any staff
ask string overlaps this file, so the submission prompts cannot drift into the
held-out set without breaking the build.

---

*Full per-prompt output:* `PYTHONPATH=. .venv/bin/python evals/run_heldout.py`
