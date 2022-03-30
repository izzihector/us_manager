# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritVendorStockPicking(models.Model):
    _inherit = 'vendor.stock.picking'

    def mass_validate_do(self):
        for x in self:
            x.action_fill_and_validate()

class InheritVendorProduct(models.Model):
    _inherit = 'vendor.product'

    def action_mass_validate(self):
        for x in self:
            x.action_validate()

class Wizard(models.Model):
    _name = 'vendor.product.validate.wizard'