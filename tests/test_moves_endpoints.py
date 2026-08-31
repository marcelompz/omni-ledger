import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.core.database import get_db
from src.core.security import get_tenant_id
from src.models.accounting import AccountMove


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


def _make_mock_move(move_id=1):
    move = MagicMock(spec=AccountMove)
    move.id = move_id
    move.name = "TEST-001"
    move.ref = "TEST-REF"
    move.date = "2024-01-15T10:30:00Z"
    move.state = "posted"
    move.move_type = "out_invoice"
    move.description = "Test"
    move.partner_id = 1
    move.amount_total = 100.0
    move.amount_tax = 10.0
    move.amount_untaxed = 90.0
    move.invoice_date = "2024-01-15T10:30:00Z"
    move.invoice_number = "001-001-0000001"
    move.fiscal_document = True
    move.is_ed = False
    move.created_at = "2024-01-15T10:30:00Z"
    return move


@pytest.mark.asyncio
async def test_create_move_unbalanced_returns_422(mock_db):
    from src.api.v1.moves import router
    from src.services.ledger_service import DoubleEntryValidationError
    
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_id] = lambda: 1

    mock_db.execute.side_effect = DoubleEntryValidationError("Partida desbalanceada")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/moves",
            json={
                "date": "2024-01-15T10:30:00Z",
                "move_type": "out_invoice",
                "lines": [
                    {"account_id": 4110, "debit": 100.0, "credit": 0},
                    {"account_id": 1120, "debit": 0, "credit": 99.99},
                ],
            },
            headers={"X-OmniLedger-Tenant-Id": "1"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_moves_empty(mock_db):
    from src.api.v1.moves import router
    
    app.include_router(router, prefix="/api/v1")
    
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = execute_result
    
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_id] = lambda: 1

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/moves", headers={"X-OmniLedger-Tenant-Id": "1"})

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_move_not_found(mock_db):
    from src.api.v1.moves import router
    
    app.include_router(router, prefix="/api/v1")
    
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = execute_result
    
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_id] = lambda: 1

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/moves/999", headers={"X-OmniLedger-Tenant-Id": "1"})

    app.dependency_overrides.clear()
    assert response.status_code == 404