from decimal import Decimal
from sqlalchemy import select, func
from src.models.accounting import AccountMove, AccountMoveLine
from src.core.database import get_db


class LedgerService:
    @staticmethod
    async def validate_double_entry(db, move_lines: list[dict]) -> None:
        total_debit = sum(Decimal(str(line.get("debit", 0))) for line in move_lines)
        total_credit = sum(Decimal(str(line.get("credit", 0))) for line in move_lines)

        if total_debit != total_credit:
            raise ValueError(
                f"Partida desbalanceada: Débitos={total_debit}, Créditos={total_credit}"
            )

    @staticmethod
    async def get_account_balance(db, tenant_id: int, account_code: str) -> Decimal:
        stmt = (
            select(func.coalesce(func.sum(AccountMoveLine.debit), 0) - func.coalesce(func.sum(AccountMoveLine.credit), 0))
            .join(AccountMove, AccountMoveLine.move_id == AccountMove.id)
            .where(AccountMove.tenant_id == tenant_id)
            .where(AccountMoveLine.account_id == account_code)
            .where(AccountMove.state == "posted")
        )
        result = await db.execute(stmt)
        return result.scalar_one() or Decimal("0.00")