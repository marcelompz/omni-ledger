import pytest
from decimal import Decimal
from src.services.ledger_service import LedgerService, DoubleEntryValidationError


class TestLedgerService:
    def test_quantize_half_even(self):
        assert LedgerService.quantize(Decimal("1.005")) == Decimal("1.00")
        assert LedgerService.quantize(Decimal("1.015")) == Decimal("1.02")
        assert LedgerService.quantize(Decimal("1.025")) == Decimal("1.02")

    @pytest.mark.asyncio
    async def test_validate_double_entry_balanced(self):
        lines = [
            {"debit": Decimal("100.00"), "credit": Decimal("0")},
            {"debit": Decimal("0"), "credit": Decimal("100.00")},
        ]
        await LedgerService.validate_double_entry(None, lines, 1)

    @pytest.mark.asyncio
    async def test_validate_double_entry_unbalanced(self):
        lines = [
            {"debit": Decimal("100.00"), "credit": Decimal("0")},
            {"debit": Decimal("0"), "credit": Decimal("99.99")},
        ]
        with pytest.raises(DoubleEntryValidationError):
            await LedgerService.validate_double_entry(None, lines, 1)

    @pytest.mark.asyncio
    async def test_validate_double_entry_with_tax(self):
        lines = [
            {"debit": Decimal("1000.00"), "credit": Decimal("0"), "tax_line_id": 1},
            {"debit": Decimal("0"), "credit": Decimal("909.09"), "tax_line_id": 1},
            {"debit": Decimal("0"), "credit": Decimal("90.91"), "tax_line_id": 1},
        ]
        await LedgerService.validate_double_entry(None, lines, 1)

    @pytest.mark.asyncio
    async def test_validate_double_entry_rounding(self):
        lines = [
            {"debit": Decimal("10.005"), "credit": Decimal("0")},
            {"debit": Decimal("0"), "credit": Decimal("10.005")},
        ]
        await LedgerService.validate_double_entry(None, lines, 1)