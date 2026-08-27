-- OmniLedger baseline schema (v18-compat)
-- FEAT-105: 8 tablas canónicas + RLS obligatorio desde el primer CREATE TABLE

CREATE TABLE IF NOT EXISTS account_accounts (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  code VARCHAR(100) NOT NULL,
  name VARCHAR(200) NOT NULL,
  parent_id INTEGER,
  level INTEGER NOT NULL DEFAULT 0,
  account_type VARCHAR(50),
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
  ref VARCHAR(100),
  date TIMESTAMP NOT NULL,
  state VARCHAR(20) NOT NULL DEFAULT 'draft',
  description VARCHAR(500),
  partner_id INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT now(),
  updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS account_move_lines (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  move_id INTEGER NOT NULL,
  account_id INTEGER NOT NULL,
  partner_id INTEGER,
  debit NUMERIC(19,2) NOT NULL DEFAULT 0,
  credit NUMERIC(19,2) NOT NULL DEFAULT 0,
  description VARCHAR(500),
  created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS account_taxes (
  id SERIAL PRIMARY KEY,
  tenant_id INTEGER NOT NULL,
  code VARCHAR(50) NOT NULL,
  name VARCHAR(200) NOT NULL,
  amount NUMERIC(5,2) NOT NULL,
  type VARCHAR(20) NOT NULL,
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

-- Unique constraints
CREATE UNIQUE INDEX IF NOT EXISTS uq_account_accounts_tenant_code ON account_accounts(tenant_id, code);
CREATE UNIQUE INDEX IF NOT EXISTS uq_account_journals_tenant_code ON account_journals(tenant_id, code);
CREATE UNIQUE INDEX IF NOT EXISTS uq_account_taxes_tenant_code ON account_taxes(tenant_id, code);
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

CREATE POLICY tenant_isolation_account_accounts ON account_accounts FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_journals ON account_journals FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_moves ON account_moves FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_move_lines ON account_move_lines FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_taxes ON account_taxes FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_partner_ledgers ON partner_ledgers FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_account_mapping_rules ON account_mapping_rules FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);
CREATE POLICY tenant_isolation_tenant_schema_version ON tenant_schema_version FOR ALL TO omniledger_app USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::INTEGER);