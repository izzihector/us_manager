# -*- coding: utf-8 -*-
# from odoo import http


# class McsProductNamingBrandCategory(http.Controller):
#     @http.route('/mcs_product_naming_brand_category/mcs_product_naming_brand_category/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_product_naming_brand_category/mcs_product_naming_brand_category/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_product_naming_brand_category.listing', {
#             'root': '/mcs_product_naming_brand_category/mcs_product_naming_brand_category',
#             'objects': http.request.env['mcs_product_naming_brand_category.mcs_product_naming_brand_category'].search([]),
#         })

#     @http.route('/mcs_product_naming_brand_category/mcs_product_naming_brand_category/objects/<model("mcs_product_naming_brand_category.mcs_product_naming_brand_category"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_product_naming_brand_category.object', {
#             'object': obj
#         })
