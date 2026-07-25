-- Synthetic demo shop. Fictional names and balances — never real customer PII.
-- Pauline Ngo and Bidco carry NULL money fields on purpose, to exercise refusals.

INSERT OR REPLACE INTO shop_meta(key, value) VALUES
  ('shop_name', 'Boutique Demo Douala'),
  ('fixture_id', 'duka_a'),
  ('as_of', '2026-07-25');

INSERT OR REPLACE INTO customers(customer_id, display_name, credit_limit, outstanding, currency, status, updated_at) VALUES
  ('cust_amina', 'Amina Wanjiru', 8000, 6250, 'XAF', 'active', '2026-07-25T10:00:00Z'),
  ('cust_jean',  'Jean Mbarga',   15000, 2000, 'XAF', 'active', '2026-07-25T10:00:00Z'),
  ('cust_null',  'Pauline Ngo',   NULL,  500,  'XAF', 'active', '2026-07-25T10:00:00Z');

INSERT OR REPLACE INTO suppliers(supplier_id, display_name, balance_owed, last_invoice_at, status, updated_at) VALUES
  ('sup_bidco', 'Bidco Distributors', NULL, '2026-07-20', 'pending_confirmation', '2026-07-25T10:00:00Z'),
  ('sup_nest',  'Nest Wholesale',     42000, '2026-07-18', 'active', '2026-07-25T10:00:00Z');

INSERT OR REPLACE INTO skus(sku_id, name, unit_price, on_hand, currency, updated_at) VALUES
  ('sku_soda',  'CRATE-SODA-300ML', 720, 14, 'XAF', '2026-07-25T10:00:00Z'),
  ('sku_rice',  'BAG-RICE-25KG',    18500, 6, 'XAF', '2026-07-25T10:00:00Z'),
  ('sku_oil',   'JERRY-OIL-5L',     4500,  0, 'XAF', '2026-07-25T10:00:00Z');
