# -*- coding: utf-8 -*-
"""
Created on 2024-11-12 08:46:07

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMoveReceiptType(models.Model):
    _name = 'account.move.receipt.type'
    _description = 'Códigos de tipos de comprobantes'

    name = fields.Char(
        string='Nombre')


class AccountMoveReceiptCode(models.Model):
    _name = 'account.move.receipt.code'
    _description = 'Códigos de tipos de comprobantes'

    code = fields.Char(
        string='Código')
    name = fields.Char(
        string='Nombre')
    type_ids = fields.Many2many(
        'account.move.receipt.type', string='Tipo de registro')
