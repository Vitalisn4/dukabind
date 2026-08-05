"""Binder security and correctness tests — no network, no GGUF required."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.binder.allowlist import run_query
from app.binder.pipeline import handle_ask, result_with_citation_json
from app.db.connection import connect, init_db
from app.db.fixture import KNOWN_SKUS


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


def test_allowlist_rejects_missing_params(db: sqlite3.Connection) -> None:
    with pytest.raises(ValueError, match="missing params"):
        run_query(db, "customer_credit", {})


def test_credit_fotso_three_crates_refuses_over_limit(db: sqlite3.Connection) -> None:
    # 3 * 720 = 2160; 6250 + 2160 = 8410 > 8000
    r = handle_ask(db, "Can I give Marie-Claire three crates on credit?")
    assert r.ok is True
    assert r.approved is False
    assert "No" in r.message
    assert "8410" in r.message
    assert r.citation_rows

    payload = result_with_citation_json(r)
    assert payload["ok"] is True
    assert payload["approved"] is False


def test_credit_tchamba_missing_limit_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Can I give Esther Tchamba credit for 1 crate?")
    assert r.ok is False
    assert r.approved is None
    assert r.refuse_reason == "credit_limit_null"
    assert "ask the owner" in r.message.lower()


def test_supplier_soca_null_balance_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "How much do we owe SOCA Distribution Douala?")
    assert r.ok is False
    assert r.refuse_reason == "balance_owed_null"
    # 42000 is Bonaberi's balance; leaking it here would be a hallucination.
    assert "42000" not in r.message


def test_supplier_bonaberi_answers_from_ledger(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "How much do we owe Grosserie Portuaire Bonaberi?")
    assert r.ok is True
    assert "42000" in r.message
    assert r.citation_rows[0]["balance_owed"] == 42000


def test_stock_soda(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "How many soda crates on hand?")
    assert r.ok is True
    assert "14" in r.message


def test_english_stock_stays_english(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "What stock of soda do we have on hand?")
    assert r.lang == "en"
    assert r.ok is True


def test_swahili_ask_is_unknown_without_english_cues(db: sqlite3.Connection) -> None:
    """Path A: no Swahili lexicon — pure SW asks do not route to credit."""
    r = handle_ask(db, "Naweza kumpa Fotso deni kwa crate 3?")
    assert r.lang == "en"
    assert r.ok is False
    assert r.refuse_reason == "unknown_intent"

def test_sku_alias_not_substring_of_unrelated_word() -> None:
    from app.binder.intents import _extract_known_name

    assert _extract_known_name("the price is high", KNOWN_SKUS) is None
    assert _extract_known_name("do not spoil the oil", KNOWN_SKUS) == "oil"
    assert _extract_known_name("one bag of rice please", KNOWN_SKUS) == "rice"


def test_overlong_ask_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "x" * 501)
    assert r.ok is False
    assert r.refuse_reason == "unknown_intent"


def test_zero_qty_credit_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Can I give Fotso 0 crates on credit?")
    assert r.ok is False
    assert r.refuse_reason == "not_found"


def test_credit_named_rice_uses_rice_price(db: sqlite3.Connection) -> None:
    # 1 * 18500 + 6250 = 24750 > 8000
    r = handle_ask(db, "Can I give Marie Claire 1 bag of rice on credit?")
    assert r.ok is True
    assert "18500" in r.message or "24750" in r.message


def test_flip_ledger_changes_answer(db: sqlite3.Connection) -> None:
    before = handle_ask(db, "Can I give Fotso 3 crates on credit?")
    assert "No" in before.message
    assert before.approved is False

    db.execute(
        "UPDATE customers SET credit_limit = ? WHERE display_name = ?",
        (20000, "Marie-Claire Fotso"),
    )
    db.commit()

    after = handle_ask(db, "Can I give Fotso 3 crates on credit?")
    assert "Yes" in after.message
    assert after.approved is True


def test_readonly_missing_nested_path_does_not_mkdir(tmp_path: Path) -> None:
    missing = tmp_path / "nested" / "missing" / "ledger.sqlite"
    with pytest.raises(FileNotFoundError, match="database not found"):
        connect(missing, readonly=True)
    assert not (tmp_path / "nested").exists()
