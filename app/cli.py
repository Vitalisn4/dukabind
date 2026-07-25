"""Interactive CLI so you can exercise the binder without a UI or LLM.

Usage:
  PYTHONPATH=. python -m app.cli "Can I give Amina three crates on credit?"
  PYTHONPATH=. python -m app.cli   # then type questions; empty line to quit
"""

from __future__ import annotations

import json
import sys

from app.binder.pipeline import handle_ask, result_with_citation_json
from app.db.connection import DEFAULT_DB, connect, init_db


def _ensure_db() -> None:
    if not DEFAULT_DB.exists():
        init_db()


def run_one(text: str) -> None:
    conn = connect()
    try:
        result = handle_ask(conn, text)
        payload = result_with_citation_json(result)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    _ensure_db()
    if len(argv) > 1:
        run_one(" ".join(argv[1:]))
        return 0

    print("DukaBind binder CLI (no LLM). Empty line to exit.")
    print(f"Ledger: {DEFAULT_DB}")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            break
        run_one(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
