"""Binder pipeline: utterance → intent → allowlisted SQL → decision or refuse.

Produces the authoritative answer without any model call.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from app.binder.allowlist import run_query
from app.binder.citations import citations_to_json
from app.binder.intents import Intent, parse_ask
from app.binder.refuse import (
    BinderResult,
    credit_decision,
    refuse_not_found,
    refuse_supplier_missing_balance,
    refuse_unknown,
)
from app.db.fixture import DEFAULT_CREDIT_SKU


def handle_ask(conn: sqlite3.Connection, text: str) -> BinderResult:
    """Answer a staff question from the ledger, or refuse when data is missing."""
    parsed = parse_ask(text)

    if parsed.intent == Intent.UNKNOWN:
        return refuse_unknown(parsed.lang)

    if parsed.intent == Intent.CREDIT_CHECK:
        if not parsed.customer:
            return refuse_not_found(parsed.lang, "customer")
        rows = run_query(conn, "customer_credit", {"name": parsed.customer})
        if not rows:
            return refuse_not_found(parsed.lang, parsed.customer)
        row = rows[0]
        qty = parsed.qty if parsed.qty is not None else 1
        if qty < 1:
            return refuse_not_found(parsed.lang, "quantity")
        # Unnamed "crates on credit" uses the shop's default soft-drink crate.
        sku_name = parsed.sku or DEFAULT_CREDIT_SKU
        sku_rows = run_query(conn, "sku_stock", {"name": sku_name})
        if not sku_rows or int(sku_rows[0]["unit_price"]) <= 0:
            return refuse_not_found(parsed.lang, sku_name)
        unit_price = int(sku_rows[0]["unit_price"])
        return credit_decision(parsed.lang, row, qty, unit_price)

    if parsed.intent == Intent.SUPPLIER_BALANCE:
        if not parsed.supplier:
            return refuse_not_found(parsed.lang, "supplier")
        rows = run_query(conn, "supplier_balance", {"name": parsed.supplier})
        if not rows:
            return refuse_not_found(parsed.lang, parsed.supplier)
        row = rows[0]
        if row.get("balance_owed") is None:
            return refuse_supplier_missing_balance(parsed.lang, row["display_name"])
        bal = int(row["balance_owed"])
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=parsed.lang,
            citation_rows=[dict(row)],
            message=f"Amount owed to {row['display_name']}: {bal}.",
        )

    if parsed.intent == Intent.STOCK_CHECK:
        if not parsed.sku:
            return refuse_not_found(parsed.lang, "sku")
        rows = run_query(conn, "sku_stock", {"name": parsed.sku})
        if not rows:
            return refuse_not_found(parsed.lang, parsed.sku)
        row = rows[0]
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=parsed.lang,
            citation_rows=[dict(row)],
            message=(
                f"{row['name']}: on_hand={row['on_hand']}, "
                f"unit_price={row['unit_price']} {row['currency']}."
            ),
        )

    return refuse_unknown(parsed.lang)


def result_with_citation_json(result: BinderResult) -> dict[str, Any]:
    """Serialize a binder result with its ledger citations attached."""
    return {
        "ok": result.ok,
        "approved": result.approved,
        "intent": result.intent.value,
        "lang": result.lang,
        "message": result.message,
        "refuse_reason": result.refuse_reason,
        "citation_json": citations_to_json(result.citation_rows),
    }
