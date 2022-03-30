# -*- coding: utf-8 -*-
# from odoo import http


# class McsAsplPosDiscountAuto(http.Controller):
#     @http.route('/mcs_aspl_pos_discount_auto/mcs_aspl_pos_discount_auto/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_aspl_pos_discount_auto/mcs_aspl_pos_discount_auto/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_aspl_pos_discount_auto.listing', {
#             'root': '/mcs_aspl_pos_discount_auto/mcs_aspl_pos_discount_auto',
#             'objects': http.request.env['mcs_aspl_pos_discount_auto.mcs_aspl_pos_discount_auto'].search([]),
#         })

#     @http.route('/mcs_aspl_pos_discount_auto/mcs_aspl_pos_discount_auto/objects/<model("mcs_aspl_pos_discount_auto.mcs_aspl_pos_discount_auto"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_aspl_pos_discount_auto.object', {
#             'object': obj
#         })
