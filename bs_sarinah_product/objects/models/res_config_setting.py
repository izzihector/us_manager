from odoo import api, fields, models


class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_negative_stock = fields.Boolean(string="Allow Negative Stock",
        help="Allow negative stock levels for the stockable products attached to this company.",
        related="company_id.allow_negative_stock", readonly=False
    )