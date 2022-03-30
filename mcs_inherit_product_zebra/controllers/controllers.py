# -*- coding: utf-8 -*-
# from odoo import http


# class McsInheritProductZebra(http.Controller):
#     @http.route('/mcs_inherit_product_zebra/mcs_inherit_product_zebra/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_inherit_product_zebra/mcs_inherit_product_zebra/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_inherit_product_zebra.listing', {
#             'root': '/mcs_inherit_product_zebra/mcs_inherit_product_zebra',
#             'objects': http.request.env['mcs_inherit_product_zebra.mcs_inherit_product_zebra'].search([]),
#         })

#     @http.route('/mcs_inherit_product_zebra/mcs_inherit_product_zebra/objects/<model("mcs_inherit_product_zebra.mcs_inherit_product_zebra"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_inherit_product_zebra.object', {
#             'object': obj
#         })
