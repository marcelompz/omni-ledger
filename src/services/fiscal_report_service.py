from decimal import Decimal, ROUND_HALF_EVEN
from typing import Optional
from sqlalchemy import select, and_, extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime
from src.models.accounting import AccountMove, AccountMoveLine


class FiscalReportService:
    @staticmethod
    def quantize(amount: Decimal) -> Decimal:
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

    @staticmethod
    async def get_sales_book(
        db: AsyncSession,
        tenant_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        fiscal_year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> list[dict]:
        stmt = (
            select(
                AccountMove.id,
                AccountMove.invoice_date,
                AccountMove.invoice_number,
                AccountMove.partner_id,
                AccountMove.amount_untaxed,
                AccountMove.amount_tax,
                AccountMove.amount_total,
                AccountMove.move_type,
                AccountMove.is_ed,
                AccountMove.fiscal_document,
                AccountMove.timbrado_id,
                AccountMove.res90_tipo_comprobante,
                AccountMove.res90_nro_timbrado,
            )
            .where(AccountMove.tenant_id == tenant_id)
            .where(AccountMove.state == "posted")
            .where(AccountMove.move_type.in_(["out_invoice", "out_refund"]))
            .order_by(AccountMove.invoice_date.asc(), AccountMove.id.asc())
        )

        if fiscal_year:
            stmt = stmt.where(extract("year", AccountMove.invoice_date) == fiscal_year)
        elif from_date and to_date:
            stmt = stmt.where(
                AccountMove.invoice_date >= from_date,
                AccountMove.invoice_date <= to_date,
            )
        elif month and fiscal_year:
            stmt = stmt.where(
                extract("year", AccountMove.invoice_date) == fiscal_year,
                extract("month", AccountMove.invoice_date) == month,
            )

        result = await db.execute(stmt)
        rows = result.all()

        report = []
        totals = {
            "total_untaxed": Decimal("0.00"),
            "total_tax": Decimal("0.00"),
            "total_total": Decimal("0.00"),
        }

        for row in rows:
            totals["total_untaxed"] += FiscalReportService.quantize(Decimal(str(row.amount_untaxed or 0)))
            totals["total_tax"] += FiscalReportService.quantize(Decimal(str(row.amount_tax or 0)))
            totals["total_total"] += FiscalReportService.quantize(Decimal(str(row.amount_total or 0)))

            report.append({
                "id": row.id,
                "invoice_date": row.invoice_date.isoformat() if row.invoice_date else None,
                "invoice_number": row.invoice_number,
                "partner_id": row.partner_id,
                "amount_untaxed": float(FiscalReportService.quantize(Decimal(str(row.amount_untaxed or 0)))),
                "amount_tax": float(FiscalReportService.quantize(Decimal(str(row.amount_tax or 0)))),
                "amount_total": float(FiscalReportService.quantize(Decimal(str(row.amount_total or 0)))),
                "move_type": row.move_type,
                "is_ed": row.is_ed,
                "fiscal_document": row.fiscal_document,
                "timbrado_id": row.timbrado_id,
                "tipo_comprobante": row.res90_tipo_comprobante,
                "nro_timbrado": row.res90_nro_timbrado,
            })

        return {
            "report_type": "libro_ventas",
            "tenant_id": tenant_id,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "fiscal_year": fiscal_year,
            "month": month,
            "total_records": len(report),
            "totals": {k: float(v) for k, v in totals.items()},
            "records": report,
        }

    @staticmethod
    async def get_purchases_book(
        db: AsyncSession,
        tenant_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        fiscal_year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> dict:
        stmt = (
            select(
                AccountMove.id,
                AccountMove.invoice_date,
                AccountMove.invoice_number,
                AccountMove.partner_id,
                AccountMove.amount_untaxed,
                AccountMove.amount_tax,
                AccountMove.amount_total,
                AccountMove.move_type,
                AccountMove.is_ed,
                AccountMove.fiscal_document,
                AccountMove.timbrado_id,
                AccountMove.res90_tipo_comprobante,
                AccountMove.res90_nro_timbrado,
            )
            .where(AccountMove.tenant_id == tenant_id)
            .where(AccountMove.state == "posted")
            .where(AccountMove.move_type.in_(["in_invoice", "in_refund"]))
            .order_by(AccountMove.invoice_date.asc(), AccountMove.id.asc())
        )

        if fiscal_year:
            stmt = stmt.where(extract("year", AccountMove.invoice_date) == fiscal_year)
        elif from_date and to_date:
            stmt = stmt.where(
                AccountMove.invoice_date >= from_date,
                AccountMove.invoice_date <= to_date,
            )
        elif month and fiscal_year:
            stmt = stmt.where(
                extract("year", AccountMove.invoice_date) == fiscal_year,
                extract("month", AccountMove.invoice_date) == month,
            )

        result = await db.execute(stmt)
        rows = result.all()

        report = []
        totals = {
            "total_untaxed": Decimal("0.00"),
            "total_tax": Decimal("0.00"),
            "total_total": Decimal("0.00"),
        }

        for row in rows:
            totals["total_untaxed"] += FiscalReportService.quantize(Decimal(str(row.amount_untaxed or 0)))
            totals["total_tax"] += FiscalReportService.quantize(Decimal(str(row.amount_tax or 0)))
            totals["total_total"] += FiscalReportService.quantize(Decimal(str(row.amount_total or 0)))

            report.append({
                "id": row.id,
                "invoice_date": row.invoice_date.isoformat() if row.invoice_date else None,
                "invoice_number": row.invoice_number,
                "partner_id": row.partner_id,
                "amount_untaxed": float(FiscalReportService.quantize(Decimal(str(row.amount_untaxed or 0)))),
                "amount_tax": float(FiscalReportService.quantize(Decimal(str(row.amount_tax or 0)))),
                "amount_total": float(FiscalReportService.quantize(Decimal(str(row.amount_total or 0)))),
                "move_type": row.move_type,
                "is_ed": row.is_ed,
                "fiscal_document": row.fiscal_document,
                "timbrado_id": row.timbrado_id,
                "tipo_comprobante": row.res90_tipo_comprobante,
                "nro_timbrado": row.res90_nro_timbrado,
            })

        return {
            "report_type": "libro_compras",
            "tenant_id": tenant_id,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "fiscal_year": fiscal_year,
            "month": month,
            "total_records": len(report),
            "totals": {k: float(v) for k, v in totals.items()},
            "records": report,
        }

    @staticmethod
    async def get_aivi_report(
        db: AsyncSession,
        tenant_id: int,
        fiscal_year: int,
        month: int,
    ) -> dict:
        stmt = (
            select(
                AccountMove.id,
                AccountMove.invoice_date,
                AccountMove.invoice_number,
                AccountMove.partner_id,
                AccountMove.amount_untaxed,
                AccountMove.amount_tax,
                AccountMove.amount_total,
                AccountMove.move_type,
                AccountMove.is_ed,
            )
            .where(AccountMove.tenant_id == tenant_id)
            .where(AccountMove.state == "posted")
            .where(AccountMove.move_type == "out_invoice")
            .where(extract("year", AccountMove.invoice_date) == fiscal_year)
            .where(extract("month", AccountMove.invoice_date) == month)
            .order_by(AccountMove.invoice_date.asc(), AccountMove.id.asc())
        )

        result = await db.execute(stmt)
        rows = result.all()

        report = []
        totals = {
            "total_untaxed": Decimal("0.00"),
            "total_tax": Decimal("0.00"),
            "total_total": Decimal("0.00"),
        }

        for row in rows:
            totals["total_untaxed"] += FiscalReportService.quantize(Decimal(str(row.amount_untaxed or 0)))
            totals["total_tax"] += FiscalReportService.quantize(Decimal(str(row.amount_tax or 0)))
            totals["total_total"] += FiscalReportService.quantize(Decimal(str(row.amount_total or 0)))

            report.append({
                "id": row.id,
                "invoice_date": row.invoice_date.isoformat() if row.invoice_date else None,
                "invoice_number": row.invoice_number,
                "partner_id": row.partner_id,
                "amount_untaxed": float(FiscalReportService.quantize(Decimal(str(row.amount_untaxed or 0)))),
                "amount_tax": float(FiscalReportService.quantize(Decimal(str(row.amount_tax or 0)))),
                "amount_total": float(FiscalReportService.quantize(Decimal(str(row.amount_total or 0)))),
                "move_type": row.move_type,
                "is_ed": row.is_ed,
            })

        return {
            "report_type": "aivi",
            "tenant_id": tenant_id,
            "fiscal_year": fiscal_year,
            "month": month,
            "total_records": len(report),
            "totals": {k: float(v) for k, v in totals.items()},
            "records": report,
        }

    @staticmethod
    async def get_0251_report(
        db: AsyncSession,
        tenant_id: int,
        fiscal_year: int,
        month: int,
    ) -> dict:
        stmt = (
            select(
                AccountMove.id,
                AccountMove.invoice_date,
                AccountMove.invoice_number,
                AccountMove.partner_id,
                AccountMove.amount_untaxed,
                AccountMove.amount_tax,
                AccountMove.amount_total,
                AccountMove.move_type,
                AccountMove.is_ed,
                AccountMove.res90_tipo_comprobante,
                AccountMove.res90_nro_timbrado,
            )
            .where(AccountMove.tenant_id == tenant_id)
            .where(AccountMove.state == "posted")
            .where(AccountMove.move_type.in_(["out_invoice", "out_refund"]))
            .where(extract("year", AccountMove.invoice_date) == fiscal_year)
            .where(extract("month", AccountMove.invoice_date) == month)
            .order_by(AccountMove.invoice_date.asc(), AccountMove.id.asc())
        )

        result = await db.execute(stmt)
        rows = result.all()

        report = []
        totals = {
            "total_untaxed": Decimal("0.00"),
            "total_tax": Decimal("0.00"),
            "total_total": Decimal("0.00"),
        }

        for row in rows:
            totals["total_untaxed"] += FiscalReportService.quantize(Decimal(str(row.amount_untaxed or 0)))
            totals["total_tax"] += FiscalReportService.quantize(Decimal(str(row.amount_tax or 0)))
            totals["total_total"] += FiscalReportService.quantize(Decimal(str(row.amount_total or 0)))

            report.append({
                "id": row.id,
                "invoice_date": row.invoice_date.isoformat() if row.invoice_date else None,
                "invoice_number": row.invoice_number,
                "partner_id": row.partner_id,
                "amount_untaxed": float(FiscalReportService.quantize(Decimal(str(row.amount_untaxed or 0)))),
                "amount_tax": float(FiscalReportService.quantize(Decimal(str(row.amount_tax or 0)))),
                "amount_total": float(FiscalReportService.quantize(Decimal(str(row.amount_total or 0)))),
                "move_type": row.move_type,
                "is_ed": row.is_ed,
                "tipo_comprobante": row.res90_tipo_comprobante,
                "nro_timbrado": row.res90_nro_timbrado,
            })

        return {
            "report_type": "0251",
            "tenant_id": tenant_id,
            "fiscal_year": fiscal_year,
            "month": month,
            "total_records": len(report),
            "totals": {k: float(v) for k, v in totals.items()},
            "records": report,
        }