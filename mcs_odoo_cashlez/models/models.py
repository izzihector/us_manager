# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class mcs_odoo_cashlez(models.Model):
#     _name = 'mcs_odoo_cashlez.mcs_odoo_cashlez'
#     _description = 'mcs_odoo_cashlez.mcs_odoo_cashlez'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
