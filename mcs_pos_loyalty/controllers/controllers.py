# -*- coding: utf-8 -*-
# from odoo import http


# class McsPosLoyalty(http.Controller):
#     @http.route('/mcs_pos_loyalty/mcs_pos_loyalty/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_pos_loyalty/mcs_pos_loyalty/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_pos_loyalty.listing', {
#             'root': '/mcs_pos_loyalty/mcs_pos_loyalty',
#             'objects': http.request.env['mcs_pos_loyalty.mcs_pos_loyalty'].search([]),
#         })

#     @http.route('/mcs_pos_loyalty/mcs_pos_loyalty/objects/<model("mcs_pos_loyalty.mcs_pos_loyalty"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_pos_loyalty.object', {
#             'object': obj
#         })
