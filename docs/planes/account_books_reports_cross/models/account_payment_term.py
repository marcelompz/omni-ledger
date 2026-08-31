# -*- coding: utf-8 -*-
"""
Created on 2024-12-16 16:46:13

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentTermInherit(models.Model):
    _inherit = 'account.payment.term'

    is_installment_payment = fields.Boolean(
        string=_('Es un pago a cuota?'))

    @api.constrains('is_cash_payment', 'is_installment_payment')
    def _check_payment_types(self):
        for record in self:
            if record.is_cash_payment and record.is_installment_payment:
                raise ValidationError(_('Solo uno de los campos "Es un pago al contado?" o "Es un pago a cuota?" puede estar seleccionado.'))
