# -*- coding: utf-8 -*-
# from odoo import http


# class McsAsplPosPromotion(http.Controller):
#     @http.route('/mcs_aspl_pos_promotion/mcs_aspl_pos_promotion/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_aspl_pos_promotion/mcs_aspl_pos_promotion/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_aspl_pos_promotion.listing', {
#             'root': '/mcs_aspl_pos_promotion/mcs_aspl_pos_promotion',
#             'objects': http.request.env['mcs_aspl_pos_promotion.mcs_aspl_pos_promotion'].search([]),
#         })

#     @http.route('/mcs_aspl_pos_promotion/mcs_aspl_pos_promotion/objects/<model("mcs_aspl_pos_promotion.mcs_aspl_pos_promotion"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_aspl_pos_promotion.object', {
#             'object': obj
#         })
