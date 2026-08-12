"""French and Swahili binder-track tests (no network, no GGUF required).

French is an official Cameroon language; Swahili is a pan-African language.
Both bind to the same allowlisted queries and localized fail-closed messages,
and narration prompts are localized (verified on Qwen2.5-1.5B Q4_K_M).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.binder.intents import detect_lang, parse_ask
from app.binder.pipeline import handle_ask
from app.db.connection import SEED_DUKA_B, init_db


@pytest.fixture()
def db(tmp_path: Path) -> sqlite3.Connection:
    path = tmp_path / "test.sqlite"
    init_db(path, seed=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture()
def db_b(tmp_path: Path) -> sqlite3.Connection:
    path = tmp_path / "duka_b.sqlite"
    init_db(path, seed=True, seed_file=SEED_DUKA_B)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# --- language detection -----------------------------------------------------


def test_detect_lang_english_default() -> None:
    assert detect_lang("How much do we owe SOCA?") == "en"
    assert detect_lang("Can I give Marie-Claire three crates on credit?") == "en"
    assert detect_lang("random gibberish qwerty") == "en"


def test_detect_lang_french() -> None:
    assert (
        detect_lang("Puis-je donner trois caisses de crédit à Marie-Claire ?") == "fr"
    )
    assert detect_lang("Combien devons-nous à SOCA ?") == "fr"


def test_detect_lang_swahili() -> None:
    assert (
        detect_lang("Je, ninaweza kumpa Marie-Claire kreti ya makreti matatu?") == "sw"
    )
    assert detect_lang("Tunadaiwa kiasi gani na SOCA?") == "sw"


# --- French pipeline --------------------------------------------------------


def test_french_credit_over_limit(db: sqlite3.Connection) -> None:
    # 3 × 720 = 2160; 6250 + 2160 = 8410 > 8000
    r = handle_ask(db, "Puis-je donner trois caisses de crédit à Marie-Claire ?")
    assert r.ok is True
    assert r.approved is False
    assert r.lang == "fr"
    assert "8410" in r.message
    assert "dépasse" in r.message
    assert "Quantité maximale" in r.message


def test_french_credit_within_limit(db: sqlite3.Connection) -> None:
    # 1 × 720 = 720; 6250 + 720 = 6970 <= 8000
    r = handle_ask(db, "Peut-on accorder une caisse de crédit à Fotso ?")
    assert r.ok is True
    assert r.approved is True
    assert r.lang == "fr"
    assert "6970" in r.message
    assert "Oui" in r.message


def test_french_supplier_balance(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Combien devons-nous à Bonaberi ?")
    assert r.ok is True
    assert r.lang == "fr"
    assert "42000" in r.message
    assert "Montant dû" in r.message


def test_french_supplier_null_balance_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Combien devons-nous à SOCA Distribution Douala ?")
    assert r.ok is False
    assert r.refuse_reason == "balance_owed_null"
    assert r.lang == "fr"
    assert "n'est pas enregistré" in r.message
    assert "42000" not in r.message


def test_french_stock(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Combien de soda avons-nous en stock ?")
    assert r.ok is True
    assert r.lang == "fr"
    assert "en stock=14" in r.message


def test_french_null_limit_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Puis-je donner une caisse de crédit à Esther Tchamba ?")
    assert r.ok is False
    assert r.refuse_reason == "credit_limit_null"
    assert r.lang == "fr"
    assert "Pas de limite de crédit" in r.message


# --- Swahili pipeline -------------------------------------------------------


def test_swahili_credit_over_limit(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Je, ninaweza kumpa Marie-Claire kreti ya makreti matatu?")
    assert r.ok is True
    assert r.approved is False
    assert r.lang == "sw"
    assert "8410" in r.message
    assert "inazidi" in r.message
    assert "Idadi ya juu" in r.message


def test_swahili_credit_within_limit(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Je, ninaweza kumpa Fotso kreti ya sanduku moja?")
    assert r.ok is True
    assert r.approved is True
    assert r.lang == "sw"
    assert "6970" in r.message
    assert "Ndiyo" in r.message


def test_swahili_supplier_balance(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Tunadaiwa kiasi gani na Bonaberi?")
    assert r.ok is True
    assert r.lang == "sw"
    assert "42000" in r.message
    assert "Kiasi kinachodaiwa" in r.message


def test_swahili_supplier_null_balance_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Tunadaiwa kiasi gani na SOCA?")
    assert r.ok is False
    assert r.refuse_reason == "balance_owed_null"
    assert r.lang == "sw"
    assert "hakipo kwenye kumbukumbu" in r.message
    assert "42000" not in r.message


def test_swahili_stock(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Tuna hifadhi ngapi ya soda?")
    assert r.ok is True
    assert r.lang == "sw"
    assert "hifadhi=14" in r.message


def test_swahili_stock_sugar(db_b: sqlite3.Connection) -> None:
    # "sukari" (sugar) binds to the Sucre 25kg SKU on the second fixture.
    r = handle_ask(db_b, "Tuna hifadhi ngapi ya sukari?")
    assert r.ok is True
    assert r.lang == "sw"
    assert "Sucre 25kg" in r.message
    assert "hifadhi=" in r.message


def test_swahili_stock_flour(db_b: sqlite3.Connection) -> None:
    r = handle_ask(db_b, "Kuna unga kiasi gani?")
    assert r.ok is True
    assert r.lang == "sw"
    assert "Farine 50kg" in r.message


def test_swahili_stock_oil(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Tuna mafuta kiasi gani?")
    assert r.ok is True
    assert r.lang == "sw"
    assert "Bidon huile palme 5L" in r.message


def test_swahili_unknown_intent_refuses(db: sqlite3.Connection) -> None:
    r = handle_ask(db, "Nani anamiliki duka hili?")
    assert r.ok is False
    assert r.refuse_reason == "unknown_intent"
    assert r.lang == "sw"
    assert "Naweza kujibu tu" in r.message


# --- French/Swahili on the second fixture (binding, not memorization) -------


def test_french_duka_b_credit(db_b: sqlite3.Connection) -> None:
    # 2 × 13500 = 27000; 9800 + 27000 = 36800 > 25000
    r = handle_ask(db_b, "Puis-je donner deux sacs de sucre à crédit à Amina Bello ?")
    assert r.ok is True
    assert r.approved is False
    assert r.lang == "fr"
    assert "36800" in r.message


def test_swahili_duka_b_supplier(db_b: sqlite3.Connection) -> None:
    r = handle_ask(db_b, "Tunadaiwa kiasi gani na Sanaga Épicerie?")
    assert r.ok is True
    assert r.lang == "sw"
    assert "15500" in r.message


# --- quantity parsing edge cases in-language --------------------------------


def test_french_word_quantity_parsed() -> None:
    p = parse_ask("Puis-je donner quatre caisses de crédit à Fotso ?")
    assert p.intent.value == "credit_check"
    assert p.lang == "fr"
    assert p.qty == 4


def test_french_une_caisse_is_one() -> None:
    p = parse_ask("Peut-on accorder une caisse de crédit à Fotso ?")
    assert p.qty == 1


def test_french_un_article_is_not_a_quantity() -> None:
    # "un crédit" is an article, not a count. The real quantity (2) wins.
    p = parse_ask("Peut-on accorder un crédit à Fotso pour deux caisses ?")
    assert p.lang == "fr"
    assert p.qty == 2


def test_swahili_word_quantity_parsed() -> None:
    p = parse_ask("Je, ninaweza kumpa Fotso kreti ya makreti mawili?")
    assert p.intent.value == "credit_check"
    assert p.lang == "sw"
    assert p.qty == 2


def test_swahili_noun_before_digit_quantity() -> None:
    # Noun-before-digit: "kreti 2,000" is a unit-qualified quantity, not a
    # bare ledger amount; it must parse at full value and bypass MAX_BARE_QTY.
    p = parse_ask("Ninaweza kumpa Fotso kreti 2,000?")
    assert p.intent.value == "credit_check"
    assert p.lang == "sw"
    assert p.qty == 2000
    p2 = parse_ask("Je, ninaweza kumpa Fotso makreti 2,000?")
    assert p2.qty == 2000


def test_swahili_large_credit_flow_refuses(db: sqlite3.Connection) -> None:
    # 2000 crates @ 720 = 1,440,000, far over the 8000 limit; must refuse
    # (approved False), never default to a single crate.
    r = handle_ask(db, "Ninaweza kumpa Fotso kreti 2,000?")
    assert r.ok is True
    assert r.approved is False
    assert r.lang == "sw"
    assert "1440000" in r.message
    assert "inazidi" in r.message


def test_detect_lang_tie_falls_back_to_english() -> None:
    # One French and one Swahili marker; a tie must resolve to English,
    # matching the docstring contract for detect_lang.
    assert detect_lang("combien kreti") == "en"
    assert detect_lang("devons duka") == "en"
    assert detect_lang("bonjour") == "en"


def test_refuse_not_found_identifier_localized(db: sqlite3.Connection) -> None:
    # An ask naming no customer in French/Swahili must refuse with a
    # localized identifier ("client" / "mteja"), never mixed-language.
    r = handle_ask(db, "Puis-je donner trois caisses de crédit ?")
    assert r.ok is False
    assert r.lang == "fr"
    assert "client" in r.message
    assert "customer" not in r.message
    r2 = handle_ask(db, "Ninaweza kumpa mtu kreti ya makreti matatu?")
    assert r2.ok is False
    assert r2.lang == "sw"
    assert "mteja" in r2.message
    assert "customer" not in r2.message


def test_refuse_not_found_preserves_ledger_name(db: sqlite3.Connection) -> None:
    # A known name with no row in this shop (duka_b supplier asked against the
    # Akwa ledger) is not a translation key; it stays verbatim.
    r = handle_ask(db, "Combien devons-nous à Sanaga Épicerie ?")
    assert r.ok is False
    assert "Sanaga Épicerie" in r.message
    assert "fournisseur" not in r.message


def test_english_still_default() -> None:
    p = parse_ask("How much do we owe SOCA?")
    assert p.lang == "en"
    assert p.intent.value == "supplier_balance"
