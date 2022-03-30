# -*- coding: utf-8 -*-
# from odoo import http


# class McsInheritPpbkConsignment(http.Controller):
#     @http.route('/mcs_inherit_ppbk_consignment/mcs_inherit_ppbk_consignment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_inherit_ppbk_consignment/mcs_inherit_ppbk_consignment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_inherit_ppbk_consignment.listing', {
#             'root': '/mcs_inherit_ppbk_consignment/mcs_inherit_ppbk_consignment',
#             'objects': http.request.env['mcs_inherit_ppbk_consignment.mcs_inherit_ppbk_consignment'].search([]),
#         })

#     @http.route('/mcs_inherit_ppbk_consignment/mcs_inherit_ppbk_consignment/objects/<model("mcs_inherit_ppbk_consignment.mcs_inherit_ppbk_consignment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_inherit_ppbk_consignment.object', {
#             'object': obj
#         })
