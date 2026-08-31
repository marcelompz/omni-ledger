# -*- coding: utf-8 -*-
"""
Created on 2025-04-11 10:21:51

@author: drojo
"""
# python
import base64
from io import BytesIO
import logging

# odoo
from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)


class FinancialReportCollectpayWizard(models.TransientModel):
    _name = 'financial.report.collectpay.wizard'
    _description = 'Reporte financiero'

    name = fields.Char(
        string='Título del reporte')
    date_from = fields.Date(
        string='Desde')
    date_to = fields.Date(
        string='Hasta')
    move_ids = fields.Many2many(
        'account.move', string='Facturas')

    def generate_xlsx_report(self):
        '''Genera el reporte en formato xlsx'''

        with BytesIO() as output:
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet()
            worksheet.hide_gridlines(2) # oculta las lineas de la cuadrícula

            # Define formatos
            title_cells = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
            subtitle_cells = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter'})
            header_column = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 8, 'align': 'center', 'bg_color': '#3F93CA', 'border': 1, 'valign': 'vcenter'})
            identities = workbook.add_format({'font_name': 'Arial', 'font_size': 8, 'align': 'left'})
            identities_title = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 8, 'align': 'center', 'border': 1, 'valign': 'vcenter'})
            identities_data = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 8, 'align': 'left', 'border': 1, 'valign': 'vcenter'})
            data_cells = workbook.add_format({'font_name': 'Arial', 'font_size': 8, 'align': 'center', 'border': 1})
            data_cells_names = workbook.add_format({'font_name': 'Arial', 'font_size': 8, 'align': 'left', 'border': 1})

            # Obtener el número de decimales de la moneda de la empresa
            decimal_places = self.env.company.currency_id.decimal_places
            # Crear el formato de número basado en la cantidad de decimales
            decimal_format_str = '#,##0.' + ('0' * decimal_places if decimal_places > 0 else '')

            number_cells_company_currency = workbook.add_format({
                'font_name': 'Arial',
                'font_size': 8,
                'align': 'right',
                'border': 1,
                'num_format': decimal_format_str
            })

            # Definimos la anchura de las columnas
            worksheet.set_column('A:C', 15)
            worksheet.set_column('D:E', 7)
            worksheet.set_column('E:E', 1)
            worksheet.set_column('F:F', 1)
            worksheet.set_column('G:H', 15)
            worksheet.set_column('I:I', 1)
            worksheet.set_column('J:L', 15)
            worksheet.set_column('M:M', 1)
            worksheet.set_column('N:N', 7)
            worksheet.set_column('O:P', 15)
            worksheet.set_column('Q:R', 7)

            # Establecemos el alto de la fila y escribimos el encabezado
            worksheet.set_row(0, 20)
            worksheet.merge_range(0, 0, 0, 17, self.name, title_cells)
            
            # Actividades de la empresa
            activities =' / '.join(line.name for line in self.env.company.type_obligations_id)
            worksheet.set_row(1, 20)
            worksheet.merge_range(1, 0, 1, 17, f'ACTIVIDAD: {activities} - A LA FECHA: {self.date_to}', subtitle_cells)
            
            worksheet.write(2, 0, '1. Identificador del Contribuyente', identities)
            worksheet.write(2, 6, '2. Periodo Fiscal', identities)
            worksheet.write(2, 9, '3. Representante Legal', identities)
            worksheet.write(2, 13, '4. Identificador del Contador', identities)

            worksheet.merge_range(3, 0, 3, 2, 'RAZON SOCIAL/NOMBRES Y APELLIDOS', identities_title)
            worksheet.merge_range(3, 3, 3, 4, 'RUC', identities_title)
            worksheet.merge_range(4, 0, 4, 2, self.env.company.name, identities_data)
            worksheet.merge_range(4, 3, 4, 4, self.env.company.vat, identities_data)

            worksheet.write(3, 6, 'DESDE', identities_title)
            worksheet.write(3, 7, 'HASTA', identities_title)
            worksheet.write(4, 6, self.date_to.strftime('%d-%m-%Y'), identities_data)
            worksheet.write(4, 7, self.date_from.strftime('%d-%m-%Y'), identities_data)
            
            worksheet.merge_range(3, 9, 3, 11, 'NOMBRES Y APELLIDOS', identities_title)
            worksheet.merge_range(4, 9, 4, 11, self.env.company.legal_representative_id.name or '', identities_data)
            
            worksheet.merge_range(3, 13, 3, 15, 'NOMBRES Y APELLIDOS', identities_title)
            worksheet.merge_range(3, 16, 3, 17, 'RUC', identities_title)
            worksheet.merge_range(4, 13, 4, 15, self.env.company.accountant_identifier_id.name or '', identities_data)
            worksheet.merge_range(4, 16, 4, 17, self.env.company.accountant_identifier_id.vat or '', identities_data)

            # Definimos las filas (y)
            y = 6
        
            # Creamos el encabezado de las columnas
            worksheet.write(y, 0,'DOCUMENTO', header_column)
            worksheet.write(y, 1,'FECHA', header_column)
            worksheet.write(y, 2,'RUC', header_column)
            worksheet.merge_range(y, 3, y, 12,'RAZON SOCIAL', header_column)
            worksheet.write(y, 13,'MON.', header_column)
            worksheet.write(y, 14,'TOTAL', header_column)
            worksheet.write(y, 15,'SALDO', header_column)
            worksheet.merge_range(y, 16, y, 17,'SALDO GS.', header_column)
        
            # Escribir los datos
            row = y + 1
            for line in self.move_ids:
                # Obtener el número de decimales de la moneda de la línea
                decimal_places = line.currency_id.decimal_places
                # Crear el formato de número basado en la cantidad de decimales
                decimal_format_str = '#,##0.' + ('0' * decimal_places if decimal_places > 0 else '')

                number_cells = workbook.add_format({
                    'font_name': 'Arial',
                    'font_size': 8,
                    'align': 'right',
                    'border': 1,
                    'num_format': decimal_format_str
                })

                worksheet.write(row, 0, line.invoice_number or line.name or '',data_cells)
                worksheet.write(row, 1, line.invoice_date.strftime('%d-%m-%Y'),data_cells)
                worksheet.write(row, 2, line.partner_id.vat or '',data_cells)
                worksheet.merge_range(row, 3, row, 12, line.partner_id.name or '',data_cells_names)
                worksheet.write(row, 13, line.currency_id.name or '',data_cells)
                worksheet.write(row, 14, line.amount_total_in_currency_signed or 0,number_cells)
                worksheet.write(row, 15, line.amount_residual or 0,number_cells)
                worksheet.merge_range(row, 16, row, 17, line.amount_residual_signed or 0,number_cells_company_currency)

                row += 1

            # Cerramos y preparamos la descarga
            workbook.close()
            output.seek(0)

            xlsx_data = output.read()

        # Asignamos el nombre al reporte
        report_name = _('%s - %s a %s' % (
            self.name, 
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
