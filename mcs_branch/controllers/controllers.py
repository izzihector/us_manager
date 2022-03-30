# -*- coding: utf-8 -*-
# from odoo import http


# class McsBranch(http.Controller):
#     @http.route('/mcs_branch/mcs_branch/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_branch/mcs_branch/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_branch.listing', {
#             'root': '/mcs_branch/mcs_branch',
#             'objects': http.request.env['mcs_branch.mcs_branch'].search([]),
#         })

#     @http.route('/mcs_branch/mcs_branch/objects/<model("mcs_branch.mcs_branch"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_branch.object', {
#             'object': obj
#         })
