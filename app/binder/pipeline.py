"""End-to-end binder pipeline (no LLM required for truth).

Flow: utterance → intent → allowlisted SQL → deterministic decision / refuse.
The LLM (later) only narrates citation_rows; it must not invent amounts.
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


def handle_ask(conn: sqlite3.Connection, text: str) -> BinderResult:
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
        # Default demo sku price for soda crate when qty present; else qty=1 price lookup
        qty = parsed.qty or 1
        sku_rows = run_query(conn, "sku_stock", {"name": "CRATE-SODA-300ML"})
        unit_price = int(sku_rows[0]["unit_price"]) if sku_rows else 0
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
        lang = parsed.lang
        msg = (
            f"Amount owed to {row['display_name']}: {bal}."
            if lang == "en"
            else f"Kiasi kinachodaiwa {row['display_name']}: {bal}."
        )
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=lang,
            citation_rows=[dict(row)],
            message=msg,
        )

    if parsed.intent == Intent.STOCK_CHECK:
        if not parsed.sku:
            return refuse_not_found(parsed.lang, "sku")
        rows = run_query(conn, "sku_stock", {"name": parsed.sku})
        if not rows:
            return refuse_not_found(parsed.lang, parsed.sku)
        row = rows[0]
        lang = parsed.lang
        msg = (
            f"{row['name']}: on_hand={row['on_hand']}, unit_price={row['unit_price']} {row['currency']}."
            if lang == "en"
            else f"{row['name']}: idadi={row['on_hand']}, bei={row['unit_price']} {row['currency']}."
        )
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=lang,
            citation_rows=[dict(row)],
            message=msg,
        )

    return refuse_unknown(parsed.lang)


def result_with_citation_json(result: BinderResult) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "intent": result.intent.value,
        "lang": result.lang,
        "message": result.message,
        "refuse_reason": result.refuse_reason,
        "citation_json": citations_to_json(result.citation_rows),
    }
