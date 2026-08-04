"""SQLite connection helpers.

Connections are local-file only; queries must go through the allowlist module.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "marche_akwa.sqlite"
SCHEMA = Path(__file__).with_name("schema.sql")
SEED = Path(__file__).with_name("seed.sql")


def connect(db_path: Path | None = None, *, readonly: bool = False) -> sqlite3.Connection:
    """Open the ledger with row access by name, foreign keys, and WAL.

    Ask paths should use ``readonly=True`` so the binder cannot mutate the file.
    """
    path = db_path or DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    if readonly:
        if not path.exists():
            raise FileNotFoundError(f"database not found: {path}")
        uri = path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if not readonly:
        conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(db_path: Path | None = None, seed: bool = True) -> Path:
    """Create the schema and optionally load shop rows."""
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
