from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import get_tenant_id
from src.schemas.move_dto import MoveCreateDTO, MoveResponseDTO
from src.services.ledger_service import LedgerService
from src.models.accounting import AccountMove, AccountMoveLine
from sqlalchemy import insert

router = APIRouter(prefix="/moves", tags=["moves"])


@router.post("", response_model=MoveResponseDTO)
async def create_move(
    dto: MoveCreateDTO,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    await LedgerService.validate_double_entry(db, dto.lines)

    move_stmt = (
        insert(AccountMove)
        .values(
            tenant_id=tenant_id,
            ref=dto.ref,
            date=dto.date,
            state=dto.state,
            description=dto.description,
            partner_id=dto.partner_id,
        )
        .returning(AccountMove)
    )
    result = await db.execute(move_stmt)
    move = result.scalar_one()
    await db.flush()

    for line in dto.lines:
        line_stmt = insert(AccountMoveLine).values(
            tenant_id=tenant_id,
            move_id=move.id,
            account_id=line.account_code,
            debit=line.debit,
            credit=line.credit,
            description=line.description,
        )
        await db.execute(line_stmt)

    await db.commit()
    await db.refresh(move)

    return MoveResponseDTO(
        id=move.id,
        ref=move.ref,
        date=move.date,
        state=move.state,
        description=move.description,
        partner_id=move.partner_id,
        created_at=move.created_at,
    )