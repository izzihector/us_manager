# -*- coding: utf-8 -*-
from odoo import http

# class NamingConvention(http.Controller):
#     @http.route('/naming_convention/naming_convention/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/naming_convention/naming_convention/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('naming_convention.listing', {
#             'root': '/naming_convention/naming_convention',
#             'objects': http.request.env['naming_convention.naming_convention'].search([]),
#         })

#     @http.route('/naming_convention/naming_convention/objects/<model("naming_convention.naming_convention"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('naming_convention.object', {
#             'object': obj
#         })