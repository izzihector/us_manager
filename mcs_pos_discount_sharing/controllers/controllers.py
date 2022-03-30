# -*- coding: utf-8 -*-
from odoo import http

# class NamaModul(http.Controller):
#     @http.route('/nama_modul/nama_modul/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/nama_modul/nama_modul/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('nama_modul.listing', {
#             'root': '/nama_modul/nama_modul',
#             'objects': http.request.env['nama_modul.nama_modul'].search([]),
#         })

#     @http.route('/nama_modul/nama_modul/objects/<model("nama_modul.nama_modul"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nama_modul.object', {
#             'object': obj
#         })