# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class hk_wishlist_api(models.Model):
#     _name = 'hk_wishlist_api.hk_wishlist_api'
#     _description = 'hk_wishlist_api.hk_wishlist_api'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
