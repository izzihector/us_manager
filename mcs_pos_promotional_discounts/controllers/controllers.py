# -*- coding: utf-8 -*-
# from odoo import http


# class McsPosPromotionalDiscounts(http.Controller):
#     @http.route('/mcs_pos_promotional_discounts/mcs_pos_promotional_discounts/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_pos_promotional_discounts/mcs_pos_promotional_discounts/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_pos_promotional_discounts.listing', {
#             'root': '/mcs_pos_promotional_discounts/mcs_pos_promotional_discounts',
#             'objects': http.request.env['mcs_pos_promotional_discounts.mcs_pos_promotional_discounts'].search([]),
#         })

#     @http.route('/mcs_pos_promotional_discounts/mcs_pos_promotional_discounts/objects/<model("mcs_pos_promotional_discounts.mcs_pos_promotional_discounts"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_pos_promotional_discounts.object', {
#             'object': obj
#         })
