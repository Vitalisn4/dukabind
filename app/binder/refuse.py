"""Fail-closed refuse rules (control C4).

If a required field is NULL/missing, we refuse — the LLM must not invent amounts.
Cashier messages are English (Gate 1 Path A).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.binder.intents import Intent


@dataclass(frozen=True)
class BinderResult:
    """Authoritative binder answer: message, citations, and optional refuse reason.

    ``ok`` means the binder finished a lookup/decision (or a structured refuse).
    ``approved`` is set only for credit decisions: True = within limit, False = over
    limit. Other intents leave it None so consumers do not treat ``ok`` as approval.
    """

    ok: bool
    intent: Intent
    lang: str
    citation_rows: list[dict[str, Any]]
    message: str
    refuse_reason: str | None = None
    approved: bool | None = None


def refuse_credit_missing_limit(lang: str, name: str) -> BinderResult:
    """Refuse when credit_limit is NULL — never invent a limit."""
    return BinderResult(
        ok=False,
        intent=Intent.CREDIT_CHECK,
        lang=lang,
        citation_rows=[],
        refuse_reason="credit_limit_null",
        message=f"No credit limit on file for {name} — ask the owner.",
    )


def refuse_credit_missing_outstanding(lang: str, name: str) -> BinderResult:
    """Refuse when outstanding is NULL — never invent a balance."""
    return BinderResult(
        ok=False,
        intent=Intent.CREDIT_CHECK,
        lang=lang,
        citation_rows=[],
        refuse_reason="outstanding_null",
        message=f"No outstanding balance on file for {name} — ask the owner.",
    )


def refuse_supplier_missing_balance(lang: str, name: str) -> BinderResult:
    """Refuse when balance_owed is NULL — never invent an amount."""
    return BinderResult(
        ok=False,
        intent=Intent.SUPPLIER_BALANCE,
        lang=lang,
        citation_rows=[],
        refuse_reason="balance_owed_null",
        message=f"Amount owed to {name} is not on file — ask the owner.",
    )


def refuse_not_found(lang: str, what: str) -> BinderResult:
    """Refuse when the named customer, supplier, or SKU is absent."""
    return BinderResult(
        ok=False,
        intent=Intent.UNKNOWN,
        lang=lang,
        citation_rows=[],
        refuse_reason="not_found",
        message=f"No ledger row found for {what} — ask the owner.",
    )


def refuse_unknown(lang: str) -> BinderResult:
    """Refuse intents outside credit, supplier balance, and stock."""
    return BinderResult(
        ok=False,
        intent=Intent.UNKNOWN,
        lang=lang,
        citation_rows=[],
        refuse_reason="unknown_intent",
        message=(
            "I can only answer credit, supplier balances, or stock from this shop ledger."
        ),
    )


def credit_decision(
    lang: str,
    row: dict[str, Any],
    qty: int,
    unit_price: int,
) -> BinderResult:
    """Deterministic arithmetic — do not leave this to the LLM."""
    if qty < 1 or unit_price <= 0:
        return refuse_not_found(lang, "quantity" if qty < 1 else "unit_price")

    limit = row["credit_limit"]
    if limit is None:
        return refuse_credit_missing_limit(lang, row["display_name"])

    outstanding = row["outstanding"]
    if outstanding is None:
        return refuse_credit_missing_outstanding(lang, row["display_name"])

    outstanding = int(outstanding)
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
            approved=False,
            message=(
                f"No — {qty} × {unit_price} = {add}; "
                f"{outstanding} + {add} = {projected} exceeds limit {limit_i} "
                f"by {over} {currency}. "
                f"Max qty within limit: {max_qty}."
            ),
        )

    return BinderResult(
        ok=True,
        intent=Intent.CREDIT_CHECK,
        lang=lang,
        citation_rows=citation,
        approved=True,
        message=(
            f"Yes — {qty} × {unit_price} = {add}; "
            f"projected outstanding {projected} ≤ limit {limit_i} {currency}."
        ),
    )
