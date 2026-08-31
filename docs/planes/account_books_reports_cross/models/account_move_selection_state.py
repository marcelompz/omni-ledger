# -*- coding: utf-8 -*-
"""
Created on 2024-12-02 11:52:01

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMoveSelectionState(models.Model):
    _name = 'account.move.selection.state'
    _description = 'Seleccion de estados de factura'

    name = fields.Char(
        string='Estado')
    value = fields.Char(
        string='valor')
