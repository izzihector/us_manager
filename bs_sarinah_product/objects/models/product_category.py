# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_for_coupon = fields.Boolean(string='For Coupon Product')

