"""Tests for the 4 new binder edge cases.

- CREDIT_HEADROOM: How much credit left for Fotso?
- TOTAL_STOCK_VALUE: Total value of all stock?
- TOTAL_DEBT: Total outstanding debt from customers?
- TOTAL_SUPPLIER_PAYABLES: How much do we owe all suppliers?
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.binder.intents import Intent, parse_ask
from app.binder.pipeline import handle_ask, result_with_citation_json
from app.db.connection import init_db


@pytest.fixture()
def db(tmp_path: Path) -> sqlite3.Connection:
    """Fresh seeded Marché Akwa ledger for each test."""
    path = tmp_path / "test.sqlite"
    init_db(path, seed=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# ── Intent detection ──────────────────────────────────────────────


class TestCreditHeadroomIntent:
    """How much credit left for Fotso? maps to CREDIT_HEADROOM intent."""

    def test_intent_english(self) -> None:
        p = parse_ask("How much credit does Fotso have left?")
        assert p.intent == Intent.CREDIT_HEADROOM
        assert p.customer == "Marie-Claire Fotso"

    def test_intent_english_remaining(self) -> None:
        p = parse_ask("What is the remaining credit for Fotso?")
        assert p.intent == Intent.CREDIT_HEADROOM

    def test_intent_english_available(self) -> None:
        p = parse_ask("How much available credit does Fotso have?")
        assert p.intent == Intent.CREDIT_HEADROOM

    def test_intent_french(self) -> None:
        p = parse_ask("Combien de crédit reste pour Fotso?")
        assert p.intent == Intent.CREDIT_HEADROOM

    def test_intent_french_disponible(self) -> None:
        p = parse_ask("Crédit disponible pour Fotso?")
        assert p.intent == Intent.CREDIT_HEADROOM

    def test_intent_swahili(self) -> None:
        p = parse_ask("Kreti inapatikana kwa Fotso?")
        assert p.intent == Intent.CREDIT_HEADROOM


class TestTotalStockValueIntent:
    """Total value of all stock? maps to TOTAL_STOCK_VALUE intent."""

    def test_intent_english(self) -> None:
        p = parse_ask("What is the total value of all stock?")
        assert p.intent == Intent.TOTAL_STOCK_VALUE

    def test_intent_english_inventory(self) -> None:
        p = parse_ask("Total inventory value?")
        assert p.intent == Intent.TOTAL_STOCK_VALUE

    def test_intent_english_worth(self) -> None:
        p = parse_ask("How much is all stock worth?")
        assert p.intent == Intent.TOTAL_STOCK_VALUE

    def test_intent_french(self) -> None:
        p = parse_ask("Quelle est la valeur totale du stock?")
        assert p.intent == Intent.TOTAL_STOCK_VALUE

    def test_intent_swahili(self) -> None:
        p = parse_ask("Thamani ya jumla ya hifadhi?")
        assert p.intent == Intent.TOTAL_STOCK_VALUE


class TestTotalDebtIntent:
    """Total outstanding debt? maps to TOTAL_DEBT intent."""

    def test_intent_english(self) -> None:
        p = parse_ask("What is the total outstanding debt?")
        assert p.intent == Intent.TOTAL_DEBT

    def test_intent_english_customers(self) -> None:
        p = parse_ask("How much do all customers owe?")
        assert p.intent == Intent.TOTAL_DEBT

    def test_intent_english_receivable(self) -> None:
        p = parse_ask("Total receivable from customers?")
        assert p.intent == Intent.TOTAL_DEBT

    def test_intent_french(self) -> None:
        p = parse_ask("Quelle est la dette totale?")
        assert p.intent == Intent.TOTAL_DEBT

    def test_intent_swahili(self) -> None:
        p = parse_ask("Deni la jumla?")
        assert p.intent == Intent.TOTAL_DEBT


class TestTotalSupplierPayablesIntent:
    """How much do we owe all suppliers? maps to TOTAL_SUPPLIER_PAYABLES intent."""

    def test_intent_english(self) -> None:
        p = parse_ask("How much do we owe all suppliers?")
        assert p.intent == Intent.TOTAL_SUPPLIER_PAYABLES

    def test_intent_english_total(self) -> None:
        p = parse_ask("Total supplier payables?")
        assert p.intent == Intent.TOTAL_SUPPLIER_PAYABLES

    def test_intent_english_owed(self) -> None:
        p = parse_ask("Total supplier debt?")
        assert p.intent == Intent.TOTAL_SUPPLIER_PAYABLES

    def test_intent_french(self) -> None:
        p = parse_ask("Combien devons-nous à tous les fournisseurs?")
        assert p.intent == Intent.TOTAL_SUPPLIER_PAYABLES

    def test_intent_swahili(self) -> None:
        p = parse_ask("Jumla ya deni la wasambazaji?")
        assert p.intent == Intent.TOTAL_SUPPLIER_PAYABLES


# ── Binder pipeline (real SQL) ────────────────────────────────────


class TestCreditHeadroomBinder:
    """Credit headroom: limit - outstanding = available."""

    def test_fotso_headroom(self, db: sqlite3.Connection) -> None:
        """Fotso: limit 8000, outstanding 6250 = headroom 1750."""
        r = handle_ask(db, "How much credit does Fotso have left?")
        assert r.ok is True
        assert r.intent == Intent.CREDIT_HEADROOM
        assert "1750" in r.message
        assert "8000" in r.message
        assert "6250" in r.message
        assert r.citation_rows

    def test_njoya_headroom(self, db: sqlite3.Connection) -> None:
        """Njoya: limit 15000, outstanding 2000 = headroom 13000."""
        r = handle_ask(db, "How much credit does Njoya have left?")
        assert r.ok is True
        assert "13000" in r.message

    def test_tchamba_null_limit_refuses(self, db: sqlite3.Connection) -> None:
        """Tchamba: NULL credit_limit must refuse, not invent."""
        r = handle_ask(db, "How much credit does Esther have left?")
        assert r.ok is False
        assert r.refuse_reason == "credit_limit_null"

    def test_unknown_customer_refuses(self, db: sqlite3.Connection) -> None:
        """Unknown customer must refuse."""
        r = handle_ask(db, "How much credit does Unknown Person have left?")
        assert r.ok is False

    def test_french_headroom(self, db: sqlite3.Connection) -> None:
        """French credit headroom."""
        r = handle_ask(db, "Crédit disponible pour Fotso?")
        assert r.ok is True
        assert "1750" in r.message

    def test_swahili_headroom(self, db: sqlite3.Connection) -> None:
        """Swahili credit headroom."""
        r = handle_ask(db, "Kreti inapatikana kwa Fotso?")
        assert r.ok is True
        assert "1750" in r.message

    def test_citation_json_includes_headroom(self, db: sqlite3.Connection) -> None:
        """Citation JSON includes the ledger row."""
        r = handle_ask(db, "How much credit does Fotso have left?")
        payload = result_with_citation_json(r)
        assert payload["ok"] is True
        assert payload["intent"] == "credit_headroom"
        assert payload["citation_json"]
        assert "1750" in r.message


class TestTotalStockValueBinder:
    """Total stock value: sum of (on_hand × unit_price) across all SKUs."""

    def test_total_stock_value(self, db: sqlite3.Connection) -> None:
        """malt: 14×720=10080, riz: 6×18500=111000, huile: 0×4500=0 = total 121080."""
        r = handle_ask(db, "What is the total value of all stock?")
        assert r.ok is True
        assert r.intent == Intent.TOTAL_STOCK_VALUE
        assert "121080" in r.message
        assert "3" in r.message  # 3 products
        assert r.citation_rows

    def test_total_inventory_english(self, db: sqlite3.Connection) -> None:
        """Alternative phrasing."""
        r = handle_ask(db, "Total inventory value?")
        assert r.ok is True
        assert "121080" in r.message

    def test_french_total_stock(self, db: sqlite3.Connection) -> None:
        """French total stock value."""
        r = handle_ask(db, "Valeur totale du stock?")
        assert r.ok is True
        assert "121080" in r.message

    def test_swahili_total_stock(self, db: sqlite3.Connection) -> None:
        """Swahili total stock value."""
        r = handle_ask(db, "Thamani ya jumla ya hifadhi?")
        assert r.ok is True
        assert "121080" in r.message

    def test_citation_json_includes_aggregate(self, db: sqlite3.Connection) -> None:
        """Citation JSON includes the aggregate row."""
        r = handle_ask(db, "What is the total value of all stock?")
        payload = result_with_citation_json(r)
        assert payload["ok"] is True
        assert payload["intent"] == "total_stock_value"
        assert payload["citation_json"]


class TestTotalDebtBinder:
    """Total debt: sum of outstanding across all active customers."""

    def test_total_debt(self, db: sqlite3.Connection) -> None:
        """Fotso 6250 + Njoya 2000 + Tchamba 500 = 8750."""
        r = handle_ask(db, "What is the total outstanding debt?")
        assert r.ok is True
        assert r.intent == Intent.TOTAL_DEBT
        assert "8750" in r.message
        assert "3" in r.message  # 3 active customers
        assert r.citation_rows

    def test_how_much_customers_owe(self, db: sqlite3.Connection) -> None:
        """Alternative phrasing."""
        r = handle_ask(db, "How much do all customers owe?")
        assert r.ok is True
        assert "8750" in r.message

    def test_french_total_debt(self, db: sqlite3.Connection) -> None:
        """French total debt."""
        r = handle_ask(db, "Dette totale?")
        assert r.ok is True
        assert "8750" in r.message

    def test_swahili_total_debt(self, db: sqlite3.Connection) -> None:
        """Swahili total debt."""
        r = handle_ask(db, "Deni la jumla?")
        assert r.ok is True
        assert "8750" in r.message

    def test_citation_json_includes_aggregate(self, db: sqlite3.Connection) -> None:
        """Citation JSON includes the aggregate row."""
        r = handle_ask(db, "What is the total outstanding debt?")
        payload = result_with_citation_json(r)
        assert payload["ok"] is True
        assert payload["intent"] == "total_debt"
        assert payload["citation_json"]


class TestTotalSupplierPayablesBinder:
    """Total supplier payables: sum of balance_owed across all suppliers."""

    def test_total_supplier_payables(self, db: sqlite3.Connection) -> None:
        """SOCA has NULL balance_owed refuses, not silently sum to zero."""
        r = handle_ask(db, "How much do we owe all suppliers?")
        assert r.ok is False
        assert r.refuse_reason is not None

    def test_total_payable_english(self, db: sqlite3.Connection) -> None:
        """Alternative phrasing still refuses on NULL supplier."""
        r = handle_ask(db, "Total supplier payables?")
        assert r.ok is False

    def test_french_total_payables(self, db: sqlite3.Connection) -> None:
        """French total supplier payables refuses on NULL."""
        r = handle_ask(db, "Total fournisseurs?")
        assert r.ok is False

    def test_swahili_total_payables(self, db: sqlite3.Connection) -> None:
        """Swahili total supplier payables refuses on NULL."""
        r = handle_ask(db, "Jumla ya deni la wasambazaji?")
        assert r.ok is False

    def test_citation_json_includes_aggregate(self, db: sqlite3.Connection) -> None:
        """Citation JSON includes the aggregate row."""
        r = handle_ask(db, "How much do we owe all suppliers?")
        payload = result_with_citation_json(r)
        # SOCA has NULL balance_owed, so this refuses
        assert payload["ok"] is False
        assert payload["refuse_reason"] is not None


# ── Edge case: empty database ─────────────────────────────────────


class TestEmptyDatabaseEdgeCases:
    """When the database is empty, aggregate queries must refuse gracefully."""

    @pytest.fixture()
    def db_empty(self, tmp_path: Path) -> sqlite3.Connection:
        """Empty database (no seed data)."""
        path = tmp_path / "empty.sqlite"
        init_db(path, seed=False)
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        yield conn
        conn.close()

    def test_total_stock_value_empty(self, db_empty: sqlite3.Connection) -> None:
        """No products must refuse, not crash."""
        r = handle_ask(db_empty, "What is the total value of all stock?")
        assert r.ok is False

    def test_total_debt_empty(self, db_empty: sqlite3.Connection) -> None:
        """No customers must refuse, not crash."""
        r = handle_ask(db_empty, "What is the total outstanding debt?")
        assert r.ok is False

    def test_total_supplier_payables_empty(self, db_empty: sqlite3.Connection) -> None:
        """No suppliers must refuse, not crash."""
        r = handle_ask(db_empty, "How much do we owe all suppliers?")
        assert r.ok is False


# ── Cross-shop (duka_b) ──────────────────────────────────────────


class TestDukaBCrossShop:
    """Verify new intents work on the second fixture (duka_b)."""

    @pytest.fixture()
    def db_b(self, tmp_path: Path) -> sqlite3.Connection:
        """Fresh seeded Duka B (Nkolmébé) ledger."""
        from app.db.connection import SEED_DUKA_B, init_db

        path = tmp_path / "duka_b.sqlite"
        init_db(path, seed=True, seed_file=SEED_DUKA_B)
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        yield conn
        conn.close()

    def test_duka_b_total_stock_value(self, db_b: sqlite3.Connection) -> None:
        """Duka B total stock value."""
        r = handle_ask(db_b, "What is the total value of all stock?")
        assert r.ok is True
        assert r.intent == Intent.TOTAL_STOCK_VALUE
        assert r.citation_rows

    def test_duka_b_total_debt(self, db_b: sqlite3.Connection) -> None:
        """Duka B total customer debt."""
        r = handle_ask(db_b, "How much do all customers owe?")
        assert r.ok is True
        assert r.intent == Intent.TOTAL_DEBT

    def test_duka_b_total_supplier_payables(self, db_b: sqlite3.Connection) -> None:
        """Duka B: Ciment du Cameroun has NULL balance_owed refuses."""
        r = handle_ask(db_b, "Total supplier payables?")
        assert r.ok is False
        assert r.refuse_reason is not None

    def test_duka_b_credit_headroom(self, db_b: sqlite3.Connection) -> None:
        """Duka B credit headroom for Amina."""
        r = handle_ask(db_b, "How much credit does Amina have left?")
        assert r.ok is True
        assert r.intent == Intent.CREDIT_HEADROOM
        assert r.citation_rows
