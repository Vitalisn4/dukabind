"""Allowlisted SQL — the only queries this program may run (control C1/C2).

Research: OWASP A03 / CWE-89 — never concatenate user text into SQL.
The LLM never sees this module's SQL strings as executable; it only sees
citation JSON produced from query results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import sqlite3


@dataclass(frozen=True)
class AllowlistedQuery:
    name: str
    sql: str
    required_params: tuple[str, ...]


# Finite surface — add new intents by extending this map, never by free-form SQL.
QUERIES: dict[str, AllowlistedQuery] = {
    "customer_credit": AllowlistedQuery(
        name="customer_credit",
        sql="""
            SELECT customer_id, display_name, credit_limit, outstanding, currency, status
            FROM customers
            WHERE lower(display_name) = lower(?)
               OR lower(customer_id) = lower(?)
            LIMIT 1
        """,
        required_params=("name", "name"),
    ),
    "supplier_balance": AllowlistedQuery(
        name="supplier_balance",
        sql="""
            SELECT supplier_id, display_name, balance_owed, last_invoice_at, status
            FROM suppliers
            WHERE lower(display_name) = lower(?)
               OR lower(supplier_id) = lower(?)
            LIMIT 1
        """,
        required_params=("name", "name"),
    ),
    "sku_stock": AllowlistedQuery(
        name="sku_stock",
        sql="""
            SELECT sku_id, name, unit_price, on_hand, currency
            FROM skus
            WHERE lower(name) = lower(?)
               OR lower(sku_id) = lower(?)
            LIMIT 1
        """,
        required_params=("name", "name"),
    ),
}


def run_query(
    conn: sqlite3.Connection,
    query_name: str,
    params: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if query_name not in QUERIES:
        raise ValueError(f"query not allowlisted: {query_name}")
    q = QUERIES[query_name]
    # Same user-facing name bound twice for OR match on id/display — still parameterized.
    values = tuple(params[p] for p in q.required_params)
    cur = conn.execute(q.sql, values)
    rows = cur.fetchall()
    return [dict(r) for r in rows]
