# -*- coding: utf-8 -*-
"""
Created on 2024-12-10 14:26:51

@author: drojo
"""
# python
import requests  # api
import json  # json format
import codecs  # bytes to xml

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMoveGetinfoWizard(models.TransientModel):
    _name = 'account.move.getinfo.wizard'
    _description = 'Obtener informacion con CDC'

    name = fields.Char(
        string='CDC')

    def get_info(self):
        params = self._get_conection()
        headers = {"Authorization": f'Bearer api_key_{params["api_key"]}'}
        try:
            if self.name != None:
                url = params["url_api"] + "de/xml/" + self.name + "?json=false"
                result = requests.get(url=url, verify=False, headers=headers)

                if result.status_code == 200:
                    raise UserError(f'{codecs.decode(result.content, "UTF-8")}')
                    # return codecs.decode(result.content, "UTF-8")

            # else:
                # for ed_line in self.l10n_py_ids:
                #     if ed_line.name:
                #         url = (
                #             params["url_api"] + "de/xml/" + ed_line.name + "?json=false"
                #         )
                #         result = requests.get(url=url, verify=False, headers=headers)

                #         if result.status_code == 200:
                #             return codecs.decode(result.content, "UTF-8")

            return False

        except Exception as e:
            raise UserError(_(f"error 424: {e}"))



        # params = self._get_conection()

        # try:
        #     url = params["url_api"] + "de/xml/"
        #     headers = {
        #         "Authorization": f'Bearer api_key_{params["api_key"]}',
        #         "Content-Type": "application/json; charset=utf-8",
        #     }

        #     data = f'{self.name or ""}?json=false'
        #     result = requests.get(url=url, verify=False, headers=headers, data=json.dumps(data))
        #     res_json = result.json()

        #     if result.status_code == 200:

        #         raise UserError(f'Result: {result}, json: {res_json}')
                # if res_json['success'] == True:
                #     self.de_requested = True

                #     for delist in res_json["deList"]:
                #         reg.de_status = str(delist['situacion'])
                #         reg.response_code = delist['respuesta_codigo']
                #         reg.response_message = delist['respuesta_mensaje']

                #         if reg.de_status == '2':
                #             reg.is_ed_cancelled = False
                        
                #         if delist['situacion'] == 4 and len(reg.l10n_py_ids) > 0:
                #             reg.l10n_py_ids[0].ed_status = 'refused'

                #         # Mostrar notificación solo si show_notification es True
                #         if show_notification:
                #             return {
                #                 'type': 'ir.actions.client',
                #                 'tag': 'display_notification',
                #                 'params': {
                #                     'title': _('Consulta exitosa!'),
                #                     'type': 'success',
                #                     'sticky': False,
                #                 },
                #             }

        #     else:
        #         raise UserError(f'error 67: {result}')

        # except Exception as e:
        #     raise UserError(_(f"error 70: {e}"))

    def _get_conection(self, company=False):
        company = company or self.env.company

        return {
            'url_api': company.url_api_facturasend or False,
            'api_key': company.api_key_facturasend or False,
            'sync_communication': company.sync_communication_facturasend or False,
        }
