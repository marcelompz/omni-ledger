# -*- coding: utf-8 -*-
"""
Created on 2024-10-28 11:28:27

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResCompanyTypeObligations(models.Model):
    _name = 'res.company.type.obligations'
    _description = _('Tipo de obligaciones de la Compañía')

    name = fields.Char(
        string=_('Nombre'))
