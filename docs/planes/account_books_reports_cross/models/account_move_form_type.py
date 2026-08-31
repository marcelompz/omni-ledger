# -*- coding: utf-8 -*-
"""
Created on 2024-12-02 11:03:49

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMoveFormType(models.Model):
    _name = 'account.move.form.type'
    _description = 'Tipo y descripción de formulario'

    name = fields.Char(
        string='Descripción')
    form_number = fields.Selection(
        string='Formulario', 
        selection=[('form120', 'Formulario 120'), ('form145', 'Formulario 145')])
