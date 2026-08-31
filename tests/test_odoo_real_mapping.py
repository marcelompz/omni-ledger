import json
import pytest
from decimal import Decimal
from src.models.accounting import AccountMove, AccountMoveLine, AccountTax, AccountAccount


class TestOdooRealMapping:
    @pytest.fixture
    def real_fixtures(self):
        with open('/opt/omniledger/tests/fixtures_odoo_real.json') as f:
            return json.load(f)

    def test_map_odoo_move_to_omniledger(self, real_fixtures):
        odoo_move = real_fixtures["moves"][0]
        
        move = AccountMove(
            tenant_id=1,
            name=odoo_move.get("name"),
            ref=odoo_move.get("name"),
            date=odoo_move["invoice_date"],
            state=odoo_move["state"],
            move_type=odoo_move["move_type"],
            partner_id=odoo_move["partner_id"],
            amount_total=Decimal(str(odoo_move["amount_total"])),
            amount_tax=Decimal(str(odoo_move["amount_tax"])),
            amount_untaxed=Decimal(str(odoo_move["amount_untaxed"])),
            invoice_date=odoo_move["invoice_date"],
            invoice_number=odoo_move["invoice_number"],
            fiscal_document=odoo_move.get("fiscal_document", False),
            is_ed=odoo_move.get("is_ed", False),
            authorization_id=odoo_move.get("authorization_id"),
            timbrado_id=odoo_move.get("timbrado_id"),
        )
        
        assert move.tenant_id == 1
        assert move.move_type in ("out_invoice", "in_invoice", "out_refund", "in_refund")
        assert move.amount_total >= 0
        assert move.fiscal_document in (True, False)
        assert move.is_ed in (True, False)

    def test_map_odoo_line_to_omniledger(self, real_fixtures):
        first_move_id = list(real_fixtures["lines"].keys())[0]
        lines = real_fixtures["lines"][first_move_id]
        
        if not lines:
            pytest.skip("No lines for this move")
        
        line = lines[0]
        move_line = AccountMoveLine(
            tenant_id=1,
            move_id=int(first_move_id),
            account_id=line["account_id"],
            quantity=Decimal(str(line["quantity"])),
            price_unit=Decimal(str(line["price_unit"])),
            price_total=Decimal(str(line["price_total"])),
            debit=Decimal(str(line["debit"])),
            credit=Decimal(str(line["credit"])),
            tax_base_amount=Decimal(str(line["tax_base_amount"])),
            tax_line_id=line.get("tax_line_id"),
        )
        
        assert move_line.tenant_id == 1
        assert move_line.move_id == int(first_move_id)
        assert move_line.debit >= 0
        assert move_line.credit >= 0

    def test_map_odoo_tax_to_omniledger(self, real_fixtures):
        taxes = real_fixtures["taxes"]
        assert len(taxes) > 0
        
        for tax in taxes:
            assert "amount" in tax
            assert "name" in tax
            assert Decimal(str(tax["amount"])) >= 0

    def test_partner_vat_format_paraguay(self, real_fixtures):
        partners = real_fixtures["partners"]
        assert len(partners) > 0
        
        for partner in partners.values():
            vat = partner.get("vat", "")
            if vat:
                assert "-" in vat or vat in ["X", "1"], f"RUC Paraguay debe tener formato XXXXXXXX-X: {vat}"