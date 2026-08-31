# -*- coding: utf-8 -*-
"""
Created on 2024-12-02 12:48:41

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMoveReasonsInclusion(models.Model):
    _name = 'account.move.reasons.inclusion'
    _description = 'Motivos de inclusión'

    name = fields.Char(
        string='Motivo')
