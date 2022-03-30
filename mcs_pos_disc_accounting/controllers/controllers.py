# -*- coding: utf-8 -*-
# from odoo import http


# class McsPosDiscAccounting(http.Controller):
#     @http.route('/mcs_pos_disc_accounting/mcs_pos_disc_accounting/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_pos_disc_accounting/mcs_pos_disc_accounting/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_pos_disc_accounting.listing', {
#             'root': '/mcs_pos_disc_accounting/mcs_pos_disc_accounting',
#             'objects': http.request.env['mcs_pos_disc_accounting.mcs_pos_disc_accounting'].search([]),
#         })

#     @http.route('/mcs_pos_disc_accounting/mcs_pos_disc_accounting/objects/<model("mcs_pos_disc_accounting.mcs_pos_disc_accounting"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_pos_disc_accounting.object', {
#             'object': obj
#         })
