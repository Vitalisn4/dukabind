"""Allowlisted SQL. These are the only queries this program may run (controls C1/C2).

User and model text is never concatenated into SQL; callers pass a query name
and bound parameters only.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AllowlistedQuery:
    """One named, parameterized SQL statement the binder may execute."""

    name: str
    sql: str
    required_params: tuple[str, ...]


# Extend this map for new intents. Never assemble SQL at call sites.
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
    missing = [p for p in dict.fromkeys(q.required_params) if p not in params]
    if missing:
        raise ValueError(f"missing params for {query_name}: {missing}")
    # required_params may repeat a key (display_name OR id bind uses the same value twice).
    values = tuple(params[p] for p in q.required_params)
    cur = conn.execute(q.sql, values)
    rows = cur.fetchall()
    return [dict(r) for r in rows]
