# -*- coding: utf-8 -*-
# from odoo import http


# class McsOdooCashlez(http.Controller):
#     @http.route('/mcs_odoo_cashlez/mcs_odoo_cashlez/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_odoo_cashlez/mcs_odoo_cashlez/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_odoo_cashlez.listing', {
#             'root': '/mcs_odoo_cashlez/mcs_odoo_cashlez',
#             'objects': http.request.env['mcs_odoo_cashlez.mcs_odoo_cashlez'].search([]),
#         })

#     @http.route('/mcs_odoo_cashlez/mcs_odoo_cashlez/objects/<model("mcs_odoo_cashlez.mcs_odoo_cashlez"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_odoo_cashlez.object', {
#             'object': obj
#         })
