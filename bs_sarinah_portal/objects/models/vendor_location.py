# -*- coding: utf-8 -*-
# Copyright 2020 Bumiswa
from odoo import api, fields, models


class VendorLocation(models.Model):
    _inherit = 'vendor.location'

    branch_id = fields.Many2one(comodel_name="res.branch", string="Branch")
    location_id = fields.Many2one(comodel_name="stock.location", string="Stock Location")
    vendor_quant_ids = fields.One2many(comodel_name="vendor.quant", inverse_name="vendor_location_id", string="Vendor Quant ",)
    stock_quant_ids = fields.One2many(comodel_name="stock.quant", related="location_id.quant_ids", string="Stock Quant ",)

    def get_vendor_stock_quants(self):
        self.ensure_one()
        return self.stock_quant_ids.filtered(
            lambda quant: quant.sudo().product_id.owner_id == self.env.user.partner_id
        )

