"""SQLite connection helpers.

Connections are local-file only; queries must go through the allowlist module.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "duka_a.sqlite"
SCHEMA = Path(__file__).with_name("schema.sql")
SEED = Path(__file__).with_name("seed_demo.sql")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open the ledger with row access by name, foreign keys, and WAL."""
    path = db_path or DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(db_path: Path | None = None, seed: bool = True) -> Path:
    """Create the schema and optionally load synthetic demo rows."""
    path = db_path or DEFAULT_DB
    conn = connect(path)
    try:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        if seed:
            conn.executescript(SEED.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()
    return path


if __name__ == "__main__":
    out = init_db()
    print(f"initialized {out}")
