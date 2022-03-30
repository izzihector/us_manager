from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if not vals.get('default_code') or vals.get('default_code') == '/':
            categ = self.env['product.category'].browse(vals['categ_id'])
            vals.update({
              'default_code': categ.get_product_default_code()
            })
        return super(ProductTemplate, self).create(vals)
