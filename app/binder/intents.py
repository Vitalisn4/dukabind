"""Rule-based intent detection (English, French, Swahili keywords).

Routing is deterministic: the model never chooses the intent or the query.
English is the primary language; French (Cameroon official language) and
Swahili (pan-African) asks bind to the same allowlisted queries. The binder
`message` is localized per ask; narration follows the same language when the
local model can produce it (verified on Qwen2.5-1.5B Q4_K_M).
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


SUPPORTED_LANGS = ("en", "fr", "sw")


@dataclass(frozen=True)
class ParsedAsk:
    """Slots extracted from a staff utterance before any SQL runs."""

    intent: Intent
    lang: str  # one of SUPPORTED_LANGS
    customer: str | None = None
    supplier: str | None = None
    sku: str | None = None
    qty: int | None = None


# Language markers for detection, matched on word boundaries only (a marker
# must not fire inside an English word — e.g. "deni" must not match
# "denizen"). Shared words (e.g. "stock", "credit") are deliberately excluded
# from FR/SW marker lists so an English ask is never misrouted; accented
# "crédit"/"à crédit"/"dû" and unaccented French verbs are unambiguous, and
# "kreti"/"mkopo"/"tunadaiwa" are unambiguously Swahili.
_LANG_MARKERS: dict[str, tuple[str, ...]] = {
    "fr": (
        "crédit",
        "à crédit",
        "devons",
        "dû",
        "fournisseur",
        "combien",
        "en stock",
        "combien de",
        "donner",
        "donnez",
        "accorder",
        "vendre",
        "inventaire",
        "puis",
        "peut",
        "nous",
    ),
    "sw": (
        "kreti",
        "mkopo",
        "mikopo",
        "tunadaiwa",
        "deni",
        "msambazaji",
        "hifadhi",
        "idadi",
        "ngapi",
        "vifaa",
        "kumpa",
        "malipo",
        "nani",
        "nini",
        "wapi",
        "duka",
        "kiasi",
        "mangapi",
    ),
}

_INTENT_PATTERNS: dict[str, dict[Intent, re.Pattern[str]]] = {
    "en": {
        Intent.CREDIT_CHECK: re.compile(
            r"\b(credit|on\s+credit|can\s+i\s+(give|sell)|allow\s+credit)\b",
            re.IGNORECASE,
        ),
        Intent.SUPPLIER_BALANCE: re.compile(
            r"\b(owe|owed|payable|supplier|vendor|pay\s+them)\b", re.IGNORECASE
        ),
        Intent.STOCK_CHECK: re.compile(
            r"\b(stock|on\s+hand|inventory|how\s+many|crates?\s+left)\b", re.IGNORECASE
        ),
    },
    "fr": {
        Intent.CREDIT_CHECK: re.compile(
            r"\b(crédit|credit|à\s+crédit|a\s+credit|donner|accorder|vendre)\b",
            re.IGNORECASE,
        ),
        Intent.SUPPLIER_BALANCE: re.compile(
            r"\b(devons|doit|dû|due|fournisseur)\b", re.IGNORECASE
        ),
        Intent.STOCK_CHECK: re.compile(
            r"\b(stock|en\s+stock|inventaire|combien\s+de|reste)\b", re.IGNORECASE
        ),
    },
    "sw": {
        Intent.CREDIT_CHECK: re.compile(
            r"\b(kreti|mkopo|mikopo|kumpa|kutoa)\b", re.IGNORECASE
        ),
        Intent.SUPPLIER_BALANCE: re.compile(
            r"\b(tunadaiwa|deni|msambazaji|malipo|dai)\b", re.IGNORECASE
        ),
        Intent.STOCK_CHECK: re.compile(
            r"\b(hifadhi|idadi|ngapi|vifaa|bidhaa|kiasi|mangapi)\b", re.IGNORECASE
        ),
    },
}

# Unit words shared across languages; "kreti" is the Swahili word for
# crate/credit and is a quantity qualifier here ("kreti 2,000"). The
# noun may precede or follow the digit ("3 crates" / "makreti 2,000").
_UNIT_WORDS = r"crates?|bags?|units?|caisses?|sacs?|makreti|mifuko|kreti"
_QTY = re.compile(
    rf"\b(?:(?P<num1>\d{{1,3}}(?:,\d{{3}})+|\d+)\s*(?P<unit1>{_UNIT_WORDS})?"
    rf"|(?P<unit2>{_UNIT_WORDS})\s+(?P<num2>\d{{1,3}}(?:,\d{{3}})+|\d+))\b",
    re.IGNORECASE,
)
# Bare digits at or above this are ledger amounts (limits/prices/balances),
# not crate counts — “his limit is 8000” must not become a quantity of 8000.
MAX_BARE_QTY = 999
# Scaled word quantities (“eight thousand crates”) must refuse, never be read
# as a small count by the word fallback. Sentinel is large enough that any
# credit ask computes far over any plausible MSME limit.
_SCALED_QTY_SENTINEL = 10**6
_SCALED = re.compile(
    r"\b(hundreds?|thousands?|millions?|billions?|milliards?|elfu|milioni)\b",
    re.IGNORECASE,
)
_WORD_QTY: dict[str, dict[str, int]] = {
    "en": {
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
    },
    "fr": {
        "un": 1,
        "une": 1,
        "deux": 2,
        "trois": 3,
        "quatre": 4,
        "cinq": 5,
        "six": 6,
        "sept": 7,
        "huit": 8,
        "neuf": 9,
        "dix": 10,
    },
    "sw": {
        "moja": 1,
        "mmoja": 1,
        "mbili": 2,
        "mawili": 2,
        "tatu": 3,
        "matatu": 3,
        "nne": 4,
        "tano": 5,
        "sita": 6,
        "saba": 7,
        "nane": 8,
        "tisa": 9,
        "kumi": 10,
    },
}

# Bound prompt / narration cost on the 8 GB contest laptop.
MAX_ASK_CHARS = 500


def detect_lang(text: str) -> str:
    """Pick the ask language from distinctive markers; English is the default.

    Scores by marker count so an ask that mixes languages still binds to the
    language it most resembles; ties and no-marker asks resolve to ``en``.
    """
    lower = text.lower()

    def _hits(markers: tuple[str, ...]) -> int:
        total = 0
        for m in markers:
            total += len(re.findall(rf"\b{re.escape(m)}\b", lower))
        return total

    scores = {lang: _hits(markers) for lang, markers in _LANG_MARKERS.items()}
    if scores["sw"] > scores["fr"] and scores["sw"] > 0:
        return "sw"
    if scores["fr"] > scores["sw"] and scores["fr"] > 0:
        return "fr"
    return "en"


def _extract_qty(text: str, lang: str) -> int | None:
    """Parse a digit or word quantity (one…ten) from the utterance.

    A digit is a quantity only when it carries a unit word (``3 crates``,
    ``1 bag``, ``trois caisses``, ``makreti matatu``, or noun-before-digit
    ``kreti 2,000`` → 2000), is a small bare count (< ``MAX_BARE_QTY``), or
    is a comma-grouped magnitude parsed at its full value (``2,000 crates``
    → 2000). Ledger amounts like limits, prices, or balances in the question
    are never quantities — but an amount mentioned before the real quantity
    must not swallow it (``his balance is 6250, can I give Fotso 2 crates?``
    → 2).

    Known limitations (all fail closed — toward refuse, never a wrong
    approval): word-written amounts (``eight thousand crates``) refuse via a
    scaled-quantity sentinel instead of being read as small counts; a
    sub-threshold price mention (``the price is 720 per crate``) or a false
    unit word (``2000 units of credit``) is read as a large quantity. Each
    can only move a credit decision toward refuse, never toward a wrong Yes.
    """
    for m in _QTY.finditer(text):
        qty = int((m.group("num1") or m.group("num2")).replace(",", ""))
        if m.group("unit1") or m.group("unit2") or qty < MAX_BARE_QTY:
            return qty
    lower = text.lower()
    if _SCALED.search(lower):
        return _SCALED_QTY_SENTINEL
    # French indefinite articles ("un crédit", "une caisse") are not
    # quantities: only read them as 1 when followed by a countable unit so
    # "un crédit pour deux caisses" parses as 2, not 1.
    if lang == "fr" and re.search(
        r"\bun(?:e)?\s+(caisse|caisses|sac|sacs|bidon|bidons|carton|cartons|bouteille|bouteilles)\b",
        lower,
    ):
        return 1
    for word, n in _WORD_QTY[lang].items():
        if word in ("un", "une"):
            continue
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

    lang = detect_lang(text)
    qty = _extract_qty(text, lang)
    sku = normalize_sku(_extract_known_name(text, KNOWN_SKUS))

    patterns = _INTENT_PATTERNS[lang]
    if patterns[Intent.CREDIT_CHECK].search(text):
        cust = normalize_customer(_extract_known_name(text, KNOWN_CUSTOMERS))
        return ParsedAsk(Intent.CREDIT_CHECK, lang, customer=cust, sku=sku, qty=qty)

    if patterns[Intent.SUPPLIER_BALANCE].search(text):
        sup = normalize_supplier(_extract_known_name(text, KNOWN_SUPPLIERS))
        return ParsedAsk(Intent.SUPPLIER_BALANCE, lang, supplier=sup)

    if patterns[Intent.STOCK_CHECK].search(text):
        return ParsedAsk(Intent.STOCK_CHECK, lang, sku=sku, qty=qty)

    return ParsedAsk(Intent.UNKNOWN, lang)
