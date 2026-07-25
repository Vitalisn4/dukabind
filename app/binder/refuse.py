"""Fail-closed refuse rules (control C4).

If a required field is NULL/missing, we refuse — the LLM must not invent amounts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.binder.intents import Intent


@dataclass(frozen=True)
class BinderResult:
    """Authoritative binder answer: message, citations, and optional refuse reason."""

    ok: bool
    intent: Intent
    lang: str
    citation_rows: list[dict[str, Any]]
    message: str
    refuse_reason: str | None = None


def _msg(lang: str, en: str, sw: str) -> str:
    """Pick the English or Swahili cashier string."""
    return sw if lang == "sw" else en


def refuse_credit_missing_limit(lang: str, name: str) -> BinderResult:
    """Refuse when credit_limit is NULL — never invent a limit."""
    return BinderResult(
        ok=False,
        intent=Intent.CREDIT_CHECK,
        lang=lang,
        citation_rows=[],
        refuse_reason="credit_limit_null",
        message=_msg(
            lang,
            f"No credit limit on file for {name} — ask the owner.",
            f"Hakuna kikomo cha deni kwenye faili kwa {name} — muulize mmiliki.",
        ),
    )


def refuse_supplier_missing_balance(lang: str, name: str) -> BinderResult:
    """Refuse when balance_owed is NULL — never invent an amount."""
    return BinderResult(
        ok=False,
        intent=Intent.SUPPLIER_BALANCE,
        lang=lang,
        citation_rows=[],
        refuse_reason="balance_owed_null",
        message=_msg(
            lang,
            f"Amount owed to {name} is not on file — ask the owner.",
            f"Kiasi kinachodaiwa {name} hakipo kwenye faili — muulize mmiliki.",
        ),
    )


def refuse_not_found(lang: str, what: str) -> BinderResult:
    """Refuse when the named customer, supplier, or SKU is absent."""
    return BinderResult(
        ok=False,
        intent=Intent.UNKNOWN,
        lang=lang,
        citation_rows=[],
        refuse_reason="not_found",
        message=_msg(
            lang,
            f"No ledger row found for {what} — ask the owner.",
            f"Hakuna rekodi kwa {what} — muulize mmiliki.",
        ),
    )


def refuse_unknown(lang: str) -> BinderResult:
    """Refuse intents outside credit, supplier balance, and stock."""
    return BinderResult(
        ok=False,
        intent=Intent.UNKNOWN,
        lang=lang,
        citation_rows=[],
        refuse_reason="unknown_intent",
        message=_msg(
            lang,
            "I can only answer credit, supplier balances, or stock from this shop ledger.",
            "Ninaweza kujibu tu kuhusu deni, salio la msambazaji, au stock kutoka leja ya duka hili.",
        ),
    )


def credit_decision(
    lang: str,
    row: dict[str, Any],
    qty: int,
    unit_price: int,
) -> BinderResult:
    """Deterministic arithmetic — do not leave this to the LLM."""
    limit = row["credit_limit"]
    outstanding = int(row["outstanding"])
    if limit is None:
        return refuse_credit_missing_limit(lang, row["display_name"])

    limit_i = int(limit)
    add = qty * unit_price
    projected = outstanding + add
    currency = row.get("currency") or "XAF"
    citation = [
        dict(row),
        {
            "sku_unit_price": unit_price,
            "qty_requested": qty,
            "projected_outstanding": projected,
            "currency": currency,
        },
    ]

    if projected > limit_i:
        over = projected - limit_i
        room = limit_i - outstanding
        max_qty = max(0, room // unit_price) if unit_price else 0
        return BinderResult(
            ok=True,
            intent=Intent.CREDIT_CHECK,
            lang=lang,
            citation_rows=citation,
            message=_msg(
                lang,
                (
                    f"No — {qty} × {unit_price} = {add}; "
                    f"{outstanding} + {add} = {projected} exceeds limit {limit_i} "
                    f"by {over} {currency}. "
                    f"Max qty within limit: {max_qty}."
                ),
                (
                    f"Hapana — {qty} × {unit_price} = {add}; "
                    f"{outstanding} + {add} = {projected} inazidi kikomo {limit_i} "
                    f"kwa {over} {currency}. "
                    f"Idadi max ndani ya kikomo: {max_qty}."
                ),
            ),
        )

    return BinderResult(
        ok=True,
        intent=Intent.CREDIT_CHECK,
        lang=lang,
        citation_rows=citation,
        message=_msg(
            lang,
            (
                f"Yes — {qty} × {unit_price} = {add}; "
                f"projected outstanding {projected} ≤ limit {limit_i} {currency}."
            ),
            (
                f"Ndiyo — {qty} × {unit_price} = {add}; "
                f"deni litakaloonekana {projected} ≤ kikomo {limit_i} {currency}."
            ),
        ),
    )
