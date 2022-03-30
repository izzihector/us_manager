# -*- coding: utf-8 -*-
# from odoo import http


# class McsGsfInheritPrForAsset(http.Controller):
#     @http.route('/mcs_gsf_inherit_pr_for_asset/mcs_gsf_inherit_pr_for_asset/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mcs_gsf_inherit_pr_for_asset/mcs_gsf_inherit_pr_for_asset/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mcs_gsf_inherit_pr_for_asset.listing', {
#             'root': '/mcs_gsf_inherit_pr_for_asset/mcs_gsf_inherit_pr_for_asset',
#             'objects': http.request.env['mcs_gsf_inherit_pr_for_asset.mcs_gsf_inherit_pr_for_asset'].search([]),
#         })

#     @http.route('/mcs_gsf_inherit_pr_for_asset/mcs_gsf_inherit_pr_for_asset/objects/<model("mcs_gsf_inherit_pr_for_asset.mcs_gsf_inherit_pr_for_asset"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mcs_gsf_inherit_pr_for_asset.object', {
#             'object': obj
#         })
