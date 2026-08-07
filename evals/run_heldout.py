"""Offline held-out evaluation for the binder (no model, no network).

Runs every prompt in ``evals/heldout/prompts.json`` against the ledger fixture
it names, adds cross-shop anti-memorization checks, and proves answers track a
live ledger flip on both shops. Exits 1 if any expectation fails.

Usage (from repo root):
    PYTHONPATH=. .venv/bin/python evals/run_heldout.py
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from app.binder.pipeline import handle_ask
from app.binder.refuse import BinderResult
from app.db.connection import SEED, SEED_DUKA_B, init_db

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_FILE = ROOT / "evals" / "heldout" / "prompts.json"

FIXTURE_SEEDS = {
    "marche_akwa": SEED,
    "duka_b": SEED_DUKA_B,
}

# (fixture, prompt, SQL flip, expected token in the flipped answer)
FLIP_CHECKS = [
    (
        "marche_akwa",
        "Can I give Marie-Claire three crates on credit?",
        ("UPDATE customers SET credit_limit = 20000 "
         "WHERE display_name = 'Marie-Claire Fotso'"),
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


def run_heldout() -> tuple[int, int, int, list[str]]:
    """Run the full held-out suite.

    Returns ``(n_prompts, prompt_failures, flip_failures, report_lines)`` so
    callers can score T11 (bind/refuse accuracy) separately from the flip
    proofs (answers tracking ledger changes).
    """
    data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    prompts = data["prompts"]
    lines: list[str] = []
    prompt_failures = 0
    flip_failures = 0

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

        for fixture, prompt, sql, token in FLIP_CHECKS:
            conn = conns[fixture]
            before = handle_ask(conn, prompt)
            conn.execute(sql)
            after = handle_ask(conn, prompt)
            conn.rollback()
            if before.message == after.message or token not in after.message:
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

        for conn in conns.values():
            conn.close()

    return len(prompts), prompt_failures, flip_failures, lines


def main() -> int:
    """Print the report (incl. T11 score) and return a process exit code."""
    n_prompts, prompt_fail, flip_fail, lines = run_heldout()
    correct = n_prompts - prompt_fail
    t11 = 100.0 * correct / n_prompts if n_prompts else 0.0
    print("== DukaBind held-out eval (offline, binder only) ==")
    for line in lines:
        print(line)
    print(f"\nT11 held-out bind/refuse: {correct}/{n_prompts} prompts correct "
          f"({t11:.1f}%) — target ≥90%")
    print(f"ledger-flip proofs: {len(FLIP_CHECKS) - flip_fail}/{len(FLIP_CHECKS)}")
    print(f"total: {n_prompts + len(FLIP_CHECKS)} checks, "
          f"{prompt_fail + flip_fail} failures")
    return 1 if (prompt_fail + flip_fail) else 0


if __name__ == "__main__":
    raise SystemExit(main())
