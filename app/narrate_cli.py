"""Narrate CLI — binder first, then optional local LLM polish.

Usage:
  PYTHONPATH=. python -m app.narrate_cli "Can I give Amina three crates on credit?"
  PYTHONPATH=. python -m app.narrate_cli --no-llm "How much do we owe Bidco?"
"""

from __future__ import annotations

import argparse
import json
import sys

from app.db.connection import DEFAULT_DB, connect, init_db
from app.llm.ask import ask


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="DukaBind ask (binder + optional llama-server)")
    p.add_argument("question", nargs="+", help="Staff question")
    p.add_argument("--no-llm", action="store_true", help="Binder only (no llama-server)")
    p.add_argument("--base-url", default="http://127.0.0.1:8080")
    args = p.parse_args(argv)

    if not DEFAULT_DB.exists():
        init_db()

    text = " ".join(args.question)
    conn = connect()
    try:
        out = ask(conn, text, use_llm=not args.no_llm, base_url=args.base_url)
    finally:
        conn.close()

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
