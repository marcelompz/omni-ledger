# -*- coding: utf-8 -*-
"""
Created on 2024-12-16 18:01:08

@author: drojo
"""
# python
import requests  # api
import json  # json format

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResCancelDocumentWizardInherit(models.TransientModel):
    _inherit = 'res.cancel.document.wizard'

    def action_cancel_document(self):
        self.account_id.write({'books_reports_cancel_reason': self.reason})
        return super().action_cancel_document()
