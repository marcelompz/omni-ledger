-- OmniLedger baseline schema (v18-compat)
-- FEAT-105: 8 tablas canónicas + RLS obligatorio desde el primer CREATE TABLE
-- Adaptado al schema real de Odoo prod_16_08_2026

CREATE TABLE IF NOT EXISTS account_accounts (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  code_store JSONB NOT NULL,
  name TEXT NOT NULL,
  account_type VARCHAR(50),
  deprecated BOOLEAN NOT NULL DEFAULT FALSE,
  reconcile BOOLEAN NOT NULL DEFAULT FALSE,
  currency_id INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS account_journals (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  code VARCHAR(50) NOT NULL,
  name VARCHAR(200) NOT NULL,
  type VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS account_moves (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  name VARCHAR(100),
  ref VARCHAR(100),
  date TIMESTAMP NOT NULL,
  state VARCHAR(20) NOT NULL DEFAULT 'draft',
  move_type VARCHAR(20) NOT NULL,
  description TEXT,
  partner_id INTEGER,
  journal_id INTEGER,
  currency_id INTEGER,
  amount_untaxed NUMERIC(19,2) NOT NULL DEFAULT 0,
  amount_tax NUMERIC(19,2) NOT NULL DEFAULT 0,
  amount_total NUMERIC(19,2) NOT NULL DEFAULT 0,
  amount_residual NUMERIC(19,2) NOT NULL DEFAULT 0,
  invoice_date TIMESTAMP,
  invoice_number VARCHAR(100),
  authorization_id INTEGER,
  timbrado_id INTEGER,
  fiscal_document BOOLEAN NOT NULL DEFAULT FALSE,
  is_ed BOOLEAN NOT NULL DEFAULT FALSE,
  is_ed_cancelled BOOLEAN NOT NULL DEFAULT FALSE,
  res90_tipo_identificacion VARCHAR(10),
  res90_tipo_comprobante VARCHAR(10),
  res90_nro_timbrado VARCHAR(50),
  res90_nro_comprobante_asociado VARCHAR(50),
  res90_timbrado_comprobante_asociado VARCHAR(50),
  res90_imputa_iva BOOLEAN,
  res90_imputa_ire BOOLEAN,
  res90_imputa_irp_rsp BOOLEAN,
  res90_no_imputa BOOLEAN,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS account_move_lines (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  move_id INTEGER NOT NULL,
  account_id INTEGER NOT NULL,
  partner_id INTEGER,
  name TEXT,
  quantity NUMERIC(19,2) NOT NULL DEFAULT 1,
  price_unit NUMERIC(19,2) NOT NULL DEFAULT 0,
  price_total NUMERIC(19,2) NOT NULL DEFAULT 0,
  debit NUMERIC(19,2) NOT NULL DEFAULT 0,
  credit NUMERIC(19,2) NOT NULL DEFAULT 0,
  tax_base_amount NUMERIC(19,2) NOT NULL DEFAULT 0,
  tax_line_id INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS account_taxes (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  name VARCHAR(200) NOT NULL,
  amount NUMERIC(5,2) NOT NULL,
  type_tax_use VARCHAR(20) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_ledgers (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  partner_id INTEGER NOT NULL,
  opening_balance NUMERIC(19,2) NOT NULL DEFAULT 0,
  current_balance NUMERIC(19,2) NOT NULL DEFAULT 0,
  credit_limit NUMERIC(19,2),
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS account_mapping_rules (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  external_code VARCHAR(100) NOT NULL,
  canonical_code VARCHAR(100) NOT NULL,
  valid_from TIMESTAMP NOT NULL,
  valid_to TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_schema_version (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  schema_version VARCHAR(50) NOT NULL,
  applied_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS authorizations (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  name VARCHAR(200),
  stamped VARCHAR(50),
  date_to TIMESTAMP,
  pre_printed_invoice BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Unique constraints
CREATE UNIQUE INDEX IF NOT EXISTS uq_account_journals_tenant_code ON account_journals(tenant_id, code);
CREATE UNIQUE INDEX IF NOT EXISTS uq_account_taxes_tenant_name ON account_taxes(tenant_id, name);
CREATE UNIQUE INDEX IF NOT EXISTS uq_partner_ledgers_tenant_partner ON partner_ledgers(tenant_id, partner_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_tenant_schema_version_tenant ON tenant_schema_version(tenant_id);

-- RLS policies
ALTER TABLE account_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_journals ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_moves ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_move_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_taxes ENABLE ROW LEVEL SECURITY;
ALTER TABLE partner_ledgers ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_mapping_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_schema_version ENABLE ROW LEVEL SECURITY;
ALTER TABLE authorizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_account_accounts ON account_accounts FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_journals ON account_journals FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_moves ON account_moves FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_move_lines ON account_move_lines FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_taxes ON account_taxes FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_partner_ledgers ON partner_ledgers FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_mapping_rules ON account_mapping_rules FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_tenant_schema_version ON tenant_schema_version FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_authorizations ON authorizations FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);