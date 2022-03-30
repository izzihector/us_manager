# -*- coding: utf-8 -*-
# from odoo import http


# class McsVernossProduct(http.Controller):
#     @http.route('/mcs_vernoss_product/mcs_vernoss_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_vernoss_product/mcs_vernoss_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_vernoss_product.listing', {
#             'root': '/mcs_vernoss_product/mcs_vernoss_product',
#             'objects': http.request.env['mcs_vernoss_product.mcs_vernoss_product'].search([]),
#         })

#     @http.route('/mcs_vernoss_product/mcs_vernoss_product/objects/<model("mcs_vernoss_product.mcs_vernoss_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_vernoss_product.object', {
#             'object': obj
#         })
