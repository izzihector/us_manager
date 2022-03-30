from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    auto_add_tax_amount = fields.Monetary(string="Auto Add WAPU Limit Amount", default=10000000)
    consignment_tax_id = fields.Many2one(comodel_name="account.tax", string="Taxes")
    auto_add_second_tax_amount = fields.Monetary(string="Auto Add PPH 22 Limit Amount", default=10000000)
    consignment_second_tax_id = fields.Many2one(comodel_name="account.tax", string="Taxes")
