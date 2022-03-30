from datetime import datetime

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    brand_id = fields.Many2one(comodel_name="product.brand", string="Brand", related='product_tmpl_id.brand_id',
                               store=True, readonly=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.context.get('from_portal'):
                # create with unique generated code, then replace it with vendor product variant code
                vals.update({
                    'default_code': '{}_{}'.format(vals['product_tmpl_id'], str(datetime.timestamp(datetime.now())))
                })
            else:
                product_tmpl = self.env['product.template'].browse(vals['product_tmpl_id'])
                categ = product_tmpl.categ_id
                vals.update({
                  'default_code': categ.get_product_default_code()
                })
        return super(ProductProduct, self).create(vals_list)

    def name_get(self):
        result = []
        for product in self:
            name = u"[{}] {}".format(
                product.default_code and product.default_code or '',
                product.name and product.name or '',
            )
            if product.product_template_attribute_value_ids:
                name += ' (' + ', '.join(product.product_template_attribute_value_ids.mapped('name')) + ')'
            result.append((product.id, name))
        return result

    def get_current_margin(self):
        vendor_product_id = self.env['vendor.product.variant'].sudo().search([
            ('product_id', '=', self.id),
        ], limit=1)
        if vendor_product_id:
            return vendor_product_id.margin_percentage
        return 0
