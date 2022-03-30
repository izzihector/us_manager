from odoo import api, fields, models


class VendorProductImage(models.Model):
    _name = 'vendor.product.image'
    _description = 'Images of vendor product'

    name = fields.Char(string='Name')
    image_1920 = fields.Image(string='Image')
    product_id = fields.Many2one(comodel_name='vendor.product', string='Vendor Product')
    sequence = fields.Integer(string='Sequence')

