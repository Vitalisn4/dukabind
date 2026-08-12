-- Marché Nkolmébé (Nkolmébé, Yaoundé · XAF), second shop fixture.
-- Distinct names/balances/stock from seed.sql (anti-memorization held-out proof).
-- Keep names in sync with app/db/fixture.py.
-- Maman Rachel: NULL credit_limit forces a credit refusal.
-- Ciment du Cameroun: NULL balance_owed forces a payable refusal.

INSERT OR REPLACE INTO shop_meta(key, value) VALUES
  ('shop_name', 'Marché Nkolmébé'),
  ('fixture_id', 'duka_b'),
  ('as_of', '2026-08-06'),
  ('neighbourhood', 'Nkolmébé, Yaoundé'),
  ('currency', 'XAF');

INSERT OR REPLACE INTO customers(customer_id, display_name, credit_limit, outstanding, currency, status, updated_at) VALUES
  ('cust_bello',  'Amina Bello',  25000, 9800, 'XAF', 'active', '2026-08-06T08:00:00Z'),
  ('cust_okafor', 'Chidi Okafor', 12000, 4000, 'XAF', 'active', '2026-08-06T08:00:00Z'),
  ('cust_rachel', 'Maman Rachel',   NULL,    0, 'XAF', 'active', '2026-08-06T08:00:00Z');

INSERT OR REPLACE INTO suppliers(supplier_id, display_name, balance_owed, last_invoice_at, status, updated_at) VALUES
  ('sup_sanaga',   'Sanaga Épicerie',    15500, '2026-08-04', 'active',               '2026-08-06T08:00:00Z'),
  ('sup_cimencam', 'Ciment du Cameroun',   NULL, '2026-08-02', 'pending_confirmation', '2026-08-06T08:00:00Z');

INSERT OR REPLACE INTO skus(sku_id, name, unit_price, on_hand, currency, updated_at) VALUES
  ('sku_sucre',  'Sucre 25kg',     13500, 4, 'XAF', '2026-08-06T08:00:00Z'),
  ('sku_savon',  'Savon carton 24', 9800, 0, 'XAF', '2026-08-06T08:00:00Z'),
  ('sku_farine', 'Farine 50kg',    22000, 9, 'XAF', '2026-08-06T08:00:00Z');
