"""Offline held-out evaluation for the binder (no model, no network).

Runs every prompt in ``evals/heldout/prompts.json`` against the ledger fixture
it names, adds cross-shop anti-memorization checks, and proves answers track a
live ledger flip on both shops. Exits 1 if any expectation fails.

Usage (from repo root):
    PYTHONPATH=. .venv/bin/python evals/run_heldout.py
    PYTHONPATH=. .venv/bin/python evals/run_heldout.py --write-report  # also writes evals/heldout/REPORT.md

The ``--write-report`` flag regenerates the committed evidence report
(``evals/heldout/REPORT.md``) from the measured run — numbers are always
recomputed, never hand-edited.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.binder.pipeline import handle_ask
from app.binder.refuse import BinderResult
from app.db.connection import SEED, SEED_DUKA_B, init_db

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_FILE = ROOT / "evals" / "heldout" / "prompts.json"
REPORT_FILE = ROOT / "evals" / "heldout" / "REPORT.md"

FIXTURE_SEEDS = {
    "marche_akwa": SEED,
    "duka_b": SEED_DUKA_B,
}

# (fixture, prompt, SQL flip, expected token in the flipped answer)
FLIP_CHECKS = [
    (
        "marche_akwa",
        "Can I give Marie-Claire three crates on credit?",
        (
            "UPDATE customers SET credit_limit = 20000 "
            "WHERE display_name = 'Marie-Claire Fotso'"
        ),
        "Yes",
    ),
    (
        "marche_akwa",
        "How many soda crates on hand?",
        "UPDATE skus SET on_hand = 30 WHERE name = 'Caisse boisson malt 300ml'",
        "on_hand=30",
    ),
    (
        "duka_b",
        "Can I give Amina Bello two bags of sugar on credit?",
        "UPDATE customers SET credit_limit = 50000 WHERE display_name = 'Amina Bello'",
        "Yes",
    ),
]


def _check(expect: dict[str, Any], result: BinderResult) -> list[str]:
    """Return unmet expectations for one prompt as human-readable strings."""
    problems: list[str] = []
    if "intent" in expect and result.intent.value != expect["intent"]:
        problems.append(f"intent {result.intent.value!r} != {expect['intent']!r}")
    if "ok" in expect and result.ok != expect["ok"]:
        problems.append(f"ok={result.ok} != {expect['ok']}")
    if "approved" in expect and result.approved != expect["approved"]:
        problems.append(f"approved={result.approved} != {expect['approved']}")
    if "refuse_reason" in expect and result.refuse_reason != expect["refuse_reason"]:
        problems.append(
            f"refuse_reason={result.refuse_reason!r} != {expect['refuse_reason']!r}"
        )
    for token in expect.get("message_contains", []):
        if token not in result.message:
            problems.append(f"message lacks {token!r}: {result.message!r}")
    for token in expect.get("message_excludes", []):
        if token in result.message:
            problems.append(f"message must not contain {token!r}: {result.message!r}")
    return problems


def run_heldout_detailed() -> tuple[int, int, int, list[str], dict[str, Any]]:
    """Run the full held-out suite and return per-prompt detail records.

    Returns ``(n_prompts, prompt_failures, flip_failures, report_lines,
    details)``. ``details`` holds ``{"prompts": [...], "flips": [...]}`` used
    by the markdown report writer; callers that only need the counters should
    use ``run_heldout()`` instead.
    """
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    prompts = data["prompts"]
    lines: list[str] = []
    prompt_failures = 0
    flip_failures = 0
    prompt_details: list[dict[str, Any]] = []
    flip_details: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as tmp:
        conns: dict[str, sqlite3.Connection] = {}
        for name, seed_file in FIXTURE_SEEDS.items():
            path = Path(tmp) / f"{name}.sqlite"
            init_db(path, seed=True, seed_file=seed_file)
            conns[name] = sqlite3.connect(str(path))
            conns[name].row_factory = sqlite3.Row

        for p in prompts:
            result = handle_ask(conns[p["fixture"]], p["prompt"])
            problems = _check(p["expect"], result)
            if problems:
                prompt_failures += 1
            tag = "PASS" if not problems else "FAIL"
            lines.append(
                f"[{tag}] {p['id']:7s} {p['fixture']:11s} {p['category']:12s} "
                f"{p['prompt']}"
            )
            for prob in problems:
                lines.append(f"       expected: {prob}")
            lines.append(f"       binder: {result.message}")
            prompt_details.append(
                {
                    "id": p["id"],
                    "fixture": p["fixture"],
                    "category": p["category"],
                    "prompt": p["prompt"],
                    "ok": not problems,
                    "problems": problems,
                    "message": result.message,
                }
            )

        for fixture, prompt, sql, token in FLIP_CHECKS:
            conn = conns[fixture]
            before = handle_ask(conn, prompt)
            conn.execute(sql)
            after = handle_ask(conn, prompt)
            conn.rollback()
            flipped = before.message != after.message and token in after.message
            if not flipped:
                flip_failures += 1
                lines.append(
                    f"[FAIL] flip {fixture}: answer did not track ledger change "
                    f"({before.message!r} -> {after.message!r})"
                )
            else:
                lines.append(
                    f"[PASS] flip {fixture}: answer tracks ledger change "
                    f"({token!r} now in message)"
                )
            flip_details.append(
                {
                    "fixture": fixture,
                    "ok": flipped,
                    "token": token,
                    "before": before.message,
                    "after": after.message,
                }
            )

        for conn in conns.values():
            conn.close()

    return (
        len(prompts),
        prompt_failures,
        flip_failures,
        lines,
        {"prompts": prompt_details, "flips": flip_details},
    )


def run_heldout() -> tuple[int, int, int, list[str]]:
    """Run the full held-out suite.

    Returns ``(n_prompts, prompt_failures, flip_failures, report_lines)`` so
    callers can score T11 (bind/refuse accuracy) separately from the flip
    proofs (answers tracking ledger changes).
    """
    n_prompts, prompt_fail, flip_fail, lines, _ = run_heldout_detailed()
    return n_prompts, prompt_fail, flip_fail, lines


def _summary_table(details: dict[str, Any]) -> list[list[Any]]:
    """Per-category and per-fixture pass tables for the markdown report."""
    prompts = details["prompts"]
    categories: dict[str, list[bool]] = {}
    fixtures: dict[str, list[bool]] = {}
    for p in prompts:
        categories.setdefault(p["category"], []).append(p["ok"])
        fixtures.setdefault(p["fixture"], []).append(p["ok"])
    rows: list[list[Any]] = []
    for name in sorted(categories):
        ok = sum(categories[name])
        rows.append([name, f"{ok}/{len(categories[name])}"])
    rows.append(
        ["**All prompts**", f"{sum(1 for p in prompts if p['ok'])}/{len(prompts)}"]
    )
    rows.append(["", ""])
    for name in sorted(fixtures):
        ok = sum(fixtures[name])
        rows.append([f"fixture: {name}", f"{ok}/{len(fixtures[name])}"])
    return rows


def _write_report_text(
    n_prompts: int, prompt_fail: int, flip_fail: int, details: dict[str, Any]
) -> str:
    """Build the markdown report text from one measured run (no re-run)."""
    correct = n_prompts - prompt_fail
    t11 = 100.0 * correct / n_prompts if n_prompts else 0.0
    cross_shop = [p for p in details["prompts"] if p["category"] == "cross_shop"]
    cross_ok = sum(1 for p in cross_shop if p["ok"])

    rows = _summary_table(details)
    width = max(len(str(r[0])) for r in rows)
    body = "\n".join(f"| {str(r[0]).ljust(width)} | {r[1]} |" for r in rows)

    flip_lines = "\n".join(
        f"- `{f['fixture']}` — {'PASS' if f['ok'] else 'FAIL'} "
        f"(token `{f['token']}` in the flipped answer)"
        for f in details["flips"]
    )

    generated = datetime.now(timezone.utc).date().isoformat()
    return f"""# Held-out evaluation report — DukaBind

