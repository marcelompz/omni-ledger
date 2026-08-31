# -*- coding: utf-8 -*-
"""
Created on 2024-11-06 08:40:08

@author: drojo
"""
# python
import base64
from datetime import datetime
import csv
import io
import zipfile
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


class RG90ReportWizard(models.TransientModel):
    _name = 'rg90.report.wizard'
    _descripcion = 'Reportes de RG90'

    TYPE_SELECTION = [
        ('out_invoice',_('VENTAS')),
        ('in_invoice',_('COMPRAS')),
        ('income',_('INGRESOS')),
        ('revenue',_('EGRESOS')),
    ]

    date_from = fields.Date(
        string='Fecha desde', default=lambda self: self._get_date_from_to(option='from'))
    date_to = fields.Date(
        string='Fecha hasta', default=lambda self: self._get_date_from_to())
    report_type = fields.Selection(
        string='Tipo', selection=TYPE_SELECTION, default='out_invoice')
    invoice_state_ids = fields.Many2many(
        'account.move.selection.state', string='Estado', default=lambda self: self._default_invoice_state_ids())
    file_type = fields.Selection(
        string='Tipo de archivo', selection=[('txt','TXT'),('csv','CSV')], default='txt')
    lines_ids = fields.One2many(
        'rg90.lines.wizard', 'report_id', string='Líneas del reporte')
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

    def get_fiscal_years(self, date_from, date_to, to_report_name=False):
        if to_report_name:      # Generamos el periodo fiscal para el nombre del reporte
            # Convertir las fechas a objetos datetime si no lo están
            if isinstance(date_from, str):
                date_from = datetime.strptime(date_from, "%Y-%m-%d")
            if isinstance(date_to, str):
                date_to = datetime.strptime(date_to, "%Y-%m-%d")
            
            # Comparar el mes y año de las dos fechas
            if date_from.year == date_to.year and date_from.month == date_to.month:
                # Mismo mes y año, retornar mes y año en formato MMYYYY
                return f"{date_from.month:02}{date_from.year}"
            else:
                # Mes o año diferente, retornar solo el año
                return str(date_from.year)

        # Extraer los años de date_from y date_to
        year_from = date_from.year
        year_to = date_to.year
        
        # Si los años son iguales, devolver ese año
        if year_from == year_to:
            return str(year_from)
        
        # Si los años son diferentes, devolver el rango de años
        return ', '.join(str(year) for year in range(year_from, year_to + 1))

    def button_action_generate_report(self):
        # Codigo del registro
        register_code = {
            'out_invoice': 1,
            'in_invoice': 2,
            'income': 3,
            'revenue': 4,
        }
        # Mapeo de códigos del tipo de identificación
        identification_type_map = {
            0: 11,  # RUC
            1: 12,  # CI
            2: 13,  # Pasaporte
            3: 14,  # Cedula extranjero
            5: 15,  # Sin nombre
            6: 16,  # Diplomatico
            17: 17, # Identificacion tributaria
            18: 18, # Cliente del exterior
        }
        # Tipo de movimiento y Código del tipo de comprobante
        # Definir los posibles tipos de movimiento
        outbound_types = {'out_invoice', 'income'}
        inbound_types = {'in_invoice', 'revenue'}

        # Determinar el tipo de movimiento
        move_type = 'out_invoice' if self.report_type in outbound_types else 'in_invoice'

        # Mapeo de tipos de reporte a referencias
        receipt_type_map = {
            'out_invoice': 'account_books_reports_cross.cross_amrt_out_invoice',
            'income': 'account_books_reports_cross.cross_amrt_income',
            'in_invoice': 'account_books_reports_cross.cross_amrt_in_invoice',
            'revenue': 'account_books_reports_cross.cross_amrt_revenue'
        }

        # Obtener la referencia del tipo de comprobante
        receipt_type_ref = receipt_type_map.get(self.report_type)
        if not receipt_type_ref:
            raise ValidationError(_("Tipo de reporte inválido: %s") % self.report_type)

        receipt_type = self.env.ref(receipt_type_ref, raise_if_not_found=False)
        if not receipt_type:
            raise ValidationError(_("No se encontró la referencia para el tipo de comprobante: %s") % self.report_type)

        # Obtener los tipos de timbrado habilitados para el reporte
        latam_doc_type_enabled = self.env['l10n_latam.document.type'].search([
            ('name', 'not ilike', '%virtual%'),
            ('name', 'not ilike', '%electr%')
        ]).ids

        # Búsqueda de facturas según los criterios de tipo, fecha y estado
        invoices = self.env['account.move'].search([
            ('move_type', '=', move_type),                                  # Tipo de factura (ventas, compras, ingreso o egreso)
            ('invoice_date', '>=', self.date_from),                         # Fecha desde
            ('invoice_date', '<=', self.date_to),                           # Fecha hasta
            ('state', 'in', self.invoice_state_ids.mapped('value')),        # Estado de la factura
            ('fiscal_document', '=', True),                                 # Es documento fiscal?
            ('is_ed', '=', False),                                          # No es facturación electrónica
            ('company_id', '=', self.env.company.id),                       # Compañía actual
            ('receipt_type_id.type_ids', 'in', receipt_type.ids),           # Tipo de comprobante
            # ('latam_doc_type_id', 'in', latam_doc_type_enabled),            # Tipo de timbrados habilitados para el reporte
        ])

        # Tipo de imputaciones de la compañía
        company_impute_types = [type.name for type in self.env.company.type_obligations_id]

        # Eliminar líneas de reporte anteriores
        self.lines_ids.unlink()

        lines = []

        # Recorrer las facturas para generar las líneas de reporte
        for line in invoices:
            # Obtener montos por tipo de impuesto
            tax0 = self._get_amount_with_taxes(0, line)
            tax5 = self._get_amount_with_taxes(5, line)
            tax10 = self._get_amount_with_taxes(10, line)
            
            # Definir valor por defecto según el país y tipo de documento
            if line.partner_id.country_code == 'PY':
                identification_type = identification_type_map.get(5)  # 'Sin nombre' por defecto

                if line.partner_id.vat and line.partner_id.l10n_latam_identification_type_id:
                    identification_type = identification_type_map.get(
                        line.partner_id.l10n_latam_identification_type_id.document_id, 5)
            else:
                # Clientes del exterior
                identification_type = identification_type_map.get(18)  # 'Cliente del exterior'
                if not line.partner_id.vat or not line.partner_id.l10n_latam_identification_type_id:
                    identification_type = 18  # Aplicar código para cliente del exterior

            # Pasamos la fecha o periodo a str            
            if line.receipt_period:
                receipt_period_str = line.receipt_period.strftime('%d/%m/%Y')
                receipt_period_str = receipt_period_str[3:] if line.receipt_type_id.code == '208' else receipt_period_str

            else:
                receipt_period_str = ''

            # Número de timbrado
            if line.move_type == 'out_invoice':
                stamped = line.authorization_id.stamped if line.authorization_id else ''

            else:
                stamped = line.in_invoice_stamped or ''

            # Número de identificacion
            if identification_type not in [15, 18]:
                partner_vat = line.partner_id.vat.split('-')[0]

            elif identification_type == 15:
                partner_vat = 'X'

            else:
                partner_vat = '1'

            # Crear líneas de reporte
            lines.append((0, 0, {
                'code': register_code.get(self.report_type),
                'identification_type': identification_type,
                'partner_vat': partner_vat,
                'partner_id': line.partner_id.id or '',
                'receipt_type': line.receipt_type_id.code if line.receipt_type_id else '',
                'date': line.invoice_date,
                'stamped': stamped,
                'receipt_number': line.invoice_number or line.name,
                'currency_id': line.currency_id.id,
                'amount_iva10_tax_included': tax10,
                'amount_iva5_tax_included': tax5,
                'amount_iva0': tax0,
                'amount_total': (tax0 + tax5 + tax10),
                'receipt_condition': 1 if line.invoice_payment_term_id.is_cash_payment else 2,
                'foreign_currency': 'N' if line.currency_id.name == 'PYG' else 'S',
                'impute_iva': 'S' if 'IVA' in company_impute_types else 'N',
                'impute_ire': 'S' if any("IRE" in type_name for type_name in company_impute_types) else 'N',
                'impute_irp': 'S' if 'IRP' in company_impute_types else 'N',
                'no_impute': 'N',
                'associated_receipt': (line.reversal_move_id.invoice_number or line.reversal_move_id.name) if line.reversal_move_id else '',
                'stamped_associated_receipt': line.reversal_move_id.authorization_id.stamped if line.reversal_move_id else '',
                'receipt_period': receipt_period_str,
                'specify_document_type': line.specify_document_type,
            }))

        # Asignar las líneas generadas al campo correspondiente
        self.lines_ids = lines

        if self.file_type in ['csv','txt']:
            # Llamada para generar CSV
            return self.generate_csv_report(self.file_type)

        else:
            raise UserError(f'Seleccione un tipo de archivo permitido.')

    def _get_amount_with_taxes(self, tax, invoice):
        # Inicialización de los montos de impuestos
        tax10 = tax5 = tax0 = 0

        # Verificamos si se realizo con moneda de la empresa
        # company_currency = invoice.currency_id == self.env.company.currency_id

        # Recorrer las líneas de factura para sumar montos por tipo de impuesto
        for line in invoice.invoice_line_ids:
            # Cambiamos de acuerdo a la cotizacion en caso de ser moneda extranjera
            # price = line.price_total if company_currency else invoice.currency_id._convert(
                # line.price_total, self.env.company.currency_id, self.env.company, invoice.invoice_date)

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
            return tax10
        elif tax == 5:
            return tax5
        else:
            return tax0

    def generate_csv_report(self, format):
        """
        Genera un archivo CSV en memoria para diferentes tipos de reportes.

        Parámetros:
            format (str): El formato del archivo ('csv' o 'txt').

        Retorna:
            str: Los datos del archivo CSV en formato base64.
        """
        try:
            output = io.StringIO()
            delimiter = '\t' if format == 'txt' else ','
            writer = csv.writer(output, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)

            if self.report_type == 'out_invoice':
                self._write_sales_data(writer)
            elif self.report_type == 'in_invoice':
                self._write_purchase_data(writer)
            elif self.report_type == 'income':
                self._write_income_data(writer)
            elif self.report_type == "revenue":
                self._write_revenue_data(writer)
            else:
                return ""

            output.seek(0)
            file_data = output.getvalue()
            output.close()

        except Exception as e:
            raise UserError(f"Error al generar el reporte CSV: {e}")

        # Extraemos el RUC de la empresa sin el DV
        company_vat = self.env.company.vat.split('-')[0]

        # Obtenemos el periodo fiscal
        fiscal_period = self.get_fiscal_years(self.date_from, self.date_to, to_report_name=True)

        # Obtenemos el número del archivo desde la secuencia rg90.report.wizard
        type_mapping = dict(self.TYPE_SELECTION)
        version = type_mapping.get(self.report_type, 'V')[:1] + self.env['ir.sequence'].next_by_code('rg90.report.wizard')

        # Obtenemos la extensión del archivo según la selección del usuario (TXT o CSV)
        file_extension = self.file_type  # Será 'txt' o 'csv'

        # Nombre del archivo original (TXT o CSV)
        original_filename = _('%s_REG_%s_%s.%s' % (company_vat, fiscal_period, version, file_extension))

        # Nombre del archivo ZIP
        zip_filename = _('%s_REG_%s_%s.zip' % (company_vat, fiscal_period, version))

        # Crear un ZIP en memoria
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(original_filename, file_data)  # Agregamos el TXT o CSV al ZIP

        # Obtener el contenido del ZIP
        zip_buffer.seek(0)
        zip_data = zip_buffer.getvalue()

        # Codificar el ZIP en base64
        zip_base64 = base64.b64encode(zip_data)

        # Crear el archivo adjunto en Odoo
        attachment = self.env['ir.attachment'].create({
            'name': zip_filename,
            'type': 'binary',
            'datas': zip_base64,
            'store_fname': zip_filename,
            'mimetype': 'application/zip'
        })

        # Descargar el ZIP
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def _write_sales_data(self, writer):
        """Escribe los datos de ventas en el archivo CSV."""
        for line in self.lines_ids:
            try:
                # Obtener los decimales de la moneda
                decimal_places = line.currency_id.decimal_places or 0

                # Formatear montos con punto decimal
                tax10_str = f"{line.amount_iva10_tax_included:.{decimal_places}f}"
                tax5_str = f"{line.amount_iva5_tax_included:.{decimal_places}f}"
                tax0_str = f"{line.amount_iva0:.{decimal_places}f}"
                total_str = f"{line.amount_total:.{decimal_places}f}"

                row = [
                    line.code,
                    line.identification_type,
                    line.partner_vat,
                    line.partner_id.name,
                    line.receipt_type,
                    line.date.strftime('%d/%m/%Y'),
                    line.stamped,
                    line.receipt_number,
                    tax10_str,
                    tax5_str,
                    tax0_str,
                    total_str,
                    line.receipt_condition,
                    line.foreign_currency,
                    line.impute_iva,
                    line.impute_ire,
                    line.impute_irp,
                    line.associated_receipt,
                    line.stamped_associated_receipt,
                ]
                writer.writerow(row)
            except (ValueError, AttributeError) as e:
                raise UserError(f"Error en la línea de ventas: {e}")

    def _write_purchase_data(self, writer):
        """Escribe los datos de compras en el archivo CSV."""
        for line in self.lines_ids:
            try:
                # Obtener los decimales de la moneda
                decimal_places = line.currency_id.decimal_places or 0

                # Formatear montos con punto decimal
                tax10_str = f"{line.amount_iva10_tax_included:.{decimal_places}f}"
                tax5_str = f"{line.amount_iva5_tax_included:.{decimal_places}f}"
                tax0_str = f"{line.amount_iva0:.{decimal_places}f}"
                total_str = f"{line.amount_total:.{decimal_places}f}"

                row = [
                    line.code,
                    line.identification_type,
                    line.partner_vat,
                    line.partner_id.name,
                    line.receipt_type,
                    line.date.strftime('%d/%m/%Y'),
                    line.stamped,
                    line.receipt_number,
                    tax10_str,
                    tax5_str,
                    tax0_str,
                    total_str,
                    line.receipt_condition,
                    line.foreign_currency,
                    line.impute_iva,
                    line.impute_ire,
                    line.impute_irp,
                    line.no_impute,
                    line.associated_receipt,
                    line.stamped_associated_receipt,
                ]
                writer.writerow(row)
            except (ValueError, AttributeError) as e:
                raise UserError(f"Error en la línea de compras: {e}")

    def _write_income_data(self, writer):
        """Escribe los datos de ingresos en el archivo CSV."""
        for line in self.lines_ids:
            try:
                # Obtener los decimales de la moneda
                decimal_places = line.currency_id.decimal_places or 0

                # Sumar antes de formatear
                tax_sum = line.amount_iva10_tax_included + line.amount_iva5_tax_included

                # Luego convertís todo a string con decimales
                tax0_str = f"{line.amount_iva0:.{decimal_places}f}"
                total_str = f"{line.amount_total:.{decimal_places}f}"
                tax_sum_str = f"{tax_sum:.{decimal_places}f}"

                row = [
                    line.code,
                    line.receipt_type,
                    line.receipt_period,
                    line.receipt_number,
                    line.identification_type,
                    line.partner_vat,
                    line.partner_id.name,
                    tax_sum_str,
                    tax0_str,
                    total_str,
                    line.impute_ire,
                    line.impute_irp,
                    line.specify_document_type,
                    line.associated_receipt,
                    line.stamped_associated_receipt,
                ]
                writer.writerow(row)
            except (ValueError, AttributeError) as e:
                raise UserError(f"Error en la línea de ingresos: {e}")

    def _write_revenue_data(self, writer):
        """Escribe los datos de egresos en el archivo CSV."""
        for line in self.lines_ids:
            try:
                # Obtener los decimales de la moneda
                decimal_places = line.currency_id.decimal_places or 0

                # Luego convertís todo a string con decimales
                total_str = f"{line.amount_total:.{decimal_places}f}"
                row = [
                    line.code,
                    line.receipt_type,
                    line.date.strftime('%d/%m/%Y'),
                    line.receipt_number,
                    line.identification_type,
                    line.partner_vat,
                    line.partner_id.name,
                    total_str,
                    line.impute_iva,
                    line.impute_ire,
                    line.impute_irp,
                    line.no_impute,
                    line.account_number,
                    line.bank,
                    line.employer_vat,
                    line.receipt_type_specific,
                    line.associated_receipt,
                    line.stamped_associated_receipt,
                ]
                writer.writerow(row)
            except (ValueError, AttributeError) as e:
                raise UserError(f"Error en la línea de egresos: {e}")


