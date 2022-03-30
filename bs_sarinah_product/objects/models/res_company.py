from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    allow_negative_stock = fields.Boolean( string="Allow Negative Stock",
        help="Allow negative stock levels for the stockable products attached to this company."
    )
