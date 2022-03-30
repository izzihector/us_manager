# -*- coding: utf-8 -*-
# Copyright 2021 Linksoft Mitra Informatika

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vendor_quant_validation_method = fields.Selection(string="Vendor Quant Validation Method", selection=[
                        ("goods_receipt","Goods Receipt"), 
                        ("inventory_adjustment","Inventory Adjustment"), 
                        ], required=False  )

    # @api.model
    def get_values(self):
        """
        Overwrite to add new system params
        """
        ICP = self.env['ir.config_parameter'].sudo()
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'vendor_quant_validation_method': ICP.get_param('vendor_portal.quant_validation_method') or 'goods_receipt'
        })
        return res

    def set_values(self):
        """
        Overwrite to add new system params
        """
        ICP = self.env['ir.config_parameter'].sudo()
        super(ResConfigSettings, self).set_values()
        value = getattr(self, 'vendor_quant_validation_method', 'False')
        ICP.set_param('vendor_portal.quant_validation_method', value)
