# -*- coding: utf-8 -*-
"""
Created on 2024-10-11 10:40:39

@author: drojo
"""
# python
import base64
from io import BytesIO
from datetime import datetime
import csv
import io
import logging

# odoo
from odoo import models, fields, api, _
from odoo.tools import date_utils
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)


class AccountBooksReportWizard(models.TransientModel):
    _name = 'account.books.report.wizard'
    _descripcion = 'Reportes de libros IVA'

    date_from = fields.Date(
        string='Fecha desde', default=lambda self: self._get_date_from_to(option='from'))
    date_to = fields.Date(
        string='Fecha hasta', default=lambda self: self._get_date_from_to())
    report_type = fields.Selection(
        string='Tipo', selection=[('out_invoice', 'VENTA'),('in_invoice','COMPRA')], default='out_invoice')
    invoice_state_ids = fields.Many2many(
        'account.move.selection.state', string='Estado', default=lambda self: self._default_invoice_state_ids())
    file_type = fields.Selection(
        string='Tipo de archivo', selection=[('pdf', 'PDF'),('xls','XLSX'),('txt','TXT'),('csv','CSV')], default='pdf')
    lines_ids = fields.One2many(
        'account.books.lines.wizard', 'report_id', string='Líneas del reporte')
    currency_id = fields.Many2one(
        'res.currency', string='Moneda del reporte', default=lambda self: self.env.company.currency_id)
    
    @api.model
    def _default_invoice_state_ids(self):
        return self.env['account.move.selection.state'].search([
            ('value', 'in', ['posted', 'cancel'])
        ])

    def _get_date_from_to(self, option='to'):
        """
        Devuelve la fecha desde como el uno de enero del corriente año y la fecha hasta `hoy`

        """
        if option == 'from':
            # Obtener el año actual
            current_year = datetime.now().year
            # Establecer la fecha como el 1 de enero del año actual
            date_from = datetime(current_year, 1, 1).strftime('%Y-%m-%d')
            return date_from
        # Retornar la fecha actual para 'to'
        return fields.Date.context_today(self)

    def get_fiscal_years(self, date_from, date_to):
        # Extraer los años de date_from y date_to
        year_from = date_from.year
        year_to = date_to.year
        
        # Si los años son iguales, devolver ese año
        if year_from == year_to:
            return str(year_from)
        
        # Si los años son diferentes, devolver el rango de años
        return ', '.join(str(year) for year in range(year_from, year_to + 1))
        
    def button_action_generate_report(self):
        report_type = [self.report_type]

        if self.report_type == 'out_invoice': report_type.append('out_refund')

        # Búsqueda de facturas según los criterios de tipo, fecha y estado
        invoices = self.env['account.move'].search([
            ('move_type', 'in', report_type),     # Tipo de factura (ventas o compras)
            ('invoice_date', '>=', self.date_from),   # Fecha desde
            ('invoice_date', '<=', self.date_to),     # Fecha hasta
            ('state', 'in', self.invoice_state_ids.mapped('value')),           # Estado de la factura
            ('fiscal_document', '=', True),           # Es documento fiscal?
        ])

        # Eliminar líneas de reporte anteriores
        self.lines_ids.unlink()

        lines = []

        # Recorrer las facturas para generar las líneas de reporte
        for line in invoices:
            # Obtener montos por tipo de impuesto
            tax0 = self._get_amount_with_taxes(0, line)
            tax5 = self._get_amount_with_taxes(5, line)
            tax10 = self._get_amount_with_taxes(10, line)

            # Calcular los impuestos específicos
            tax5_excluded = tax5 / 21 if tax5 != 0 else 0
            tax10_excluded = tax10 / 11 if tax10 != 0 else 0
            
            # Separar el RUC y su dígito verificador
            vat = line.partner_id.vat or ''
            vat_split = vat.split('-') if '-' in vat else [vat, '']
            vat_number = vat_split[0]
            vat_dv = vat_split[1]
            
            # Crear líneas de reporte
            lines.append((0, 0, {
                'invoice_id': line.id,
                'partner_vat': vat_number,
                'partner_vat_dv': vat_dv,
                'amount_iva0': tax0,
                'amount_iva5_tax_included': tax5 - round(tax5 / 21, line.currency_id.decimal_places),
                'amount_iva5': tax5_excluded,
                'amount_iva10_tax_included': tax10 - round(tax10 / 11, line.currency_id.decimal_places),
                'amount_iva10': tax10_excluded,
            }))

        # Asignar las líneas generadas al campo correspondiente
        self.lines_ids = lines

        if self.file_type == 'pdf':
            return self.env.ref('account_books_reports_cross.action_report_account_books_report').report_action(self)

        elif self.file_type == 'xls':
            # Llama directamente al método que genera el archivo XLSX
            xlsx_report = self.generate_xlsx_report()
            return xlsx_report

        elif self.file_type in ['csv','txt']:
            # Llamada para generar CSV
            return self.generate_csv_report(self.file_type)

        else:
            raise UserError(f'Seleccione un tipo de archivo permitido.')

    def _get_amount_with_taxes(self, tax, invoice):
        # Inicialización de los montos de impuestos
        tax10 = tax5 = tax0 = 0

        # Recorrer las líneas de factura para sumar montos por tipo de impuesto
        for line in invoice.invoice_line_ids:
            if line.tax_ids:
                # Verificar y sumar montos según el valor del impuesto
                for tax_line in line.tax_ids:
                    if tax_line.amount == 10:
                        tax10 += line.price_total
                    
                    elif tax_line.amount == 5:
                        tax5 += line.price_total

            else:
                # Si no hay impuestos, se suma como exento
                tax0 += line.price_total

        # Devolver el monto según el tipo de impuesto solicitado
        if tax == 10:
            if invoice.currency_id != self.currency_id:
                tax10 = invoice.currency_id._convert(tax10, self.currency_id, invoice.company_id, invoice.invoice_date or fields.Date.context_today(self))
            return tax10
        
        elif tax == 5:
            if invoice.currency_id != self.currency_id:
                tax5 = invoice.currency_id._convert(tax5, self.currency_id, invoice.company_id, invoice.invoice_date or fields.Date.context_today(self))
            return tax5
        
        else:
            if invoice.currency_id != self.currency_id:
                tax0 = invoice.currency_id._convert(tax0, self.currency_id, invoice.company_id, invoice.invoice_date or fields.Date.context_today(self))
            return tax0

    def generate_xlsx_report(self):
        '''Genera el reporte en formato xlsx'''

        with BytesIO() as output:
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet()

            # Define formatos
            title_cells = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
            subtitle_cells = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter'})
            header_column = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 8, 'align': 'center', 'bg_color': '#3F93CA', 'border': 1, 'valign': 'vcenter'})
            data_cells = workbook.add_format({'font_name': 'Arial', 'font_size': 8, 'align': 'left', 'border': 1})

            # Establecemos el alto de la fila y escribimos el encabezado
            worksheet.set_row(0, 30)
            worksheet.merge_range(0, 0, 0, 26, 'LIBRO VENTAS LEY 125/91' if self.report_type == 'out_invoice' else 'LIBRO COMPRAS LEY 125/91', title_cells)
            
            worksheet.set_row(1, 20)
            worksheet.merge_range(1, 0, 1, 26, f'CONTRIBUYENTE: {self.env.company.vat} - {self.env.company.name}', subtitle_cells)
            
            activities = '/'.join(line.name for line in self.env.company.type_obligations_id)
            worksheet.set_row(2, 20)
            worksheet.merge_range(2, 0, 2, 26, f'PERIODO: {self.date_from} al {self.date_to} - ACTIVIDAD: {activities}', subtitle_cells)

            worksheet.set_row(4, 20)
            worksheet.set_row(5, 20)
            
            # Definimos las filas (y)
            y = 4

            # Creamos el encabezado de las columnas
            # if self.report_type == 'out_invoice':
            worksheet.merge_range(y, 0, y+1, 0, 'FECHA', header_column)
            worksheet.merge_range(y, 1, y+1, 1, 'TIPO TIMBRADO', header_column)
            worksheet.merge_range(y, 2, y+1, 2, 'DOCUMENTO', header_column)
            worksheet.merge_range(y, 3, y+1, 3, 'SERIE', header_column)
            worksheet.merge_range(y, 4, y+1, 4, 'CDC DOCUMENTO', header_column)
            worksheet.merge_range(y, 5, y+1, 5, 'TIMBRADO', header_column)
            worksheet.merge_range(y, 6, y+1, 6, 'VENCIM.', header_column)
            worksheet.merge_range(y, 7, y, 9, 'CLIENTE' if self.report_type == 'out_invoice' else 'PROVEEDOR', header_column)
            worksheet.write(y+1, 7, 'RAZÓN SOCIAL', header_column)
            worksheet.write(y+1, 8, 'RUC', header_column)
            worksheet.write(y+1, 9, 'DV', header_column)
            worksheet.merge_range(y, 10, y, 15, 'VALORES DE VENTAS' if self.report_type == 'out_invoice' else 'VALORES DE COMPRAS', header_column)
            worksheet.write(y+1, 10, 'GRAV. 10%', header_column)
            worksheet.write(y+1, 11, 'GRAV. 5%', header_column)
            worksheet.write(y+1, 12, 'IVA 10%', header_column)
            worksheet.write(y+1, 13, 'IVA 5%', header_column)
            worksheet.write(y+1, 14, 'EXENTAS', header_column)
            worksheet.write(y+1, 15, 'TOTAL', header_column)
            worksheet.merge_range(y, 16, y+1, 16, 'MON.', header_column)
            worksheet.merge_range(y, 17, y+1, 17, 'CONDICIÓN', header_column)
            worksheet.merge_range(y, 18, y+1, 18, 'CUOTAS', header_column)
            worksheet.merge_range(y, 19, y+1, 19, 'OBSERVACIÓN', header_column)
            worksheet.merge_range(y, 20, y+1, 20, 'CUENTAS CONTABLES', header_column)
            worksheet.merge_range(y, 21, y+1, 21, 'CATEGORIA DEL PRODUCTO', header_column)
            worksheet.merge_range(y, 22, y+1, 22, 'FORMULARIO 145', header_column)
            worksheet.merge_range(y, 23, y+1, 23, 'MOTIVOS INCLUSIÓN', header_column)
            worksheet.merge_range(y, 24, y+1, 24, 'DETALLES INCLUSIÓN', header_column)
            worksheet.merge_range(y, 25, y+1, 25, 'MOTIVO ANULADO', header_column)
            worksheet.merge_range(y, 26, y+1, 26, 'FORMULARIO 120' if self.report_type == 'out_invoice' else 'TIPO', header_column)

            # Definimos la anchura de las columnas
            worksheet.set_column('A:A', 8)
            worksheet.set_column('B:C', 12)
            worksheet.set_column('D:D', 8)
            worksheet.set_column('E:E', 32)
            worksheet.set_column('F:G', 8)
            worksheet.set_column('H:H', 32)
            worksheet.set_column('I:I', 8)
            worksheet.set_column('J:J', 4)
            worksheet.set_column('K:O', 12)
            worksheet.set_column('P:P', 15)
            worksheet.set_column('Q:Q', 4)
            worksheet.set_column('R:S', 8)
            worksheet.set_column('T:V', 35)
            worksheet.set_column('W:W', 15)
            worksheet.set_column('X:Y', 25)
            worksheet.set_column('Z:Z', 13)
            worksheet.set_column('AA:AA', 15)

            # Escribir los datos
            row = y + 2 
            for line in self.lines_ids:
                # Obtener el número de decimales de la moneda seleccionada para el reporte
                decimal_places = self.currency_id.decimal_places
                # Crear el formato de número basado en la cantidad de decimales
                decimal_format_str = '#,##0.' + ('0' * decimal_places if decimal_places > 0 else '')

                number_cells = workbook.add_format({
                    'font_name': 'Arial',
                    'font_size': 8,
                    'align': 'right',
                    'border': 1,
                    'num_format': decimal_format_str
                })

                worksheet.write(row, 0, line.invoice_date.strftime('%d-%m-%Y'),data_cells)
                worksheet.write(row, 2, line.invoice_number or '',data_cells)
                worksheet.write(row, 3, line.serie or '',data_cells)
                worksheet.write(row, 4, line.cdc or '',data_cells)

                if self.report_type == 'out_invoice':   # Venta
                    worksheet.write(row, 1, line.authorization_id.name or '',data_cells)
                    worksheet.write(row, 5, line.out_invoice_stamped or '',data_cells)
                    worksheet.write(row, 6, line.out_invoice_stamped_date_due.strftime('%d-%m-%Y') if line.authorization_id.pre_printed_invoice else '',data_cells) # Columna VENC.

                else:                                   # Compra
                    worksheet.write(row, 1, line.in_invoice_latam_doc_type_id.name or '',data_cells)
                    worksheet.write(row, 5, line.in_invoice_stamped or '',data_cells)
                    worksheet.write(row, 6, (line.in_invoice_stamped_date_due.strftime('%d-%m-%Y')) if line.in_invoice_stamped_date_due else '',data_cells) # Columna VENC.

                worksheet.write(row, 7, line.partner_id.name or '',data_cells)
                worksheet.write(row, 8, line.partner_vat or '',data_cells)
                worksheet.write(row, 9, line.partner_vat_dv or '',data_cells)
                worksheet.write(row, 10, line.amount_iva10_tax_included or 0,number_cells)
                worksheet.write(row, 11, line.amount_iva5_tax_included or 0,number_cells)
                worksheet.write(row, 12, line.amount_iva10 or 0,number_cells)
                worksheet.write(row, 13, line.amount_iva5 or 0,number_cells)
                worksheet.write(row, 14, line.amount_iva0 or 0,number_cells)
                worksheet.write(row, 15, self._get_report_currency_amount(line) or 0,number_cells)
                worksheet.write(row, 16, line.invoice_id.currency_id.symbol or '',data_cells)
                worksheet.write(row, 17, line.invoice_condition or '',data_cells)
                worksheet.write(row, 18, line.installment_qty if line.invoice_id.invoice_payment_term_id.is_installment_payment else '',data_cells)
                worksheet.write(row, 19, '',data_cells)
                worksheet.write(row, 20, line.accounts or '',data_cells)
                worksheet.write(row, 21, line.product_categ or '',data_cells)
                worksheet.write(row, 22, line.form145_id.name or '',data_cells)
                worksheet.write(row, 23, line.reasons_inclusion_id.name or '',data_cells)
                worksheet.write(row, 24, line.details_inclusion or '',data_cells)
                worksheet.write(row, 25, line.reasons_cancelled or '',data_cells)
                worksheet.write(row, 26, line.form120_id.name or '',data_cells)

                row += 1
            
            # Cerramos y preparamos la descarga
            workbook.close()
            output.seek(0)

            xlsx_data = output.read()

        # Asignamos el nombre al reporte
        report_name = _('Reporte Libro %s - %s a %s.xlsx' % (
            dict(self.fields_get(allfields=['report_type'])['report_type']['selection'])[self.report_type], 
            self.date_from.strftime('%d-%m-%Y'), 
            self.date_to.strftime('%d-%m-%Y')
        ))

        # Devolver el archivo en base64 para la descarga
        attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }

    def _get_report_currency_amount(self, line):
        """
        Devuelve el monto de la factura en la moneda del reporte
        """
        if line.invoice_id.currency_id != self.currency_id:
            return line.invoice_id.currency_id._convert(line.amount_total, self.currency_id, line.invoice_id.company_id, line.invoice_id.invoice_date or fields.Date.context_today(self))
        return line.amount_total

    def generate_csv_report(self, format):
        # Crear un buffer de memoria para el archivo CSV
        output = io.StringIO()

        # Configurar delimitador según el formato de archivo
        delimiter = '\t' if self.file_type == 'txt' else ','

        # Crear el escritor CSV con el delimitador adecuado
        writer = csv.writer(output, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)

        # Crear encabezados de tabla dependiendo del tipo de reporte
        # if self.report_type == 'out_invoice':
        header = [
            'FECHA',
            'TIPO TIMBRADO',
            'DOCUMENTO',
            'SERIE',
            'CDC DOCUMENTO',
            'TIMBRADO',
            'VENCIM.',
            'CLIENTE' if self.report_type == 'out_invoice' else 'PROVEEDOR', 
            'RAZÓN SOCIAL',
            'RUC',
            'DV',
            'VALORES DE VENTAS' if self.report_type == 'out_invoice' else 'VALORES DE COMPRAS',
            'GRAV. 10%',
            'GRAV. 5%',
            'IVA 10%',
            'IVA 5%',
            'EXENTAS',
            'TOTAL',
            'MON.',
            'CONDICIÓN',
            'CUOTAS',
            'OBSERVACIÓN',
            'CUENTAS CONTABLES',
            'CATEGORIA DEL PRODUCTO',
            'FORMULARIO 145',
            'MOTIVOS INCLUSIÓN',
            'DETALLES INCLUSIÓN',
            'MOTIVO ANULADO',
            'FORMULARIO 120' if self.report_type == 'out_invoice' else 'TIPO',
        ]

        writer.writerow(header)

        # Escribir datos de las facturas
        for line in self.lines_ids:
            invoice_stamped = line.out_invoice_stamped if self.report_type == 'out_invoice' else line.in_invoice_stamped

            # Validamos si authorization_id no es None antes de acceder a sus atributos
            authorization = line.authorization_id or False
            pre_printed = authorization.pre_printed_invoice if authorization else False

            invoice_stamped_date_due = (
                line.out_invoice_stamped_date_due.strftime('%d-%m-%Y') if self.report_type == 'out_invoice' and pre_printed
                else line.in_invoice_stamped_date_due.strftime('%d-%m-%Y') if self.report_type != 'out_invoice' and pre_printed
                else ''
            )

            # Se usa getattr() para evitar errores si latam_doc_type_id es None
            stamped_type = (
                line.in_invoice_latam_doc_type_id.name if self.report_type == 'in_invoice' 
                else getattr(authorization, "latam_doc_type_id", False) and authorization.latam_doc_type_id.name or ''
            )

            writer.writerow([
                line.invoice_date.strftime('%d-%m-%Y'),
                stamped_type or '',
                line.invoice_number or '',
                line.serie or '',
                line.cdc or '',
                invoice_stamped or '',
                invoice_stamped_date_due,
                line.partner_id.name or '',
                line.partner_vat or '',
                line.partner_vat_dv or '',
                line.amount_iva10_tax_included or 0,
                line.amount_iva5_tax_included or 0,
                line.amount_iva10 or 0,
                line.amount_iva5 or 0,
                line.amount_iva0 or 0,
                line.amount_total or 0,
                line.invoice_id.currency_id.symbol or '',
                line.invoice_condition or '',
                line.installment_qty if line.invoice_id.invoice_payment_term_id.is_installment_payment else '',
                '',
                line.accounts or '',
                line.product_categ or '',
                line.form145_id.name or '',
                line.reasons_inclusion_id.name or '',
                line.details_inclusion or '',
                line.reasons_cancelled or '',
                line.form120_id.name or '',
            ])

        # Convertir el archivo a base64 y adjuntar al modelo
        output.seek(0)
        file_data = output.getvalue().encode()
        output.close()

        # Codificar el archivo en base64 para que Odoo pueda almacenarlo
        csv_data = base64.b64encode(file_data)

        # Asignamos el nombre al reporte
        report_name = _('Reporte Libro %s - %s a %s.%s' % (
            dict(self.fields_get(allfields=['report_type'])['report_type']['selection'])[self.report_type], 
            self.date_from.strftime('%d-%m-%Y'), 
            self.date_to.strftime('%d-%m-%Y'),
            self.file_type,
        ))

        # Crear el archivo adjunto
        attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': csv_data,
            'store_fname': report_name,
            'mimetype': 'text/csv'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def action_test(self):
        # Búsqueda de facturas según los criterios de tipo, fecha y estado
        invoices = self.env['account.move'].search([
            ('move_type', '=', self.report_type),     # Tipo de factura (ventas o compras)
            ('invoice_date', '>=', self.date_from),   # Fecha desde
            ('invoice_date', '<=', self.date_to),     # Fecha hasta
            ('state', 'in', self.invoice_state_ids.mapped('value')),           # Estado de la factura
            ('fiscal_document', '=', True),           # Es documento fiscal?
        ])

        # Eliminar líneas de reporte anteriores
        self.lines_ids.unlink()

        lines = []

        # Recorrer las facturas para generar las líneas de reporte
        for line in invoices:
            # Obtener montos por tipo de impuesto
            tax0 = self._get_amount_with_taxes(0, line)
            tax5 = self._get_amount_with_taxes(5, line)
            tax10 = self._get_amount_with_taxes(10, line)
            
            # Calcular los impuestos específicos
            tax5_excluded = tax5 / 21 if tax5 != 0 else 0
            tax10_excluded = tax10 / 11 if tax10 != 0 else 0
            total_tax_excluded = (tax0 + tax5 + tax10) - (tax5_excluded + tax10_excluded)
            
            # Separar el RUC y su dígito verificador
            vat = line.partner_id.vat or ''
            vat_split = vat.split('-') if '-' in vat else [vat, '']
            vat_number = vat_split[0]
            vat_dv = vat_split[1]
            
            # Crear líneas de reporte
            lines.append((0, 0, {
                'invoice_id': line.id,
                'partner_vat': vat_number,
                'partner_vat_dv': vat_dv,
                'amount_iva0': tax0,
                'amount_iva5_tax_included': tax5 - round(tax5 / 21, 0),
                'amount_iva5': tax5_excluded,
                'amount_iva10_tax_included': tax10 - round(tax10 / 11, 0),
                'amount_iva10': tax10_excluded,
            }))

        # Asignar las líneas generadas al campo correspondiente
        self.lines_ids = lines

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


