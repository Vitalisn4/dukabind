-- Marché Akwa Viviane (Akwa, Douala · XAF).
-- Keep names in sync with app/db/fixture.py.
-- Esther Tchamba: NULL credit_limit forces a credit refusal.
-- SOCA Distribution Douala: NULL balance_owed forces a payable refusal.

INSERT OR REPLACE INTO shop_meta(key, value) VALUES
  ('shop_name', 'Marché Akwa Viviane'),
  ('fixture_id', 'marche_akwa'),
  ('as_of', '2026-07-25'),
  ('neighbourhood', 'Akwa, Douala'),
  ('currency', 'XAF');

INSERT OR REPLACE INTO customers(customer_id, display_name, credit_limit, outstanding, currency, status, updated_at) VALUES
  ('cust_fotso',   'Marie-Claire Fotso', 8000, 6250, 'XAF', 'active', '2026-07-25T10:00:00Z'),
  ('cust_njoya',   'Ibrahim Njoya',     15000, 2000, 'XAF', 'active', '2026-07-25T10:00:00Z'),
  ('cust_tchamba', 'Esther Tchamba',     NULL,  500,  'XAF', 'active', '2026-07-25T10:00:00Z');

INSERT OR REPLACE INTO suppliers(supplier_id, display_name, balance_owed, last_invoice_at, status, updated_at) VALUES
  ('sup_soca',      'SOCA Distribution Douala',     NULL,  '2026-07-20', 'pending_confirmation', '2026-07-25T10:00:00Z'),
  ('sup_portuaire', 'Grosserie Portuaire Bonaberi', 42000, '2026-07-18', 'active',               '2026-07-25T10:00:00Z');

INSERT OR REPLACE INTO skus(sku_id, name, unit_price, on_hand, currency, updated_at) VALUES
  ('sku_malt',  'Caisse boisson malt 300ml', 720,   14, 'XAF', '2026-07-25T10:00:00Z'),
  ('sku_riz',   'Sac riz 25kg',              18500,  6, 'XAF', '2026-07-25T10:00:00Z'),
  ('sku_huile', 'Bidon huile palme 5L',      4500,   0, 'XAF', '2026-07-25T10:00:00Z');
