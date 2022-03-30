# -*- coding: utf-8 -*-
from odoo import http

# class PurchaseDiscountTotal(http.Controller):
#     @http.route('/purchase_rmdoo/purchase_rmdoo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/purchase_rmdoo/purchase_rmdoo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('purchase_rmdoo.listing', {
#             'root': '/purchase_rmdoo/purchase_rmdoo',
#             'objects': http.request.env['purchase_rmdoo.purchase_rmdoo'].search([]),
#         })

#     @http.route('/purchase_rmdoo/purchase_rmdoo/objects/<model("purchase_rmdoo.purchase_rmdoo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('purchase_rmdoo.object', {
#             'object': obj
#         })