-- DukaBind ledger schema (Gate 1)
-- Security: app never executes arbitrary SQL from users/LLM — only allowlisted statements in Python.
-- See docs/SECURITY.md controls C1–C4.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS shop_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id     TEXT PRIMARY KEY,
    display_name    TEXT NOT NULL,
    credit_limit    INTEGER,          -- NULL means "not on file" → must refuse credit decisions
    outstanding     INTEGER NOT NULL DEFAULT 0,
    currency        TEXT NOT NULL DEFAULT 'XAF',
    status          TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'blocked', 'pending')),
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id     TEXT PRIMARY KEY,
    display_name    TEXT NOT NULL,
    balance_owed    INTEGER,          -- NULL → refuse payment-amount answers
    last_invoice_at TEXT,
    status          TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'pending_confirmation', 'blocked')),
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS skus (
    sku_id      TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    unit_price  INTEGER NOT NULL CHECK (unit_price >= 0),
    on_hand     INTEGER NOT NULL DEFAULT 0 CHECK (on_hand >= 0),
    currency    TEXT NOT NULL DEFAULT 'XAF',
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    lang       TEXT NOT NULL,
    intent     TEXT NOT NULL,
    ok         INTEGER NOT NULL,      -- 1 answer, 0 refuse
    detail     TEXT NOT NULL,
    citation   TEXT                   -- JSON citation block or null
);

CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(display_name);
CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(display_name);
CREATE INDEX IF NOT EXISTS idx_skus_name ON skus(name);
