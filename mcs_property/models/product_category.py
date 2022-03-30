from odoo import models, fields, api
import string
from odoo.exceptions import UserError

class ProductCategory(models.Model):
    _inherit = 'mcs_property.product.category'
    _rec_name = 'complete_name'

    name = fields.Char('Name', index=True, required=True)
    parent_id = fields.Many2one('product.category')
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', store=True)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name