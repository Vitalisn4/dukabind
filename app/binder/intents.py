"""Rule-based intent detection (EN + SW keywords).

Routing is deterministic: the model never chooses the intent or the query.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


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
    lang: str  # "en" | "sw"
    customer: str | None = None
    supplier: str | None = None
    sku: str | None = None
    qty: int | None = None


_CREDIT_EN = re.compile(
    r"\b(credit|on\s+credit|can\s+i\s+(give|sell)|allow\s+credit)\b",
    re.I,
)
_CREDIT_SW = re.compile(r"\b(deni|mkopo|naweza\s+kumpa|kumpa)\b", re.I)
_SUPPLIER_EN = re.compile(r"\b(owe|owed|payable|supplier|vendor|pay\s+them)\b", re.I)
_SUPPLIER_SW = re.compile(r"\b(msambazaji|tunadaiwa|deni\s+la|sali[o]?)\b", re.I)
_STOCK_EN = re.compile(r"\b(stock|on\s+hand|inventory|how\s+many|crates?\s+left)\b", re.I)
# Do not include English "stock" here — it would mis-label EN asks as Swahili.
_STOCK_SW = re.compile(r"\b(idadi|ipo\s+ngapi|bee?bi)\b", re.I)

_QTY = re.compile(r"\b(\d+)\s*(crates?|bags?|units?|crate|bag)?\b", re.I)
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


def _extract_qty(text: str) -> int | None:
    """Parse a digit or word quantity (one…ten) from the utterance."""
    m = _QTY.search(text)
    if m:
        return int(m.group(1))
    lower = text.lower()
    for word, n in _WORD_QTY.items():
        if re.search(rf"\b{word}\b", lower):
            return n
    return None


def _extract_known_name(text: str, known: list[str]) -> str | None:
    """Return the first known entity name contained in the text."""
    lower = text.lower()
    for name in known:
        if name.lower() in lower:
            return name
    return None


# Names present in seed_demo.sql — keep in sync when fixtures change.
KNOWN_CUSTOMERS = ["Amina Wanjiru", "Jean Mbarga", "Pauline Ngo", "Amina"]
KNOWN_SUPPLIERS = ["Bidco Distributors", "Nest Wholesale", "Bidco"]
KNOWN_SKUS = ["CRATE-SODA-300ML", "BAG-RICE-25KG", "JERRY-OIL-5L", "soda", "rice", "oil"]

_SKU_ALIASES = {
    "soda": "CRATE-SODA-300ML",
    "crate-soda-300ml": "CRATE-SODA-300ML",
    "rice": "BAG-RICE-25KG",
    "bag-rice-25kg": "BAG-RICE-25KG",
    "oil": "JERRY-OIL-5L",
    "jerry-oil-5l": "JERRY-OIL-5L",
}


def normalize_sku(raw: str | None) -> str | None:
    """Map demo aliases to canonical sku_id / name keys."""
    if not raw:
        return None
    return _SKU_ALIASES.get(raw.lower(), raw)


def detect_lang(text: str) -> str:
    """Return 'sw' only when Swahili-specific cues are present."""
    if _CREDIT_SW.search(text) or _SUPPLIER_SW.search(text) or _STOCK_SW.search(text):
        return "sw"
    if re.search(r"\b(naweza|tunadaiwa|msambazaji|hakuna|muulize)\b", text, re.I):
        return "sw"
    return "en"


def parse_ask(text: str) -> ParsedAsk:
    """Map a staff utterance to intent + slots (no LLM, no SQL)."""
    lang = detect_lang(text)
    qty = _extract_qty(text)
    sku = normalize_sku(_extract_known_name(text, KNOWN_SKUS))

    if _CREDIT_EN.search(text) or _CREDIT_SW.search(text):
        cust = _extract_known_name(text, KNOWN_CUSTOMERS)
        if cust == "Amina":
            cust = "Amina Wanjiru"
        return ParsedAsk(Intent.CREDIT_CHECK, lang, customer=cust, sku=sku, qty=qty)

    if _SUPPLIER_EN.search(text) or _SUPPLIER_SW.search(text):
        sup = _extract_known_name(text, KNOWN_SUPPLIERS)
        if sup == "Bidco":
            sup = "Bidco Distributors"
        return ParsedAsk(Intent.SUPPLIER_BALANCE, lang, supplier=sup)

    if _STOCK_EN.search(text) or _STOCK_SW.search(text):
        return ParsedAsk(Intent.STOCK_CHECK, lang, sku=sku, qty=qty)

    return ParsedAsk(Intent.UNKNOWN, lang)
