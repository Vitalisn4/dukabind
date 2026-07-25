"""Binder security and correctness tests — no network, no GGUF required."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.binder.allowlist import run_query
from app.binder.pipeline import handle_ask
from app.db.connection import init_db


@pytest.fixture()
def db(tmp_path: Path) -> sqlite3.Connection:
    path = tmp_path / "test.sqlite"
    init_db(path, seed=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_allowlist_rejects_unknown_query(db: sqlite3.Connection) -> None:
    with pytest.raises(ValueError, match="not allowlisted"):
        run_query(db, "drop_customers", {"name": "x"})


def test_credit_amina_three_crates_refuses_over_limit(db: sqlite3.Connection) -> None:
    # 3 * 720 = 2160; 6250 + 2160 = 8410 > 8000
    r = handle_ask(db, "Can I give Amina three crates on credit?")
    assert r.ok is True
    assert "No" in r.message or "Hapana" in r.message
    assert "8410" in r.message or "8,410" in r.message or "exceeds" in r.message.lower() or "inazidi" in r.message
    assert r.citation_rows


def test_credit_pauline_missing_limit_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Can I give Pauline Ngo credit for 1 crate?")
    assert r.ok is False
    assert r.refuse_reason == "credit_limit_null"
    assert "ask the owner" in r.message.lower() or "muulize" in r.message.lower()


def test_supplier_bidco_null_balance_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "How much do we owe Bidco Distributors?")
    assert r.ok is False
    assert r.refuse_reason == "balance_owed_null"
    # Must not invent a shilling figure in the refuse message beyond naming the supplier
    assert "42000" not in r.message


def test_supplier_nest_answers_from_ledger(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "How much do we owe Nest Wholesale?")
    assert r.ok is True
    assert "42000" in r.message
    assert r.citation_rows[0]["balance_owed"] == 42000


def test_stock_soda(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "How many soda crates on hand?")
    assert r.ok is True
    assert "14" in r.message


def test_swahili_credit_path(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Naweza kumpa Amina deni kwa crate 3?")
    assert r.lang == "sw"
    assert r.citation_rows or r.refuse_reason


def test_english_stock_stays_english(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "What stock of soda do we have on hand?")
    assert r.lang == "en"
    assert r.ok is True


def test_credit_named_rice_uses_rice_price(db: sqlite3.Connection) -> None:
    # 1 * 18500 + 6250 = 24750 > 8000
    r = handle_ask(db, "Can I give Amina 1 bag of rice on credit?")
    assert r.ok is True
    assert "18500" in r.message or "24750" in r.message


def test_flip_ledger_changes_answer(db: sqlite3.Connection) -> None:
    before = handle_ask(db, "Can I give Amina 3 crates on credit?")
    assert "No" in before.message or "exceeds" in before.message.lower() or "inazidi" in before.message

    db.execute(
        "UPDATE customers SET credit_limit = ? WHERE display_name = ?",
        (20000, "Amina Wanjiru"),
    )
    db.commit()

    after = handle_ask(db, "Can I give Amina 3 crates on credit?")
    assert "Yes" in after.message or "Ndiyo" in after.message
