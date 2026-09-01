import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from datetime import date
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


def _make_mock_move(**overrides):
    move = MagicMock(spec=AccountMove)
    move.id = overrides.get("id", 1)
    move.invoice_date = overrides.get("invoice_date", date(2024, 1, 15))
    move.invoice_number = overrides.get("invoice_number", "001-001-0000001")
    move.partner_id = overrides.get("partner_id", 1)
    move.amount_untaxed = overrides.get("amount_untaxed", 1000.0)
    move.amount_tax = overrides.get("amount_tax", 110.0)
    move.amount_total = overrides.get("amount_total", 1110.0)
    move.move_type = overrides.get("move_type", "out_invoice")
    move.state = overrides.get("state", "posted")
    move.is_ed = overrides.get("is_ed", True)
    move.fiscal_document = overrides.get("fiscal_document", True)
    move.timbrado_id = overrides.get("timbrado_id", 1)
    move.res90_tipo_comprobante = overrides.get("res90_tipo_comprobante", "1")
    move.res90_nro_timbrado = overrides.get("res90_nro_timbrado", "123456")
    return move


def _setup_db_mock(mock_db, rows):
    execute_result = MagicMock()
    execute_result.all.return_value = rows
    mock_db.execute.return_value = execute_result


@pytest.mark.asyncio
async def test_sales_book_requires_filter(mock_db):
    from src.api.v1.reports import router
    app.include_router(router, prefix="/api/v1")

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_id] = lambda: 1

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/reports/sales-book", headers={"X-OmniLedger-Tenant-Id": "1"})

    app.dependency_overrides.clear()
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_sales_book_with_month_year(mock_db):
    from src.api.v1.reports import router
    app.include_router(router, prefix="/api/v1")

    moves = [_make_mock_move(invoice_date=date(2024, 3, 15))]
    _setup_db_mock(mock_db, moves)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_id] = lambda: 1

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/reports/sales-book?fiscal_year=2024&month=3",
            headers={"X-OmniLedger-Tenant-Id": "1"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "libro_ventas"
    assert data["total_records"] == 1
    assert data["totals"]["total_total"] == 1110.0


@pytest.mark.asyncio
async def test_purchases_book_empty(mock_db):
    from src.api.v1.reports import router
    app.include_router(router, prefix="/api/v1")

    _setup_db_mock(mock_db, [])

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_id] = lambda: 1

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/reports/purchases-book?fiscal_year=2024&month=1",
            headers={"X-OmniLedger-Tenant-Id": "1"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "libro_compras"
    assert data["total_records"] == 0
    assert data["totals"]["total_total"] == 0.0


@pytest.mark.asyncio
async def test_aivi_report(mock_db):
    from src.api.v1.reports import router
    app.include_router(router, prefix="/api/v1")

    moves = [_make_mock_move(invoice_date=date(2024, 5, 10))]
    _setup_db_mock(mock_db, moves)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_id] = lambda: 1

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/reports/aivi?fiscal_year=2024&month=5",
            headers={"X-OmniLedger-Tenant-Id": "1"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "aivi"
    assert data["fiscal_year"] == 2024
    assert data["month"] == 5


@pytest.mark.asyncio
async def test_report_0251(mock_db):
    from src.api.v1.reports import router
    app.include_router(router, prefix="/api/v1")

    moves = [_make_mock_move(invoice_date=date(2024, 7, 20))]
    _setup_db_mock(mock_db, moves)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_id] = lambda: 1

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/reports/0251?fiscal_year=2024&month=7",
            headers={"X-OmniLedger-Tenant-Id": "1"},
        )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "0251"
    assert data["records"][0]["tipo_comprobante"] == "1"