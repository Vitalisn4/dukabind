"""Binder pipeline: utterance, intent, allowlisted SQL, decision or refuse.

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
    refuse_no_customers,
    refuse_no_skus,
    refuse_no_suppliers,
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

    if parsed.intent == Intent.CREDIT_HEADROOM:
        if not parsed.customer:
            from dataclasses import replace
            return replace(refuse_not_found(parsed.lang, "customer"), intent=Intent.CREDIT_HEADROOM)
        rows = run_query(conn, "customer_credit", {"name": parsed.customer})
        if not rows:
            from dataclasses import replace
            return replace(refuse_not_found(parsed.lang, parsed.customer), intent=Intent.CREDIT_HEADROOM)
        row = rows[0]
        limit = row["credit_limit"]
        if limit is None:
            from dataclasses import replace

            from app.binder.refuse import refuse_credit_missing_limit
            return replace(refuse_credit_missing_limit(parsed.lang, row["display_name"]), intent=Intent.CREDIT_HEADROOM)
        outstanding = row["outstanding"]
        if outstanding is None:
            from dataclasses import replace

            from app.binder.refuse import refuse_credit_missing_outstanding
            return replace(refuse_credit_missing_outstanding(parsed.lang, row["display_name"]), intent=Intent.CREDIT_HEADROOM)
        room = int(limit) - int(outstanding)
        currency = row.get("currency") or "XAF"
        msg = {
            "en": (
                f"{row['display_name']} credit: limit {limit}, "
                f"outstanding {outstanding}, available {room} {currency}."
            ),
            "fr": (
                f"Crédit de {row['display_name']} : limite {limit}, "
                f"dû {outstanding}, disponible {room} {currency}."
            ),
            "sw": (
                f"Kreti ya {row['display_name']}: kikomo {limit}, "
                f"deni {outstanding}, inapatikana {room} {currency}."
            ),
        }.get(parsed.lang, f"{row['display_name']} credit: available {room} {currency}.")
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=parsed.lang,
            citation_rows=[dict(row)],
            message=msg,
        )

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
        msg = {
            "en": f"Amount owed to {row['display_name']}: {bal}.",
            "fr": f"Montant dû à {row['display_name']} : {bal}.",
            "sw": f"Kiasi kinachodaiwa na {row['display_name']}: {bal}.",
        }.get(parsed.lang, f"Amount owed to {row['display_name']}: {bal}.")
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=parsed.lang,
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
        msg = {
            "en": (
                f"{row['name']}: on_hand={row['on_hand']}, "
                f"unit_price={row['unit_price']} {row['currency']}."
            ),
            "fr": (
                f"{row['name']} : en stock={row['on_hand']}, "
                f"prix unitaire={row['unit_price']} {row['currency']}."
            ),
            "sw": (
                f"{row['name']}: hifadhi={row['on_hand']}, "
                f"bei ya kitengo={row['unit_price']} {row['currency']}."
            ),
        }.get(
            parsed.lang,
            f"{row['name']}: on_hand={row['on_hand']}, "
            f"unit_price={row['unit_price']} {row['currency']}.",
        )
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=parsed.lang,
            citation_rows=[dict(row)],
            message=msg,
        )

    if parsed.intent == Intent.TOTAL_STOCK_VALUE:
        rows = run_query(conn, "total_stock_value", {})
        if not rows or int(rows[0]["item_count"]) == 0:
            return refuse_no_skus(parsed.lang)
        row = rows[0]
        total_value = int(row["total_value"])
        total_units = int(row["total_units"])
        item_count = int(row["item_count"])
        currency = row.get("currency") or "XAF"
        msg = {
            "en": (
                f"Total inventory: {item_count} products, {total_units} units, "
                f"total value {total_value} {currency}."
            ),
            "fr": (
                f"Inventaire total : {item_count} produits, {total_units} unités, "
                f"valeur totale {total_value} {currency}."
            ),
            "sw": (
                f"Hifadhi yote: bidhaa {item_count}, vitengo {total_units}, "
                f"thamani yote {total_value} {currency}."
            ),
        }.get(
            parsed.lang,
            f"Total inventory value: {total_value} {currency}.",
        )
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=parsed.lang,
            citation_rows=[dict(row)],
            message=msg,
        )

    if parsed.intent == Intent.TOTAL_DEBT:
        rows = run_query(conn, "total_debt", {})
        if not rows or int(rows[0]["customer_count"]) == 0:
            return refuse_no_customers(parsed.lang)
        row = rows[0]
        total_outstanding = int(row["total_outstanding"])
        customer_count = int(row["customer_count"])
        currency = row.get("currency") or "XAF"
        msg = {
            "en": (
                f"Total debt from {customer_count} active customers: "
                f"{total_outstanding} {currency}."
            ),
            "fr": (
                f"Dette totale de {customer_count} clients actifs : "
                f"{total_outstanding} {currency}."
            ),
            "sw": (
                f"Deni la jumla kutoka kwa wateja {customer_count} wanaofanya kazi: "
                f"{total_outstanding} {currency}."
            ),
        }.get(
            parsed.lang,
            f"Total outstanding debt: {total_outstanding} {currency}.",
        )
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=parsed.lang,
            citation_rows=[dict(row)],
            message=msg,
        )

    if parsed.intent == Intent.TOTAL_SUPPLIER_PAYABLES:
        rows = run_query(conn, "total_supplier_payables", {})
        if not rows or int(rows[0]["supplier_count"]) == 0:
            return refuse_no_suppliers(parsed.lang)
        row = rows[0]
        null_count = int(row["null_count"])
        if null_count > 0:
            # Some suppliers have unknown balances. Cannot give a reliable total.
            return refuse_unknown(parsed.lang)
        total_owed = int(row["total_owed"])
        supplier_count = int(row["supplier_count"])
        msg = {
            "en": (
                f"Total owed to {supplier_count} suppliers: "
                f"{total_owed} XAF."
            ),
            "fr": (
                f"Total dû à {supplier_count} fournisseurs : "
                f"{total_owed} XAF."
            ),
            "sw": (
                f"Jumla ya deni kwa wasambazaji {supplier_count}: "
                f"{total_owed} XAF."
            ),
        }.get(
            parsed.lang,
            f"Total supplier payables: {total_owed} XAF.",
        )
        return BinderResult(
            ok=True,
            intent=parsed.intent,
            lang=parsed.lang,
            citation_rows=[dict(row)],
            message=msg,
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
