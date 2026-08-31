# -*- coding: utf-8 -*-
"""
Created on 2024-12-10 10:14:19

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountBooksCancelWizard(models.TransientModel):
    _name = 'account.books.cancel.wizard'
    _description = 'Motivo de cancelación de documentos'

    reason = fields.Char(
        string='Motivo de la cancelación', help='El motivo por el cual desea cancelar el documento')
    account_id = fields.Many2one(
        'account.move', string='Facturas')

    @api.model
    def create(self, vals):
        # Convertir el valor del campo 'reason' a mayúsculas antes de crear el registro
        if 'reason' in vals and vals['reason']:
            vals['reason'] = vals['reason'].upper()
        return super().create(vals)

    def action_cancel_document(self):
        if not self.account_id:
            raise ValidationError(_('No hay ningúna factura asociado a este registro.'))
        
        # Opcional: Manejo del flujo, por ejemplo, si deseas detener o confirmar:
        if not self.reason:
            raise ValidationError(_('Proporcione un motivo para la cancelación.'))

        self.account_id.write({'books_reports_cancel_reason': self.reason})
        self.account_id.button_cancel()
