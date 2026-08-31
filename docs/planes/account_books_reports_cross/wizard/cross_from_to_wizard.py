# -*- coding: utf-8 -*-
"""
Created on 2025-04-11 10:23:59

@author: drojo
"""
# python
from datetime import datetime
import logging

# odoo
from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CrossFromToWizard(models.TransientModel):
    _name = 'cross.from.to.wizard'
    _description = 'From - To Wizard'

    @api.model
    def _default_date_today(self):
        user_time = fields.Datetime.context_timestamp(self, datetime.now())
        return user_time.date()

    partner_id = fields.Many2one(
        'res.partner', string='Cliente/Proveedor')
    date_from = fields.Date(
        string='Desde', default=_default_date_today)
    date_to = fields.Date(
        string='Hasta', default=_default_date_today)
    report_origin = fields.Char(
        string='Origen')
    file_type = fields.Selection(
        string='Tipo de archivo', selection=[('pdf', 'PDF'),('xls','XLSX')], default='xls')

    def action_done(self):
        self.date_from = self.date_from or fields.Date.from_string('1900-01-01')
        self.date_to = self.date_to or self._default_date_today()

        if self.date_from > self.date_to:
            raise UserError(_('La fecha de inicio no puede ser mayor a la fecha de fin'))

        move_type = 'out_invoice' if self.report_origin == 'receivable' else 'in_invoice'

        domain = [
            ('fiscal_document', '=', True),
            ('move_type', '=', move_type),
            ('state', '=', 'posted'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('payment_state', 'in', ['not_paid', 'in_payment', 'partial', 'invoicing_legacy']),
        ]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        invoices = self.env['account.move'].search(domain)

        self.env['financial.report.collectpay.wizard'].search([]).unlink()

        # Guardar el nuevo wizard generado
        report_wizard = self.env['financial.report.collectpay.wizard'].create({
            'name': _('DOCUMENTOS A COBRAR') if self.report_origin == 'receivable' else _('DOCUMENTOS A PAGAR'),
            'date_from': self.date_from,
            'date_to': self.date_to,
            'move_ids': [Command.set(invoices.ids)],
        })

        # Si no hay documentos, lanzar un error
        if len(invoices) == 0:
            raise UserError(_('No se encontraron documentos para el periodo seleccionado'))

        # Pasar ese objeto al reporte
        if self.file_type == 'pdf':
            return self.env.ref('account_books_reports_cross.action_financial_report_collectpay').report_action(report_wizard)

        else:
            # Generar el reporte en formato xlsx
            return report_wizard.generate_xlsx_report()
