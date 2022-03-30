from odoo import api, fields, models


class ProductBrand(models.Model):
    _inherit = 'product.brand'

    consignment_margin = fields.Float(string="Consignment Margin (%)", required=False)
    margin_ids = fields.One2many(comodel_name='product.brand.margin',
            inverse_name='brand_id', string='Margins')
    

class ProductBrandMargin(models.Model):
    _name = 'product.brand.margin'
    _description = 'Product Brand Margin by Categories'

    brand_id = fields.Many2one(comodel_name='product.brand', string='Brand',
            required=True)
    category_id = fields.Many2one(comodel_name='product.category',
            string='Product Category', required=True)
    consignment_margin = fields.Float(string="Consignment Margin (%)",
            required=True)

    def name_get(self):
        result = []
        for record in self:
            if self._context.get('m2m_tags'):
                margin = record.consignment_margin
                category = record.category_id.display_name
                result.append((record.id, f'{margin}% ({category})'))
            else:
                brand = record.brand_id.display_name
                category = record.category_id.display_name
                result.append((record.id, f'{brand} ({category})'))
        return result