**Generated:** {generated} by `evals/run_heldout.py --write-report` (measured run — numbers recomputed, never hand-edited)  
**Set:** `evals/heldout/prompts.json` — frozen 2026-08-06, English only  
**Command:** `PYTHONPATH=. .venv/bin/python evals/run_heldout.py`  
**Fixtures:** Marché Akwa Viviane (`marche_akwa`) and Marché Nkolmébé (`duka_b`) — two disjoint ledgers

## Summary

| Metric | Result |
|---|---|
| T11 held-out bind/refuse | {correct}/{n_prompts} (**{t11:.1f}%**) — target ≥ 90 % |
| Ledger-flip proofs | {len(details["flips"]) - flip_fail}/{len(details["flips"])} |
| Total checks | {n_prompts + len(details["flips"])}, **{prompt_fail + flip_fail} failures** |

## Per category / fixture

{body}

## Cross-shop non-leak

{cross_ok}/{len(cross_shop)} cross-shop prompts passed — entities of one shop
asked against the other ledger refuse with `not_found` and never leak the other
shop's numbers (no memorization between fixtures).

## Ledger flips (answers track ledger rows)

{flip_lines}

## T13 — submission prompts stay disjoint

The 2 submission prompts in `metadata.json` are chosen from a pool **disjoint**
from this held-out set (T13). `tests/test_metadata.py` fails CI if any staff
ask string overlaps this file, so the submission prompts cannot drift into the
held-out set without breaking the build.

