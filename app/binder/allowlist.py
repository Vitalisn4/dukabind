"""Allowlisted SQL — the only queries this program may run (controls C1/C2).

User and model text is never concatenated into SQL; callers pass a query name
and bound parameters only.
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


# Add new intents by extending this map — never by building SQL at call sites.
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
    """Execute one allowlisted query; raise ValueError for anything else."""
    if query_name not in QUERIES:
        raise ValueError(f"query not allowlisted: {query_name}")
    q = QUERIES[query_name]
    # `name` repeats in required_params because each query matches display_name OR id.
    values = tuple(params[p] for p in q.required_params)
    cur = conn.execute(q.sql, values)
    rows = cur.fetchall()
    return [dict(r) for r in rows]
