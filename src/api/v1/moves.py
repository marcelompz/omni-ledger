from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from src.core.database import get_db
from src.core.security import get_tenant_id
from src.schemas.move_dto import MoveCreateDTO, MoveResponseDTO, MovePostDTO, MoveReverseDTO
from src.services.ledger_service import LedgerService, DoubleEntryValidationError
from src.models.accounting import AccountMove, AccountMoveLine

router = APIRouter(prefix="/moves", tags=["moves"])


@router.post("", response_model=MoveResponseDTO)
async def create_move(
    dto: MoveCreateDTO,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    try:
        await LedgerService.validate_double_entry(db, dto.lines, tenant_id)
    except DoubleEntryValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    move = AccountMove(
        tenant_id=tenant_id,
        name=dto.name,
        ref=dto.ref,
        date=dto.date,
        state=dto.state,
        move_type=dto.move_type,
        description=dto.description,
        partner_id=dto.partner_id,
        journal_id=dto.journal_id,
        currency_id=dto.currency_id,
        amount_untaxed=dto.amount_untaxed,
        amount_tax=dto.amount_tax,
        amount_total=dto.amount_total,
        amount_residual=dto.amount_residual,
        invoice_date=dto.invoice_date,
        invoice_number=dto.invoice_number,
        authorization_id=dto.authorization_id,
        timbrado_id=dto.timbrado_id,
        fiscal_document=dto.fiscal_document,
        is_ed=dto.is_ed,
        is_ed_cancelled=dto.is_ed_cancelled,
        res90_tipo_identificacion=dto.res90_tipo_identificacion,
        res90_tipo_comprobante=dto.res90_tipo_comprobante,
        res90_nro_timbrado=dto.res90_nro_timbrado,
        res90_nro_comprobante_asociado=dto.res90_nro_comprobante_asociado,
        res90_timbrado_comprobante_asociado=dto.res90_timbrado_comprobante_asociado,
        res90_imputa_iva=dto.res90_imputa_iva,
        res90_imputa_ire=dto.res90_imputa_ire,
        res90_imputa_irp_rsp=dto.res90_imputa_irp_rsp,
        res90_no_imputa=dto.res90_no_imputa,
    )
    db.add(move)
    await db.flush()

    for line in dto.lines:
        move_line = AccountMoveLine(
            tenant_id=tenant_id,
            move_id=move.id,
            account_id=line.account_id,
            partner_id=dto.partner_id,
            name=line.name,
            quantity=line.quantity,
            price_unit=line.price_unit,
            price_total=line.price_total,
            debit=line.debit,
            credit=line.credit,
            tax_base_amount=line.tax_base_amount,
            tax_line_id=line.tax_line_id,
        )
        db.add(move_line)

    await db.commit()
    await db.refresh(move)

    return MoveResponseDTO(
        id=move.id,
        name=move.name,
        ref=move.ref,
        date=move.date,
        state=move.state,
        move_type=move.move_type,
        description=move.description,
        partner_id=move.partner_id,
        amount_total=move.amount_total,
        amount_tax=move.amount_tax,
        amount_untaxed=move.amount_untaxed,
        invoice_date=move.invoice_date,
        invoice_number=move.invoice_number,
        fiscal_document=move.fiscal_document,
        is_ed=move.is_ed,
        created_at=move.created_at,
    )


@router.post("/{move_id}/post", response_model=MoveResponseDTO)
async def post_move(
    move_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    try:
        move = await LedgerService.post_move(db, move_id, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MoveResponseDTO(
        id=move.id,
        name=move.name,
        ref=move.ref,
        date=move.date,
        state=move.state,
        move_type=move.move_type,
        description=move.description,
        partner_id=move.partner_id,
        amount_total=move.amount_total,
        amount_tax=move.amount_tax,
        amount_untaxed=move.amount_untaxed,
        invoice_date=move.invoice_date,
        invoice_number=move.invoice_number,
        fiscal_document=move.fiscal_document,
        is_ed=move.is_ed,
        created_at=move.created_at,
    )


@router.post("/{move_id}/reverse", response_model=MoveResponseDTO)
async def reverse_move(
    move_id: int,
    dto: MoveReverseDTO,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    try:
        reversal = await LedgerService.reverse_move(db, move_id, tenant_id, dto.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MoveResponseDTO(
        id=reversal.id,
        name=reversal.name,
        ref=reversal.ref,
        date=reversal.date,
        state=reversal.state,
        move_type=reversal.move_type,
        description=reversal.description,
        partner_id=reversal.partner_id,
        amount_total=reversal.amount_total,
        amount_tax=reversal.amount_tax,
        amount_untaxed=reversal.amount_untaxed,
        invoice_date=reversal.invoice_date,
        invoice_number=reversal.invoice_number,
        fiscal_document=reversal.fiscal_document,
        is_ed=reversal.is_ed,
        created_at=reversal.created_at,
    )


@router.get("", response_model=list[MoveResponseDTO])
async def list_moves(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    state: Optional[str] = Query(None),
    partner_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    stmt = select(AccountMove).where(AccountMove.tenant_id == tenant_id)

    if state:
        stmt = stmt.where(AccountMove.state == state)
    if partner_id:
        stmt = stmt.where(AccountMove.partner_id == partner_id)

    stmt = stmt.order_by(desc(AccountMove.date)).limit(limit).offset(offset)
    result = await db.execute(stmt)
    moves = result.scalars().all()

    return [
        MoveResponseDTO(
            id=move.id,
            name=move.name,
            ref=move.ref,
            date=move.date,
            state=move.state,
            move_type=move.move_type,
            description=move.description,
            partner_id=move.partner_id,
            amount_total=move.amount_total,
            amount_tax=move.amount_tax,
            amount_untaxed=move.amount_untaxed,
            invoice_date=move.invoice_date,
            invoice_number=move.invoice_number,
            fiscal_document=move.fiscal_document,
            is_ed=move.is_ed,
            created_at=move.created_at,
        )
        for move in moves
    ]


@router.get("/{move_id}", response_model=MoveResponseDTO)
async def get_move(
    move_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    stmt = select(AccountMove).where(AccountMove.id == move_id, AccountMove.tenant_id == tenant_id)
    result = await db.execute(stmt)
    move = result.scalar_one_or_none()

    if not move:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")

    return MoveResponseDTO(
        id=move.id,
        name=move.name,
        ref=move.ref,
        date=move.date,
        state=move.state,
        move_type=move.move_type,
        description=move.description,
        partner_id=move.partner_id,
        amount_total=move.amount_total,
        amount_tax=move.amount_tax,
        amount_untaxed=move.amount_untaxed,
        invoice_date=move.invoice_date,
        invoice_number=move.invoice_number,
        fiscal_document=move.fiscal_document,
        is_ed=move.is_ed,
        created_at=move.created_at,
    )