---

*Full per-prompt output:* `PYTHONPATH=. .venv/bin/python evals/run_heldout.py`
"""


def write_report(path: Path = REPORT_FILE) -> None:
    """Regenerate the committed held-out evidence report from a measured run."""
    n_prompts, prompt_fail, flip_fail, _, details = run_heldout_detailed()
    path.write_text(
        _write_report_text(n_prompts, prompt_fail, flip_fail, details),
        encoding="utf-8",
    )
    try:
        shown = path.relative_to(ROOT)
    except ValueError:
        shown = path
    print(f"wrote held-out report -> {shown}")


def _console_lines(
    n_prompts: int, prompt_fail: int, flip_fail: int, lines: list[str]
) -> list[str]:
    """Build the console report lines for a measured run."""
    correct = n_prompts - prompt_fail
    t11 = 100.0 * correct / n_prompts if n_prompts else 0.0
    return [
        "== DukaBind held-out eval (offline, binder only) ==",
        *lines,
        "",
        (
            f"T11 held-out bind/refuse: {correct}/{n_prompts} prompts correct "
            f"({t11:.1f}%) — target ≥90%"
        ),
        f"ledger-flip proofs: {len(FLIP_CHECKS) - flip_fail}/{len(FLIP_CHECKS)}",
        (
            f"total: {n_prompts + len(FLIP_CHECKS)} checks, "
            f"{prompt_fail + flip_fail} failures"
        ),
    ]


def main() -> int:
    """Print the report (incl. T11 score) and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--write-report",
        nargs="?",
        const=str(REPORT_FILE),
        default=None,
        metavar="PATH",
        help="regenerate the committed held-out evidence report (default: "
        "evals/heldout/REPORT.md)",
    )
    args = parser.parse_args()

    # One measured run serves both the written report and the console output,
    # so the committed artifact can never disagree with the printed numbers.
    n_prompts, prompt_fail, flip_fail, lines, details = run_heldout_detailed()
    if args.write_report:
        path = Path(args.write_report)
        path.write_text(
            _write_report_text(n_prompts, prompt_fail, flip_fail, details),
            encoding="utf-8",
        )
        try:
            shown = path.relative_to(ROOT)
        except ValueError:
            shown = path
        print(f"wrote held-out report -> {shown}")

    for line in _console_lines(n_prompts, prompt_fail, flip_fail, lines):
        print(line)
    return 1 if (prompt_fail + flip_fail) else 0


if __name__ == "__main__":
    raise SystemExit(main())
