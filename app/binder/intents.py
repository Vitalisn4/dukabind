"""Rule-based intent detection (EN + SW keywords).

Research: keep routing deterministic and RAM-cheap. LLM JSON parse is a later
fallback — not required for the vertical-slice binder proof.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    CREDIT_CHECK = "credit_check"
    SUPPLIER_BALANCE = "supplier_balance"
    STOCK_CHECK = "stock_check"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ParsedAsk:
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
_STOCK_SW = re.compile(r"\b(idadi|stock|ipo\s+ngapi|bee?bi)\b", re.I)

# Simple entity patterns for demo fixtures — extend carefully; do not exec user regex.
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
    m = _QTY.search(text)
    if m:
        return int(m.group(1))
    lower = text.lower()
    for word, n in _WORD_QTY.items():
        if re.search(rf"\b{word}\b", lower):
            return n
    return None


def _extract_known_name(text: str, known: list[str]) -> str | None:
    lower = text.lower()
    for name in known:
        if name.lower() in lower:
            return name
    return None


# Names present in seed_demo.sql — keep in sync when fixtures change.
KNOWN_CUSTOMERS = ["Amina Wanjiru", "Jean Mbarga", "Pauline Ngo", "Amina"]
KNOWN_SUPPLIERS = ["Bidco Distributors", "Nest Wholesale", "Bidco"]
KNOWN_SKUS = ["CRATE-SODA-300ML", "BAG-RICE-25KG", "JERRY-OIL-5L", "soda", "rice", "oil"]


def detect_lang(text: str) -> str:
    if _CREDIT_SW.search(text) or _SUPPLIER_SW.search(text) or _STOCK_SW.search(text):
        return "sw"
    if re.search(r"\b(naweza|tunadaiwa|msambazaji|hakuna|muulize)\b", text, re.I):
        return "sw"
    return "en"


def parse_ask(text: str) -> ParsedAsk:
    lang = detect_lang(text)
    qty = _extract_qty(text)

    if _CREDIT_EN.search(text) or _CREDIT_SW.search(text):
        cust = _extract_known_name(text, KNOWN_CUSTOMERS)
        if cust == "Amina":
            cust = "Amina Wanjiru"
        return ParsedAsk(Intent.CREDIT_CHECK, lang, customer=cust, qty=qty)

    if _SUPPLIER_EN.search(text) or _SUPPLIER_SW.search(text):
        sup = _extract_known_name(text, KNOWN_SUPPLIERS)
        if sup == "Bidco":
            sup = "Bidco Distributors"
        return ParsedAsk(Intent.SUPPLIER_BALANCE, lang, supplier=sup)

    if _STOCK_EN.search(text) or _STOCK_SW.search(text):
        sku = _extract_known_name(text, KNOWN_SKUS)
        if sku and sku.lower() == "soda":
            sku = "CRATE-SODA-300ML"
        elif sku and sku.lower() == "rice":
            sku = "BAG-RICE-25KG"
        elif sku and sku.lower() == "oil":
            sku = "JERRY-OIL-5L"
        return ParsedAsk(Intent.STOCK_CHECK, lang, sku=sku, qty=qty)

    return ParsedAsk(Intent.UNKNOWN, lang)
