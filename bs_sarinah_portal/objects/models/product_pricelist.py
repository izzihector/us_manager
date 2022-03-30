# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    vendor_product_id = fields.Many2one(comodel_name="vendor.product", string="Vendor Product", required=False)
