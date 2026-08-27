from sqlalchemy import Column, Integer, String, Numeric, DateTime, Index
from sqlalchemy.sql import func
from src.models.base import Base


class AccountAccount(Base):
    __tablename__ = "account_accounts"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    code = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, nullable=True)
    level = Column(Integer, nullable=False, default=0)
    account_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("uq_account_accounts_tenant_code", "tenant_id", "code", unique=True),
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
    ref = Column(String(100), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)
    state = Column(String(20), nullable=False, default="draft")
    description = Column(String(500), nullable=True)
    partner_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_account_moves_tenant_state", "tenant_id", "state"),
    )


class AccountMoveLine(Base):
    __tablename__ = "account_move_lines"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    move_id = Column(Integer, nullable=False, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    partner_id = Column(Integer, nullable=True)
    debit = Column(Numeric(19, 2), nullable=False, default=0)
    credit = Column(Numeric(19, 2), nullable=False, default=0)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_account_move_lines_tenant", "tenant_id"),
        Index("ix_account_move_lines_move", "move_id"),
    )


class AccountTax(Base):
    __tablename__ = "account_taxes"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    amount = Column(Numeric(5, 2), nullable=False)
    type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("uq_account_taxes_tenant_code", "tenant_id", "code", unique=True),
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