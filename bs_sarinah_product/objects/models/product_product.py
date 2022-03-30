# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        vals['active'] = False
        return super(ProductProduct, self).create(vals)

    def write(self, vals):
        if vals.get('active') and not self.env.user.has_group('bs_sarinah_product.group_product_approval'):
            raise ValidationError("Sorry you are not allowed to approve/activate product.")
        return super(ProductProduct, self).write(vals)