class RG90LinesWizard(models.TransientModel):
    _name = 'rg90.lines.wizard'
    _descripcion = 'Líneas del reportes de libros IVA'

    report_id = fields.Many2one(
        'rg90.report.wizard', string='Reporte')
    code = fields.Integer(
        string='Código tipo de registro')
    identification_type = fields.Integer(
        string='Código tipo de identificación')
    partner_vat = fields.Char(
        string='Número de identificación')
    partner_id = fields.Many2one(
        'res.partner', string='Nombre o Razón Social')
    receipt_type = fields.Integer(
        string='Código tipo de comprobante')
    date = fields.Date(
        string='Fecha de emisión del comprobante')
    stamped = fields.Char(
        string='Número de timbrado')
    receipt_number = fields.Char(
        string='Número del comprobante')
    currency_id = fields.Many2one(
        'res.currency', string='Moneda')
    amount_iva10_tax_included = fields.Monetary(
        string='Monto gravado al 10% (IVA incluido)', currency_field='currency_id', default=0.0)
    amount_iva5_tax_included = fields.Monetary(
        string='Monto gravado al 5% (IVA incluido)', currency_field='currency_id', default=0.0)
    amount_iva0 = fields.Monetary(
        string='Monto no gravado o exento', currency_field='currency_id', default=0.0)
    amount_total = fields.Monetary(
        string='Monto total del comprobante', currency_field='currency_id', default=0.0)
    receipt_condition = fields.Integer(
        string='Código condición de venta')
    foreign_currency = fields.Char(
        string='Operación en moneda extranjera')
    impute_iva = fields.Char(
        string='Imputa al IVA')
    impute_ire = fields.Char(
        string='Imputa al IRE')
    impute_irp = fields.Char(
        string='Imputa al IRP-RSP')
    associated_receipt = fields.Char(
        string='Número del comprobante de venta asociado')
    stamped_associated_receipt = fields.Char(
        string='Timbrado de comprobante de venta asociado')
    no_impute = fields.Char(
        string='No imputa')
    receipt_type_specific = fields.Char(
        string='Especificar tipo de documento')
    account_number = fields.Char(
        string='Número de cuenta')
    bank = fields.Char(
        string='Banco / Financiera / Cooperativa')
    employer_vat = fields.Char(
        string='Número de identificación del empleador (IPS)')
    receipt_period = fields.Char(
        string='Fecha de emisión o periodo de del comprobante')
    specify_document_type = fields.Char(
        string='Especificar tipo de documento')
    