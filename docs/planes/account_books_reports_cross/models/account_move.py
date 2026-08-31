# -*- coding: utf-8 -*-
"""
Created on 2024-11-12 12:13:05

@author: drojo
"""
# odoo
from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    receipt_type_id = fields.Many2one(
        'account.move.receipt.code', string='Tipo de comprobante')
    form120_id = fields.Many2one(
        'account.move.form.type', string='Formulario 120', domain='[("form_number","=","form120")]')
    form145_id = fields.Many2one(
        'account.move.form.type', string='Formulario 145', domain='[("form_number","=","form145")]')
    form145_reasons_inclusion_id = fields.Many2one(
        'account.move.reasons.inclusion', string='Motivo de inclusión')
    show_form145_reasons = fields.Boolean(
        string='Mostrar las razones de inclusiones del formulario 145?', store=True, compute='_compute_show_form145_reasons')
    books_reports_cancel_reason = fields.Char(
        string='Motivo de la cancelación')
    is_installment_payment = fields.Boolean(
        related='invoice_payment_term_id.is_installment_payment')
    installment_payment_qty = fields.Integer(
        string='Cantidad de Cuota')
    in_invoice_stamped = fields.Char(
        string='Timbrado')
    in_invoice_date_due = fields.Date(
        string='Venc. timbrado')
    latam_doc_type_id = fields.Many2one(
        'l10n_latam.document.type', string='Tipo timbrado')
    receipt_period = fields.Date(
        string='Fecha de emisión o periodo de del comprobante', default=lambda self : fields.Date.context_today(self))
    is_income_revenue = fields.Boolean(
        string='Es un ingreso/egreso?')
    invoice_tooltip = fields.Char(
        compute='_compute_invoice_tooltip')
    specify_document_type = fields.Char(
        string='Especificar tipo de documento')
    expired_stamp_alert = fields.Boolean(
        string='Alerta de timbrado vencido', compute='_compute_expired_stamp_alert', store=True)

    @api.depends('invoice_date', 'in_invoice_date_due')
    def _compute_expired_stamp_alert(self):
        for rec in self:
            rec.expired_stamp_alert = False

            if rec.move_type == 'in_invoice' and rec.invoice_date and rec.in_invoice_date_due and rec.invoice_date > rec.in_invoice_date_due:
                rec.expired_stamp_alert = True

    @api.depends('is_income_revenue')
    def _compute_invoice_tooltip(self):
        for rec in self:
            rec.invoice_tooltip = _('Si el comprobante es 208 (LIQUIDACION DE SALARIO) se tendrá en cuenta solo el mes y año.')
    
    @api.onchange('receipt_type_id')
    def onchange_receipt_type_id(self):
        # Obtener referencias de tipos de comprobante
        receipt_types_list = [self.env.ref('account_books_reports_cross.cross_amrt_income', raise_if_not_found=False).id, self.env.ref('account_books_reports_cross.cross_amrt_revenue', raise_if_not_found=False).id]
        # self.is_income_revenue = self.receipt_type_id.type_ids.ids in receipt_types_list
        self.is_income_revenue = any(bool(type) for type in self.receipt_type_id.type_ids if type.id in receipt_types_list)
                
    @api.onchange('invoice_number')
    def _onchange_invoice_number(self):
        if self.invoice_number:
            # Quitar espacios y normalizar el valor
            raw_number = self.invoice_number.replace(" ", "")
            parts = raw_number.split("-")

            if len(parts) != 3:  # Si no tiene 3 partes, asumimos que es un numero que no necesita ser formateado
                return
            # Asegurar que cada parte tenga el formato esperado
            try:
                part1 = parts[0].zfill(3) if len(parts) > 0 else "000"
                part2 = parts[1].zfill(3) if len(parts) > 1 else "000"
                part3 = parts[2].zfill(7) if len(parts) > 2 else "0000000"

                # Actualizar el campo con el formato estándar
                self.invoice_number = f"{part1}-{part2}-{part3}"
            except IndexError:
                self.invoice_number = ""  # Limpia si hay un error en el formato    

    @api.depends('form145_id')
    def _compute_show_form145_reasons(self):
        for record in self:
            try:
                xml_ref = self.env.ref('account_books_reports_cross.cross_amft_6').id
            
            except ValueError:
                xml_ref = None

            record.show_form145_reasons = True if record.form145_id.id == xml_ref else False
    
    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)

        if res.get('move_type') and res.get('move_type') in ['out_invoice', 'in_invoice']:
            receipt_type_id = self.env['account.move.receipt.code'].search([('code', '=', '109')], limit=1)

            res.update({
                'receipt_type_id': receipt_type_id.id or False
            })

        if res.get('move_type') and res.get('move_type') in ['out_refund', 'in_refund']:
            receipt_type_id = self.env['account.move.receipt.code'].search([('code', '=', '110')], limit=1)

            res.update({
                'receipt_type_id': receipt_type_id.id or False
            })
    
        return res

    @api.onchange('move_type')
    def _onchange_move_type(self):
        """Establece el dominio para receipt_type_id según el tipo de factura."""

        # Obtener referencias de tipos de comprobante
        receipt_types = {
            'out_invoice': self.env.ref('account_books_reports_cross.cross_amrt_out_invoice', raise_if_not_found=False),
            'income': self.env.ref('account_books_reports_cross.cross_amrt_income', raise_if_not_found=False),
            'in_invoice': self.env.ref('account_books_reports_cross.cross_amrt_in_invoice', raise_if_not_found=False),
            'revenue': self.env.ref('account_books_reports_cross.cross_amrt_revenue', raise_if_not_found=False)
        }

        # Definir los tipos de comprobante según move_type
        type_mapping = {
            'out_invoice': ['out_invoice', 'income'],  # Factura de venta
            'in_invoice': ['in_invoice', 'revenue']    # Factura de compra
        }

        # Obtener los IDs de receipt_type válidos
        receipt_type_ids = [receipt_types[t].id for t in type_mapping.get(self.move_type, []) if receipt_types[t]]

        return {
            'domain': {'receipt_type_id': [('type_ids', 'in', receipt_type_ids)]} if receipt_type_ids else {}
        }

    def button_getinfo_from_cdc(self):
        view_id = self.env.ref('account_books_reports_cross.account_move_getinfo_wizard_form')

        if view_id:
            return {
                'name': _('Obtener información desde CDC'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move.getinfo.wizard',
                'target': 'new',
                'view_id': view_id.id,
            }

    def cross_button_cancel(self):
        # Si el timbrado pertenece a una preimpresa, debemos asignar motivo de la cancelacion
        if self.authorization_id and self.authorization_id.pre_printed_invoice:
            # Obtener la vista del wizard
            view_id = self.env.ref('account_books_reports_cross.account_books_cancel_wizard_form')

            if view_id:
                return {
                    'name': _('Cancelar documento'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.books.cancel.wizard',
                    'target': 'new',
                    'view_id': view_id.id,
                    'context': {
                        'default_account_id': self.id,
                    },
                }

        else:
            # Sino, ejecuta el boton cancelar
            self.button_cancel()

    def write(self, vals):
        # Convertir el valor del campo 'reason' a mayúsculas antes de escribir en el registro
        if 'cancel_reason' in vals and vals['cancel_reason']:
            vals['cancel_reason'] = vals['cancel_reason'].upper()
        return super().write(vals)

    @api.constrains('is_installment_payment', 'installment_payment_qty')
    def _check_payment_types(self):
        for record in self:
            if record.is_installment_payment and record.installment_payment_qty <= 0:
                raise ValidationError(_('Debes especificar una cantidad de cuota valida.'))

    def accounts_receivable_payable_report(self):
        # raise UserError(f'{self.env.context.get("active_model")} - {self.env.context.get("active_ids")}')
        invoices = self.env['account.move'].search([('id', 'in', self.env.context.get('active_ids'))])
        if not invoices:
            raise UserError(_('No se encontraron documentos para el periodo seleccionado'))

        self.env['financial.report.collectpay.wizard'].search([]).unlink()

        # Guardar el nuevo wizard generado
        report_wizard = self.env['financial.report.collectpay.wizard'].create({
            'name': _('FACTURAS A COBRAR') if invoices[0].move_type == 'out_invoice' else _('FACTURAS A PAGAR'),
            'move_ids': [Command.set(invoices.ids)],
        })

        # Pasar ese objeto al reporte
        return self.env.ref('account_books_reports_cross.action_partner_financial_report_collectpay').report_action(report_wizard)
