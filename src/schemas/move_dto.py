from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional


class MoveLineDTO(BaseModel):
    account_code: str
    debit: Decimal
    credit: Decimal
    description: Optional[str] = None


class MoveCreateDTO(BaseModel):
    ref: Optional[str] = None
    date: datetime
    state: str = "draft"
    description: Optional[str] = None
    partner_id: Optional[int] = None
    lines: list[MoveLineDTO]


class MoveResponseDTO(BaseModel):
    id: int
    ref: Optional[str]
    date: datetime
    state: str
    description: Optional[str]
    partner_id: Optional[int]
    created_at: datetime