from decimal import Decimal, ROUND_HALF_EVEN
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.accounting import AccountMove, AccountMoveLine, AccountTax, PartnerLedger


class DoubleEntryValidationError(Exception):
    pass


class LedgerService:
    @staticmethod
    def quantize(amount: Decimal) -> Decimal:
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

    @staticmethod
    async def validate_double_entry(db: AsyncSession, move_lines: list, tenant_id: int) -> None:
        total_debit = sum(
            LedgerService.quantize(Decimal(str(line.get("debit", 0) if isinstance(line, dict) else line.debit)))
            for line in move_lines
        )
        total_credit = sum(
            LedgerService.quantize(Decimal(str(line.get("credit", 0) if isinstance(line, dict) else line.credit)))
            for line in move_lines
        )

        if total_debit != total_credit:
            raise DoubleEntryValidationError(
                f"Partida desbalanceada: Débitos={total_debit}, Créditos={total_credit}"
            )

    @staticmethod
    async def get_account_balance(db: AsyncSession, tenant_id: int, account_code: str) -> Decimal:
        stmt = (
            select(
                func.coalesce(func.sum(AccountMoveLine.debit), 0)
                - func.coalesce(func.sum(AccountMoveLine.credit), 0)
            )
            .join(AccountMove, AccountMoveLine.move_id == AccountMove.id)
            .where(AccountMove.tenant_id == tenant_id)
            .where(AccountMoveLine.account_id == account_code)
            .where(AccountMove.state == "posted")
        )
        result = await db.execute(stmt)
        return LedgerService.quantize(result.scalar_one() or Decimal("0.00"))

    @staticmethod
    async def post_move(db: AsyncSession, move_id: int, tenant_id: int) -> AccountMove:
        stmt = select(AccountMove).where(AccountMove.id == move_id, AccountMove.tenant_id == tenant_id)
        result = await db.execute(stmt)
        move = result.scalar_one_or_none()

        if not move:
            raise ValueError("Asiento no encontrado")

        if move.state != "draft":
            raise ValueError(f"Asiento en estado {move.state}, no se puede publicar")

        lines_stmt = select(AccountMoveLine).where(AccountMoveLine.move_id == move_id)
        lines_result = await db.execute(lines_stmt)
        lines = lines_result.scalars().all()

        move_lines_dicts = [
            {"debit": line.debit, "credit": line.credit}
            for line in lines
        ]
        await LedgerService.validate_double_entry(db, move_lines_dicts, tenant_id)

        move.state = "posted"
        await db.commit()
        await db.refresh(move)
        return move

    @staticmethod
    async def reverse_move(db: AsyncSession, move_id: int, tenant_id: int, reason: Optional[str] = None) -> AccountMove:
        stmt = select(AccountMove).where(AccountMove.id == move_id, AccountMove.tenant_id == tenant_id)
        result = await db.execute(stmt)
        original_move = result.scalar_one_or_none()

        if not original_move:
            raise ValueError("Asiento original no encontrado")

        if original_move.state != "posted":
            raise ValueError("Solo se pueden revertir asientos publicados")

        reversal_move = AccountMove(
            tenant_id=tenant_id,
            name=f"REV-{original_move.name or original_move.id}",
            ref=f"Reversión de {original_move.ref or original_move.id}",
            date=func.now(),
            state="posted",
            move_type=original_move.move_type,
            description=reason or f"Reversión de asiento {move_id}",
            partner_id=original_move.partner_id,
            journal_id=original_move.journal_id,
            currency_id=original_move.currency_id,
            amount_untaxed=original_move.amount_untaxed,
            amount_tax=original_move.amount_tax,
            amount_total=original_move.amount_total,
            amount_residual=original_move.amount_residual,
        )
        db.add(reversal_move)
        await db.flush()

        lines_stmt = select(AccountMoveLine).where(AccountMoveLine.move_id == move_id)
        lines_result = await db.execute(lines_stmt)
        original_lines = lines_result.scalars().all()

        for line in original_lines:
            reversal_line = AccountMoveLine(
                tenant_id=tenant_id,
                move_id=reversal_move.id,
                account_id=line.account_id,
                partner_id=line.partner_id,
                name=line.name,
                quantity=line.quantity,
                price_unit=line.price_unit,
                price_total=line.price_total,
                debit=line.credit,
                credit=line.debit,
                tax_base_amount=line.tax_base_amount,
                tax_line_id=line.tax_line_id,
            )
            db.add(reversal_line)

        await db.commit()
        await db.refresh(reversal_move)
        return reversal_move