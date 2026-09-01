from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional
from src.core.database import get_db
from src.core.security import get_tenant_id
from src.schemas.fiscal_report_dto import ReportQueryDTO, FiscalReportResponseDTO
from src.services.fiscal_report_service import FiscalReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales-book", response_model=FiscalReportResponseDTO)
async def sales_book(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    fiscal_year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
):
    if not any([from_date, fiscal_year, month]):
        raise HTTPException(status_code=400, detail="Se requiere from_date, fiscal_year o month")

    try:
        result = await FiscalReportService.get_sales_book(
            db, tenant_id, from_date, to_date, fiscal_year, month
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")

    return FiscalReportResponseDTO(**result)


@router.get("/purchases-book", response_model=FiscalReportResponseDTO)
async def purchases_book(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    fiscal_year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
):
    if not any([from_date, fiscal_year, month]):
        raise HTTPException(status_code=400, detail="Se requiere from_date, fiscal_year o month")

    try:
        result = await FiscalReportService.get_purchases_book(
            db, tenant_id, from_date, to_date, fiscal_year, month
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")

    return FiscalReportResponseDTO(**result)


@router.get("/aivi", response_model=FiscalReportResponseDTO)
async def aivi_report(
    fiscal_year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    try:
        result = await FiscalReportService.get_aivi_report(db, tenant_id, fiscal_year, month)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")

    return FiscalReportResponseDTO(**result)


@router.get("/0251", response_model=FiscalReportResponseDTO)
async def report_0251(
    fiscal_year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    try:
        result = await FiscalReportService.get_0251_report(db, tenant_id, fiscal_year, month)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando reporte: {str(e)}")

    return FiscalReportResponseDTO(**result)