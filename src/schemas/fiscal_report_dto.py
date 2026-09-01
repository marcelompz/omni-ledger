from pydantic import BaseModel
from datetime import date
from typing import Optional


class ReportQueryDTO(BaseModel):
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    fiscal_year: Optional[int] = None
    month: Optional[int] = None


class FiscalReportResponseDTO(BaseModel):
    report_type: str
    tenant_id: int
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    fiscal_year: Optional[int] = None
    month: Optional[int] = None
    total_records: int
    totals: dict
    records: list