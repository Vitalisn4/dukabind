"""Rule-based intent detection (English keywords).

Routing is deterministic: the model never chooses the intent or the query.
Product language for Gate 1 is English (Path A).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from app.db.fixture import (
    KNOWN_CUSTOMERS,
    KNOWN_SKUS,
    KNOWN_SUPPLIERS,
    normalize_customer,
    normalize_sku,
    normalize_supplier,
)


class Intent(str, Enum):
    """Supported binder intents; UNKNOWN triggers a refuse."""

    CREDIT_CHECK = "credit_check"
    SUPPLIER_BALANCE = "supplier_balance"
    STOCK_CHECK = "stock_check"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ParsedAsk:
    """Slots extracted from a staff utterance before any SQL runs."""

    intent: Intent
    lang: str  # always "en" for Gate 1
    customer: str | None = None
    supplier: str | None = None
    sku: str | None = None
    qty: int | None = None


_CREDIT = re.compile(
    r"\b(credit|on\s+credit|can\s+i\s+(give|sell)|allow\s+credit)\b",
    re.IGNORECASE,
)
_SUPPLIER = re.compile(r"\b(owe|owed|payable|supplier|vendor|pay\s+them)\b", re.IGNORECASE)
_STOCK = re.compile(r"\b(stock|on\s+hand|inventory|how\s+many|crates?\s+left)\b", re.IGNORECASE)

_QTY = re.compile(r"\b(\d+)\s*(crates?|bags?|units?)?\b", re.IGNORECASE)
# Bare digits at or above this are ledger amounts (limits/prices/balances),
# not crate counts — “his limit is 8000” must not become a quantity of 8000.
MAX_BARE_QTY = 999
_WORD_QTY = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

# Bound prompt / narration cost on the 8 GB contest laptop.
MAX_ASK_CHARS = 500


def _extract_qty(text: str) -> int | None:
    """Parse a digit or word quantity (one…ten) from the utterance.

    A digit is a quantity only when it carries a unit word (``3 crates``,
    ``1 bag``) or is a small bare count (< ``MAX_BARE_QTY``). Ledger amounts
    like limits, prices, or balances in the question are never quantities —
    but an amount mentioned before the real quantity must not swallow it
    (``his balance is 6250, can I give Fotso 2 crates?`` → 2).

    Known limitations (both fail closed — toward refuse, never a wrong
    approval): word-written amounts (``eight thousand``) hit the word-quantity
    fallback and are read as small counts; a sub-threshold price mention
    (``the price is 720 per crate``) or a false unit word (``2000 units of
    credit``) is read as a large quantity. Each can only move a credit
    decision toward refuse, never toward a wrong Yes.
    """
    for m in _QTY.finditer(text):
        qty = int(m.group(1))
        if m.group(2) or qty < MAX_BARE_QTY:
            return qty
    lower = text.lower()
    for word, n in _WORD_QTY.items():
        if re.search(rf"\b{word}\b", lower):
            return n
    return None


def _extract_known_name(text: str, known: list[str]) -> str | None:
    """Return the longest known entity matched on word boundaries.

    Substring checks are unsafe (`rice` matches inside `price`).
    """
    lower = text.lower()
    for name in sorted(known, key=len, reverse=True):
        pattern = rf"(?<!\w){re.escape(name.lower())}(?!\w)"
        if re.search(pattern, lower):
            return name
    return None


def parse_ask(text: str) -> ParsedAsk:
    """Map a staff utterance to intent + slots (no LLM, no SQL)."""
    text = text.strip()
    if not text or len(text) > MAX_ASK_CHARS:
        return ParsedAsk(Intent.UNKNOWN, "en")

    lang = "en"
    qty = _extract_qty(text)
    sku = normalize_sku(_extract_known_name(text, KNOWN_SKUS))

    if _CREDIT.search(text):
        cust = normalize_customer(_extract_known_name(text, KNOWN_CUSTOMERS))
        return ParsedAsk(Intent.CREDIT_CHECK, lang, customer=cust, sku=sku, qty=qty)

    if _SUPPLIER.search(text):
        sup = normalize_supplier(_extract_known_name(text, KNOWN_SUPPLIERS))
        return ParsedAsk(Intent.SUPPLIER_BALANCE, lang, supplier=sup)

    if _STOCK.search(text):
        return ParsedAsk(Intent.STOCK_CHECK, lang, sku=sku, qty=qty)

    return ParsedAsk(Intent.UNKNOWN, lang)
