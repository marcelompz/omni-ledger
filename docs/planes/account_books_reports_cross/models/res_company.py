# -*- coding: utf-8 -*-
"""
Created on 2024-10-28 10:03:39

@author: drojo
"""
# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    legal_personality_id = fields.Many2one(
        'res.company.legal.personality', string=_('Personería Jurídica'))
    type_obligations_id = fields.Many2many(
        'res.company.type.obligations',string=_('Tipo de obligaciones'))
    economic_activity_ids = fields.One2many(
        'res.company.economic.activity', 'company_id', string=_('Actividad económica'))
    accountant_identifier_id = fields.Many2one(
        'res.partner', string=_('Identificador del contador'))
    legal_representative_id = fields.Many2one(
        'res.partner', string=_('Representante legal'))
    