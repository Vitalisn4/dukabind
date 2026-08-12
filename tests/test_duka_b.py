"""Second-fixture tests: generalization, refusal, and anti-memorization.

``duka_b`` (Marché Nkolmébé, Yaoundé) uses names/balances/stock disjoint from
Marché Akwa Viviane. Passing these proves answers bind to the live ledger
instead of memorized rows from the first shop.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.binder.pipeline import handle_ask
from app.db.connection import SEED_DUKA_B, init_db


@pytest.fixture()
def db_b(tmp_path: Path) -> sqlite3.Connection:
    path = tmp_path / "duka_b.sqlite"
    init_db(path, seed=True, seed_file=SEED_DUKA_B)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture()
def db_a(tmp_path: Path) -> sqlite3.Connection:
    path = tmp_path / "marche_akwa.sqlite"
    init_db(path, seed=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_duka_b_seed_loads(db_b: sqlite3.Connection) -> None:
    row = db_b.execute(
        "SELECT value FROM shop_meta WHERE key = 'fixture_id'"
    ).fetchone()
    assert row["value"] == "duka_b"


def test_duka_b_credit_over_limit(db_b: sqlite3.Connection) -> None:
    # 2 * 13500 = 27000; 9800 + 27000 = 36800 > 25000
    r = handle_ask(db_b, "Can I give Amina Bello two bags of sugar on credit?")
    assert r.ok is True
    assert r.approved is False
    assert "36800" in r.message


def test_duka_b_credit_within_limit(db_b: sqlite3.Connection) -> None:
    # 1 * 13500 = 13500; 9800 + 13500 = 23300 <= 25000
    r = handle_ask(db_b, "Can I give Amina Bello one bag of sugar on credit?")
    assert r.ok is True
    assert r.approved is True
    assert "23300" in r.message


def test_duka_b_credit_null_limit_refuses(db_b: sqlite3.Connection) -> None:
    r = handle_ask(db_b, "Can I give Maman Rachel credit for a box of soap?")
    assert r.ok is False
    assert r.refuse_reason == "credit_limit_null"
    assert "ask the owner" in r.message.lower()


def test_duka_b_supplier_amount(db_b: sqlite3.Connection) -> None:
    r = handle_ask(db_b, "How much do we owe Sanaga Épicerie?")
    assert r.ok is True
    assert "15500" in r.message


def test_duka_b_supplier_accent_insensitive(db_b: sqlite3.Connection) -> None:
    """ASCII typing without accents still routes to the accented display name."""
    r = handle_ask(db_b, "How much do we owe Sanaga Epicerie?")
    assert r.ok is True
    assert "15500" in r.message
    assert r.citation_rows[0]["display_name"] == "Sanaga Épicerie"


def test_duka_b_supplier_null_balance_refuses(db_b: sqlite3.Connection) -> None:
    r = handle_ask(db_b, "What do we owe Ciment du Cameroun?")
    assert r.ok is False
    assert r.refuse_reason == "balance_owed_null"
    assert "15500" not in r.message


def test_duka_b_stock(db_b: sqlite3.Connection) -> None:
    r = handle_ask(db_b, "How much sugar stock do we have on hand?")
    assert r.ok is True
    assert "on_hand=4" in r.message


def test_cross_shop_duka_b_data_never_leaks_into_marche(
    db_a: sqlite3.Connection,
) -> None:
    r = handle_ask(db_a, "How much do we owe Sanaga Épicerie?")
    assert r.ok is False
    assert r.refuse_reason == "not_found"
    assert "15500" not in r.message

    r = handle_ask(db_a, "Can I give Amina Bello two bags of sugar on credit?")
    assert r.ok is False
    assert r.refuse_reason == "not_found"
    assert "36800" not in r.message


def test_cross_shop_marche_data_never_leaks_into_duka_b(
    db_b: sqlite3.Connection,
) -> None:
    r = handle_ask(db_b, "Can I give Marie-Claire two crates on credit?")
    assert r.ok is False
    assert r.refuse_reason == "not_found"
    assert "8410" not in r.message


def test_duka_b_flip_changes_answer(db_b: sqlite3.Connection) -> None:
    before = handle_ask(db_b, "Can I give Amina Bello two bags of sugar on credit?")
    assert before.approved is False

    db_b.execute(
        "UPDATE customers SET credit_limit = 50000 WHERE display_name = 'Amina Bello'"
    )
    db_b.commit()

    after = handle_ask(db_b, "Can I give Amina Bello two bags of sugar on credit?")
    assert after.approved is True
    assert after.message != before.message


def test_heldout_suite_passes() -> None:
    """The full offline held-out eval must stay green under pytest."""
    from evals.run_heldout import run_heldout

    n_prompts, prompt_fail, flip_fail, _ = run_heldout()
    assert prompt_fail == 0
    assert flip_fail == 0
    assert n_prompts >= 20  # minimum size of the held-out set
