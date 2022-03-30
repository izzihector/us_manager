from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = 'product.category'

    consignment_margin = fields.Float(string="Consignment Margin (%)", required=False)
    code = fields.Char(string="Code", required=False)
    sequence_padding = fields.Integer(string="Sequence Padding", default=7)
    next_number = fields.Integer(string="Next Number", default=1)
    is_available_on_portal = fields.Boolean(string="Is Available On Portal ",  )

    vendor_product_next_number = fields.Integer(string="Next Number", default=1)
    level = fields.Integer(string="Level", compute='compute_level', store=True)

    def write(self, vals):
        res = super(ProductCategory, self).write(vals)
        # TODO: seharusnya difilter menggunakan child_of, tapi filter dibawah menghasilkan recordset kosong
        # categs = self.env['product.category'].search([('id', 'child_of', self.id)])
        if 'parent_id' in vals:
            categs = self.env['product.category'].search([])
            categs.compute_level()
        return res

    def get_product_default_code(self):
        categ = self.env['product.category'].search([('id', 'parent_of', self.id), ('level', '=', 3)])
        if categ:
            code = categ.code
            padding = categ.sequence_padding
            if code == '':
                raise ValidationError("Please set code for product category {}".format(categ.display_name))
            sequence = str(categ.next_number).zfill(padding)
            categ.next_number += 1
            return code + sequence
        return '/'

    def get_vendor_product_default_code(self):
        categ = self.env['product.category'].search([('id', 'parent_of', self.id), ('level', '=', 3)])
        if categ:
            code = categ.code
            padding = categ.sequence_padding
            if code:
                sequence = str(categ.vendor_product_next_number).zfill(padding)
                categ.vendor_product_next_number += 1
                return code + sequence
        return ''

    @api.depends('parent_id', 'parent_id.parent_id')
    def compute_level(self):
        for rec in self:
            level = 1
            parent = rec.parent_id
            while parent.id != False:
                level += 1
                parent = parent.parent_id
            else:
                rec.level = level
