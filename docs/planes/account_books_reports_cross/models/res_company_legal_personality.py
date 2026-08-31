# -*- coding: utf-8 -*-
"""
Created on 2024-10-28 10:24:04

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResCompanyLegalPersonality(models.Model):
    _name = 'res.company.legal.personality'
    _description = _('Personaría Jurídica de la Compañía')

    name = fields.Char(
        string=_('Nombre'))