class AccountBooksLinesWizard(models.TransientModel):
    _name = 'account.books.lines.wizard'
    _descripcion = 'Líneas del reportes de libros IVA'

    report_id = fields.Many2one(
        'account.books.report.wizard', string='Reporte')
    invoice_id = fields.Many2one(
        'account.move', string='Facturas')
    partner_id = fields.Many2one(
        related='invoice_id.partner_id')
    partner_vat = fields.Char(
        string='RUC')
    partner_vat_dv = fields.Char(
        string='DV')
    authorization_id = fields.Many2one(
        related='invoice_id.authorization_id')
    invoice_number = fields.Char(
        related='invoice_id.invoice_number')
    invoice_condition = fields.Char(
        string='Condición (Contado / Crédito)', compute='_compute_invoices')
    invoice_date = fields.Date(
        related='invoice_id.invoice_date')
    currency_id = fields.Many2one(
        related='invoice_id.currency_id')
    amount_total = fields.Monetary(
        string='Monto de la factura', currency_field='currency_id', compute='_compute_amount_total')
    amount_iva0 = fields.Monetary(
        string='Exenta', currency_field='currency_id')
    amount_iva5_tax_included = fields.Monetary(
        string='IVA 5% (IVA Incluido)', currency_field='currency_id')
    amount_iva5 = fields.Monetary(
        string='IVA 5%', currency_field='currency_id')
    amount_iva10_tax_included = fields.Monetary(
        string='IVA 10% (IVA Incluido)', currency_field='currency_id')
    amount_iva10 = fields.Monetary(
        string='IVA 10%', currency_field='currency_id')
    serie = fields.Char(
        string='Serie')
    cdc = fields.Char(
        related='invoice_id.cdc_l10n_py')
    out_invoice_stamped = fields.Char(
        related='authorization_id.stamped')
    out_invoice_stamped_date_due = fields.Date(
        related='authorization_id.date_to')
    in_invoice_stamped = fields.Char(
        related='invoice_id.in_invoice_stamped')
    in_invoice_stamped_date_due = fields.Date(
        related='invoice_id.in_invoice_date_due')
    accounts = fields.Char(
        string='Cuentas Contables', compute='_compute_invoices')
    form145_id = fields.Many2one(
        related='invoice_id.form145_id')
    reasons_inclusion_id = fields.Many2one(
        related='invoice_id.form145_reasons_inclusion_id')
    details_inclusion = fields.Char(
        string='Detalles inclusión')
    reasons_cancelled = fields.Char(
        related='invoice_id.books_reports_cancel_reason')
    form120_id = fields.Many2one(
        related='invoice_id.form120_id')
    product_categ = fields.Char(
        string='Categoría de productos', compute='_compute_invoices')
    installment_qty = fields.Integer(
        related='invoice_id.installment_payment_qty')
    in_invoice_latam_doc_type_id = fields.Many2one(
        related='invoice_id.latam_doc_type_id')

    @api.depends('invoice_id')
    def _compute_invoices(self):
        for record in self:
            # Determinar la condición de la factura
            if record.invoice_id.move_type == 'out_refund':
                if 'Descuento' in record.invoice_id.creditdebit_note_id.name:
                    record.invoice_condition = 'DES'

                else:
                    record.invoice_condition = 'DEV'

            else:
                if not record.invoice_id:
                    record.invoice_condition = 'SIN'

                elif record.invoice_id.state == 'cancel':
                    record.invoice_condition = 'ANL'
                
                elif record.invoice_id.invoice_payment_term_id and record.invoice_id.invoice_payment_term_id.is_cash_payment:
                    record.invoice_condition = 'CON'
                
                else:
                    record.invoice_condition = 'CRE'

            # Concatenar los nombres de las cuentas contables
            if record.invoice_id and record.invoice_id.line_ids:
                record.accounts = ', '.join(
                    line.account_id.display_name for line in record.invoice_id.line_ids if line.account_id and line.account_id.name
                )
            else:
                record.accounts = ''

            # Concatenar las categorias de los productos
            if record.invoice_id and record.invoice_id.invoice_line_ids:
                record.product_categ = ', '.join(
                    line.product_id.categ_id.name for line in record.invoice_id.invoice_line_ids if line.product_id and line.product_id.categ_id
                )
            else:
                record.product_categ = ''

    @api.depends('invoice_id')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = abs(record.invoice_id.amount_total_in_currency_signed)
    