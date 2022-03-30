# -*- coding: utf-8 -*-
# from odoo import http


# class McsImportProductVendor(http.Controller):
#     @http.route('/mcs_import_product_vendor/mcs_import_product_vendor/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_import_product_vendor/mcs_import_product_vendor/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_import_product_vendor.listing', {
#             'root': '/mcs_import_product_vendor/mcs_import_product_vendor',
#             'objects': http.request.env['mcs_import_product_vendor.mcs_import_product_vendor'].search([]),
#         })

#     @http.route('/mcs_import_product_vendor/mcs_import_product_vendor/objects/<model("mcs_import_product_vendor.mcs_import_product_vendor"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_import_product_vendor.object', {
#             'object': obj
#         })
