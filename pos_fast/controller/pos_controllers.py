# -*- coding: utf-8 -*-
##############################################################################
#
#    TL Technology
#    Copyright (C) 2019 ­TODAY TL Technology (<https://www.posodoo.com>).
#    Odoo Proprietary License v1.0 along with this program.
#
##############################################################################
from odoo.http import request
from odoo.addons.bus.controllers.main import BusController
from odoo.addons.point_of_sale.controllers.main import PosController
import werkzeug.utils
from odoo import http, _
from odoo.osv.expression import AND

import logging

_logger = logging.getLogger(__name__)


class pos_controller(PosController):

    @http.route('/pos/web', type='http', auth='user')
    def pos_web(self, config_id=False, **k):
        domain = [
            ('state', '=', 'opened'),
            ('user_id', '=', request.session.uid),
            ('rescue', '=', False)
        ]
        if config_id:
            domain = AND([domain, [('config_id', '=', int(config_id))]])
        pos_session = request.env['pos.session'].sudo().search(domain, limit=1)
        if not pos_session:
            return werkzeug.utils.redirect('/web#action=point_of_sale.action_client_pos_menu')
        # The POS only work in one company, so we enforce the one of the session in the context
        session_info = request.env['ir.http'].session_info()
        session_info['model_ids'] = {
            'product.product': {
                'min_id': 0,
                'max_id': 0
            },
            'res.partner': {
                'min_id': 0,
                'max_id': 0
            },
        }
        request.env.cr.execute("select max(id) from product_product")
        product_max_ids = request.env.cr.fetchall()
        session_info['model_ids']['product.product']['max_id'] = product_max_ids[0][0] if len(
            product_max_ids) == 1 else 1
        request.env.cr.execute("select count(id) from product_product")
        count_products = request.env.cr.fetchall()
        session_info['model_ids']['product.product']['count'] = count_products[0][0] if len(
            count_products) == 1 else None
        request.env.cr.execute("select max(id) from res_partner")
        partner_max_ids = request.env.cr.fetchall()
        session_info['model_ids']['res.partner']['max_id'] = partner_max_ids[0][0] if len(partner_max_ids) == 1 else 10
        request.env.cr.execute("select count(id) from res_partner")
        count_partners = request.env.cr.fetchall()
        session_info['model_ids']['res.partner']['count'] = count_partners[0][0] if len(count_partners) == 1 else None
        session_info['user_context']['allowed_company_ids'] = pos_session.company_id.ids
        session_info['user_context']['pos_session_company_ids'] = pos_session.company_id.ids
        session_info['company_currency_id'] = request.env.user.company_id.currency_id.id
        context = {
            'session_info': session_info,
            'login_number': pos_session.login(),
        }
        return request.render('point_of_sale.index', qcontext=context)

class pos_bus(BusController):

    def _poll(self, dbname, channels, last, options):
        channels = list(channels)
        channels.append((request.db, 'pos.sync.backend', request.env.user.id))
        return super(pos_bus, self)._poll(dbname, channels, last, options)
