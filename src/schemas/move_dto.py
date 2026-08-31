from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional, List


class MoveLineDTO(BaseModel):
    account_id: int
    name: Optional[str] = None
    quantity: Decimal = Decimal("1")
    price_unit: Decimal = Decimal("0")
    price_total: Decimal = Decimal("0")
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    tax_base_amount: Decimal = Decimal("0")
    tax_line_id: Optional[int] = None


class MoveCreateDTO(BaseModel):
    name: Optional[str] = None
    ref: Optional[str] = None
    date: datetime
    state: str = "draft"
    move_type: str = "out_invoice"
    description: Optional[str] = None
    partner_id: Optional[int] = None
    journal_id: Optional[int] = None
    currency_id: Optional[int] = None
    amount_untaxed: Decimal = Decimal("0")
    amount_tax: Decimal = Decimal("0")
    amount_total: Decimal = Decimal("0")
    amount_residual: Decimal = Decimal("0")
    invoice_date: Optional[datetime] = None
    invoice_number: Optional[str] = None
    authorization_id: Optional[int] = None
    timbrado_id: Optional[int] = None
    fiscal_document: bool = False
    is_ed: bool = False
    is_ed_cancelled: bool = False
    res90_tipo_identificacion: Optional[str] = None
    res90_tipo_comprobante: Optional[str] = None
    res90_nro_timbrado: Optional[str] = None
    res90_nro_comprobante_asociado: Optional[str] = None
    res90_timbrado_comprobante_asociado: Optional[str] = None
    res90_imputa_iva: Optional[bool] = None
    res90_imputa_ire: Optional[bool] = None
    res90_imputa_irp_rsp: Optional[bool] = None
    res90_no_imputa: Optional[bool] = None
    lines: List[MoveLineDTO]


class MoveResponseDTO(BaseModel):
    id: int
    name: Optional[str]
    ref: Optional[str]
    date: datetime
    state: str
    move_type: str
    description: Optional[str]
    partner_id: Optional[int]
    amount_total: Decimal
    amount_tax: Decimal
    amount_untaxed: Decimal
    invoice_date: Optional[datetime]
    invoice_number: Optional[str]
    fiscal_document: bool
    is_ed: bool
    created_at: datetime


class MovePostDTO(BaseModel):
    id: int


class MoveReverseDTO(BaseModel):
    id: int
    reason: Optional[str] = None