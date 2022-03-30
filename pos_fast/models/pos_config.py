# -*- coding: utf-8 -*-
##############################################################################
#
#    TL Technology
#    Copyright (C) 2019 ­TODAY TL Technology (<https://www.posodoo.com>).
#    Odoo Proprietary License v1.0 along with this program.
#
##############################################################################
from odoo import api, fields, models, _
import logging

try:
    to_unicode = unicode
except NameError:
    to_unicode = str

_logger = logging.getLogger(__name__)

class pos_config(models.Model):
    _inherit = "pos.config"

    big_datas_sync_backend = fields.Boolean(
        'Auto Sync Reltime with Backend',
        help='If have any change Products/Customer. POS auto sync with event change',
        default=1)


    def update_required_reinstall_cache(self):
        return self.write({'required_reinstall_cache': False})

    def reinstall_database(self):
        ###########################################################################################################
        # new field append :
        #                    - update param
        #                    - remove logs datas
        #                    - remove cache
        #                    - reload pos
        #                    - reinstall pos data
        # reinstall data button:
        #                    - remove all param
        #                    - pos start save param
        #                    - pos reinstall with new param
        # refresh call logs:
        #                    - get fields domain from param
        #                    - refresh data with new fields and domain
        ###########################################################################################################
        parameters = self.env['ir.config_parameter'].sudo().search([('key', 'in',
                                                                     ['product.product', 'res.partner',
                                                                      'account.invoice',
                                                                      'account.invoice.line', 'pos.order',
                                                                      'pos.order.line',
                                                                      'sale.order', 'sale.order.line'])])
        if parameters:
            parameters.sudo().unlink()
        del_database_sql = ''' delete from pos_cache_database'''
        del_log_sql = ''' delete from pos_call_log'''
        self.env.cr.execute(del_database_sql)
        self.env.cr.execute(del_log_sql)
        self.env.cr.commit()
        for config in self:
            sessions = self.env['pos.session'].sudo().search(
                [('config_id', '!=', config.id), ('state', '!=', 'closed')])
            sessions.write({'required_reinstall_cache': True})
        return {
            'type': 'ir.actions.act_url',
            'url': '/pos/web',
            'target': 'self',
        }