# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    custom_discount_id = fields.Many2one(comodel_name='pos.custom.discount', string="Custom Discount")
