from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    denied_purchase = fields.Boolean(string="Denied Purchase")
