# -*- coding: utf-8 -*-
"""
Created on 2024-10-28 11:41:41

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResCompanyEconomicActivity(models.Model):
    _name = 'res.company.economic.activity'
    _description = _('Actividad Económica de la Compañía')

    name = fields.Char(
        string=_('Descripción de la actividad'))
    code = fields.Char(
        string=_('Código de la actividad'))
    company_id = fields.Many2one(
        'res.company',
        string='Compañía')
