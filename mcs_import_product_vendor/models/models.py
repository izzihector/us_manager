# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritVendorStockPicking(models.Model):
    _inherit = 'vendor.stock.picking'

    def mass_validate_do(self):
        for x in self:
            x.action_validate()

class InheritVendorProduct(models.Model):
    _inherit = 'vendor.product'

    def action_mass_validate(self):
        for x in self:
            x.action_validate()

