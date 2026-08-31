from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Text, Index, JSON
from sqlalchemy.sql import func
from src.models.base import Base


class AccountAccount(Base):
    __tablename__ = "account_accounts"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    code_store = Column(JSON, nullable=False)  # JSONB real de Odoo
    name = Column(Text, nullable=False)
    account_type = Column(String(50), nullable=True)
    deprecated = Column(Boolean, nullable=False, default=False)
    reconcile = Column(Boolean, nullable=False, default=False)
    currency_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("uq_account_accounts_tenant_code", "tenant_id", "code_store", unique=True, postgresql_using="gin"),
    )


class AccountJournal(Base):
    __tablename__ = "account_journals"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("uq_account_journals_tenant_code", "tenant_id", "code", unique=True),
    )


class AccountMove(Base):
    __tablename__ = "account_moves"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    ref = Column(String(100), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    state = Column(String(20), nullable=False, default="draft")
    move_type = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    partner_id = Column(Integer, nullable=True)
    journal_id = Column(Integer, nullable=True)
    currency_id = Column(Integer, nullable=True)
    amount_untaxed = Column(Numeric(19, 2), nullable=False, default=0)
    amount_tax = Column(Numeric(19, 2), nullable=False, default=0)
    amount_total = Column(Numeric(19, 2), nullable=False, default=0)
    amount_residual = Column(Numeric(19, 2), nullable=False, default=0)
    invoice_date = Column(DateTime(timezone=True), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    authorization_id = Column(Integer, nullable=True)
    timbrado_id = Column(Integer, nullable=True)
    fiscal_document = Column(Boolean, nullable=False, default=False)
    is_ed = Column(Boolean, nullable=False, default=False)
    is_ed_cancelled = Column(Boolean, nullable=False, default=False)
    res90_tipo_identificacion = Column(String(10), nullable=True)
    res90_tipo_comprobante = Column(String(10), nullable=True)
    res90_nro_timbrado = Column(String(50), nullable=True)
    res90_nro_comprobante_asociado = Column(String(50), nullable=True)
    res90_timbrado_comprobante_asociado = Column(String(50), nullable=True)
    res90_imputa_iva = Column(Boolean, nullable=True)
    res90_imputa_ire = Column(Boolean, nullable=True)
    res90_imputa_irp_rsp = Column(Boolean, nullable=True)
    res90_no_imputa = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_account_moves_tenant_state", "tenant_id", "state"),
        Index("ix_account_moves_tenant_type", "tenant_id", "move_type"),
    )


class AccountMoveLine(Base):
    __tablename__ = "account_move_lines"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    move_id = Column(Integer, nullable=False, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    partner_id = Column(Integer, nullable=True)
    name = Column(Text, nullable=True)
    quantity = Column(Numeric(19, 2), nullable=False, default=1)
    price_unit = Column(Numeric(19, 2), nullable=False, default=0)
    price_total = Column(Numeric(19, 2), nullable=False, default=0)
    debit = Column(Numeric(19, 2), nullable=False, default=0)
    credit = Column(Numeric(19, 2), nullable=False, default=0)
    tax_base_amount = Column(Numeric(19, 2), nullable=False, default=0)
    tax_line_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_account_move_lines_tenant", "tenant_id"),
        Index("ix_account_move_lines_move", "move_id"),
    )


class AccountTax(Base):
    __tablename__ = "account_taxes"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    amount = Column(Numeric(5, 2), nullable=False)
    type_tax_use = Column(String(20), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("uq_account_taxes_tenant_name", "tenant_id", "name", unique=True),
    )


class PartnerLedger(Base):
    __tablename__ = "partner_ledgers"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    partner_id = Column(Integer, nullable=False, index=True)
    opening_balance = Column(Numeric(19, 2), nullable=False, default=0)
    current_balance = Column(Numeric(19, 2), nullable=False, default=0)
    credit_limit = Column(Numeric(19, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("uq_partner_ledgers_tenant_partner", "tenant_id", "partner_id", unique=True),
    )


class AccountMappingRule(Base):
    __tablename__ = "account_mapping_rules"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    external_code = Column(String(100), nullable=False)
    canonical_code = Column(String(100), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TenantSchemaVersion(Base):
    __tablename__ = "tenant_schema_version"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    schema_version = Column(String(50), nullable=False)
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("uq_tenant_schema_version_tenant", "tenant_id", unique=True),
    )


class Authorization(Base):
    __tablename__ = "authorizations"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    stamped = Column(String(50), nullable=True)
    date_to = Column(DateTime(timezone=True), nullable=True)
    pre_printed_invoice = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)