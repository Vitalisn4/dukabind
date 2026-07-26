"""Tests for ask() path without requiring llama-server."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db.connection import init_db
from app.llm.ask import ask
from app.llm.client import LlamaServerError, assert_loopback_http


@pytest.fixture()
def db(tmp_path: Path) -> sqlite3.Connection:
    path = tmp_path / "test.sqlite"
    init_db(path, seed=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_ask_refuse_skips_llm(db: sqlite3.Connection) -> None:
    out = ask(db, "How much do we owe Bidco Distributors?", use_llm=True)
    assert out["ok"] is False
    assert out["refuse_reason"] == "balance_owed_null"
    assert out["narrated"] is False
    assert out["narration"] is None
    assert out["source"] == "binder"


def test_ask_binder_only_credit(db: sqlite3.Connection) -> None:
    out = ask(db, "Can I give Amina three crates on credit?", use_llm=False)
    assert out["ok"] is True
    assert "8410" in out["message"]
    assert "No" in out["message"]
    assert out["narrated"] is False
    assert out["narration"] is None


def test_loopback_url_rejects_remote() -> None:
    with pytest.raises(LlamaServerError):
        assert_loopback_http("https://example.com")
    with pytest.raises(LlamaServerError):
        assert_loopback_http("http://192.168.1.10:8080")
    assert_loopback_http("http://127.0.0.1:8080")
